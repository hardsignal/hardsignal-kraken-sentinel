"""Offline tests for the complete formal prefix shared by history and provenance."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai.history import HISTORY_FEATURES, build_history_bundle
from ai.history_artifact import build_history_artifact, build_source_record_hashes
from ai.history import load_history_snapshot
from ai.history_report import build_history_report
from ai.history_experiment import build_history_experiment_prompt


PREFIX_015 = (5, 6, 7, 8, 9, 10, 11, 12, 13, 15)


def session_id(number):
    return f"TPMS-NATURAL-{number:03d}-20260925-000000"


class HistoryCompletenessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = session_id(15)
        for number in PREFIX_015:
            self.write(number)

    def write(self, number):
        path = self.root / f"{session_id(number)}.json"
        path.write_text(json.dumps({
            "session_id": session_id(number),
            "assigned_cluster": 1,
            "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
            "feature_row": {key: float(number) for key in HISTORY_FEATURES},
        }), encoding="utf-8")
        return path

    def history(self):
        return build_history_bundle(self.target, results_dir=self.root)

    def manifest(self):
        return build_source_record_hashes(self.target, results_dir=self.root)

    def artifact(self):
        snapshot = load_history_snapshot(self.target, results_dir=self.root)
        report = build_history_report(self.target, snapshot=snapshot)
        return build_history_artifact(
            target_session_id=self.target,
            history_bundle=report["history"],
            history_report=report["text"],
            experiment_prompt=build_history_experiment_prompt(self.target, snapshot=snapshot),
            experiment_suggestion="Repeat and measure.", model_digest="offline",
            snapshot=snapshot,
        )

    def assert_rejected(self, message):
        for operation in (self.history, self.manifest, self.artifact):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, message):
                    operation()

    def test_complete_015_prefix_and_exact_source_manifest(self):
        history = self.history()
        self.assertEqual(history["formal_session_count_total"], 10)
        self.assertEqual(history["prior_formal_session_count"], 9)
        expected = {
            session_id(number): hashlib.sha256(
                (self.root / f"{session_id(number)}.json").read_bytes()
            ).hexdigest()
            for number in PREFIX_015
        }
        self.assertEqual(self.manifest(), expected)
        self.assertEqual(self.artifact()["source_record_sha256"], expected)

    def test_each_missing_required_prior_fails_before_provenance_hashing(self):
        for number in PREFIX_015[:-1]:
            with self.subTest(missing=number):
                path = self.root / f"{session_id(number)}.json"
                original = path.read_bytes()
                path.unlink()
                try:
                    with patch("ai.history_artifact.sha256_file") as hash_file:
                        self.assert_rejected(
                            f"incomplete formal session prefix; missing required sessions: {number:03d}$"
                        )
                    hash_file.assert_not_called()
                finally:
                    path.write_bytes(original)

    def test_missing_014_does_not_change_history_or_manifest(self):
        excluded = self.write(14)
        before = self.history(), self.manifest()
        excluded.unlink()
        self.assertEqual(before, (self.history(), self.manifest()))
        self.assertNotIn(session_id(14), before[1])

    def test_005_alone_passes_with_target_only_manifest(self):
        for number in PREFIX_015[1:]:
            (self.root / f"{session_id(number)}.json").unlink()
        self.target = session_id(5)
        history = self.history()
        self.assertEqual(history["formal_session_count_total"], 1)
        self.assertEqual(history["prior_formal_session_count"], 0)
        self.assertEqual(history["nearest_prior_sessions"], [])
        self.assertEqual(set(self.manifest()), {self.target})
        self.assertEqual(self.artifact()["source_record_sha256"], self.manifest())

    def test_future_additions_do_not_change_015_or_source_manifest(self):
        before = self.history(), self.manifest()
        for number in (16, 17, 18):
            self.write(number)
        self.assertEqual(before, (self.history(), self.manifest()))
        self.assertEqual(self.artifact()["source_record_sha256"], before[1])

    def test_identity_integrity_checked_before_completeness(self):
        (self.root / f"{session_id(5)}.json").unlink()
        path = self.root / f"{session_id(13)}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["session_id"] = session_id(12)
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assert_rejected("filename/session_id mismatch")

    def test_duplicate_identity_checked_before_completeness(self):
        (self.root / f"{session_id(5)}.json").unlink()
        identity = "TPMS-NATURAL-013-20260925-000001"
        (self.root / f"{identity}.json").write_text(
            json.dumps({"session_id": identity}), encoding="utf-8",
        )
        self.assert_rejected("duplicate formal session identity: 013")

    def test_multiple_missing_sessions_have_sorted_diagnostic(self):
        for number in (13, 5, 9):
            (self.root / f"{session_id(number)}.json").unlink()
        self.assert_rejected("missing required sessions: 005, 009, 013$")


if __name__ == "__main__":
    unittest.main()
