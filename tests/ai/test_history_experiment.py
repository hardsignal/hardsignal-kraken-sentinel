import unittest

from ai.experiment_guard import SentinelExperimentGuardError
from ai.history_experiment import suggest_history_experiment


class HistoryExperimentTests(unittest.TestCase):
    def test_rejected_first_attempt_is_repaired(self):
        calls = []

        def generate(prompt):
            calls.append(prompt)

            if len(calls) == 1:
                return (
                    "Repeat the capture and measure propagation changes."
                )

            return (
                "Repeat the session with unchanged settings. "
                "Measure bearing variability and median confidence, "
                "then compare them with the prior C1 mean."
            )

        result = suggest_history_experiment(
            "TPMS-NATURAL-015-20260925-020456",
            generate_fn=generate,
        )

        self.assertEqual(len(calls), 2)
        self.assertIn("REPAIR INSTRUCTION", calls[1])
        self.assertIn("prior C1 mean", result)

    def test_second_rejection_is_not_published(self):
        def generate(prompt):
            return "Measure propagation changes in another capture."

        with self.assertRaises(SentinelExperimentGuardError):
            suggest_history_experiment(
                "TPMS-NATURAL-015-20260925-020456",
                generate_fn=generate,
            )

    def test_zero_attempts_fails(self):
        with self.assertRaises(ValueError):
            suggest_history_experiment(
                "TPMS-NATURAL-015-20260925-020456",
                max_attempts=0,
                generate_fn=lambda prompt: "unused",
            )


if __name__ == "__main__":
    unittest.main()
