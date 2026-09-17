# Episode Grouping V1 — Capture 004 Validation Status

Status: COUNT-CONCORDANT CONTROLLED VALIDATION

Capture ID:

    PIPELINE-TPMS-004-20260917-233423

The controlled activation logger completed normally with six operator
activation markers (A1 through A6).

Capture provenance verification passed:

- IQ files before capture: 630
- IQ files after capture: 660
- New IQ recorder files: 30
- Changed pre-existing IQ files: 0
- Kraken settings unchanged: True
- Git start and finish revision identical
- IQ size and SHA-256 verification passed
- files.sha256 verification passed

The frozen Episode Grouping V1 implementation was used without
modification.

Frozen rule:

    Start a new candidate episode when inter-file gap > 4.000 seconds.

Frozen grouper SHA-256:

    c14586d6304eca3ea906b320f43607ffe6a982929b6bdacd9adb71f973fe98e6

Frozen activation logger SHA-256:

    bc713946f2181e59c23a37d1b04a83ee35a0994aff8b908b72d66f0dc80034d5

Observed result:

- Controlled operator activation markers: 6
- Kraken IQ recorder files: 30
- Candidate episodes: 6

Episode file counts:

    E01: 5
    E02: 5
    E03: 5
    E04: 5
    E05: 6
    E06: 4

Therefore Capture 004 produced count concordance between six controlled
operator activations and six candidate episodes under the frozen
Episode Grouping V1 rule.

Interpretation is deliberately limited. A candidate episode is a
deterministic temporal grouping of Kraken recorder files. This result
does not establish that a candidate episode universally corresponds
one-to-one with a physical activation, RF transmission, packet/frame,
or device.

No device-identity, unique-fingerprint, or transmitter-location claim
is made.
