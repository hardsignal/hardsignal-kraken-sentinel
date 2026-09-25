import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ai.artifact import (
    build_report_artifact,
    save_report_artifact,
)


class ArtifactTests(unittest.TestCase):
    def test_artifact_records_hybrid_provenance(self):
        bundle = {
            "ml": {
                "assigned_cluster": 1,
                "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
                "training_dataset_sha256": "dataset123",
            },
            "provenance": {
                "ml_result_sha256": "ml123",
            },
        }

        artifact = build_report_artifact(
            session_id="TEST",
            evidence_bundle=bundle,
            experiment_prompt="PROMPT",
            experiment_suggestion="Repeat and measure.",
            report="REPORT",
            model_digest="digest123",
        )

        self.assertEqual(
            artifact["report_mode"],
            "deterministic_with_ai_experiment",
        )
        self.assertEqual(
            artifact["ai_scope"],
            "next_controlled_experiment_only",
        )
        self.assertEqual(
            artifact["model_digest"],
            "digest123",
        )
        self.assertEqual(
            artifact["experiment_suggestion"],
            "Repeat and measure.",
        )

        self.assertEqual(
            artifact["experiment_suggestion_sha256"],
            hashlib.sha256(
                b"Repeat and measure."
            ).hexdigest(),
        )

    def test_saved_artifact_round_trips(self):
        bundle = {
            "ml": {
                "assigned_cluster": 1,
                "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
                "training_dataset_sha256": "dataset123",
            },
            "provenance": {
                "ml_result_sha256": "ml123",
            },
        }

        artifact = build_report_artifact(
            session_id="TEST",
            evidence_bundle=bundle,
            experiment_prompt="PROMPT",
            experiment_suggestion="Repeat and measure.",
            report="REPORT",
            model_digest="digest123",
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = save_report_artifact(
                artifact,
                output_dir=Path(tmp),
            )

            loaded = json.loads(
                path.read_text(encoding="utf-8")
            )

        self.assertEqual(loaded, artifact)


if __name__ == "__main__":
    unittest.main()
