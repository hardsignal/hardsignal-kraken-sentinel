import json
from pathlib import Path
import tempfile
import unittest

from ai.history_report import build_history_report


def record(number, cluster=1):
    session_id = f"TPMS-NATURAL-{number:03d}-20260925-000000"

    return {
        "session_id": session_id,
        "assigned_cluster": cluster,
        "novelty": "WITHIN_OBSERVED_TRAINING_RANGE",
        "feature_row": {
            "bearing_circular_std_deg": float(number),
            "peak_power_mean_db": -20.0 - number,
            "median_confidence_mean": 3.0 + number / 100,
            "doa_width_mean_deg": 50.0 + number / 10,
            "single_peak_ratio_mean": 0.9,
            "burst_count": 10,
        },
    }


class HistoryReportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

        for number in (
            5, 6, 7, 8, 9, 10,
            11, 12, 13, 14, 15, 16, 17,
        ):
            cluster = 2 if number in (5, 6) else 1
            item = record(number, cluster)

            (self.root / f"{item['session_id']}.json").write_text(
                json.dumps(item),
                encoding="utf-8",
            )

    def test_015_report_uses_prior_history_only(self):
        result = build_history_report(
            "TPMS-NATURAL-015-20260925-000000",
            results_dir=self.root,
        )

        text = result["text"]

        self.assertIn(
            "- prior formal sessions: 9",
            text,
        )
        self.assertIn("- C1: 7", text)
        self.assertIn("- C2: 2", text)

        self.assertNotIn(
            "TPMS-NATURAL-016",
            text,
        )
        self.assertNotIn(
            "TPMS-NATURAL-017",
            text,
        )

    def test_014_never_appears_as_history(self):
        result = build_history_report(
            "TPMS-NATURAL-015-20260925-000000",
            results_dir=self.root,
        )

        nearest = result["history"]["nearest_prior_sessions"]

        self.assertTrue(
            all(
                "-014-" not in item["session_id"]
                for item in nearest
            )
        )

    def test_feature_deltas_are_reported(self):
        result = build_history_report(
            "TPMS-NATURAL-015-20260925-000000",
            results_dir=self.root,
        )

        text = result["text"]

        self.assertIn(
            "Target vs prior same-cluster mean:",
            text,
        )
        self.assertIn("bearing circular std:", text)
        self.assertIn("median confidence:", text)
        self.assertIn("DoA width mean:", text)

    def test_earliest_session_reports_no_prior_history(self):
        result = build_history_report(
            "TPMS-NATURAL-005-20260925-000000",
            results_dir=self.root,
        )

        text = result["text"]

        self.assertIn(
            "- prior formal sessions: 0",
            text,
        )
        self.assertIn(
            "Nearest prior sessions:\n- none",
            text,
        )
        self.assertIn(
            "unavailable; no prior same-cluster sessions",
            text,
        )


if __name__ == "__main__":
    unittest.main()
