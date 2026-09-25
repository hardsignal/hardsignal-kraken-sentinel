import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai.evidence_bundle import build_evidence_bundle, load_ml_result
from ai.schemas import validate_evidence_bundle


SESSION = "TEST-SESSION-001"


def core_summary(session_id=SESSION):
    return {
        "version": 1,
        "session_id": session_id,
        "bursts": {
            "total": 3,
            "STABLE": 3,
            "MULTIPATH": 0,
            "LOW_QUALITY": 0,
        },
        "track_events": {},
        "episodes": {},
        "missing_logs": [],
    }


def ml_record(session_id=SESSION):
    return {
        "session_id": session_id,
        "model_version": "0.1",
        "record_version": "0.1",
        "assigned_cluster": 1,
        "distances": {"0": 4.0, "1": 1.0, "2": 3.0},
        "nearest_distance": 1.0,
        "second_nearest_distance": 3.0,
        "separation_ratio": 3.0,
        "distance_vs_training_max": 0.5,
        "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
        "scientific_scope": "RF/DoA behavioural regime assignment; not transmitter identity",
        "feature_row": {"session_id": session_id},
        "training_dataset_sha256": "abc123",
    }


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.ml_dir = self.root / "prospective"
        self.ml_dir.mkdir()

    def write_ml(self, record=None):
        record = record or ml_record()
        path = self.ml_dir / f"{SESSION}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_build_bundle_binds_core_and_ml_evidence(self):
        ml_path = self.write_ml()

        with patch(
            "ai.evidence_bundle.build_core_session_summary",
            return_value=core_summary(),
        ):
            bundle = build_evidence_bundle(
                SESSION,
                bursts_log=self.root / "bursts.log",
                track_log=self.root / "track.log",
                episode_log=self.root / "episodes.jsonl",
                ml_results_dir=self.ml_dir,
            )

        self.assertEqual(bundle["schema_version"], "0.1")
        self.assertEqual(bundle["session_id"], SESSION)
        self.assertEqual(bundle["core"]["session_id"], SESSION)
        self.assertEqual(bundle["ml"]["session_id"], SESSION)

        expected = hashlib.sha256(ml_path.read_bytes()).hexdigest()
        self.assertEqual(
            bundle["provenance"]["ml_result_sha256"],
            expected,
        )

    def test_missing_ml_result_fails(self):
        with self.assertRaises(FileNotFoundError):
            load_ml_result(SESSION, self.ml_dir)

    def test_ml_session_mismatch_fails(self):
        self.write_ml(ml_record("WRONG-SESSION"))

        with self.assertRaisesRegex(ValueError, "ML result session_id mismatch"):
            load_ml_result(SESSION, self.ml_dir)

    def test_core_session_mismatch_fails(self):
        path = self.write_ml()

        bundle = {
            "schema_version": "0.1",
            "session_id": SESSION,
            "core": core_summary("WRONG-SESSION"),
            "ml": ml_record(),
            "provenance": {
                "ml_result_path": str(path),
                "ml_result_sha256": hashlib.sha256(
                    path.read_bytes()
                ).hexdigest(),
            },
        }

        with self.assertRaisesRegex(ValueError, "Core session_id"):
            validate_evidence_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
