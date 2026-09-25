import unittest

from ai.experiment_guard import (
    SentinelExperimentGuardError,
    validate_experiment_suggestion,
)


class ExperimentGuardTests(unittest.TestCase):
    def test_controlled_measurement_passes(self):
        text = (
            "Repeat the session with unchanged settings. "
            "Measure burst classifications and compare the result "
            "with the original session."
        )

        self.assertEqual(
            validate_experiment_suggestion(text),
            text,
        )

    def test_empty_suggestion_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_experiment_suggestion("")

    def test_identity_goal_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_experiment_suggestion(
                "Repeat the capture and measure the RF features "
                "to identify the transmitter identity."
            )

    def test_absolute_direction_goal_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_experiment_suggestion(
                "Repeat the experiment and measure additional data "
                "to determine calibration-grade absolute direction."
            )

    def test_non_measurable_suggestion_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_experiment_suggestion(
                "Think about performing another experiment later."
            )


if __name__ == "__main__":
    unittest.main()
