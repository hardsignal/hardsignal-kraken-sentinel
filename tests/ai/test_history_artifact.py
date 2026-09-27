import json
from pathlib import Path
import tempfile
import unittest

from ai.history import HISTORY_FEATURES, load_history_snapshot
from ai.history_report import build_history_report
from ai.history_experiment import build_history_experiment_prompt

from ai.history_artifact import (
    build_history_artifact,
    build_source_record_hashes,
    save_history_artifact,
)


def write_record(root, number):
    session_id = f"TPMS-NATURAL-{number:03d}-20260925-000000"

    record = {
        "session_id": session_id,
        "assigned_cluster": 1,
        "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
        "feature_row": {key: float(number) for key in HISTORY_FEATURES},
    }

    path = root / f"{session_id}.json"
    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )

    return session_id


class HistoryArtifactTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        self.root = Path(tmp.name)

        for number in (
            5, 6, 7, 8, 9, 10,
            11, 12, 13, 14, 15, 16, 17,
        ):
            write_record(self.root, number)

        self.target = "TPMS-NATURAL-015-20260925-000000"

    def artifact(self):
        snapshot = load_history_snapshot(self.target, results_dir=self.root)
        report = build_history_report(self.target, snapshot=snapshot)
        return build_history_artifact(
            target_session_id=self.target,
            history_bundle=report["history"], history_report=report["text"],
            experiment_prompt=build_history_experiment_prompt(self.target, snapshot=snapshot),
            experiment_suggestion="Repeat and measure.", model_digest="digest123",
            snapshot=snapshot,
        )

    def test_source_manifest_is_prior_only_plus_target(self):
        hashes = build_source_record_hashes(
            self.target,
            results_dir=self.root,
        )

        self.assertEqual(len(hashes), 10)

        self.assertNotIn(
            "TPMS-NATURAL-014-20260925-000000",
            hashes,
        )
        self.assertNotIn(
            "TPMS-NATURAL-016-20260925-000000",
            hashes,
        )
        self.assertNotIn(
            "TPMS-NATURAL-017-20260925-000000",
            hashes,
        )
        self.assertIn(self.target, hashes)

    def test_artifact_records_v02_scope(self):
        artifact = self.artifact()

        self.assertEqual(
            artifact["artifact_version"],
            "0.2",
        )
        self.assertEqual(
            artifact["report_mode"],
            "deterministic_history_with_ai_experiment",
        )
        self.assertEqual(
            artifact["ai_scope"],
            "historical_next_controlled_experiment_only",
        )
        self.assertEqual(
            artifact["model_digest"],
            "digest123",
        )

    def test_history_target_mismatch_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "history target_session_id mismatch",
        ):
            build_history_artifact(
                target_session_id=self.target,
                history_bundle={
                    "target_session_id": "WRONG",
                },
                history_report="HISTORY",
                experiment_prompt="PROMPT",
                experiment_suggestion="Repeat and measure.",
                model_digest="digest123",
                results_dir=self.root,
            )

    def test_saved_history_artifact_round_trips(self):
        artifact = self.artifact()

        with tempfile.TemporaryDirectory() as tmp:
            path = save_history_artifact(
                artifact,
                output_dir=Path(tmp),
            )

            loaded = json.loads(
                path.read_text(encoding="utf-8")
            )

        self.assertEqual(loaded, artifact)


if __name__ == "__main__":
    unittest.main()
