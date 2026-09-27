"""Local Ollama client for Sentinel AI."""

import json
from urllib import error, request

from ai.output_guard import validate_generated_report


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:14b"
EXPECTED_MODEL_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"


class SentinelLLMError(RuntimeError):
    pass


def get_model_digest(
    *,
    model=DEFAULT_MODEL,
    base_url=DEFAULT_BASE_URL,
    timeout=10,
):
    req = request.Request(
        f"{base_url}/api/tags",
        method="GET",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            record = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SentinelLLMError(
            f"Could not read Ollama model inventory: {exc}"
        ) from exc

    for item in record.get("models", []):
        if item.get("name") == model:
            digest = item.get("digest")
            if isinstance(digest, str) and digest:
                return digest

    raise SentinelLLMError(
        f"Ollama model not found or missing digest: {model}"
    )


def verify_model_digest(
    *,
    model=DEFAULT_MODEL,
    expected=EXPECTED_MODEL_DIGEST,
    base_url=DEFAULT_BASE_URL,
):
    actual = get_model_digest(
        model=model,
        base_url=base_url,
    )

    if actual != expected:
        raise SentinelLLMError(
            "Ollama model digest mismatch: "
            f"expected {expected}, got {actual}"
        )

    return actual


def generate_text(
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

    return text.strip()


def generate_report(
    prompt,
    *,
    model=DEFAULT_MODEL,
    base_url=DEFAULT_BASE_URL,
    timeout=180,
):
    text = generate_text(
        prompt,
        model=model,
        base_url=base_url,
        timeout=timeout,
    )
    return validate_generated_report(text)
