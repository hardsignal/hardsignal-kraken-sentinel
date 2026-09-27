import json
import unittest
from unittest.mock import MagicMock, patch

from ai.llm_client import (
    EXPECTED_MODEL_DIGEST,
    SentinelLLMError,
    generate_report,
    get_model_digest,
    verify_model_digest,
)


VALID_REPORT = """**Summary**
Coherent session.

**Evidence**
Evidence retained.

**Interpretation**
The session is consistent with the frozen training observations.

**Uncertainty**
No transmitter identity inference is supported.

**Next controlled experiment**
Repeat the controlled session.

**Scientific boundary**
This does not establish transmitter identity.
"""


class LLMClientTests(unittest.TestCase):
    @patch("ai.llm_client.request.urlopen")
    def test_ollama_request_and_response(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "response": VALID_REPORT,
        }).encode("utf-8")

        urlopen.return_value.__enter__.return_value = response

        result = generate_report(
            "TEST PROMPT",
            timeout=10,
        )

        self.assertEqual(result, VALID_REPORT.strip())

        req = urlopen.call_args.args[0]
        payload = json.loads(req.data.decode("utf-8"))

        self.assertEqual(payload["model"], "qwen3:14b")
        self.assertEqual(payload["prompt"], "TEST PROMPT")
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(payload["options"]["temperature"], 0)

    @patch("ai.llm_client.request.urlopen")
    def test_ollama_error_field_fails(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "error": "model unavailable",
        }).encode("utf-8")

        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(
            SentinelLLMError,
            "model unavailable",
        ):
            generate_report("prompt")

    @patch("ai.llm_client.request.urlopen")
    def test_model_digest_inventory_lookup(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "models": [{
                "name": "qwen3:14b",
                "digest": EXPECTED_MODEL_DIGEST,
            }]
        }).encode("utf-8")

        urlopen.return_value.__enter__.return_value = response

        self.assertEqual(
            get_model_digest(),
            EXPECTED_MODEL_DIGEST,
        )

    @patch("ai.llm_client.get_model_digest")
    def test_model_digest_mismatch_fails(self, get_digest):
        get_digest.return_value = "wrong-digest"

        with self.assertRaisesRegex(
            SentinelLLMError,
            "digest mismatch",
        ):
            verify_model_digest()


    @patch("ai.llm_client.request.urlopen")
    def test_empty_response_fails(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            "response": "",
        }).encode("utf-8")

        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(
            SentinelLLMError,
            "no report text",
        ):
            generate_report("prompt")


if __name__ == "__main__":
    unittest.main()
