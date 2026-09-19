# Kraken Between-Device Discrimination V1 — Replication Result

## Experimental status

Independent held-out replication completed under the frozen
Between-Device Discrimination V1 methodology.

Capture:

    BETWEEN-DEVICE-REPL-V1-20260919-024341

Provenance verification:

    PASS

New IQ files:

    35

Candidate episodes after frozen Episode Grouping V1:

    7

Frozen Episode Features V1 format:

    HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V1

Sample rate:

    25,000 Hz

## Frozen episode measurements

| Episode | median_strongest_component_offset_hz | strongest_component_offset_spread_hz |
|---|---:|---:|
| E01 | -5327.062162 | 28.609356 |
| E02 | -5328.778724 | 29.753731 |
| E03 | -5325.345601 | 102.993683 |
| E04 | -5347.660899 | 26.320608 |
| E05 | -5341.939028 | 21.743111 |
| E06 | -5346.516525 | 40.053099 |
| E07 | -12455.369404 | 0.000000 |

E07 is retained. No post-hoc outlier removal was performed.

## Replication capture-level summary

Capture-level median:

    -5341.939028 Hz

Minimum episode median:

    -12455.369404 Hz

Maximum episode median:

    -5325.345601 Hz

Capture-level range:

    7130.023803 Hz

## Prior same-source reference

The pre-existing same-source capture-level medians are:

- Capture 004: -5203.469743 Hz
- Capture 005: -5193.170374 Hz
- Capture 007: -5201.180994 Hz

These were established before the held-out experiments.

## Comparison with prior same-source captures

| Prior capture | Prior median (Hz) | Replication minus prior (Hz) | Absolute difference (Hz) |
|---|---:|---:|---:|
| Capture 004 | -5203.469743 | -138.469285 | 138.469285 |
| Capture 005 | -5193.170374 | -148.768654 | 148.768654 |
| Capture 007 | -5201.180994 | -140.758034 | 140.758034 |

Nearest absolute difference to a prior same-source capture:

    138.469285 Hz

## Comparison with first held-out capture

First held-out capture-level median:

    -5419.756477 Hz

Replication capture-level median:

    -5341.939028 Hz

Replication minus first held-out:

    77.817449 Hz

Absolute difference:

    77.817449 Hz

This value is an observed difference between two held-out
experiments. It is not an identity threshold and must not be
converted into one.

## Descriptive interpretation

The replication capture-level median remains separated from all three
pre-existing same-source capture-level medians under the tested
conditions.

The replication therefore provides additional descriptive evidence
consistent with between-device separation of the frozen spectral
feature under these experimental conditions.

However, the two held-out capture-level medians differ by 77.817449 Hz.
This demonstrates that the observed feature varies between the two
held-out acquisitions and reinforces that the experiment does not
establish a universal device-separation threshold.

No numerical discrimination PASS/FAIL threshold is defined in V1.

## Provenance

The replication capture was verified with:

    python3 capture/verify_capture.py \
      captures/BETWEEN-DEVICE-REPL-V1-20260919-024341

Verification result:

    VERIFICATION: PASS

The capture reported:

- 35 new IQ files
- 0 changed pre-existing IQ files
- unchanged Kraken settings
- matching Git HEAD at capture start and finish
- successful SHA-256 verification of all recorded IQ files

Frozen Episode Grouping V1 was used with:

    inter-file gap > 4.000 seconds

Frozen Episode Features V1 was used without modification.

## Limitations

This replication does not establish:

- unique device identity;
- a production fingerprint;
- a universal same-device threshold;
- a universal different-device threshold;
- packet identity;
- exact RF emission time;
- transmitter location.

The large-spread and single-file E07 observation is retained because
the frozen protocol prohibits post-hoc outlier removal.

Further independent replication is required before stronger
discrimination claims are considered.

## Reproduction

Grouping:

    python3 capture/group_episodes.py --write \
      captures/BETWEEN-DEVICE-REPL-V1-20260919-024341

Feature extraction:

    python3 analysis/episode_features_v1.py --write \
      captures/BETWEEN-DEVICE-REPL-V1-20260919-024341

The source capture bundle remains the provenance record.
Large IQ files remain outside Git.
