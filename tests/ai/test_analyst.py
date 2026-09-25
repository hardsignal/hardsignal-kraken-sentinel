import unittest

from ai.analyst import analyse_bundle, format_analysis


def bundle(
    *,
    cluster=1,
    novelty="WITHIN_OBSERVED_TRAINING_RANGE",
    missing_logs=None,
):
    session_id = "TEST-SESSION"

    return {
        "schema_version": "0.1",
        "session_id": session_id,
        "core": {
            "version": 1,
            "session_id": session_id,
            "bursts": {
                "total": 11,
                "STABLE": 10,
                "MULTIPATH": 1,
                "LOW_QUALITY": 0,
            },
            "track_events": {
                "TRACK_ACQUIRED": 1,
                "TRACK_DEGRADED": 0,
                "TRACK_LOST": 0,
                "TRACK_REACQUIRED": 0,
                "TRACK_RECOVERED": 0,
                "TRACK_SHIFT_CONFIRMED": 0,
            },
            "episodes": {},
            "missing_logs": missing_logs or [],
        },
        "ml": {
            "session_id": session_id,
            "model_version": "0.1",
            "record_version": "0.1",
            "assigned_cluster": cluster,
            "distances": {
                "0": 4.5,
                "1": 1.8,
                "2": 3.9,
            },
            "nearest_distance": 1.8149,
            "second_nearest_distance": 3.9202,
            "separation_ratio": 2.1600,
            "distance_vs_training_max": 0.5433,
            "novelty": novelty,
            "scientific_scope": (
                "RF/DoA behavioural regime assignment; "
                "not transmitter identity"
            ),
            "feature_row": {
                "session_id": session_id,
            },
            "training_dataset_sha256": "abc123",
        },
        "provenance": {
            "ml_result_path": "result.json",
            "ml_result_sha256": "deadbeef",
        },
    }


class AnalystTests(unittest.TestCase):
    def test_c1_within_range(self):
        result = analyse_bundle(bundle())

        self.assertEqual(result["assigned_cluster"], 1)
        self.assertEqual(
            result["regime_label"],
            "coherent behavioural regime",
        )
        self.assertEqual(result["warnings"], [])
        self.assertIn(
            "within the observed training range",
            result["interpretation"],
        )

    def test_outside_range_generates_warning(self):
        result = analyse_bundle(
            bundle(novelty="OUTSIDE_OBSERVED_TRAINING_RANGE")
        )

        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn(
            "outside the observed training-distance envelope",
            result["warnings"][0],
        )
        self.assertIn(
            "treated cautiously",
            result["interpretation"],
        )

    def test_missing_logs_generate_warning(self):
        result = analyse_bundle(
            bundle(missing_logs=["episode_log"])
        )

        self.assertIn(
            "episode_log",
            result["warnings"][0],
        )

    def test_boundary_rejects_identity_claim(self):
        result = analyse_bundle(bundle())

        self.assertIn(
            "does not establish transmitter identity",
            result["boundary"],
        )

    def test_formatter_contains_evidence(self):
        text = format_analysis(analyse_bundle(bundle()))

        self.assertIn("10/11 bursts classified STABLE", text)
        self.assertIn("Behavioural regime: C1", text)
        self.assertIn("nearest centroid distance: 1.8149", text)


if __name__ == "__main__":
    unittest.main()
