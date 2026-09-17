# Kraken Episode Features V1 — Independent Repeat Protocol

## Purpose

Test whether the Episode Features V1 observations from Capture 004
reappear in a fresh controlled capture without modifying the frozen
grouping or feature-analysis methods.

This is an independent descriptive replication.

It is not a device-identification test and does not establish a unique
RF fingerprint.

## Frozen components

Episode Grouping V1:

    SHA-256
    c14586d6304eca3ea906b320f43607ffe6a982929b6bdacd9adb71f973fe98e6

Episode Features V1 specification:

    SHA-256
    f0bbc8f8c0dd179486979e9aee904bf3db5fee2717073a3406b65e6c636bc7dc

Episode Features V1 analyzer:

    SHA-256
    4528ccf87557426adf50be6cf2678597d320977b046011c38f8ab0103b371259

These components must not be changed for the replication.

## Reference observation

Capture 004 produced six candidate episodes.

Episode median strongest-component offsets were:

    E01  -5187.449 Hz
    E02  -5193.170 Hz
    E03  -5206.903 Hz
    E04  -5204.614 Hz
    E05  -5202.325 Hz
    E06  -5214.627 Hz

The observed Capture 004 episode-median range was approximately:

    27.18 Hz

Two individual fragments selected substantially different strongest
components. Those observations remain part of the V1 result and are
not excluded.

## Replication acquisition

Use the same owned controlled TPMS source.

Perform six controlled activations using the frozen activation logger.

Keep the validated Kraken acquisition configuration unchanged.

Do not intentionally move the antenna array or alter the controlled
geometry during the capture.

## Capture validity

The replication capture is usable only if:

- capture provenance verification passes
- Kraken settings are unchanged across the capture
- no pre-existing IQ files are modified
- all new IQ files pass recorded size and SHA-256 verification
- the activation logger completes all six markers
- the frozen grouper hash is unchanged
- the frozen Episode Features V1 analyzer hash is unchanged

An aborted or otherwise invalid capture is preserved and not used as
replication evidence.

## Episode grouping

Run Episode Grouping V1 unchanged.

Report:

- activation-marker count
- recorder-file count
- candidate-episode count

Episode-count concordance is descriptive and is reported separately
from spectral repeatability.

The >4.000 second grouping threshold must not be altered after
inspection of the replication capture.

## Episode Features V1

Run the frozen Episode Features V1 analyzer unchanged.

Preserve all fragment-level and episode-level measurements.

Do not remove fragments because they appear anomalous.

## Primary replication observation

The primary measurement is:

    episode median strongest-component frequency offset

For the replication capture report:

- each episode median
- capture median of the episode medians
- minimum episode median
- maximum episode median
- range of episode medians

Compare these descriptively with Capture 004.

## No post-hoc pass threshold

No numerical PASS/FAIL tolerance for spectral repeatability is defined
from Capture 004 alone.

Capture 005 is used as an independent replication from which
between-capture variability can begin to be estimated.

A quantitative validation tolerance, classifier, distance metric, or
identity threshold must not be selected after inspecting Capture 005
and then retroactively described as pre-registered.

## Secondary observations

Report, without filtering:

- fragment-level strongest-component offsets
- spectral spreads
- RMS magnitude
- mean magnitude
- median magnitude
- peak magnitude
- structural episode measurements

These are secondary descriptive observations.

## Interpretation limits

Replication of the approximately -5.2 kHz episode-level spectral
behaviour would demonstrate repeatability under the tested controlled
conditions.

It would not by itself establish:

- unique device identity
- between-device discrimination
- packet identity
- transmitter identity
- transmitter location
- a validated unique RF fingerprint
