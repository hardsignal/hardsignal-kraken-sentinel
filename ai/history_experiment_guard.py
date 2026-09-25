"""Validation for history-grounded Sentinel AI v0.2 experiments."""

from ai.experiment_guard import (
    SentinelExperimentGuardError,
    validate_experiment_suggestion,
    scientific_claim_violations,
)


UNSUPPORTED_HISTORY_PATTERNS = {
    "invented reflectivity variable": r"\breflectiv(?:ity|e)\b",
    "directional accuracy claim": r"\bdirectional accuracy\b",
    "absolute accuracy claim": r"\babsolute accuracy\b",
    "invented propagation cause": (
        r"\b(?:propagation|reflection|reflections|scattering)\b"
    ),
}


def validate_history_experiment(text, *, history_report=None):
    text = validate_experiment_suggestion(text)

    violations = scientific_claim_violations(text, UNSUPPORTED_HISTORY_PATTERNS)
    if history_report is not None:
        unavailable = {}
        if "- prior formal sessions: 0" in history_report:
            unavailable["no prior historical comparison available"] = (
                r"\b(?:prior|previous|earlier|nearest)\b[^.;!?\n]{0,40}"
                r"\b(?:mean|average|sessions?|neighbou?rs?|baseline)\b"
            )
        elif "- unavailable; no prior same-cluster sessions" in history_report:
            unavailable["no prior same-cluster mean available"] = (
                r"\bprior\s+(?:same[- ]cluster|C\d+)\s+(?:mean|average)\b"
            )
        violations.extend(scientific_claim_violations(text, unavailable))

    if violations:
        raise SentinelExperimentGuardError(
            f"unsupported historical experiment claim: {violations}"
        )

    return text
