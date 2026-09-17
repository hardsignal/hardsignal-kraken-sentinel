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

---

# Development Result

Date: 17 September 2026

## Frozen implementation

V2 extractor:

`fingerprinting/tpms_topology_v2.py`

SHA-256:

`047c40aa89faf8ebe5639ab61085b67c859ef13bcd1bfcff7c42ca7eb71ba492`

The implementation was frozen in Git before the development dataset was
processed.

## Development dataset

The pre-registered development set contained:

| Capture | Short events |
|---|---:|
| Sensor 1 A | 5 |
| Sensor 1 B | 7 |
| Sensor 2 A | 5 |
| Sensor 2 B | 8 |
| Sensor 2 C | 5 |

Total: 30 candidate short events.

Derived V2 result:

`fingerprinting/results/v2/tpms_s1_s2_development.json`

SHA-256:

`2ee5e915dc43bcdc2aa3e4644dd13ed8f4c52dccf98448b2ec21bf41a32c8923`

## Observations

The dominant-to-P2 median offsets were:

| Capture | Median offset |
|---|---:|
| Sensor 1 A | 12088.0 Hz |
| Sensor 1 B | 12088.0 Hz |
| Sensor 2 A | 12085.0 Hz |
| Sensor 2 B | 12086.5 Hz |
| Sensor 2 C | 12089.5 Hz |

These values substantially overlap between Sensor 1 and Sensor 2.

The P3 median offsets also occupied a common region across the five
captures.

For later-ranked components, large median absolute deviations and wide
ranges were observed. Secondary spectral components changed amplitude
rank between events, so comparison of P4 with P4, P5 with P5, and so on
did not provide a stable topology representation.

This behaviour is consistent with the instability already observed in
the V1 second-highest-peak measurement.

## Development conclusion

The pre-registered V2 representation did not satisfy the required
between-sensor separation criterion for Sensor 1 and Sensor 2.

Recurring spectral structure remains observable and repeatable, but
amplitude-rank-based relative topology substantially overlaps between
the two controlled sensors in this development dataset.

Therefore V2 is classified as non-discriminating for the tested
Sensor 1 / Sensor 2 comparison.

No V2 parameters or features will be modified to improve this result.

## Reserved validation data

Sensor 3 and Sensor 4 remain unused by V2.

Because V2 did not satisfy its discrimination criterion on the
development sensors, Sensor 3 and Sensor 4 are retained as unseen data
for a separately pre-registered future method rather than being used to
rescue or tune V2.

## Status

**TPMS Spectral Topology V2 — DEVELOPMENT COMPLETE / NON-DISCRIMINATING**

A future method may test rank-independent recurring component families
or other pre-defined spectral relationships, but such work must be
treated as a new experimental version.
