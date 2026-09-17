# TPMS Spectral Topology V2 — Pre-Registered Hypothesis

Date: 17 September 2026

## Purpose

Stage 33 V1 showed that controlled Sensor 1 and Sensor 2 TPMS
transmissions contain repeatable short-event timing and recurring
spectral structure.

However, short-event duration and naive P1/P2 spectral spacing did not
discriminate Sensor 1 from Sensor 2 under the tested conditions.

V2 tests whether the geometry of multiple spectral components is more
informative than the amplitude rank of a single secondary peak.

## Development and validation split

Development data:

- Sensor 1 capture A
- Sensor 1 capture B
- Sensor 2 capture A
- Sensor 2 capture B
- Sensor 2 capture C

Future validation data:

- Sensor 3
- Sensor 4

Sensor 3 and Sensor 4 data must not be used to select, tune, add, or
remove V2 features or thresholds before the V2 method is frozen.

## Signal domain

V2 operates on the same candidate short events defined by the frozen V1
extractor.

V1 acquisition and segmentation assumptions remain unchanged:

- saved IQ format: headerless NumPy complex128
- sample rate: 25,000 complex samples/s
- envelope threshold: 0.05
- join gap: 25 samples
- minimum event length: 5 samples
- candidate short-event duration: 4.50–5.40 ms
- FFT size: 16384
- centre exclusion: +/-100 Hz
- minimum spectral peak separation: 300 Hz

The V1 extractor itself must not be modified.

## V2 hypothesis

A short TPMS event contains a set of separated spectral components.

Amplitude ordering of secondary components may change between events,
so peak rank alone is not assumed to be stable.

Instead, V2 represents an event using relative spectral topology.

For an event with detected peak frequencies:

    f0, f1, ..., fn

the strongest detected component is used as the local reference:

    f_ref = f0

and each additional component is represented by:

    delta_i = f_i - f_ref

The resulting signed offsets describe spectral geometry relative to the
event's dominant component.

Absolute RF carrier position is not an identity feature.

## Candidate V2 measurements

For each candidate short event, V2 will retain:

1. short-event duration
2. dominant-component frequency for diagnostic purposes only
3. separated spectral peak frequencies
4. peak amplitudes relative to the dominant component
5. signed frequency offsets from the dominant component
6. pairwise frequency differences between detected components

Peak rank and absolute component frequency are retained as diagnostic
information but are not assumed to identify a sensor.

## Comparison principle

Sensor comparison will examine whether recurring relative spectral
components or pairwise spacing relationships form stable topology
patterns across repeated captures.

A useful V2 feature must satisfy both:

1. within-sensor repeatability
2. between-sensor separation

Repeatability alone is not evidence of device discrimination.

## Excluded identity features

The following remain excluded from identity scoring:

- absolute carrier offset
- received power
- DoA
- absolute physical position

These measurements may be retained as experimental metadata.

## Failure criterion

V2 will be considered non-discriminating for the tested sensors if the
relative spectral topology of Sensor 1 and Sensor 2 substantially
overlaps, or if apparent differences are not repeatable across captures.

A negative result will be retained and reported.

## Validation rule

After the V2 implementation and development analysis are frozen in Git,
Sensor 3 and Sensor 4 may be processed as unseen validation data.

The V2 method must not then be altered to improve agreement with the
Sensor 3 / Sensor 4 results. Any such modification becomes a new
experimental version.

## Status

PRE-REGISTERED — implementation not yet frozen.

No Sensor 3 / Sensor 4 validation data has been used to construct this
hypothesis.
