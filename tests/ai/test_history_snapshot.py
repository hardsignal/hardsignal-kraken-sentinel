"""Snapshot consistency through the real historical CLI and artifact path."""

from collections import Counter
import contextlib
from dataclasses import FrozenInstanceError
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai import cli
from ai.llm_client import EXPECTED_MODEL_DIGEST
from ai.v1_artifact import TRAINING_SHA256
from ai.artifact import canonical_sha256
from ai.history import HISTORY_FEATURES, build_history_bundle, load_history_snapshot
from ai.history_artifact import (
    build_history_artifact, build_source_record_hashes, save_history_artifact,
)
from ai.history_experiment import build_history_experiment_prompt
from ai.history_report import build_history_report


PREFIX = (5, 6, 7, 8, 9, 10, 11, 12, 13, 15)


def identity(number):
    return f"TPMS-NATURAL-{number:03d}-20260925-000000"


class HistorySnapshotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = identity(15)
        self.original = {}
        for number in PREFIX:
            record = {
                "session_id": identity(number),
                "assigned_cluster": 1,
                "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
                "feature_row": {**{key: float(number) for key in HISTORY_FEATURES},
                                "session_id": identity(number), "burst_count": number},
                "model_version": "0.1", "record_version": "0.1",
                "training_dataset_sha256": TRAINING_SHA256,
                "scientific_scope": "RF/DoA behavioural regime assignment; not transmitter identity",
                "distances": {"0": 4.0, "1": 1.0, "2": 3.0},
                "nearest_distance": 1.0, "second_nearest_distance": 3.0,
                "separation_ratio": 3.0, "distance_vs_training_max": 0.5,
                "extra": ["retained", {"note": "évidence"}],
            }
            # Deliberately noncanonical formatting: provenance must hash raw bytes.
            data = (json.dumps(record, indent=3, ensure_ascii=False) + "\n\n").encode("utf-8")
            self.original[identity(number)] = data
            (self.root / f"{identity(number)}.json").write_bytes(data)
        for number in (14, 16, 17):
            (self.root / f"{identity(number)}.json").write_bytes(b"invalid excluded/future JSON")

    def snapshot(self):
        return load_history_snapshot(self.target, results_dir=self.root)

    def projection(self, snapshot):
        report = build_history_report(self.target, snapshot=snapshot)
        prompt = build_history_experiment_prompt(self.target, snapshot=snapshot)
        artifact = build_history_artifact(
            target_session_id=self.target,
            history_bundle=report["history"], history_report=report["text"],
            experiment_prompt=prompt, experiment_suggestion="Repeat and measure.",
            model_digest="offline", snapshot=snapshot,
        )
        artifact.pop("created_at")
        return report, prompt, artifact

    def test_cli_reads_each_eligible_source_once_even_when_disk_changes_during_generation(self):
        counts = Counter()
        original_open = Path.open
        snapshots = []

        def counted_open(path, mode="r", *args, **kwargs):
            if path.parent == self.root and path.suffix == ".json":
                self.assertIn(path.stem, self.original, "excluded/future file was opened")
                if mode == "rb":
                    counts[path.stem] += 1
            return original_open(path, mode, *args, **kwargs)

        def capture_snapshot(target):
            snapshot = load_history_snapshot(target, results_dir=self.root)
            snapshots.append(snapshot)
            return snapshot

        def generate(prompt):
            (self.root / f"{identity(5)}.json").write_bytes(b"changed after snapshot")
            return "Repeat the session and measure bearing variability."

        with (
            patch.object(Path, "open", counted_open),
            patch("ai.cli.load_history_snapshot", side_effect=capture_snapshot),
            patch("ai.cli.verify_model_digest", return_value=EXPECTED_MODEL_DIGEST),
            patch("ai.history_experiment.generate_text", side_effect=generate),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            status = cli.main([
                "--session", self.target, "--history", "--save",
                "--output-dir", str(self.root / "output"),
            ])
        self.assertEqual(status, 0)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(counts, Counter({key: 1 for key in self.original}))
        saved = list((self.root / "output").rglob("*.json"))
        self.assertEqual(len(saved), 1)
        artifact = json.loads(saved[0].read_text(encoding="utf-8"))
        report, prompt, expected = self.projection(snapshots[0])
        self.assertEqual(artifact["history_bundle"], report["history"])
        self.assertEqual(artifact["history_report"], report["text"])
        self.assertEqual(artifact["experiment_prompt"], prompt)
        self.assertEqual(artifact["source_record_sha256"], expected["source_record_sha256"])
        # The existing raw-byte comparison detects external mutation; no new
        # generic artifact verifier or historical verifier changes are needed.
        current = hashlib.sha256((self.root / f"{identity(5)}.json").read_bytes()).hexdigest()
        self.assertNotEqual(artifact["source_record_sha256"][identity(5)], current)

    def test_snapshot_parses_and_hashes_the_same_exact_bytes(self):
        snapshot = self.snapshot()
        self.assertEqual(dict(snapshot.sources), self.original)
        for record in snapshot.records:
            source = self.original[record["session_id"]]
            expected = json.loads(source)
            self.assertEqual(dict(record["feature_row"]), expected["feature_row"])
            self.assertEqual(record["extra"][1]["note"], expected["extra"][1]["note"])
        expected_hashes = {key: hashlib.sha256(data).hexdigest() for key, data in self.original.items()}
        self.assertEqual(snapshot.source_record_sha256, expected_hashes)
        self.assertEqual(snapshot.source_record_manifest_sha256, canonical_sha256(expected_hashes))
        self.assertEqual(set(expected_hashes), {identity(n) for n in PREFIX})

    def test_mutation_after_capture_cannot_change_any_projection(self):
        snapshot = self.snapshot()
        before = self.projection(snapshot)
        for key in self.original:
            (self.root / f"{key}.json").write_bytes(b"not JSON anymore")
        with patch.object(Path, "open", side_effect=AssertionError("unexpected filesystem read")):
            self.assertEqual(before, self.projection(snapshot))
            self.assertEqual(build_history_bundle(self.target, snapshot=snapshot), before[0]["history"])
            self.assertEqual(build_source_record_hashes(self.target, snapshot=snapshot),
                             before[2]["source_record_sha256"])

    def test_snapshot_is_deeply_immutable(self):
        snapshot = self.snapshot()
        with self.assertRaises(FrozenInstanceError):
            snapshot.target_session_id = identity(5)
        with self.assertRaises(TypeError):
            snapshot.records[0]["feature_row"]["burst_count"] = 999
        with self.assertRaises(TypeError):
            snapshot.records[0]["extra"][1]["note"] = "changed"
        hashes = snapshot.source_record_sha256
        hashes.clear()
        self.assertEqual(len(snapshot.source_record_sha256), 10)

    def test_stale_bundle_rejected_even_when_only_source_whitespace_changed(self):
        old = self.snapshot()
        report, prompt, _ = self.projection(old)
        path = self.root / f"{identity(5)}.json"
        path.write_bytes(self.original[identity(5)] + b"\n")
        new = self.snapshot()
        with self.assertRaisesRegex(ValueError, "bundle does not match evidence snapshot"):
            build_history_artifact(
                target_session_id=self.target,
                history_bundle=report["history"], history_report=report["text"],
                experiment_prompt=prompt, experiment_suggestion="Repeat and measure.",
                model_digest="offline", snapshot=new,
            )

    def test_artifact_requires_snapshot_and_never_silently_reloads(self):
        report, prompt, _ = self.projection(self.snapshot())
        with patch.object(Path, "open", side_effect=AssertionError("unexpected reload")):
            with self.assertRaisesRegex(ValueError, "snapshot is required"):
                build_history_artifact(
                    target_session_id=self.target,
                    history_bundle=report["history"], history_report=report["text"],
                    experiment_prompt=prompt, experiment_suggestion="Repeat and measure.",
                    model_digest="offline", results_dir=self.root,
                )

    def test_artifact_rejects_changed_report_and_prompt(self):
        snapshot = self.snapshot()
        report, prompt, _ = self.projection(snapshot)
        for field in ("history_report", "experiment_prompt"):
            with self.subTest(field=field):
                values = dict(
                    target_session_id=self.target, history_bundle=report["history"],
                    history_report=report["text"], experiment_prompt=prompt,
                    experiment_suggestion="Repeat and measure.", model_digest="offline", snapshot=snapshot,
                )
                values[field] += " stale"
                with self.assertRaisesRegex(ValueError, "does not match evidence snapshot"):
                    build_history_artifact(**values)

    def test_005_single_record_snapshot_and_artifact_round_trip(self):
        self.target = identity(5)
        snapshot = self.snapshot()
        self.assertEqual(len(snapshot.records), 1)
        report, _, artifact = self.projection(snapshot)
        self.assertEqual(report["history"]["prior_formal_session_count"], 0)
        self.assertEqual(report["history"]["nearest_prior_sessions"], [])
        self.assertEqual(set(artifact["source_record_sha256"]), {self.target})
        artifact["created_at"] = "2026-09-25T00:00:00+00:00"
        path = save_history_artifact(artifact, output_dir=self.root / "output")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), artifact)

    def test_artifact_does_not_alias_callers_bundle(self):
        snapshot = self.snapshot()
        report = build_history_report(self.target, snapshot=snapshot)
        artifact = build_history_artifact(
            target_session_id=self.target, history_bundle=report["history"],
            history_report=report["text"],
            experiment_prompt=build_history_experiment_prompt(self.target, snapshot=snapshot),
            experiment_suggestion="Repeat and measure.", model_digest="offline", snapshot=snapshot,
        )
        report["history"]["prior_cluster_counts"].clear()
        self.assertEqual(artifact["history_bundle"]["prior_cluster_counts"], {"1": 9})


if __name__ == "__main__":
    unittest.main()
