import csv
import unittest
from pathlib import Path

from watcher.tracker_engine import TrackerEngine


FIXTURES = Path(__file__).parent / "fixtures"

INPUTS = FIXTURES / "tpms_hysteresis_clean_v1_inputs.csv"
EXPECTED = FIXTURES / "tpms_hysteresis_clean_v1.log"


def load_inputs():
    with INPUTS.open(newline="") as f:
        return list(csv.DictReader(f))


def parse_expected_line(line):
    result = {}

    for field in line.strip().split(","):
        key, value = field.split("=", 1)
        result[key] = value

    return result


def load_expected():
    return [
        parse_expected_line(line)
        for line in EXPECTED.read_text().splitlines()
        if line.strip()
    ]


class TrackerTrueReplayTests(unittest.TestCase):

    def test_real_rf_inputs_reproduce_tracker_lifecycle(self):
        inputs = load_inputs()
        expected = load_expected()

        self.assertEqual(len(inputs), 26)
        self.assertEqual(len(inputs), len(expected))

        engine = TrackerEngine()

        for index, (observation, recorded) in enumerate(
            zip(inputs, expected),
            start=1,
        ):
            actual = engine.process(
                bearing=float(observation["bearing"]),
                quality=observation["quality"],
            )

            with self.subTest(observation=index):
                self.assertEqual(
                    actual["track_state"],
                    recorded["track_state"],
                )

                self.assertEqual(
                    actual["track_count"],
                    int(recorded["track_count"]),
                )

                self.assertEqual(
                    actual["track_health"],
                    recorded["track_health"],
                )

                self.assertEqual(
                    actual["track_maturity"],
                    recorded["track_maturity"],
                )

                self.assertEqual(
                    actual["track_support"],
                    int(recorded["track_support"]),
                )

                self.assertEqual(
                    actual["rejected_streak"],
                    int(recorded["rejected_streak"]),
                )

                self.assertEqual(
                    actual["shift_candidate"],
                    recorded["shift_candidate"],
                )

                self.assertEqual(
                    actual["shift_candidate_count"],
                    int(recorded["shift_candidate_count"]),
                )

                self.assertEqual(
                    actual["shift_candidate_required"],
                    int(recorded["shift_candidate_required"]),
                )

                if recorded["track_mean"] == "NA":
                    self.assertIsNone(actual["track_mean"])
                else:
                    self.assertEqual(
                        round(actual["track_mean"], 1),
                        float(recorded["track_mean"]),
                    )

                if recorded["track_spread"] == "NA":
                    self.assertIsNone(actual["track_spread"])
                else:
                    self.assertEqual(
                        round(actual["track_spread"], 1),
                        float(recorded["track_spread"]),
                    )

    def test_real_rf_shift_is_recomputed_at_candidate_five(self):
        engine = TrackerEngine()
        outputs = []

        for observation in load_inputs():
            outputs.append(
                engine.process(
                    float(observation["bearing"]),
                    observation["quality"],
                )
            )

        confirmed = [
            (index, result)
            for index, result in enumerate(outputs, start=1)
            if result["shift_confirmed"]
        ]

        self.assertEqual(len(confirmed), 1)

        index, result = confirmed[0]

        self.assertEqual(index, 17)
        self.assertEqual(result["shift_candidate_count"], 5)
        self.assertEqual(result["shift_candidate_required"], 5)
        self.assertAlmostEqual(result["track_mean"], 144.0, places=1)


if __name__ == "__main__":
    unittest.main()
