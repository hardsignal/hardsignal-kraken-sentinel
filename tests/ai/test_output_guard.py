import unittest

from ai.output_guard import (
    SentinelOutputGuardError,
    validate_generated_report,
)


def report(uncertainty, experiment="Repeat the controlled session."):
    return f"""**Summary**
Coherent C1-like session.

**Evidence**
10/11 bursts were STABLE.

**Interpretation**
The session is consistent with the frozen training observations.

**Uncertainty**
{uncertainty}

**Next controlled experiment**
{experiment}

**Scientific boundary**
This does not establish transmitter identity or environmental conditions.
"""


class OutputGuardTests(unittest.TestCase):
    def test_grounded_report_passes(self):
        validate_generated_report(
            report("No transmitter identity inference is supported.")
        )

    def test_environment_can_appear_in_future_experiment(self):
        validate_generated_report(
            report(
                "No causal explanation is supported.",
                "Repeat while controlling environmental conditions.",
            )
        )

    def test_environmental_hypothesis_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The evidence does not rule out environmental effects."
                )
            )

    def test_negated_identified_source_statement_passes(self):
        validate_generated_report(
            report(
                "The evidence does not establish an identified signal source."
            )
        )

    def test_known_transmitter_allowed_in_future_experiment(self):
        validate_generated_report(
            report(
                "No transmitter identity inference is supported.",
                "Repeat the experiment with a known transmitter under controlled conditions.",
            )
        )


    def test_negated_reliable_or_identified_source_passes(self):
        validate_generated_report(
            report(
                "The evidence does not confirm the presence of a reliable or identified signal source."
            )
        )

    def test_positive_reliable_source_claim_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The evidence confirms a reliable signal source."
                )
            )


    def test_positive_combined_source_claim_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The evidence confirms a reliable or identified signal source."
                )
            )

    def test_unobserved_variation_hypothesis_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The novelty status does not rule out the possibility of unobserved variations."
                )
            )


    def test_stable_signal_environment_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The observations suggest a clean and stable signal environment."
                )
            )

    def test_does_not_eliminate_unobserved_variation_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The novelty status does not eliminate the possibility of unobserved variations."
                )
            )


    def test_signal_source_claim_is_rejected(self):
        with self.assertRaises(SentinelOutputGuardError):
            validate_generated_report(
                report(
                    "The evidence supports a stable signal source."
                )
            )


if __name__ == "__main__":
    unittest.main()
