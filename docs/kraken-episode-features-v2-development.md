# Kraken Episode Features V2 — Development Specification

## Status

DEVELOPMENT SPECIFICATION

This document defines the Episode Features V2 development search space
before implementation and before inspecting V2 feature outputs.

This is not a validation protocol.

## Motivation

Episode Features V1 demonstrated repeatability of its primary spectral
quantity across repeated controlled captures of S1.

A prospectively selected held-out S2 capture did not demonstrate useful
between-device separation using that quantity alone.

Episode Features V2 therefore investigates richer within-episode RF
structure without changing or reinterpreting the V1 result.

## Development data

S1:

    PIPELINE-TPMS-004-20260917-233423
    PIPELINE-TPMS-005-20260917-235439
    PIPELINE-TPMS-007-20260918-002700

S2:

    PIPELINE-TPMS-008-20260918-003900

These captures are development data for V2.

They must not subsequently be described as independent validation of
features selected using them.

## Reserved validation source

S3 is reserved for later independent validation.

No new S3 Episode Features V2 output is to be inspected during V2
development.

A validation protocol must be frozen before acquisition or inspection
of validation data used to test the selected V2 feature set.

## Frozen inputs

Episode boundaries continue to use Episode Grouping V1.

The V1 grouping rule must not be modified to improve V2 separation.

Raw IQ remains the underlying signal evidence.

V1 artifacts remain unchanged.

## V2 development feature families

### 1. Relative spectral-component geometry

Measure relationships among spectral components within each fragment
or episode, including:

- frequency spacing between strong components;
- ordered adjacent-component spacing;
- component separation relative to the strongest component;
- number of persistent strong components;
- stability of component spacing across fragments.

Relative spacing is preferred over absolute carrier position for this
family.

### 2. Normalized spectral shape

Measure spectral shape after normalization, including:

- spectral centroid relative to the episode or fragment reference;
- spectral spread;
- spectral entropy;
- occupied spectral width;
- normalized peak prominence;
- normalized energy distribution across frequency regions.

Absolute received power must not be required for these features.

### 3. Temporal / fragment structure

Measure episode structure already present in the recorder output,
including:

- number of recorder fragments;
- fragment IQ duration;
- total IQ duration;
- episode wall-clock span;
- inter-fragment timing;
- relative fragment-duration pattern.

These are recorder/episode structural features and must not be called
packet fields or protocol timing unless independently established.

### 4. Within-episode stability

Measure how candidate features vary across fragments belonging to the
same frozen candidate episode.

Possible summaries include:

- median;
- range;
- median absolute deviation;
- interquartile range.

## Context-only quantities

The following must not become V2 identity features merely because they
appear discriminative in development:

- filename DoA;
- absolute received power;
- absolute physical position;
- operator activation latency.

Absolute carrier offset may be retained for comparison with V1 but is
not sufficient by itself as the V2 discrimination feature.

## Development procedure

1. Implement deterministic extraction of the defined feature families.
2. Run the identical extractor on all four development captures.
3. Preserve all candidate episodes.
4. Preserve extreme observations; do not remove them merely to improve
   separation.
5. Compare within-S1 repeatability against S1/S2 differences.
6. Document features that overlap as well as features that appear
   promising.
7. Do not fit a production identity classifier.
8. Do not define a validation threshold after inspecting S3.

## Feature selection rule

A feature or compact feature set may advance from development only when
the development evidence shows both:

1. reasonable repeatability across the three S1 captures; and
2. a descriptive difference between the S1 development observations
   and S2 that is not solely explained by one isolated outlier.

Selection must be documented before independent validation.

Features that fail this condition remain documented negative results.

## Validation boundary

Before S3 is used to evaluate the selected V2 feature set:

- freeze the V2 extractor;
- record its SHA-256;
- freeze the selected feature set;
- define the comparison procedure;
- define any numerical criterion prospectively if one is to be used;
- commit and push the validation protocol.

If no defensible criterion can be defined from development, validation
must remain descriptive rather than inventing a post-hoc threshold.

## Claims not supported by V2 development

V2 development cannot establish:

- unique device identity;
- universal TPMS fingerprinting;
- production-ready classification;
- packet identity;
- transmitter location;
- robustness across environments;
- robustness across receiver configurations;
- robustness across temperature, voltage, ageing, or manufacturing lots.

## Freeze rule

Any change to this development search space after V2 outputs are
inspected must be documented explicitly.

The V1 experiment and its negative held-out discrimination result remain
frozen and unchanged.
