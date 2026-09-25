import contextlib
import io
import unittest
from unittest.mock import patch

from ai import cli
from ai.output_guard import SentinelOutputGuardError


class CLITests(unittest.TestCase):
    @patch("ai.cli.generate_grounded_report")
    @patch("ai.cli.build_analyst_prompt")
    @patch("ai.cli.build_evidence_bundle")
    def test_success(
        self,
        build_bundle,
        build_prompt,
        generate,
    ):
        build_bundle.return_value = {"session_id": "TEST"}
        build_prompt.return_value = "PROMPT"
        generate.return_value = "GROUNDED REPORT"

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = cli.main(["--session", "TEST"])

        self.assertEqual(status, 0)
        self.assertIn("SENTINEL AI v0.1", output.getvalue())
        self.assertIn("GROUNDED REPORT", output.getvalue())

    @patch("ai.cli.build_evidence_bundle")
    def test_missing_session_fails(self, build_bundle):
        build_bundle.side_effect = FileNotFoundError("missing")

        error = io.StringIO()

        with contextlib.redirect_stderr(error):
            status = cli.main(["--session", "MISSING"])

        self.assertEqual(status, 2)
        self.assertIn("SENTINEL_AI_ERROR", error.getvalue())

    @patch("ai.cli.generate_grounded_report")
    @patch("ai.cli.build_analyst_prompt")
    @patch("ai.cli.build_evidence_bundle")
    def test_guard_rejection_is_not_published(
        self,
        build_bundle,
        build_prompt,
        generate,
    ):
        build_bundle.return_value = {"session_id": "TEST"}
        build_prompt.return_value = "PROMPT"
        generate.side_effect = SentinelOutputGuardError(
            "unsupported claim"
        )

        error = io.StringIO()

        with contextlib.redirect_stderr(error):
            status = cli.main(["--session", "TEST"])

        self.assertEqual(status, 3)
        self.assertIn(
            "SENTINEL_AI_FINAL_REJECT",
            error.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
