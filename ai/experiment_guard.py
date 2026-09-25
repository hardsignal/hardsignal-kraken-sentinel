"""Validation for Sentinel AI next-experiment suggestions."""

import re


class SentinelExperimentGuardError(ValueError):
    pass


FORBIDDEN_GOALS = {
    "transmitter identification": (
        r"\b(?:identify|determine|confirm|establish)\b"
        r"[^.\n]{0,80}\b(?:transmitter|signal source)\s+identity\b"
    ),
    "absolute direction claim": (
        r"\b(?:determine|confirm|establish|measure)\b"
        r"[^.\n]{0,80}\bcalibration[- ]grade absolute direction\b"
    ),
}

MEASUREMENT_WORDS = re.compile(
    r"\b(?:measure|record|collect|compare|observe|capture|"
    r"quantify|evaluate|assess|reacquire|repeat)\b",
    flags=re.IGNORECASE,
)


def validate_experiment_suggestion(text):
    if not isinstance(text, str) or not text.strip():
        raise SentinelExperimentGuardError(
            "experiment suggestion is empty"
        )

    text = text.strip()

    if len(text) > 1500:
        raise SentinelExperimentGuardError(
            "experiment suggestion is too long"
        )

    for label, pattern in FORBIDDEN_GOALS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raise SentinelExperimentGuardError(
                f"prohibited experiment goal: {label}: "
                f"{match.group(0)!r}"
            )

    if not MEASUREMENT_WORDS.search(text):
        raise SentinelExperimentGuardError(
            "experiment suggestion contains no measurable action"
        )

    return text
