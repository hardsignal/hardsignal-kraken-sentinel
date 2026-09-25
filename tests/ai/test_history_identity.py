"""Offline identity checks shared by history and artifact provenance."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai.history import HISTORY_FEATURES, build_history_bundle, load_formal_history
from ai.history_artifact import build_history_artifact, build_source_record_hashes


class HistoryIdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = "TPMS-NATURAL-005-20260925-005143"
        self.path = self.root / f"{self.target}.json"
        self.record = {
            "session_id": self.target,
            "assigned_cluster": 1,
            "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
            "feature_row": {},
        }
        self.write(self.record)

    def write(self, record):
        self.path.write_text(json.dumps(record), encoding="utf-8")

    def artifact(self):
        return build_history_artifact(
            target_session_id=self.target,
            history_bundle={"target_session_id": self.target},
            history_report="HISTORY", experiment_prompt="PROMPT",
            experiment_suggestion="Repeat and measure.", model_digest="offline",
            results_dir=self.root,
        )

    def assert_rejected(self, message):
        for operation in (
            lambda: load_formal_history(self.root),
            lambda: build_history_bundle(self.target, results_dir=self.root),
            lambda: build_source_record_hashes(self.target, results_dir=self.root),
            self.artifact,
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, message):
                    operation()

    def test_exact_identity_and_005_without_prior_pass(self):
        self.assertEqual(load_formal_history(self.root), [self.record])
        history = build_history_bundle(self.target, results_dir=self.root)
        self.assertEqual(history["prior_formal_session_count"], 0)
        self.assertEqual(history["nearest_prior_sessions"], [])
        expected = {self.target: hashlib.sha256(self.path.read_bytes()).hexdigest()}
        self.assertEqual(self.artifact()["source_record_sha256"], expected)

    def test_number_and_timestamp_mismatches_fail(self):
        for identity in ("TPMS-NATURAL-006-20260925-005143",
                         "TPMS-NATURAL-005-20260925-005144"):
            with self.subTest(identity=identity):
                self.write(dict(self.record, session_id=identity))
                self.assert_rejected("filename/session_id mismatch")

    def test_missing_session_id_fails(self):
        record = dict(self.record)
        del record["session_id"]
        self.write(record)
        self.assert_rejected("unsupported natural session id")

    def test_nonstring_session_id_fails(self):
        for identity in (None, 5, True, [], {}):
            with self.subTest(identity=identity):
                self.write(dict(self.record, session_id=identity))
                self.assert_rejected("unsupported natural session id")

    def test_malformed_session_id_fails(self):
        for identity in ("", "OTHER-005", "TPMS-NATURAL-005-",
                         self.target + "-extra", self.target + "\n",
                         "TPMS-NATURAL-5-20260925-005143",
                         "TPMS-NATURAL-005-20260230-005143",
                         "TPMS-NATURAL-005-20260925-250000"):
            with self.subTest(identity=identity):
                self.write(dict(self.record, session_id=identity))
                self.assert_rejected(".")

    def test_matching_but_malformed_filename_and_id_fail(self):
        self.path.unlink()
        self.target = "TPMS-NATURAL-005-20260925-005143-extra"
        self.path = self.root / f"{self.target}.json"
        self.write(dict(self.record, session_id=self.target))
        self.assert_rejected("unsupported natural session id")

    def test_duplicate_formal_number_with_distinct_timestamps_fails(self):
        identity = "TPMS-NATURAL-005-20260925-005144"
        (self.root / f"{identity}.json").write_text(
            json.dumps(dict(self.record, session_id=identity)), encoding="utf-8",
        )
        self.assert_rejected("duplicate formal session identity: 005")

    def test_duplicate_payload_identity_under_another_filename_fails(self):
        (self.root / "TPMS-NATURAL-005-20260925-005144.json").write_text(
            json.dumps(self.record), encoding="utf-8",
        )
        self.assert_rejected("filename/session_id mismatch")

    def test_nonobject_record_fails(self):
        for record in (None, [], "session"):
            with self.subTest(record=record):
                self.write(record)
                self.assert_rejected("historical record must be a JSON object")

    def test_014_cannot_supply_identity_or_provenance(self):
        self.path.unlink()
        excluded = self.root / "TPMS-NATURAL-014-20260925-020102.json"
        self.target = "TPMS-NATURAL-015-20260925-020456"
        excluded.write_text(json.dumps(dict(self.record, session_id=self.target)))
        self.assertEqual(load_formal_history(self.root), [])
        with self.assertRaisesRegex(ValueError, "not in the formal prospective set"):
            self.artifact()

    def test_future_bad_id_corruption_and_bad_suffix_are_not_opened(self):
        self.path.unlink()
        self.target = "TPMS-NATURAL-015-20260925-020456"
        self.path = self.root / f"{self.target}.json"
        self.write(dict(self.record, session_id=self.target,
                        feature_row={key: 15.0 for key in HISTORY_FEATURES}))
        for number in range(5, 14):
            identity = f"TPMS-NATURAL-{number:03d}-20260925-000000"
            (self.root / f"{identity}.json").write_text(json.dumps(dict(
                self.record, session_id=identity,
                feature_row={key: float(number) for key in HISTORY_FEATURES},
            )), encoding="utf-8")
        before = self.artifact()
        before.pop("created_at")
        paths = [self.root / f"TPMS-NATURAL-{n}-20260925-020743.json"
                 for n in ("016", "017")]
        paths.append(self.root / "TPMS-NATURAL-018-malformed.json")
        paths[0].write_text(json.dumps(self.record), encoding="utf-8")
        paths[1].write_bytes(b"{")
        paths[2].write_bytes(b"\xff")
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            if path in paths:
                self.fail(f"future source opened: {path}")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            after = self.artifact()
            after.pop("created_at")
            self.assertEqual(before, after)
            history = build_history_bundle(self.target, results_dir=self.root)
            self.assertEqual(history["formal_session_count_total"], 10)

    def test_provenance_rejects_identity_change_before_hashing(self):
        self.write(dict(self.record, session_id="TPMS-NATURAL-006-20260925-005606"))
        with patch("ai.history_artifact.sha256_file") as hash_file:
            with self.assertRaisesRegex(ValueError, "filename/session_id mismatch"):
                self.artifact()
        hash_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
