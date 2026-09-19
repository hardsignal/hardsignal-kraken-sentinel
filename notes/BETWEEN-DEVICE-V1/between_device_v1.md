# Kraken Between-Device Discrimination V1 — Held-Out Result

## Experimental status

Held-out controlled TPMS sensor acquisition completed under the frozen
Between-Device Discrimination V1 protocol.

Capture:

    BETWEEN-DEVICE-V1-20260919-022917

Provenance verification:

    PASS

New IQ files:

    38

Candidate episodes after frozen Episode Grouping V1:

    7

Frozen Episode Features V1 format:

    HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V1

Sample rate:

    25,000 Hz

## Frozen episode measurements

| Episode | median_strongest_component_offset_hz | strongest_component_offset_spread_hz |
|---|---:|---:|
| E01 | -5420.900851 | 54.929964 |
| E02 | -5415.178980 | 13.732491 |
| E03 | -5419.756477 | 12.588117 |
| E04 | -5415.178980 | 50.352467 |
| E05 | -5420.328664 | 27.464982 |
| E06 | -5422.045226 | 5687.540053 |
| E07 | -5406.023986 | 38.908725 |

E06 is retained despite its large spread. No post-hoc outlier removal was
performed.

## Held-out capture-level summary

Capture-level median:

    -5419.756477 Hz

Minimum episode median:

    -5422.045226 Hz

Maximum episode median:

    -5406.023986 Hz

Capture-level range:

    16.021240 Hz

## Prior same-source reference

The pre-existing same-source capture-level medians are:

- Capture 004: -5203.469743 Hz
- Capture 005: -5193.170374 Hz
- Capture 007: -5201.180994 Hz

Their descriptive range is:

    10.299368 Hz

These values were established before the held-out acquisition and were
not converted into an identity threshold.

## Descriptive comparison

| Prior capture | Prior median (Hz) | Held-out minus prior (Hz) | Absolute difference (Hz) |
|---|---:|---:|---:|
| Capture 004 | -5203.469743 | -216.286734 | 216.286734 |
| Capture 005 | -5193.170374 | -226.586103 | 226.586103 |
| Capture 007 | -5201.180994 | -218.575483 | 218.575483 |

Nearest absolute difference:

    216.286734 Hz

## Interpretation

Under the tested conditions, the held-out capture-level median is
descriptively separated from all three prior same-source capture-level
medians.

This result is descriptive evidence that the frozen
median_strongest_component_offset_hz feature may have between-device
discriminatory value under these tested conditions.

No numerical discrimination PASS/FAIL threshold is defined in V1.

This result therefore does not establish a unique device identity
classifier, production fingerprint, universal same-device threshold, or
universal different-device threshold.

Independent replication is required before stronger discrimination claims
are considered.

## Provenance

The held-out capture was verified with:

    python3 capture/verify_capture.py \
      captures/BETWEEN-DEVICE-V1-20260919-022917

Verification result:

    VERIFICATION: PASS

The capture reported:

- 38 new IQ files
- 0 changed pre-existing IQ files
- unchanged Kraken settings
- matching Git HEAD at capture start and finish
- successful SHA-256 verification of all recorded IQ files

The frozen grouping and feature extraction procedures were not modified
for this result.

## Reproduction

Grouping:

    python3 capture/group_episodes.py --write \
      captures/BETWEEN-DEVICE-V1-20260919-022917

Feature extraction:

    python3 analysis/episode_features_v1.py --write \
      captures/BETWEEN-DEVICE-V1-20260919-022917

The source capture bundle remains the provenance record. Large IQ files
remain outside Git.
