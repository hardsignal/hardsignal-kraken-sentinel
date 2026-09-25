import contextlib
import io
import unittest
from unittest.mock import patch

from ai import cli
from ai.experiment_guard import SentinelExperimentGuardError
from ai.llm_client import SentinelLLMError


class CLITests(unittest.TestCase):
    @patch("ai.cli.compose_final_report")
    @patch("ai.cli.suggest_experiment_from_prompt")
    @patch("ai.cli.build_experiment_prompt")
    @patch("ai.cli.verify_model_digest")
    @patch("ai.cli.build_evidence_bundle")
    def test_success(
        self,
        build_bundle,
        verify_digest,
        build_prompt,
        suggest,
        compose,
    ):
        bundle = {"session_id": "TEST"}

        build_bundle.return_value = bundle
        verify_digest.return_value = "digest123"
        build_prompt.return_value = "PROMPT"
        suggest.return_value = "EXPERIMENT"
        compose.return_value = "FINAL REPORT"

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = cli.main(["--session", "TEST"])

        self.assertEqual(status, 0)
        verify_digest.assert_called_once_with()
        suggest.assert_called_once_with("PROMPT")
        compose.assert_called_once_with(bundle, "EXPERIMENT")
        self.assertIn("FINAL REPORT", output.getvalue())

    @patch("ai.cli.build_evidence_bundle")
    def test_missing_session_fails(self, build_bundle):
        build_bundle.side_effect = FileNotFoundError("missing")

        error = io.StringIO()

        with contextlib.redirect_stderr(error):
            status = cli.main(["--session", "MISSING"])

        self.assertEqual(status, 2)
        self.assertIn("SENTINEL_AI_ERROR", error.getvalue())

    @patch("ai.cli.verify_model_digest")
    @patch("ai.cli.build_evidence_bundle")
    def test_model_digest_failure_is_not_published(
        self,
        build_bundle,
        verify_digest,
    ):
        build_bundle.return_value = {"session_id": "TEST"}
        verify_digest.side_effect = SentinelLLMError(
            "model digest mismatch"
        )

        output = io.StringIO()
        error = io.StringIO()

        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(error),
        ):
            status = cli.main(["--session", "TEST"])

        self.assertEqual(status, 4)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("SENTINEL_AI_LLM_ERROR", error.getvalue())

    @patch("ai.cli.suggest_experiment_from_prompt")
    @patch("ai.cli.build_experiment_prompt")
    @patch("ai.cli.verify_model_digest")
    @patch("ai.cli.build_evidence_bundle")
    def test_experiment_rejection_is_not_published(
        self,
        build_bundle,
        verify_digest,
        build_prompt,
        suggest,
    ):
        build_bundle.return_value = {"session_id": "TEST"}
        verify_digest.return_value = "digest123"
        build_prompt.return_value = "PROMPT"
        suggest.side_effect = SentinelExperimentGuardError(
            "prohibited experiment goal"
        )

        output = io.StringIO()
        error = io.StringIO()

        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(error),
        ):
            status = cli.main(["--session", "TEST"])

        self.assertEqual(status, 6)
        self.assertEqual(output.getvalue(), "")
        self.assertIn(
            "SENTINEL_AI_EXPERIMENT_REJECT",
            error.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
