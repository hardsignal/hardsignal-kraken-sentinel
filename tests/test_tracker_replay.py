import unittest
from pathlib import Path


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "tpms_hysteresis_clean_v1.log"
)


def parse_line(line):
    record = {}

    for field in line.strip().split(","):
        key, value = field.split("=", 1)
        record[key] = value

    return record


def load_fixture():
    return [
        parse_line(line)
        for line in FIXTURE.read_text().splitlines()
        if line.strip()
    ]


class TrackerReplayRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = load_fixture()

    def test_fixture_is_complete_real_rf_session(self):
        self.assertEqual(len(self.rows), 26)

        self.assertTrue(
            all(
                row["session_id"]
                == "TPMS-HYST-CLEAN-V1-20260923-020243"
                for row in self.rows
            )
        )

        self.assertTrue(
            all(
                row["frequency_mhz"] == "433.868160"
                for row in self.rows
            )
        )

    def test_established_track_exists_before_shift(self):
        stable_old = [
            row
            for row in self.rows
            if row["track_state"] == "TRACK_STABLE"
            and row["track_mean"] == "286.0"
            and row["shift_candidate"] == "NONE"
        ]

        self.assertGreaterEqual(len(stable_old), 1)

        first = stable_old[0]

        self.assertEqual(first["track_maturity"], "ESTABLISHED")
        self.assertEqual(first["track_support"], "5")
        self.assertEqual(first["track_health"], "HEALTHY")

    def test_far_clean_bearings_build_candidate_without_moving_track(self):
        pending = [
            row
            for row in self.rows
            if row["shift_candidate"] == "PENDING"
        ]

        self.assertEqual(
            [int(row["shift_candidate_count"]) for row in pending],
            [1, 2, 3, 4],
        )

        self.assertTrue(
            all(row["shift_candidate_required"] == "5" for row in pending)
        )

        self.assertTrue(
            all(row["quality"] == "STABLE" for row in pending)
        )

        # Hysteresis invariant:
        # candidate evidence grows while the active track remains unchanged.
        self.assertTrue(
            all(row["track_mean"] == "286.0" for row in pending)
        )

        bearings = [float(row["bearing"]) for row in pending]

        self.assertEqual(
            bearings,
            [145.3, 144.3, 144.0, 143.0],
        )

    def test_fifth_coherent_candidate_confirms_shift(self):
        confirmed = [
            row
            for row in self.rows
            if row["shift_candidate"] == "CONFIRMED"
        ]

        self.assertEqual(len(confirmed), 1)

        row = confirmed[0]

        self.assertEqual(row["quality"], "STABLE")
        self.assertEqual(row["shift_candidate_count"], "5")
        self.assertEqual(row["shift_candidate_required"], "5")
        self.assertEqual(row["track_state"], "TRACK_STABLE")

        self.assertAlmostEqual(float(row["bearing"]), 143.2, places=1)
        self.assertAlmostEqual(float(row["track_mean"]), 144.0, places=1)
        self.assertAlmostEqual(float(row["track_spread"]), 0.8, places=1)

        # A confirmed shift starts a fresh established-track epoch.
        self.assertEqual(row["track_support"], "5")
        self.assertEqual(row["track_age_s"], "0")

    def test_track_remains_stable_after_confirmation(self):
        confirmed_index = next(
            i
            for i, row in enumerate(self.rows)
            if row["shift_candidate"] == "CONFIRMED"
        )

        next_row = self.rows[confirmed_index + 1]

        self.assertEqual(next_row["quality"], "STABLE")
        self.assertEqual(next_row["track_state"], "TRACK_STABLE")
        self.assertEqual(next_row["track_health"], "HEALTHY")
        self.assertEqual(next_row["shift_candidate"], "NONE")
        self.assertEqual(next_row["shift_candidate_count"], "0")
        self.assertEqual(next_row["track_support"], "6")

        self.assertAlmostEqual(
            float(next_row["track_mean"]),
            144.1,
            places=1,
        )

    def test_post_shift_degrade_and_recover_sequence(self):
        confirmed_index = next(
            i
            for i, row in enumerate(self.rows)
            if row["shift_candidate"] == "CONFIRMED"
        )

        later = self.rows[confirmed_index + 1:]

        degraded = [
            row
            for row in later
            if row["track_health"] == "DEGRADED"
        ]

        self.assertEqual(len(degraded), 1)
        self.assertEqual(degraded[0]["rejected_streak"], "3")

        degraded_index = self.rows.index(degraded[0])
        recovery = self.rows[degraded_index + 1]

        self.assertEqual(recovery["quality"], "STABLE")
        self.assertEqual(recovery["track_health"], "HEALTHY")
        self.assertEqual(recovery["rejected_streak"], "0")


if __name__ == "__main__":
    unittest.main()
