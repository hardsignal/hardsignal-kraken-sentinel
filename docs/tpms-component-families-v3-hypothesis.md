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
