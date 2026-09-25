"""Guarded Sentinel AI report generation with one repair opportunity."""

from ai.llm_client import generate_report
from ai.output_guard import SentinelOutputGuardError


def generate_grounded_report(
    prompt,
    *,
    max_attempts=2,
    generate_fn=None,
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if generate_fn is None:
        generate_fn = generate_report

    current_prompt = prompt
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return generate_fn(current_prompt)
        except SentinelOutputGuardError as exc:
            last_error = exc

            if attempt == max_attempts:
                raise

            current_prompt = (
                prompt
                + "\n\nREPAIR INSTRUCTION:\n"
                + "A previous draft was rejected by the deterministic "
                  "Sentinel output guard.\n"
                + f"Rejection reason: {exc}\n\n"
                + "Generate a fresh report from the SAME authoritative "
                  "evidence.\n"
                + "Remove the rejected unsupported claim.\n"
                + "Do not replace it with another hypothetical cause, "
                  "unobserved possibility, or source-property claim.\n"
                + "Do not change any numerical evidence, cluster assignment, "
                  "novelty status, or provenance.\n"
                + "Use the required headings exactly.\n"
            )

    raise last_error
