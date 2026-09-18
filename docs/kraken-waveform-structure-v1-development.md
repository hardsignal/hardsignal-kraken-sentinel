# Kraken Waveform Structure V1 — Development Specification

## Status

DEVELOPMENT SPECIFICATION

This document defines the Waveform Structure V1 development search
space before implementation and before inspecting Waveform Structure V1
outputs.

It is not an independent validation protocol.

## Motivation

Episode Features V1 demonstrated repeatable same-source spectral
measurements under the tested conditions, but the held-out S2 test did
not demonstrate useful between-device separation.

Episode Features V2 then evaluated richer episode-level spectral shape,
relative peak geometry, and recorder-fragment structure. No feature
family satisfied the predeclared development advancement rule.

Waveform Structure V1 therefore moves to a different information layer:
time-varying structure inside individual recorded IQ fragments.

The purpose is not to retune Episode Features V1 or V2.

## Development data

Waveform Structure V1 development uses only:

S1:

    PIPELINE-TPMS-004-20260917-233423
    PIPELINE-TPMS-005-20260917-235439
    PIPELINE-TPMS-007-20260918-002700

S2:

    PIPELINE-TPMS-008-20260918-003900

These captures are development data for Waveform Structure V1.

They cannot later be described as independent validation of a feature
selected using these captures.

## Reserved source

S3 is held out from Waveform Structure V1 development.

No new Waveform Structure V1 output for S3 will be inspected during
development.

A validation protocol must be frozen before any later S3 Waveform
Structure V1 output is inspected for validation.

This statement applies specifically to Waveform Structure V1
development and does not imply that S3 has never been used in earlier,
different experiments.

## Input evidence

The analysis uses the raw complex IQ files referenced by the existing
frozen Episode Grouping V1 episode records.

Episode membership will not be modified to improve waveform
separation.

Recorder fragments remain separate time-domain observations.

Separate recorder fragments must not be concatenated and interpreted
as one continuous RF waveform across filesystem gaps.

## Fixed acquisition interpretation

The IQ recordings are:

    dtype: complex128
    sample rate: 25,000 complex samples/second

All waveform measurements must respect the information available at
this sample rate and the recorded channel bandwidth.

No inference may require unrecorded RF bandwidth.

## Development feature families

### 1. Instantaneous-frequency structure

Candidate measurements may include deterministic summaries of
phase-difference-derived instantaneous frequency within an individual
fragment.

Examples include:

- median instantaneous frequency;
- robust instantaneous-frequency spread;
- quantiles;
- within-fragment stability;
- relative frequency-state spacing;
- occupancy of repeatedly observed frequency regions.

Absolute frequency offset may be reported descriptively, but absolute
carrier offset alone is not sufficient evidence of device identity.

### 2. Time-frequency trajectory structure

Candidate measurements may include deterministic short-time spectral
analysis within individual fragments.

Examples include:

- dominant-frequency trajectory;
- trajectory spread;
- trajectory step sizes;
- dwell behaviour;
- number of repeatedly occupied frequency regions;
- relative spacing between occupied regions;
- temporal stability of those relationships.

Window length, overlap, FFT size, window function, and any masking rule
must be fixed in the analyzer before first execution on the development
captures.

### 3. Envelope structure

Candidate measurements may include normalized magnitude-envelope
structure within individual fragments.

Examples include:

- normalized envelope quantiles;
- coefficient of variation;
- active-envelope occupancy;
- transition counts under a prospectively fixed normalization/rule;
- relative active/inactive duration structure.

Absolute received power is contextual and is not sufficient evidence
of device identity.

### 4. Within-fragment temporal stability

Candidate measurements may include deterministic robust summaries
across time blocks inside each fragment.

Examples include:

- median;
- range;
- median absolute deviation;
- interquartile range;
- block-to-block change.

### 5. Episode aggregation

Fragment-level waveform measurements may be summarized at episode
level using deterministic robust statistics.

All fragments and episodes must be retained.

No episode may be removed merely because it weakens apparent
S1/S2 separation.

## Context-only quantities

The following must not become Waveform Structure V1 device-identity
features merely because they appear discriminative:

- filename DoA;
- absolute received power;
- physical source position;
- operator activation latency;
- recorder filename or capture identifier;
- episode number;
- filesystem timestamp.

These may be used only for provenance, ordering, or clearly labelled
context.

## Observable-structure interpretation

Waveform Structure V1 measures observable structure in the recorded IQ.

Unless independently established, the analysis must not label observed
states or transitions as:

- decoded bits;
- symbols;
- packet fields;
- protocol fields;
- frame boundaries;
- modulation symbols;
- unique transmitter identifiers.

A repeated frequency region is an observed waveform feature, not
automatically a protocol-defined frequency state.

## Development procedure

1. Implement one deterministic analyzer from this specification.
2. Fix all numerical analysis parameters before first execution.
3. Hash and commit the analyzer before inspecting development outputs.
4. Run the same analyzer without modification on all four development
   captures.
5. Preserve all fragment-level and episode-level observations.
6. Compare repeatability across S1 Captures 004, 005, and 007.
7. Compare S1 development behaviour with S2 Capture 008.
8. Document both overlap and apparent separation.
9. Do not fit a production identity classifier during this stage.
10. Do not inspect S3 with this analyzer during development.

## Feature advancement rule

A waveform feature may advance toward independent validation only if:

1. it shows reasonable repeatability across the three S1 development
   captures;

2. it shows a descriptive S1/S2 difference that is not solely caused
   by one isolated fragment or episode;

3. the apparent difference is not merely an absolute-power, DoA,
   physical-position, filename, timestamp, or absolute-carrier
   artifact;

4. its calculation is deterministic and frozen before validation.

If no feature satisfies these conditions, the correct result is that
no Waveform Structure V1 feature advances to validation.

## Before independent validation

Before inspecting S3 Waveform Structure V1 output:

- freeze the analyzer and record its SHA-256;
- freeze the selected feature or compact feature set;
- freeze the comparison procedure;
- define any numerical validation criterion prospectively if one is
  scientifically defensible;
- commit and push the validation protocol.

If no defensible numerical criterion exists, any later validation must
remain explicitly descriptive.

## Claims not supported by development

Waveform Structure V1 development cannot establish:

- unique device identity;
- a universal RF fingerprint;
- a production TPMS classifier;
- decoded packet contents;
- protocol semantics;
- transmitter location;
- robustness across receivers;
- robustness across bandwidths or sample rates;
- robustness across geometry, temperature, voltage, ageing, or
  production lots.

## Freeze rule

Once Waveform Structure V1 development outputs have been inspected,
changes to the analyzer or feature definitions require explicit
versioning and documentation.

Episode Features V1, Episode Features V2, and their negative
between-device results remain frozen and are not reinterpreted by this
experiment.
