import unittest

from watcher.tracker_policy import (
    maturity_and_limits,
    shift_candidate_confirmed,
    shift_confirm_required,
    track_health_for,
)


class TrackerPolicyTests(unittest.TestCase):

    def test_building_track_cannot_degrade_or_be_lost(self):
        self.assertEqual(track_health_for(0, 100), "BUILDING")
        self.assertEqual(track_health_for(4, 100), "BUILDING")

    def test_established_track_thresholds(self):
        self.assertEqual(maturity_and_limits(5)[0], "ESTABLISHED")

        self.assertEqual(track_health_for(5, 0), "HEALTHY")
        self.assertEqual(track_health_for(5, 2), "HEALTHY")
        self.assertEqual(track_health_for(5, 3), "DEGRADED")
        self.assertEqual(track_health_for(5, 4), "DEGRADED")
        self.assertEqual(track_health_for(5, 5), "LOST")

    def test_mature_boundary(self):
        self.assertEqual(maturity_and_limits(19)[0], "ESTABLISHED")
        self.assertEqual(maturity_and_limits(20)[0], "MATURE")

    def test_mature_track_has_more_rejection_tolerance(self):
        self.assertEqual(track_health_for(20, 4), "HEALTHY")
        self.assertEqual(track_health_for(20, 5), "DEGRADED")
        self.assertEqual(track_health_for(20, 7), "DEGRADED")
        self.assertEqual(track_health_for(20, 8), "LOST")

    def test_established_shift_requires_five(self):
        self.assertEqual(shift_confirm_required(5), 5)

        self.assertFalse(
            shift_candidate_confirmed(4, 1.0, 5)
        )
        self.assertTrue(
            shift_candidate_confirmed(5, 1.0, 5)
        )

    def test_mature_shift_requires_seven(self):
        self.assertEqual(shift_confirm_required(20), 7)

        self.assertFalse(
            shift_candidate_confirmed(5, 1.0, 20)
        )
        self.assertFalse(
            shift_candidate_confirmed(6, 1.0, 20)
        )
        self.assertTrue(
            shift_candidate_confirmed(7, 1.0, 20)
        )

    def test_candidate_must_also_be_coherent(self):
        self.assertFalse(
            shift_candidate_confirmed(7, 6.0, 20)
        )
        self.assertTrue(
            shift_candidate_confirmed(7, 5.0, 20)
        )


if __name__ == "__main__":
    unittest.main()
