import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import pandas as pd

import ml.prospective_session as ps


class ProspectiveSessionTests(unittest.TestCase):

    def test_frozen_score_reproduces_known_session(self):
        model = joblib.load(
            "results/ml/sentinel_behaviour_model_v001.joblib"
        )

        data = pd.read_csv(
            "results/ml/rf_behaviour_dataset_prospective_v001.csv"
        )

        row = data[
            data["session_id"]
            == "TPMS-PROSPECTIVE-001-20260925-002112"
        ].iloc[0].to_dict()

        score = ps.score_row(row, model)

        self.assertEqual(
            score["assigned_cluster"],
            1,
        )

        self.assertAlmostEqual(
            score["nearest_distance"],
            2.20606214962942,
            places=8,
        )

        self.assertAlmostEqual(
            score["second_nearest_distance"],
            3.630411766486711,
            places=8,
        )

        self.assertEqual(
            score["novelty"],
            "WITHIN_OBSERVED_TRAINING_RANGE",
        )

    def test_duplicate_guard_detects_existing_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.csv"

            with ledger.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=ps.LEDGER_COLUMNS,
                )

                writer.writeheader()

                writer.writerow({
                    "time": "2026-09-25T00:00:00+01:00",
                    "session_id": "TEST-SESSION",
                    "model_version": "0.1",
                    "training_dataset_sha256": "abc",
                    "assigned_cluster": "1",
                    "nearest_distance": "1.0",
                    "second_nearest_distance": "2.0",
                    "separation_ratio": "2.0",
                    "distance_vs_training_max": "0.5",
                    "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
                })

            with patch.object(
                ps,
                "LEDGER_PATH",
                ledger,
            ):
                with self.assertRaises(RuntimeError):
                    ps.assert_session_not_recorded(
                        "TEST-SESSION"
                    )

                ps.assert_session_not_recorded(
                    "NEW-SESSION"
                )


if __name__ == "__main__":
    unittest.main()
