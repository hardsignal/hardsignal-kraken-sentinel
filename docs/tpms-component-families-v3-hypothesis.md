# TPMS Component Families V3 — Pre-Registered Hypothesis

Date: 17 September 2026

## Purpose

V1 demonstrated repeatable TPMS short-event timing and recurring
spectral structure, but naive P1/P2 spacing did not discriminate
Sensor 1 from Sensor 2.

V2 tested spectral topology using amplitude-ranked components. It also
failed the Sensor 1 / Sensor 2 discrimination criterion because
secondary components changed amplitude rank between events.

V3 tests a different hypothesis:

Recurring spectral components may form stable relative-frequency
families even when their amplitude rank changes.

## Development and validation split

Development data:

- Sensor 1 capture A
- Sensor 1 capture B
- Sensor 2 capture A
- Sensor 2 capture B
- Sensor 2 capture C

Reserved unseen validation data:

- Sensor 3
- Sensor 4

Sensor 3 and Sensor 4 must not be used to define, select, tune, add, or
remove V3 features or thresholds before the V3 method is frozen.

## Frozen input

V3 operates only on spectral peaks already extracted by the frozen V1
method.

V1 extractor:

`fingerprinting/tpms_iq_features.py`

V1 extractor SHA-256:

`5aa9e6e0452895a355880316bf884758fbc2811f11aac8c9f8f3e9f715509c84`

V3 does not alter V1 event segmentation, FFT processing, or peak
detection.

For each candidate short event, the existing eight separated spectral
peaks are used.

## V3 hypothesis

Amplitude rank is not treated as component identity.

For an event containing detected spectral frequencies:

    F = {f1, f2, ..., fn}

the peak set is treated as unordered for component-family analysis.

The dominant spectral component may be retained as diagnostic metadata,
but P2, P3, P4, etc. are not assumed to correspond to the same physical
spectral component across events.

## Rank-independent representation

For every event, V3 derives all unique absolute pairwise frequency
differences:

    D = {|fi - fj| : i < j}

With eight detected peaks this produces 28 pairwise differences before
clustering or consolidation.

These differences are independent of the amplitude ordering of the two
components.

## Component-family construction

Pairwise differences from development events will be grouped into
recurring spacing families using a fixed frequency tolerance.

A family represents a relative spectral relationship that recurs across
events regardless of the amplitude ranks occupied by its two
components.

The implementation must define and freeze before validation:

- family matching tolerance
- minimum within-capture recurrence
- minimum cross-capture recurrence
- representation of family presence or frequency
- sensor-comparison rule

These values may be developed using only Sensor 1 and Sensor 2.

After the V3 implementation and development rule are frozen in Git,
they must not be changed after examining Sensor 3 or Sensor 4.

## Required development behaviour

A candidate component-family feature is useful for discrimination only
if it demonstrates both:

1. within-sensor repeatability across independent captures
2. between-sensor separation between Sensor 1 and Sensor 2

A family shared by both sensors may describe TPMS signal structure but
is not a device-discriminating feature.

## Diagnostic information

V3 may retain the following for interpretation:

- event duration
- original peak frequencies
- original amplitude ranks
- relative peak amplitudes
- family membership
- family recurrence counts

Amplitude rank is diagnostic only.

## Excluded identity features

The following remain excluded from identity scoring:

- absolute RF carrier offset
- received power
- DoA
- absolute physical position

## Failure criterion

V3 is non-discriminating for the development sensors if:

- recurring component families substantially overlap between Sensor 1
  and Sensor 2, or
- apparent sensor-specific families are not repeatable across that
  sensor's independent captures.

A negative result will be retained.

## Validation rule

Sensor 3 and Sensor 4 remain unseen until:

1. the V3 implementation is committed,
2. the V3 development analysis is complete,
3. all thresholds and comparison rules are frozen in Git.

No method change after exposure to Sensor 3 or Sensor 4 may be reported
as validation of this V3 method. Such a change requires a new
experimental version.

## Status

PRE-REGISTERED — implementation not yet created.

Sensor 3 and Sensor 4 remain unseen by V3.

---

# Development Rule Selection

Date: 17 September 2026

