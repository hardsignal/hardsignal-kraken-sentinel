# Kraken Episode Features V1

## Purpose

Define a frozen first-pass descriptive feature set for candidate Kraken
episodes produced by Episode Grouping V1.

The purpose is to measure repeatability across controlled episodes
without treating individual Kraken recorder fragments as independent
RF events.

This stage is descriptive. It does not establish device identity,
packet identity, transmitter location, or a unique RF fingerprint.

## Input

The analyzer consumes:

    captures/<capture-id>/episodes.json

Episode membership is taken exactly from the frozen Episode Grouping V1
output.

Raw IQ files referenced by episodes.json are read without modification.

## IQ interpretation

Format:

    NumPy complex128

Sample rate:

    25,000 complex samples/second

Recorder files are treated as gated fragments.

Files belonging to an episode MUST NOT be interpreted as one contiguous
time-domain recording merely because they belong to the same episode.

Features are calculated per fragment first and then summarized at the
episode level where appropriate.

## Episode structural features

For each candidate episode record:

- episode number
- number of recorder fragments
- filesystem episode span
- preceding inter-episode gap
- total IQ samples
- total recorded IQ duration
- minimum fragment duration
- maximum fragment duration
- median fragment duration

## Amplitude features

For each fragment calculate magnitude abs(IQ).

Episode summaries:

- RMS magnitude
- mean magnitude
- median magnitude
- peak magnitude

Amplitude measurements are descriptive only. They may depend on receiver
gain, propagation, orientation, distance, and recorder behaviour.

They are not identity features by themselves.

## Spectral features

For each fragment independently:

1. remove complex mean
2. apply a Hann window
3. calculate a power spectrum
4. determine the strongest non-DC spectral component

Episode summaries:

- median strongest-component frequency offset
- minimum strongest-component frequency offset
- maximum strongest-component frequency offset
- frequency-offset spread

Absolute RF carrier frequency is not used as a device-identity claim.

## Fragment-boundary rule

IQ from separate recorder files is never joined before time-domain or
spectral calculation.

Episode statistics summarize fragment-level measurements.

This avoids inventing samples across recorder gaps.

## Repeatability output

For a controlled capture containing multiple candidate episodes, report
the per-episode feature table.

Do not create a classifier, score, distance metric, threshold, or
device-identification decision in V1.

The first question is only:

    Which episode-level measurements are stable across repeated
    controlled activations under the tested conditions?

## Interpretation limits

A candidate episode is a deterministic temporal grouping of Kraken
recorder files.

It is not automatically equivalent to:

- one RF packet
- one RF frame
- one physical activation
- one transmitter
- one device

DoA, absolute power, and absolute carrier frequency remain contextual
measurements and must not independently be presented as device identity.

No unique fingerprint claim is permitted from Episode Features V1.
