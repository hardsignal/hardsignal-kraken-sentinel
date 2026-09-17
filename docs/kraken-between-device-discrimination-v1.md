# Kraken Between-Device Discrimination V1

## Purpose

Test whether the frozen Episode Features V1 spectral measurement that has
shown same-source repeatability also shows useful separation when applied
to a different owned controlled TPMS sensor.

This is a held-out between-device descriptive experiment.

It is not an identity classifier.

## Development / prior evidence

The existing same-source evidence consists of Captures 004, 005, and 007.

Their capture-level medians of
median_strongest_component_offset_hz are:

- Capture 004: -5203.469743 Hz
- Capture 005: -5193.170374 Hz
- Capture 007: -5201.180994 Hz

Observed range of these three capture-level medians:

    10.299368 Hz

These values motivated the between-device experiment.

They MUST NOT be converted after the fact into an identity or
same-device acceptance threshold.

## Held-out source

Use a different owned controlled TPMS sensor from the source used for
Captures 004, 005, and 007.

The held-out sensor must be selected before acquisition begins.

Do not inspect new Episode Features V1 output from the held-out sensor
before the capture is complete and provenance is closed.

## Controlled acquisition

Use the existing Kraken configuration:

- VFO: 433.868160 MHz
- bandwidth: 25 kHz
- IQ recording: True
- squelch mode: Manual
- squelch: -45 dB

Do not intentionally move the Kraken antenna array.

Use the same controlled source position and orientation used for the
current same-source repeatability captures as closely as practicable.

Record any unavoidable geometry change.

## Controlled activations

Use eight controlled operator activation markers.

Frozen logger:

    capture/log_activations.py

Parameters:

    --count 8 --quiet 15

No additional controlled activations are permitted during the capture.

After A8, leave the capture running for at least 30 seconds before
finishing the provenance boundary.

## Provenance validity

The capture is suitable for analysis only if:

1. capture/verify_capture.py reports PASS;
2. Kraken settings are unchanged across the capture;
3. no pre-existing IQ file was modified;
4. every new Capture IQ file passes size and SHA-256 verification;
5. the controlled activation logger completes all eight markers;
6. the frozen analysis tools remain unchanged.

Aborted or invalid captures must be preserved as such and must not be
silently replaced or excluded.

## Frozen grouping

Use Episode Grouping V1 without modification:

    capture/group_episodes.py

Frozen rule:

    new candidate episode iff inter-file gap > 4.000 seconds

Report the resulting candidate-episode count.

Do not change the threshold to force agreement with the eight operator
markers.

## Frozen feature extraction

Use Episode Features V1 without modification:

    analysis/episode_features_v1.py

Primary spectral quantity:

    median_strongest_component_offset_hz

For the held-out capture report:

- every candidate episode value;
- capture-level median;
- minimum;
- maximum;
- range;
- strongest_component_offset_spread_hz for every episode.

Retain all observations, including large-spread observations.

No post-hoc outlier removal is permitted.

## Primary comparison

Compare the held-out sensor's capture-level median descriptively with
the existing same-source capture-level medians from Captures 004, 005,
and 007.

Report the signed and absolute difference between the held-out
capture-level median and each prior same-source capture-level median.

Also report the nearest absolute difference to any of the three prior
capture-level medians.

## Interpretation

No numerical discrimination PASS/FAIL threshold is defined in V1.

Therefore the result must be interpreted descriptively.

If the held-out sensor is clearly separated from the existing
same-source measurements, this is evidence that the frozen feature may
have between-device discriminatory value under the tested conditions.

If the held-out sensor overlaps or lies close to the existing
same-source measurements, the feature does not demonstrate useful
between-device separation in this test.

Either result must be retained.

The existing 10.299368 Hz same-source capture-median range is descriptive
prior evidence and is not an identity threshold.

## Limits

This experiment does not establish:

- unique device identity;
- a production fingerprint;
- a universal same-device threshold;
- a universal different-device threshold;
- packet identity;
- exact RF emission time;
- transmitter location.

A positive descriptive separation result requires independent replication
before stronger discrimination claims are considered.

## Freeze rule

This document must be committed and pushed before held-out acquisition.

The grouping rule, feature extractor, comparison quantities, and
interpretation procedure must not be changed after held-out data are
inspected.

Any changed experiment requires a new version.