The following parameters were selected using only the pre-registered
Sensor 1 / Sensor 2 development dataset. Sensor 3 and Sensor 4 remained
unseen.

## Development observations

The development set contained 30 candidate short events and 840
pairwise spectral-spacing measurements.

Nearest spacing to a measurement from another event showed:

- median: 4.58 Hz
- 75th percentile: 10.68 Hz
- 90th percentile: 25.94 Hz
- 95th percentile: 44.25 Hz
- maximum: 218.20 Hz

Major recurring spacing families were substantially shared by Sensor 1
and Sensor 2. Examples included families near:

- 1.372 kHz
- 5.779 kHz
- 7.129 kHz
- 12.088 kHz
- 12.901 kHz
- 13.450 kHz
- 18.787 kHz
- 19.226 kHz

These shared families may describe common signal structure and are not,
by themselves, sensor-discriminating features.

## Frozen family matching tolerance

V3 family matching tolerance:

    +/- 50 Hz

The tolerance is fixed before Sensor 3 / Sensor 4 exposure.

It is slightly larger than the observed 95th-percentile nearest-event
spacing difference of 44.25 Hz.

## Frozen within-sensor recurrence rule

A spacing family is repeatable for a sensor only if it occurs in:

    >= 60% of candidate short events

in every independent development capture available for that sensor.

For Sensor 1 this requirement must hold independently in both S1-A and
S1-B.

For Sensor 2 it must hold independently in S2-A, S2-B and S2-C.

Pooling events across captures is not sufficient.

## Frozen between-sensor discrimination rule

A family is a candidate sensor-discriminating feature only if:

1. it satisfies the >=60% repeatability requirement in every capture of
   one sensor, and
2. its recurrence remains <40% in every development capture of the
   other sensor.

Values between 40% and 60% are treated as an indeterminate overlap
region and do not support discrimination.

## Development interpretation rule

Families satisfying the within-sensor criterion for both sensors are
classified as shared signal structure.

Families satisfying neither sensor's within-sensor criterion are
classified as insufficiently repeatable.

A family must not be promoted as discriminating merely because its
pooled Sensor 1 and Sensor 2 recurrence percentages differ.

## Methodological lock

These tolerance and recurrence rules are now part of V3.

They must not be changed after Sensor 3 or Sensor 4 is examined.

If development analysis under these frozen rules produces no
discriminating family, V3 will retain that negative development result
rather than changing the thresholds.

Any materially different family-matching or discrimination rule requires
a new experimental version.

---

# V3 Development Result

Date: 17 September 2026

The frozen V3 implementation was executed against the complete
pre-registered S1/S2 development dataset only.

Sensor 3 and Sensor 4 remained unseen.

## Frozen artifacts

Development result:

    fingerprinting/results/v3/tpms_s1_s2_development.json

Result SHA256:

    10a3b1ceef2fd1da831f2639364af4cee0fb8dcba409f4a9d8c4078daca8469a

V3 extractor SHA256:

    faf8411528a86e18447ed2ecc86c17dfb99b842048da7996f08f4557db87a487

Frozen V3 method/rules document SHA256 before this result section was
added:

    0d92f90edc7ecbec1d8fcccec07a602e218c51ad88f7b0c6ad7a20c02fc1d32a

## Development classification

The frozen extractor evaluated:

- 776 observed candidate centres
- 113 consolidated spacing families

Classification:

- shared signal structure: 4
- candidate S1-discriminating: 1
- candidate S2-discriminating: 0
- insufficient or overlapping: 108

## Development candidate

One spacing family satisfied the pre-defined S1 development
discrimination rule:

    centre:     18679.81 Hz
    tolerance:  +/- 50 Hz

Per-capture recurrence:

    S1-A: 3/5 = 60.0%
    S1-B: 5/7 = 71.4%

    S2-A: 1/5 = 20.0%
    S2-B: 3/8 = 37.5%
    S2-C: 1/5 = 20.0%

The family therefore met the frozen development criteria:

- >=60% recurrence in every S1 development capture
- <40% recurrence in every S2 development capture

No S2-discriminating family satisfied the frozen criteria.

## Interpretation

The 18679.81 Hz family is a development-set candidate only.

