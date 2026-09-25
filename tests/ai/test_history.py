import json
from pathlib import Path
from unittest.mock import patch
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

from ai.history_artifact import build_history_artifact
from ai.history_experiment import build_history_experiment_prompt
from ai.history_report import build_history_report


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
            10,
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


class PriorOnlyIsolationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.target = make_record(15)["session_id"]
        for number in sorted(FORMAL_SESSION_NUMBERS - {16, 17}):
            self.write(number)

    def write(self, number):
        record = make_record(number)
        path = self.root / f"{record['session_id']}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def snapshot(self):
        bundle = build_history_bundle(self.target, results_dir=self.root)
        report = build_history_report(self.target, results_dir=self.root)
        prompt = build_history_experiment_prompt(self.target, results_dir=self.root)
        artifact = build_history_artifact(
            target_session_id=self.target, history_bundle=bundle,
            history_report=report["text"], experiment_prompt=prompt,
            experiment_suggestion="Repeat and measure.", model_digest="offline",
            results_dir=self.root,
        )
        # Creation time is not source provenance; everything else must match.
        artifact.pop("created_at")
        return bundle, report["text"].encode("utf-8"), prompt.encode("utf-8"), artifact

    def test_adding_016_017_preserves_complete_outputs(self):
        before = self.snapshot()
        self.write(16)
        self.write(17)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(before[0]["formal_session_count_total"], 10)

    def test_deleting_016_017_preserves_complete_outputs(self):
        paths = [self.write(n) for n in (16, 17)]
        before = self.snapshot()
        for path in paths:
            path.unlink()
        self.assertEqual(before, self.snapshot())

    def test_corrupt_future_json_and_encoding_preserve_complete_outputs(self):
        before = self.snapshot()
        for data in (b"{", b"null", b"[]", b"\xff"):
            with self.subTest(data=data):
                for n in (16, 17):
                    self.write(n).write_bytes(data)
                self.assertEqual(before, self.snapshot())

    def test_arbitrary_later_names_and_disguised_payloads_are_never_read(self):
        before = self.snapshot()
        paths = [self.write(n) for n in (16, 17, 18, 99, 1000)]
        for path in paths:
            # Even an older payload under a later filename is not an input.
            path.write_text(json.dumps(make_record(5)), encoding="utf-8")
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            if path in paths:
                self.fail(f"future source opened: {path}")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            self.assertEqual(before, self.snapshot())

    def test_mutating_future_features_preserves_complete_outputs(self):
        before = self.snapshot()
        for n in (16, 17):
            record = make_record(n, cluster=999)
            record["feature_row"] = {key: 1e30 for key in record["feature_row"]}
            self.write(n).write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(before, self.snapshot())

    def test_005_alone_has_empty_history_and_stable_provenance(self):
        for path in self.root.glob("*.json"):
            path.unlink()
        self.target = make_record(5)["session_id"]
        self.write(5)
        before = self.snapshot()
        bundle = before[0]
        self.assertEqual(bundle["formal_session_count_total"], 1)
        self.assertEqual(bundle["prior_formal_session_count"], 0)
        self.assertEqual(bundle["nearest_prior_sessions"], [])
        self.assertEqual(bundle["prior_cluster_counts"], {})
        self.assertEqual(bundle["same_cluster_prior_feature_means"], {})
        self.assertEqual(bundle["target_vs_same_cluster_prior_mean"], {})
        self.assertEqual(set(before[3]["source_record_sha256"]), {self.target})
        for n in (6, 14, 16, 17, 99):
            self.write(n).write_bytes(b"{")
        self.assertEqual(before, self.snapshot())

    def test_014_remains_excluded_from_outputs_and_provenance(self):
        before = self.snapshot()
        self.write(14)
        self.assertEqual(before, self.snapshot())
        self.target = make_record(14)["session_id"]
        with self.assertRaisesRegex(ValueError, "not in the formal prospective set"):
            self.snapshot()


if __name__ == "__main__":
    unittest.main()
