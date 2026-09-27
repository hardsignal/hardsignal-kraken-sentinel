"""Offline v1 contract corruption tests, independent of any retained AI artifact."""

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from ai.artifact import canonical_sha256, text_sha256
from ai.evidence_bundle import build_evidence_bundle
from ai.experiment import build_experiment_prompt
from ai.final_report import compose_final_report
from ai.history import load_history_snapshot
from ai.history_report import build_history_report
from ai.history_experiment import build_history_experiment_prompt
from ai.llm_client import EXPECTED_MODEL_DIGEST
from ai.v1_artifact import (
    COMMON_FIELDS, MODE_FIELDS, build_v1_report_artifact, build_v1_history_artifact,
    envelope_sha256, save_v1_artifact, strict_json_loads, validate_v1_artifact, verify_v1_artifact,
)
from scripts.verify_ai_artifact import main

ROOT = Path(__file__).resolve().parents[2]
TARGET = "TPMS-NATURAL-015-20260925-020456"
SUGGESTION = "Repeat the session and measure bearing variability."


def resign(a):
    """Recompute every hash to ensure semantic tests do not just hit a checksum."""
    a["source_record_sha256"] = {key: text_sha256(text) for key, text in a["source_records_json"].items()}
    a["source_record_manifest_sha256"] = canonical_sha256(a["source_record_sha256"])
    for key in ("evidence_bundle", "history_bundle"):
        if key in a:
            a[key + "_sha256"] = canonical_sha256(a[key])
    for key in ("report", "deterministic_report", "history_report", "experiment_prompt", "experiment_suggestion"):
        if key in a:
            a[key + "_sha256"] = text_sha256(a[key])
    a["artifact_sha256"] = envelope_sha256(a)