It is not evidence of unique device identity and is not yet a validated
sensor fingerprint.

The result is based on small event counts, and S1-A lies exactly at the
pre-defined 60% repeatability boundary.

The candidate must therefore be treated as provisional until evaluated
using the separately reserved Sensor 3 and Sensor 4 data under a
validation protocol frozen before those sensors are examined.

The development thresholds, family tolerance and extractor must not be
modified in response to Sensor 3 or Sensor 4 results.

A failure to validate this candidate will be retained as a negative
result rather than followed by post-validation tuning under V3.

## Development status

TPMS Component Families V3:

    DEVELOPMENT COMPLETE

Candidate:

    18679.81 Hz +/- 50 Hz

Validation:

    NOT YET PERFORMED

Identity claim:

    NONE

---

# V3 Validation Protocol

Date: 17 September 2026

This protocol was defined before Sensor 3 or Sensor 4 was examined by
the V3 method.

## Validation target

Only the development-selected family will be tested:

    centre:     18679.81 Hz
    tolerance:  +/- 50 Hz

No additional spacing family may be selected from Sensor 3 or Sensor 4
under V3.

## Purpose of Sensor 3 and Sensor 4

Sensor 3 and Sensor 4 are previously unseen negative/specificity
validation sensors.

They do not test repeatability of Sensor 1 itself.

They test whether the S1 development candidate remains uncommon in
previously unseen sensors.

Therefore successful S3/S4 validation supports only out-of-development
specificity of the candidate under the tested conditions. It does not
establish unique device identity.

## Acquisition structure

For each validation sensor:

    Sensor 3: two independent captures
    Sensor 4: two independent captures

Target:

    >= 5 candidate short events per capture

The existing frozen V1 event definition remains authoritative.

Captures must not be combined merely to satisfy the event-count target.

If a capture contains fewer than 5 candidate short events, it is
insufficient for the primary V3 validation decision and may be repeated
as a new capture without changing the V3 rules.

All usable observations are retained.

## Frozen validation decision rule

For each independently acquired S3/S4 capture, calculate recurrence of
the already-selected 18679.81 Hz family using the already-frozen
+/-50 Hz matching tolerance.

The candidate passes the unseen-sensor specificity test only if:

    recurrence < 40%

in every sufficient S3 and S4 validation capture.

The threshold is strict.

Examples:

    0/5 =  0%  -> below threshold
    1/5 = 20%  -> below threshold
    2/5 = 40%  -> NOT below threshold

With other event counts, the percentage rule remains authoritative.

## Validation outcomes

PASS:

The 18679.81 Hz family remains below 40% recurrence in every sufficient
S3 and S4 validation capture.

Interpretation:

The development-selected candidate demonstrated out-of-development
specificity against the two reserved sensors under the tested
conditions.

This does not establish unique sensor identity.

FAIL:

The family reaches or exceeds 40% recurrence in any sufficient S3 or S4
validation capture.

Interpretation:

The candidate failed the pre-defined unseen-sensor specificity test.

The negative result is retained without modifying V3.

INCONCLUSIVE:

One or more required validation captures contains fewer than 5
candidate short events and no sufficient replacement capture has yet
been obtained.

No pass/fail conclusion is made until the acquisition requirement is
satisfied or the experiment is explicitly closed as incomplete.

## Prohibited post-validation changes

After the first S3 or S4 V3 result is examined, V3 must not change:

- 18679.81 Hz candidate centre
- +/-50 Hz tolerance
- 40% unseen-sensor threshold
- V1 event definition
- V3 extractor
- family construction method
- validation interpretation rule

Any materially changed method becomes a new experimental version.

## Identity limitation

Even a validation PASS does not demonstrate a unique RF fingerprint.

The result would show only that one pre-selected relative spectral
family separated S1 development captures from S2 development captures
and remained uncommon in the reserved S3/S4 sensors under the tested
conditions.

Further positive repeatability testing of S1 across independently
acquired sessions and broader testing across additional sensors and
conditions would be required before stronger fingerprinting claims.

## Validation status

    PROTOCOL FROZEN
    S3 NOT EXAMINED
    S4 NOT EXAMINED
