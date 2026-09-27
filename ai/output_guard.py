"""Deterministic validation of Sentinel AI generated reports."""

import re


REQUIRED_HEADINGS = (
    "Summary",
    "Evidence",
    "Interpretation",
    "Uncertainty",
    "Next controlled experiment",
    "Scientific boundary",
)

CLAIM_SECTIONS = (
    "Summary",
    "Evidence",
    "Interpretation",
    "Uncertainty",
)

SOURCE_PROPERTIES = (
    r"stable|reliable|well[- ]behaved|identified|known|consistent"
)

SOURCE_PROPERTY_PATTERNS = (
    re.compile(
        rf"\b(?:{SOURCE_PROPERTIES})"
        rf"(?:\s+(?:or|and)\s+(?:{SOURCE_PROPERTIES}))*"
        r"\s+(?:signal source|transmitter)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:signal source|transmitter)\s+"
        r"(?:is|was|appears(?:\s+to\s+be)?|seems(?:\s+to\s+be)?)\s+"
        rf"(?:{SOURCE_PROPERTIES})\b",
        flags=re.IGNORECASE,
    ),
)

NEGATION_PATTERN = re.compile(
    r"\b(?:does not|doesn't|do not|did not|cannot|can not|"
    r"is not|was not|are not|were not|"
    r"not established|not supported|not confirmed|"
    r"no evidence)\b",
    flags=re.IGNORECASE,
)

UNSUPPORTED_CAUSAL_PATTERNS = {
    "unsupported environmental explanation": (
        r"\b(?:does not rule out|cannot rule out|may|might|could|possibly|"
        r"potentially)\b[^.\n]{0,120}\benvironmental "
        r"(?:effect|effects|condition|conditions|cause|causes)\b"
    ),
    "unsupported transient explanation": (
        r"\b(?:does not rule out|cannot rule out|may|might|could|possibly|"
        r"potentially)\b[^.\n]{0,120}\btransient effects?\b"
    ),
    "unsupported unobserved hypothesis": (
        r"\b(?:does not (?:rule out|exclude|eliminate)|"
        r"cannot (?:rule out|exclude|eliminate)|"
        r"may|might|could|possibly|potentially)\b"
        r"[^.\n]{0,140}"
        r"\b(?:unobserved|unknown|unmeasured)\b"
    ),
    "unsupported environment property": (
        r"\b(?:clean|stable|consistent|quiet|noisy|reliable)\s+"
        r"(?:signal\s+)?environment\b"
    ),
}


class SentinelOutputGuardError(ValueError):
    pass


def extract_sections(text):
    pattern = re.compile(
        r"(?im)^\s*(?:\*\*)?"
        r"(Summary|Evidence|Interpretation|Uncertainty|"
        r"Next controlled experiment|Scientific boundary)"
        r"(?:\*\*)?\s*$"
    )

    matches = list(pattern.finditer(text))
    sections = {}

    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        sections[match.group(1)] = text[start:end].strip()

    return sections


def validate_generated_report(text):
    if not isinstance(text, str) or not text.strip():
        raise SentinelOutputGuardError("generated report is empty")

    sections = extract_sections(text)

    missing = [
        heading
        for heading in REQUIRED_HEADINGS
        if heading not in sections
    ]

    if missing:
        raise SentinelOutputGuardError(
            f"missing required headings: {missing}"
        )

    claim_text = "\n".join(
        sections[name]
        for name in CLAIM_SECTIONS
    )

    violations = []

    sentences = re.split(r"(?<=[.!?])\s+|\n+", claim_text)

    for sentence in sentences:
        for pattern in SOURCE_PROPERTY_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue

            prefix = sentence[
                max(0, match.start() - 160):match.start()
            ]

            if NEGATION_PATTERN.search(prefix):
                continue

            violations.append(
                "unsupported source-property claim: "
                f"{sentence.strip()!r}"
            )
            break

    for label, pattern in UNSUPPORTED_CAUSAL_PATTERNS.items():
        match = re.search(
            pattern,
            claim_text,
            flags=re.IGNORECASE,
        )

        if match:
            violations.append(
                f"{label}: {match.group(0)!r}"
            )

    if violations:
        raise SentinelOutputGuardError(
            f"unsupported or prohibited claims: {violations}"
        )

    return text.strip()
