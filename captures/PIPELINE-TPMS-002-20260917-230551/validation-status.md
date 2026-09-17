# Episode Grouping V1 — Capture 002 Validation Status

Status: INVALID / INCONCLUSIVE FOR EPISODE-GROUPING VALIDATION

Capture provenance remains independently testable.

Reason:

The independently recorded operator activation timeline contains an
unresolved timestamp inconsistency.

During acquisition, A1 was displayed in the terminal as:

    2026-09-17T23:08:37,088048814+01:00

The subsequently printed ground-truth log contained A1 as:

    2026-09-17T23:06:21,884857507+01:00

Additionally, Kraken IQ recording activity was observed beginning around
23:08:10, preventing an unambiguous mapping between the intended
activation sequence and recorder episodes.

Therefore this capture must not be used to pass, fail, tune, or modify
the frozen 4.000-second Episode Grouping V1 rule.

No identity or fingerprint conclusion is made.

The raw IQ evidence and provenance metadata are retained.