class V1ArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = self.root / "prospective"
        self.sources.mkdir()
        for path in (ROOT / "results/ml/prospective").glob("TPMS-NATURAL-*.json"):
            shutil.copyfile(path, self.sources / path.name)
        self.bundle = build_evidence_bundle(
            TARGET, ml_results_dir=self.sources, bursts_log=self.root / "bursts.log",
            track_log=self.root / "track.log", episode_log=self.root / "episodes.jsonl",
        )
        normal = build_v1_report_artifact(
            session_id=TARGET, evidence_bundle=self.bundle,
            experiment_prompt=build_experiment_prompt(self.bundle), experiment_suggestion=SUGGESTION,
            report=compose_final_report(self.bundle, SUGGESTION), model_digest=EXPECTED_MODEL_DIGEST,
        )
        snapshot = load_history_snapshot(TARGET, results_dir=self.sources)
        history = build_history_report(TARGET, snapshot=snapshot)
        historical = build_v1_history_artifact(
            target_session_id=TARGET, history_bundle=history["history"], history_report=history["text"],
            experiment_prompt=build_history_experiment_prompt(TARGET, snapshot=snapshot),
            experiment_suggestion=SUGGESTION, model_digest=EXPECTED_MODEL_DIGEST, snapshot=snapshot,
        )
        self.artifacts = {"normal": normal, "history": historical}

    def reject(self, a, *, rehash=True):
        if rehash:
            resign(a)
        with self.assertRaises(ValueError):
            validate_v1_artifact(a)

    def test_both_modes_round_trip_and_current_source_checks(self):
        for mode, a in self.artifacts.items():
            with self.subTest(mode=mode):
                path = save_v1_artifact(a, output_dir=self.root / "output")
                self.assertEqual(verify_v1_artifact(path), a)
                self.assertEqual(verify_v1_artifact(path, source_dir=self.sources), a)
                self.assertEqual(set(a), COMMON_FIELDS | MODE_FIELDS[mode])

    def test_each_required_field_missing(self):
        for mode, original in self.artifacts.items():
            for key in original:
                with self.subTest(mode=mode, field=key):
                    a = copy.deepcopy(original)
                    del a[key]
                    self.reject(a, rehash=False)

    def test_each_top_level_field_wrong_type(self):
        for mode, original in self.artifacts.items():
            for key in original:
                with self.subTest(mode=mode, field=key):
                    a = copy.deepcopy(original)
                    a[key] = []
                    self.reject(a, rehash=False)

    def test_unknown_fields_are_rejected(self):
        for original in self.artifacts.values():
            a = copy.deepcopy(original)
            a["unexpected"] = "value"
            self.reject(a)

    def test_each_internal_hash_corruption_even_with_valid_envelope(self):
        for mode, original in self.artifacts.items():
            for key in original:
                if not key.endswith("_sha256") or key == "source_record_sha256":
                    continue
                with self.subTest(mode=mode, field=key):
                    a = copy.deepcopy(original)
                    a[key] = "0" * 64
                    if key != "artifact_sha256":
                        a["artifact_sha256"] = envelope_sha256(a)
                    self.reject(a, rehash=False)

    def test_model_versions_scope_policy_and_lineage_are_locked(self):
        for mode, original in self.artifacts.items():
            for key in ("artifact_version", "schema_version", "model", "model_digest", "ai_scope",
                        "report_mode", "scientific_policy_version", "derivation_version", "ml_lineage"):
                with self.subTest(mode=mode, field=key):
                    a = copy.deepcopy(original)
                    a[key] = {} if key == "ml_lineage" else "wrong"
                    self.reject(a)

    def test_invalid_timestamp_and_pathlike_session_rejected(self):
        for original in self.artifacts.values():
            for key, value in (("created_at", "2026-09-25"), ("created_at", "bad"),
                               ("created_at", "2026-09-25T00:00:00+01:00"),
                               ("session_id", "../../escape"), ("session_id", "WRONG")):
                with self.subTest(key=key, value=value):
                    a = copy.deepcopy(original)
                    a[key] = value
                    self.reject(a)

    def test_no_014_future_or_duplicate_number_in_history_manifest(self):
        for replacement in ("TPMS-NATURAL-014-20260925-000000", "TPMS-NATURAL-016-20260925-000000",
                            "TPMS-NATURAL-005-20260925-000001"):
            with self.subTest(replacement=replacement):
                a = copy.deepcopy(self.artifacts["history"])
                record = json.loads(a["source_records_json"][TARGET])
                record["session_id"] = replacement
                record["feature_row"]["session_id"] = replacement
                a["source_records_json"][replacement] = json.dumps(record)
                self.reject(a)

    def test_each_missing_prior_source_fails_even_with_rehashed_manifest(self):
        for key in self.artifacts["history"]["source_records_json"]:
            with self.subTest(source=key):
                a = copy.deepcopy(self.artifacts["history"])
                del a["source_records_json"][key]
                self.reject(a)

    def test_normal_manifest_cannot_contain_a_second_source(self):
        a = copy.deepcopy(self.artifacts["normal"])
        other = next(key for key in self.artifacts["history"]["source_records_json"] if key != TARGET)
        a["source_records_json"][other] = self.artifacts["history"]["source_records_json"][other]
        self.reject(a)

    def test_history_derived_values_and_types_are_recomputed(self):
        for key, value in (("target_session_id", "WRONG"), ("prior_formal_session_count", 8),
                           ("formal_session_count_total", 12), ("excluded_session_numbers", []),
                           ("nearest_prior_sessions", []), ("prior_cluster_counts", {}),
                           ("target_cluster", True), ("source_record_manifest_sha256", "0" * 64),
                           ("same_cluster_prior_feature_means", {}), ("target_vs_same_cluster_prior_mean", {})):
            with self.subTest(field=key):
                a = copy.deepcopy(self.artifacts["history"])
                a["history_bundle"][key] = value
                self.reject(a)

    def test_source_record_shapes_identity_lineage_and_numeric_types(self):
        original = self.artifacts["history"]
        for value in (None, [], "text", 5):
            a = copy.deepcopy(original)
            a["source_records_json"][TARGET] = json.dumps(value)
            self.reject(a)
        for key, value in (("session_id", "WRONG"), ("model_version", "9"),
                           ("record_version", "9"), ("training_dataset_sha256", "0" * 64),
                           ("assigned_cluster", True), ("assigned_cluster", 2), ("novelty", "GUESS"),
                           ("feature_row", {}), ("distances", {}), ("nearest_distance", "1"),
                           ("second_nearest_distance", -1), ("scientific_scope", "device identity")):
            with self.subTest(field=key):
                a = copy.deepcopy(original)
                record = json.loads(a["source_records_json"][TARGET])
                record[key] = value
                a["source_records_json"][TARGET] = json.dumps(record)
                self.reject(a)

    def test_source_digest_and_manifest_membership_corruption(self):
        for original in self.artifacts.values():
            for operation in (lambda a: a["source_record_sha256"].pop(TARGET),
                              lambda a: a["source_record_sha256"].update({TARGET: "f" * 64})):
                a = copy.deepcopy(original)
                operation(a)
                a["source_record_manifest_sha256"] = canonical_sha256(a["source_record_sha256"])
                a["artifact_sha256"] = envelope_sha256(a)
                self.reject(a, rehash=False)

    def test_normal_core_ml_and_provenance_cross_field_mismatches(self):
        for mutate in (
            lambda b: b.update(session_id="WRONG"),
            lambda b: b["core"].update(session_id="WRONG"),
            lambda b: b["ml"].update(assigned_cluster=2),
            lambda b: b["provenance"].update(ml_result_sha256="0" * 64),
            lambda b: b["provenance"].update(ml_result_path="other.json"),
            lambda b: b["core"].update(bursts=[]),
            lambda b: b["core"]["bursts"].update(total=True),
            lambda b: b["core"]["bursts"].update(total=999),
            lambda b: b["core"].update(track_events={}),
            lambda b: b["core"].update(episodes={}),
        ):
            a = copy.deepcopy(self.artifacts["normal"])
            mutate(a["evidence_bundle"])
            self.reject(a)

    def test_rehashed_report_prompt_and_unsafe_suggestion_rejected(self):
        for mode, original in self.artifacts.items():
            for field in ("history_report", "deterministic_report", "report", "experiment_prompt", "experiment_suggestion"):
                if field not in original:
                    continue
                with self.subTest(mode=mode, field=field):
                    a = copy.deepcopy(original)
                    a[field] = "Repeat the capture. This is device ABC123."
                    self.reject(a)

    def test_historical_comparison_rejected_only_in_normal_artifact(self):
        text = "Compare these proportions to the prior session's values."
        normal = copy.deepcopy(self.artifacts["normal"])
        normal["experiment_suggestion"] = text
        normal["report"] = compose_final_report(normal["evidence_bundle"], text)
        resign(normal)
        with self.assertRaisesRegex(ValueError, "historical comparison unavailable"):
            validate_v1_artifact(normal)
        historical = copy.deepcopy(self.artifacts["history"])
        historical["experiment_suggestion"] = "Repeat and compare with the prior C1 mean."
        resign(historical)
        validate_v1_artifact(historical)

    def test_source_changes_require_explicit_current_file_check(self):
        for a in self.artifacts.values():
            validate_v1_artifact(a)
        path = self.sources / f"{TARGET}.json"
        path.write_bytes(path.read_bytes() + b"\n")
        for a in self.artifacts.values():
            validate_v1_artifact(a)  # Self-contained snapshot remains valid.
            with self.assertRaisesRegex(ValueError, "current source SHA256 mismatch"):
                validate_v1_artifact(a, source_dir=self.sources)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            validate_v1_artifact(self.artifacts["normal"], source_dir=self.sources)

    def test_005_and_irrelevant_future_files(self):
        first = sorted(self.artifacts["history"]["source_records_json"])[0]
        snapshot = load_history_snapshot(first, results_dir=self.sources)
        report = build_history_report(first, snapshot=snapshot)
        a = build_v1_history_artifact(
            target_session_id=first, history_bundle=report["history"], history_report=report["text"],
            experiment_prompt=build_history_experiment_prompt(first, snapshot=snapshot),
            experiment_suggestion=SUGGESTION, model_digest=EXPECTED_MODEL_DIGEST, snapshot=snapshot,
        )
        self.assertEqual(set(a["source_record_sha256"]), {first})
        for path in self.sources.glob("*.json"):
            if path.stem != first:
                path.write_bytes(b"invalid future/excluded bytes")
        validate_v1_artifact(a, source_dir=self.sources)

    def test_strict_json_rejects_duplicates_nonfinite_and_nonobjects(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                strict_json_loads(text)
        for value in (None, [], "artifact", 123):
            with self.assertRaises(ValueError):
                validate_v1_artifact(value)
        a = copy.deepcopy(self.artifacts["normal"])
        a["source_records_json"][TARGET] = '{"session_id":"x","session_id":"y"}'
        self.reject(a)

    def test_generic_cli_is_read_only_offline_and_has_controlled_failures(self):
        path = save_v1_artifact(self.artifacts["normal"], output_dir=self.root / "out")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch("ai.llm_client.request.urlopen", side_effect=AssertionError("network")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([str(path), "--source-dir", str(self.sources)]), 0)
        self.assertIn("embedded + current sources", output.getvalue())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        for data in (b"{", b"[]", b"null", b"\xff", b'{"mode":[]}'):
            path.write_bytes(data)
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(main([str(path)]), 1)
            self.assertNotIn("Traceback", error.getvalue())

    def test_normal_cli_save_uses_v1_contract(self):
        from ai import cli
        with patch("ai.cli.build_evidence_bundle", return_value=self.bundle), \
             patch("ai.cli.verify_model_digest", return_value=EXPECTED_MODEL_DIGEST), \
             patch("ai.cli.suggest_experiment_from_prompt", return_value=SUGGESTION), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["--session", TARGET, "--save", "--output-dir", str(self.root / "cli")]), 0)
        paths = list((self.root / "cli").rglob("*.json"))
        self.assertEqual(len(paths), 1)
        artifact = verify_v1_artifact(paths[0], source_dir=self.sources)
        self.assertEqual(artifact["mode"], "normal")
        self.assertEqual(artifact["artifact_version"], "1.0")

    def test_published_schema_matches_executable_envelope(self):
        schema = json.loads((ROOT / "docs/sentinel-ai-artifact-v1.schema.json").read_text())
        for branch in schema["oneOf"]:
            mode = branch["properties"]["mode"]["const"]
            self.assertEqual(set(branch["required"]), COMMON_FIELDS | MODE_FIELDS[mode])
            self.assertEqual(set(branch["properties"]), set(branch["required"]))
            self.assertFalse(branch["additionalProperties"])
            for key, spec in branch["properties"].items():
                if "const" in spec:
                    self.assertEqual(self.artifacts[mode][key], spec["const"])

    def test_source_symlink_cannot_escape_explicit_directory(self):
        path = self.sources / f"{TARGET}.json"
        outside = self.root / "outside.json"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "escapes"):
            validate_v1_artifact(self.artifacts["normal"], source_dir=self.sources)

    def test_legacy_artifact_not_silently_upgraded(self):
        a = copy.deepcopy(self.artifacts["normal"])
        a["artifact_version"] = "0.1"
        self.reject(a)

    def test_normal_capture_and_v1_build_do_not_reread_ml(self):
        # Bundle already contains the exact bytes parsed during evidence capture.
        (self.sources / f"{TARGET}.json").write_bytes(b"changed after capture")
        with patch.object(Path, "open", side_effect=AssertionError("unexpected source read")):
            artifact = build_v1_report_artifact(
                session_id=TARGET, evidence_bundle=self.bundle,
                experiment_prompt=build_experiment_prompt(self.bundle), experiment_suggestion=SUGGESTION,
                report=compose_final_report(self.bundle, SUGGESTION), model_digest=EXPECTED_MODEL_DIGEST,
            )
        self.assertEqual(artifact["source_record_sha256"], self.artifacts["normal"]["source_record_sha256"])


if __name__ == "__main__":
    unittest.main()
