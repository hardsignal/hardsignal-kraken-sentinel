"""Local Ollama client for Sentinel AI."""

import json
from urllib import error, request

from ai.output_guard import validate_generated_report


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:14b"


class SentinelLLMError(RuntimeError):
    pass


def generate_report(
    prompt,
    *,
    model=DEFAULT_MODEL,
    base_url=DEFAULT_BASE_URL,
    timeout=180,
):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
        },
    }

    req = request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            record = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SentinelLLMError(f"Ollama request failed: {exc}") from exc

    if record.get("error"):
        raise SentinelLLMError(record["error"])

    text = record.get("response")
    if not isinstance(text, str) or not text.strip():
        raise SentinelLLMError("Ollama returned no report text")

    return validate_generated_report(text)
