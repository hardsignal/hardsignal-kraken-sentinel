import json
from pathlib import Path
import tempfile
import unittest

from ai.history import (
    FORMAL_SESSION_NUMBERS,
    build_history_bundle,
    load_formal_history,
    session_number,
)


def make_record(number, cluster=1, novelty="WITHIN_OBSERVED_TRAINING_RANGE"):
    session_id = f"TPMS-NATURAL-{number:03d}-20260925-000000"

    return {
        "session_id": session_id,
        "assigned_cluster": cluster,
        "novelty": novelty,
        "feature_row": {
            "bearing_circular_std_deg": float(number),
            "peak_power_mean_db": -20.0 - number,
            "median_confidence_mean": 3.0 + number / 100,
            "doa_width_mean_deg": 50.0 + number / 10,
            "single_peak_ratio_mean": 0.9,
            "burst_count": 10,
        },
    }


class HistoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

        for number in sorted(FORMAL_SESSION_NUMBERS | {14}):
            cluster = 2 if number in (5, 6) else 1
            record = make_record(number, cluster=cluster)

            path = self.root / f"{record['session_id']}.json"
            path.write_text(
                json.dumps(record),
                encoding="utf-8",
            )

    def test_session_number(self):
        self.assertEqual(
            session_number("TPMS-NATURAL-015-20260925-020456"),
            15,
        )

    def test_non_natural_session_id_rejected(self):
        with self.assertRaises(ValueError):
            session_number("OTHER-SESSION")

    def test_formal_history_excludes_014(self):
        records = load_formal_history(self.root)
        numbers = {
            session_number(record["session_id"])
            for record in records
        }

        self.assertEqual(numbers, FORMAL_SESSION_NUMBERS)
        self.assertNotIn(14, numbers)

    def test_target_015_uses_only_prior_sessions(self):
        target = "TPMS-NATURAL-015-20260925-000000"

        result = build_history_bundle(
            target,
            results_dir=self.root,
        )

        self.assertEqual(
            result["formal_session_count_total"],
            12,
        )
        self.assertEqual(
            result["prior_formal_session_count"],
            9,
        )

        prior_numbers = {
            session_number(item["session_id"])
            for item in result["nearest_prior_sessions"]
        }

        self.assertTrue(
            all(number < 15 for number in prior_numbers)
        )
        self.assertNotIn(16, prior_numbers)
        self.assertNotIn(17, prior_numbers)

    def test_target_015_prior_cluster_counts(self):
        result = build_history_bundle(
            "TPMS-NATURAL-015-20260925-000000",
            results_dir=self.root,
        )

        self.assertEqual(
            result["prior_cluster_counts"],
            {"1": 7, "2": 2},
        )
        self.assertEqual(
            result["same_cluster_prior_count"],
            7,
        )

    def test_excluded_014_cannot_be_target(self):
        with self.assertRaisesRegex(
            ValueError,
            "not in the formal prospective set",
        ):
            build_history_bundle(
                "TPMS-NATURAL-014-20260925-000000",
                results_dir=self.root,
            )

    def test_earliest_formal_session_has_empty_prior_history(self):
        result = build_history_bundle(
            "TPMS-NATURAL-005-20260925-000000",
            results_dir=self.root,
        )

        self.assertEqual(
            result["prior_formal_session_count"],
            0,
        )
        self.assertEqual(
            result["prior_cluster_counts"],
            {},
        )
        self.assertEqual(
            result["nearest_prior_sessions"],
            [],
        )
        self.assertEqual(
            result["target_vs_same_cluster_prior_mean"],
            {},
        )


if __name__ == "__main__":
    unittest.main()
