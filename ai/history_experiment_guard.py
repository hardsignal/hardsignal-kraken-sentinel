"""Validation for history-grounded Sentinel AI v0.2 experiments."""

import re

from ai.experiment_guard import (
    SentinelExperimentGuardError,
    validate_experiment_suggestion,
)


UNSUPPORTED_HISTORY_PATTERNS = {
    "invented reflectivity variable": r"\breflectiv(?:ity|e)\b",
    "directional accuracy claim": r"\bdirectional accuracy\b",
    "absolute accuracy claim": r"\babsolute accuracy\b",
    "invented propagation cause": (
        r"\b(?:propagation|reflection|reflections|scattering)\b"
    ),
}


def validate_history_experiment(text):
    text = validate_experiment_suggestion(text)

    violations = []

    for label, pattern in UNSUPPORTED_HISTORY_PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            violations.append(
                f"{label}: {match.group(0)!r}"
            )

    if violations:
        raise SentinelExperimentGuardError(
            f"unsupported historical experiment claim: {violations}"
        )

    return text
