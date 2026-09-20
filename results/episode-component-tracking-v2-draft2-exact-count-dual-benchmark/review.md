# Exact retained-family counting review

Only the committed compact TPMS-008 E08 family models were tested. No full experiment or RF capture was run.
Validation: 17 tests passed. All counts use arbitrary-precision integers; JSON counts are decimal strings.

| Scope | Margin | Exact count | State | Count seconds | Process peak RSS KiB |
|---|---:|---:|---|---:|---:|
| group | 0.0 | 1 | EXACT | 0.505876 | 38156 |
| group | 0.25 | 191532581516 | EXACT | 0.444410 | 43368 |
| group | 1.0 | null | COMPUTATION_UNRESOLVED | 0.087659 | 62944 |
| episode | 0.0 | 2 | EXACT | 1.604546 | 62944 |
| episode | 0.25 | 17067800502243 | EXACT | 0.503482 | 62944 |
| episode | 1.0 | null | COMPUTATION_UNRESOLVED | 0.316028 | 68184 |

RSS is the process high-water mark, cumulative across cases, not isolated per-case memory. Timing includes exact counting and coefficient certification; family loading is recorded separately.
Limits were fixed before counting: 250,000 simultaneously tracked states, 5,000,000 transitions, 60 seconds per count, 32 MiB packed polynomial storage. Hitting a limit yields no partial count.

## Blockers
- group margin 1.0: {"elapsed_seconds": 0.08628193198819645, "limit": 250000, "location": {"component": "factor0/block0", "future_columns": 52, "integer_budget": 11931, "next_states": 211171, "phase": "matching frontier", "prior_states": 39964, "row": 5, "rows": 18}, "peak_states": 251135, "reason": "frontier/state budget exceeded", "states": 251135, "transitions": 433774}
- episode margin 1.0: {"elapsed_seconds": 0.3139028229925316, "limit": 250000, "location": {"component": "factor2/block0", "future_columns": 52, "integer_budget": 11931, "next_states": 211171, "phase": "matching frontier", "prior_states": 39964, "row": 5, "rows": 18}, "peak_states": 251135, "reason": "frontier/state budget exceeded", "states": 251135, "transitions": 1944070}

Exact membership, invariance and ambiguity functionality remains in the unchanged committed solver. A counting failure does not replace those functions or change a primary decision.
The minimal proposed schema change is a versioned sidecar referencing the immutable family and model hashes, with decimal exact cardinality or explicit COMPUTATION_UNRESOLVED state and resource diagnostics. Exact counts may never be replaced by lower bounds or estimates.
Compact models plus a completed exact count can replace expanded lists only after explicit schema adoption, provided required membership/quality/track outputs remain present and validators verify the predicate. Unresolved counts leave the original exact-count requirement unsatisfied.
We are not declaring readiness to rerun all 160 arms. No parameters, historical results or committed files were changed.
