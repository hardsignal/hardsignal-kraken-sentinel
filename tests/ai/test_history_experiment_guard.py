import unittest

from ai.experiment_guard import SentinelExperimentGuardError
from ai.history_experiment_guard import validate_history_experiment


class HistoryExperimentGuardTests(unittest.TestCase):
    def test_repeatability_experiment_passes(self):
        text = (
            "Repeat the session with unchanged settings and measure "
            "bearing variability and median confidence. Compare those "
            "values with the prior C1 mean."
        )

        self.assertEqual(
            validate_history_experiment(text),
            text,
        )

    def test_reflectivity_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_history_experiment(
                "Repeat the experiment while changing reflectivity "
                "and measure peak power."
            )

    def test_directional_accuracy_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_history_experiment(
                "Repeat the capture and measure directional accuracy."
            )

    def test_propagation_hypothesis_fails(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_history_experiment(
                "Repeat the session and measure whether propagation "
                "changes explain the result."
            )


if __name__ == "__main__":
    unittest.main()
