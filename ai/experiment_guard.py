"""Validation for Sentinel AI next-experiment suggestions."""

import re


class SentinelExperimentGuardError(ValueError):
    pass


# Each family ties a prohibited inference to a predicate or scientific object.
# Whole-word boundaries avoid rejecting words such as "classification" inside
# "burst classifications", or "cause" inside "causeway".
SCIENTIFIC_CLAIMS = {
    "device or fingerprint identity": (
        r"\b(?:identify|identifies|identified|identifying)\b[^.;!?\n]{0,60}"
        r"\b(?:transmitter|device|source|emitter)\b|"
        r"\b(?:transmitter|device|source|fingerprint)\s+identit(?:y|ies)\b|"
        r"\b(?:this|it|signal|source|cluster\s+C?\d+)\s+(?:is|matches|identifies)\s+"
        r"(?:the\s+|a\s+)?(?:device|transmitter|emitter)\b|"
        r"\b(?:same|unique|distinctive)\s+(?:device|transmitter|RF\s+fingerprint|fingerprint)\b|"
        r"\b(?:device|transmitter|RF)\s+fingerprint\b|"
        r"\b(?:device|transmitter|source)\s+(?:has\s+been|is|was)\s+identified\b"
    ),
    "unsupported causal explanation": (
        r"\b(?:caused?|causes|causing|due\s+to|because\s+of|attributable\s+to|"
        r"results?\s+from|resulted\s+from|explains?|explained\s+by)\b|"
        r"\b(?:indicates?|implies?|suggests?|reflects?|demonstrates?|confirms?)\b"
        r"[^.;!?\n]{0,60}\b(?:interference|multipath|reflections?|propagation|"
        r"scattering|environmental\s+(?:effects?|conditions?))\b"
    ),
    "directional accuracy": (
        r"\b(?:directional|absolute|bearing|DoA)\s+accuracy\b|"
        r"\bcalibration[- ]grade\b|\b(?:true|absolute)\s+(?:direction|bearing|azimuth)\b|"
        r"\b(?:bearing|direction|DoA|azimuth)\b[^.;!?\n]{0,60}"
        r"\b(?:calibrated|accurate|accuracy|ground\s+truth)\b"
    ),
    "classification or separation capability": (
        r"\b(?:device|transmitter|source)\s+classification\b|"
        r"\b(?:classes|devices|transmitters|sources)\s+(?:are|appear)\s+"
        r"(?:separable|distinguishable|distinct)\b|"
        r"\b(?:discriminat(?:ion|ive|es?|ing)|class[- ]separat(?:ion|ing))\b|"
        r"\b(?:distinguish|distinguishes|distinguishable|separates?|separating|classif(?:y|ies))\b"
        r"[^.;!?\n]{0,60}\b(?:devices?|transmitters?|sources?|classes?)\b|"
        r"\b(?:prove|proves|demonstrate|demonstrates|establish|establishes|confirm|confirms)\b"
        r"[^.;!?\n]{0,60}\b(?:classification|separation)\b"
    ),
    "physical source reliability or stability": (
        r"\b(?:stable|reliable|consistent|well[- ]behaved)\s+"
        r"(?:(?:or|and)\s+(?:stable|reliable|identified)\s+)?"
        r"(?:physical\s+|signal\s+)?(?:source|transmitter|device|emitter)\b|"
        r"\b(?:source|transmitter|device|emitter)\s+"
        r"(?:(?:is|was|seems|appears|remains)\s+(?:to\s+be\s+)?(?:a\s+)?|has\s+)"
        r"(?:stable|reliable|consistent|stability|reliability|well[- ]behaved)\b|"
        r"\b(?:source|transmitter|device|emitter)\s+(?:stability|reliability)\b|"
        r"\b(?:stability|reliability)\s+of\s+(?:the\s+|a\s+)?"
        r"(?:physical\s+|signal\s+)?(?:source|transmitter|device|emitter)\b"
    ),
    "physical conclusion from a cluster": (
        r"\b(?:cluster\s+C?\d+|C\d+)\s+(?:means|proves|indicates|implies|"
        r"represents|identifies|corresponds\s+to)\b[^.;!?\n]{0,80}"
        r"\b(?:device|transmitter|source|vehicle|sensor|interference|environment)\b"
    ),
}

# Negation must govern the matched claim, not occur elsewhere in the sentence.
# In particular, "does not rule out" and "not only" are not denials.
DENIAL_PREFIX = re.compile(
    r"\b(?:(?:does|do|did|is|are|was|were)\s+not|cannot|can\s+not|"
    r"doesn't|don't|can't|never|no|no\s+evidence\s+(?:of|for))"
    r"\s+(?:(?:establish|confirm|demonstrate|prove|support|infer|imply|claim)\s+)?"
    r"(?:(?:a|an|the|any)\s+)?$", re.IGNORECASE,
)
DENIAL_SUFFIX = re.compile(
    r"^\s+(?:inference\s+)?(?:is|are)\s+(?:not\s+(?:established|supported|demonstrated|confirmed)|"
    r"unsupported)\s*[.!?]?$", re.IGNORECASE,
)


def scientific_claim_violations(text, patterns=SCIENTIFIC_CLAIMS):
    violations = []
    # Separate independent assertions so a negated boundary cannot license a
    # positive claim after a conjunction or in another sentence.
    clauses = re.split(r"(?<=[.!?])\s+|[,;\n]|\b(?:but|however|yet|and)\b", text,
                       flags=re.IGNORECASE)
    for clause in clauses:
        for label, pattern in patterns.items():
            for match in re.finditer(pattern, clause, flags=re.IGNORECASE):
                if re.search(
                    r"\b(?:is|was|are|were)\s+not\s+(?:calibrated|accurate)\b$",
                    match.group(0), flags=re.IGNORECASE,
                ):
                    continue
                if DENIAL_PREFIX.search(clause[:match.start()]):
                    continue
                if DENIAL_SUFFIX.fullmatch(clause[match.end():]):
                    continue
                violations.append(f"{label}: {match.group(0)!r}")
    return violations


EXPERIMENT_BOUNDARY = (
    "Only propose measurements and comparisons of supplied behavioural quantities. "
    "Do not claim device/fingerprint identity, physical source reliability, "
    "causal RF or environmental explanations, true directional accuracy, or "
    "classification/discrimination capability. Cluster labels describe measured "
    "behaviour, not physical identity or causes. A result may be reproducibly "
    "different from a prior mean without demonstrating class separation. "
    "Explicit statements that these conclusions are not supported are allowed.\n"
)


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

    violations = scientific_claim_violations(text)
    if violations:
        raise SentinelExperimentGuardError(
            f"unsupported experiment claim: {violations}"
        )

    if not MEASUREMENT_WORDS.search(text):
        raise SentinelExperimentGuardError(
            "experiment suggestion contains no measurable action"
        )

    return text
