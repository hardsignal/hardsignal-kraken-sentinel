"""Normal mode cannot propose comparisons to unavailable session history."""

import contextlib
import io
import unittest
from unittest.mock import patch

from ai import cli
from ai.experiment import suggest_experiment_from_prompt
from ai.experiment_guard import (
    SentinelExperimentGuardError, validate_normal_experiment_suggestion,
)
from ai.history_experiment_guard import validate_history_experiment


RC_SUGGESTION = "Compare these proportions to the prior session's values."


class NormalHistoryGuardTests(unittest.TestCase):
    def test_unavailable_history_references_are_rejected(self):
        suggestions = (
            RC_SUGGESTION,
            "Repeat and compare with the previous session.",
            "Compare with earlier sessions.",
            "Compare against the nearest session.",
            "Compare against the nearest prior session.",
            "Compare with the prior mean.",
            "Compare with the prior C1 mean.",
            "Compare with the prior same-cluster mean.",
            "Compare against the historical mean.",
            "Compare against a historical baseline.",
            "Compare with the historical data.",
            "Compare against the preceding capture.",
            "Compare with the last run's results.",
            "Compare with the closest recorded session.",
            "Compare with previously recorded measurements.",
            "Compare with the baseline measured earlier.",
            "Compare against the baseline from history.",
            "Compare measurements against session history.",
            "Compare these values against history.",
            "Repeat and compare with PRIOR-SESSION values.",
        )
        for text in suggestions:
            with self.subTest(text=text):
                with self.assertRaisesRegex(SentinelExperimentGuardError, "historical comparison unavailable"):
                    validate_normal_experiment_suggestion(text)

    def test_current_session_repeatability_still_passes(self):
        for text in (
            "Repeat the session and measure bearing variability.",
            "Repeat the session and compare the proportions with this session's values.",
            "Repeat and compare with the original session.",
            "Collect repeated captures and compare their measured burst proportions.",
            "Repeat the experiment using the current session as a baseline.",
        ):
            with self.subTest(text=text):
                self.assertEqual(validate_normal_experiment_suggestion(text), text)

    def test_normal_generator_applies_context_guard(self):
        with patch("ai.experiment.generate_text", return_value=RC_SUGGESTION):
            with self.assertRaises(SentinelExperimentGuardError):
                suggest_experiment_from_prompt("PROMPT")

    def test_normal_cli_rejects_before_report_or_save(self):
        with (
            patch("ai.cli.build_evidence_bundle", return_value={"session_id": "TEST"}),
            patch("ai.cli.verify_model_digest", return_value="locked"),
            patch("ai.cli.build_experiment_prompt", return_value="PROMPT"),
            patch("ai.experiment.generate_text", return_value=RC_SUGGESTION),
            patch("ai.cli.compose_final_report") as compose,
            patch("ai.cli.save_report_artifact") as save,
            contextlib.redirect_stdout(io.StringIO()) as output,
            contextlib.redirect_stderr(io.StringIO()) as error,
        ):
            self.assertEqual(cli.main(["--session", "TEST", "--save"]), 6)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("historical comparison unavailable", error.getvalue())
        compose.assert_not_called()
        save.assert_not_called()

    def test_evidence_backed_history_comparisons_remain_allowed(self):
        report = (
            "- prior formal sessions: 9\n"
            "Nearest prior sessions:\n- TPMS-NATURAL-013-20260925-015115\n"
            "Target vs prior same-cluster mean:\n- peak power mean: +1.000000"
        )
        for text in (
            RC_SUGGESTION,
            "Repeat and compare with the prior C1 mean.",
            "Repeat and compare with the nearest prior session.",
        ):
            with self.subTest(text=text):
                self.assertEqual(validate_history_experiment(text, history_report=report), text)

    def test_history_without_priors_still_rejects_unavailable_comparison(self):
        with self.assertRaises(SentinelExperimentGuardError):
            validate_history_experiment(
                "Repeat and compare with the prior mean.",
                history_report="- prior formal sessions: 0\n",
            )


if __name__ == "__main__":
    unittest.main()
