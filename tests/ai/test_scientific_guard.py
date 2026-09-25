"""Scientific boundaries on both public experiment validation paths."""

import unittest
from unittest.mock import Mock

from ai.experiment_guard import SentinelExperimentGuardError, validate_experiment_suggestion
from ai.history_experiment_guard import validate_history_experiment
from ai.history_experiment import suggest_history_experiment_from_prompt


class ScientificGuardTests(unittest.TestCase):
    def reject(self, *examples):
        for guard in (validate_experiment_suggestion, validate_history_experiment):
            for text in examples:
                with self.subTest(guard=guard.__name__, text=text):
                    with self.assertRaises(SentinelExperimentGuardError):
                        guard(text)

    def allow(self, *examples):
        for guard in (validate_experiment_suggestion, validate_history_experiment):
            for text in examples:
                with self.subTest(guard=guard.__name__, text=text):
                    self.assertEqual(guard(text), text)

    def test_positive_identity_claims(self):
        self.reject(
            "Repeat the capture. This is device ABC123.",
            "Measure power to identify the transmitter.",
            "Repeat and confirm transmitter identity.",
            "Repeat the capture. The RF fingerprint matches the same device.",
            "Repeat and measure the unique fingerprint.",
            "Repeat and compare. The transmitter has been identified.",
        )

    def test_negated_identity_boundary(self):
        self.allow(
            "Repeat and measure power. This does not identify a transmitter.",
            "Repeat and compare measurements. This does not establish transmitter identity.",
            "Repeat and measure power. Transmitter identity is not supported.",
            "Repeat and compare. Do not infer device identity.",
            "Repeat and compare. No transmitter identity inference is supported.",
        )

    def test_causal_claims_and_unsupported_hypotheses(self):
        self.reject(
            "Repeat the capture. Reflection caused the observed variability.",
            "Measure power. Variability is due to multipath.",
            "Repeat because of environmental interference.",
            "Compare measurements. This indicates interference.",
            "Repeat and measure whether propagation changes explain the result.",
            "Repeat and compare. This may suggest multipath.",
            "Repeat and compare. The variability reflects interference.",
            "Repeat and compare. The evidence does not rule out interference caused the change.",
        )

    def test_neutral_repeatability(self):
        self.allow(
            "Repeat the session with unchanged settings. Measure bearing variability and median confidence.",
            "Repeat and compare power measurements with the original session.",
            "Repeat and compare burst classifications.",
        )

    def test_directional_accuracy(self):
        self.reject(
            "Repeat the capture. Bearing is calibrated to within 0.1 degrees.",
            "Measure directional accuracy.",
            "Repeat to determine calibration-grade absolute direction.",
            "Repeat and record the true bearing.",
        )

    def test_doa_width_is_permitted(self):
        self.allow(
            "Repeat and measure DoA width and bearing circular standard deviation.",
            "Record DoA width. This does not establish directional accuracy.",
            "Record DoA width. Bearing is not calibrated.",
        )

    def test_classification_and_separation(self):
        self.reject(
            "Repeat and compare to prove reliable device classification.",
            "Measure power. These features separate device classes.",
            "Repeat and demonstrate class separation.",
            "Repeat and confirm discrimination.",
            "Compare the discriminative features.",
            "Repeat and compare. The classes are separable.",
        )

    def test_reproducibly_different_is_not_discrimination(self):
        self.allow(
            "Repeat and compare whether peak power is reproducibly different from the prior mean.",
            "Repeat and compare. This does not demonstrate class separation.",
        )

    def test_source_reliability(self):
        self.reject(
            "Repeat and compare. The transmitter is reliable.",
            "Measure confidence. The evidence confirms a stable signal source.",
            "Repeat and confirm device reliability.",
            "Repeat and compare. The source appears to be consistent.",
            "Repeat and prove reliability of the physical source.",
        )

    def test_measurement_only_hypothesis(self):
        self.allow(
            "Repeat the session to test whether median confidence remains similar. Compare the measurements.",
            "Repeat and measure the stability of burst counts across sessions.",
            "Repeat and compare. This does not establish a reliable transmitter.",
        )

    def test_physical_cluster_conclusions(self):
        self.reject(
            "Repeat and compare. Cluster C1 represents a vehicle.",
            "Measure power. C2 indicates a reliable transmitter.",
            "Repeat and compare. C1 corresponds to a sensor.",
        )

    def test_negation_does_not_license_another_claim(self):
        self.reject(
            "Repeat and compare. This does not identify a transmitter, but the source is reliable.",
            "Repeat and compare. This does not establish transmitter identity and reflection caused the variation.",
            "Repeat and compare. This does not only identify the transmitter.",
            "Repeat and compare. This cannot rule out device identity.",
        )

    def test_ordinary_words_are_not_substring_matches(self):
        self.allow(
            "Repeat the capture near the causeway and measure power.",
            "Record the source filename and compare burst classifications.",
            "Repeat the session and measure signal stability.",
        )

    def test_two_rejections_still_fail_closed(self):
        generate = Mock(return_value="Repeat and compare. This is device ABC123.")
        with self.assertRaises(SentinelExperimentGuardError):
            suggest_history_experiment_from_prompt("PROMPT", generate_fn=generate)
        self.assertEqual(generate.call_count, 2)
        self.assertIn("REPAIR INSTRUCTION", generate.call_args.args[0])

    def test_repaired_measurement_is_accepted(self):
        valid = "Repeat and measure DoA width. Compare the measurements."
        generate = Mock(side_effect=["Repeat and compare. The transmitter is reliable.", valid])
        self.assertEqual(suggest_history_experiment_from_prompt("PROMPT", generate_fn=generate), valid)
        self.assertEqual(generate.call_count, 2)

    def test_no_prior_context_rejects_invented_comparison(self):
        prompt = "DETERMINISTIC HISTORICAL REPORT:\n- prior formal sessions: 0\n"
        for text in ("Repeat and compare to the prior C1 mean.",
                     "Repeat and compare with the nearest session."):
            with self.subTest(text=text):
                generate = Mock(return_value=text)
                with self.assertRaises(SentinelExperimentGuardError):
                    suggest_history_experiment_from_prompt(prompt, generate_fn=generate)
                self.assertEqual(generate.call_count, 2)
        valid = "Repeat and measure confidence to establish a baseline for future sessions."
        self.assertEqual(suggest_history_experiment_from_prompt(prompt, generate_fn=lambda _: valid), valid)

    def test_no_same_cluster_mean_rejects_only_unavailable_comparison(self):
        report = "- prior formal sessions: 2\n- unavailable; no prior same-cluster sessions"
        with self.assertRaises(SentinelExperimentGuardError):
            validate_history_experiment("Repeat and compare with the prior C1 mean.", history_report=report)
        valid = "Repeat and compare measurements with the nearest prior session."
        self.assertEqual(validate_history_experiment(valid, history_report=report), valid)


if __name__ == "__main__":
    unittest.main()
