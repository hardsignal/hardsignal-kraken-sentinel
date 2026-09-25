import unittest

from ai.output_guard import SentinelOutputGuardError
from ai.report import generate_grounded_report


class ReportGenerationTests(unittest.TestCase):
    def test_first_attempt_can_pass(self):
        calls = []

        def generate(prompt):
            calls.append(prompt)
            return "accepted report"

        result = generate_grounded_report(
            "original prompt",
            generate_fn=generate,
        )

        self.assertEqual(result, "accepted report")
        self.assertEqual(len(calls), 1)

    def test_rejected_first_attempt_gets_repair_prompt(self):
        calls = []

        def generate(prompt):
            calls.append(prompt)

            if len(calls) == 1:
                raise SentinelOutputGuardError(
                    "unsupported unobserved hypothesis"
                )

            return "repaired report"

        result = generate_grounded_report(
            "AUTHORITATIVE INPUT",
            generate_fn=generate,
        )

        self.assertEqual(result, "repaired report")
        self.assertEqual(len(calls), 2)
        self.assertIn(
            "REPAIR INSTRUCTION",
            calls[1],
        )
        self.assertIn(
            "AUTHORITATIVE INPUT",
            calls[1],
        )

    def test_second_rejection_is_not_published(self):
        def generate(prompt):
            raise SentinelOutputGuardError(
                "unsupported claim"
            )

        with self.assertRaises(SentinelOutputGuardError):
            generate_grounded_report(
                "original prompt",
                generate_fn=generate,
            )

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            generate_grounded_report(
                "prompt",
                max_attempts=0,
            )


if __name__ == "__main__":
    unittest.main()
