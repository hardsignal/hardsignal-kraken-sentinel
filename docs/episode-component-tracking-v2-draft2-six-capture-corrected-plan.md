# Corrected six-capture Draft 2 regression plan

New run at checkpoint `7e38dd9caeb19282ecaa7b5d8464074e77fa5986`.
The original NOT_READY six-capture regression and every investigation remain immutable.
The corrected JSON plan copies the original six captures, all 41 selected episodes,
candidate-context hashes, four arms, scientific semantics, and resource limits.
All 41 candidate-context hashes are checked before tests and case execution.

Exactly 164 cases: connected and compact margins 0, 0.25, and 1 for every episode.
No reselection, width/detector/representation sweep, capture, detection, or full matrix.
Eligibility |f| 100..11500 Hz; width <=200 Hz; step <=50 Hz; fragment increment 1 or 2;
coherent range <=100 Hz; persistence >=3; coverage >=60%. Candidate identities,
fragment denominator, path/singleton/unordered-partition semantics, and binary64
scientific arithmetic are unchanged.

Counting limits: 250,000 live states; 5,000,000 transitions; 60 seconds; 32 MiB
packed polynomials. Queries: 5,000 public calls and 120 seconds. Construction:
60 seconds. Each execution/reload worker: 400 seconds and 512 MiB observed RSS.
Limits are fixed before execution and never adjusted after outcomes.

Dispatch composes committed V3 short-path certificates with V2/dyadic/monotone
binary64 fallback and the committed E05 cutoff composition. The general exact
candidate-cover query engine runs every case. No case IDs or expected counts are
used in computational dispatch; named control values are validation assertions only.

Pre-run gate: exact solver/count/column, staged/sidecar, monotone pivot, REPL E02,
E03 query and count v1/v2/v3, E05 cutoff, limited regression, historical six-capture,
and corrected-run tests must have zero failures/errors. Historical seven-episode
controls are evaluated first. Every new case requires deterministic byte-identical
staged reload and historical scientific payload parity. Compact families must also
be byte-identical to original families. Previously incomplete query outputs must
match the committed E03 query milestone. All previously exact sub-operations remain
unchanged. Mandatory cardinalities and E03 1,012-call/status/primary controls gate
readiness. Every case records measurements, states, backend and certificate.

The baseline JSON hashes every pre-existing tracked file before execution.
Final audit requires unchanged tracked bytes and HEAD, valid source/artifact hashes,
`git diff --check`, and independent whitespace checks on all new files. Only all
164 passing cases plus every control and integrity gate permit
`READY_FOR_DRAFT2_FULL_MATRIX_REVIEW`; any failure means `NOT_READY`.
No commit or push.
