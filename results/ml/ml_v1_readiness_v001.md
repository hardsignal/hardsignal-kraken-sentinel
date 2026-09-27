# Sentinel ML 1.0 — Release Readiness Review

## Scope

Sentinel ML 1.0 is an RF/DoA behavioural-regime analysis system.

It does not establish unique transmitter identity or TPMS device fingerprinting.

## Frozen model

- Model version: 0.1
- Training sessions: 21
- Features: 11
- Frozen model commit: 49d5661
- Training dataset SHA256:
  e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51
- Prospective refitting: prohibited

## Model-development evidence

- PCA and behavioural clustering: complete
- Perturbation stability study: complete
- 1000 robustness trials: complete
- Single-feature ablation: complete
- Feature-family ablation: complete
- Frozen nearest-centroid scoring model: complete
- Provenance locking: complete

## Prospective workflow

- Frozen-model scoring automation: complete
- Duplicate-session protection: complete
- Kraken reference-setting validation: complete
- DAQ health validation: complete
- Active local-recorder validation: complete
- Natural prospective reporting: complete
- Cross-runtime block evaluation: complete

## Formal prospective evidence

Valid natural sessions: 12

Block A:
- 005: C2 / outside training envelope
- 006: C2 / outside training envelope
- 007: C1 / within training envelope

Block B:
- 008: C1 / within training envelope
- 009: C1 / within training envelope
- 010: C1 / within training envelope

Block C:
- 011: C1 / within training envelope
- 012: C1 / within training envelope
- 013: C1 / within training envelope

Block D:
- 015: C1 / within training envelope
- 016: C1 / within training envelope
- 017: C1 / within training envelope

Natural 014 was retained but excluded from formal Block D because
the DAQ preflight reported adc_overdrive=True before acquisition.

## Regime status

### Cluster 1

Status: prospectively supported.

Evidence:
- 10 natural prospective sessions
- observed in all four runtime blocks
- recurrence demonstrated across fresh Kraken runtimes
- all formal C1 prospective assignments were within the observed
  Cluster-1 training envelope

### Cluster 2

Status: exploratory.

Evidence:
- 2 natural prospective sessions
- both observed in Block A
- both outside the original Cluster-2 training-distance envelope
- cross-runtime recurrence has not yet been demonstrated

### Cluster 0

Status: not prospectively validated.

Evidence:
- no natural prospective assignment to C0 so far

## Release interpretation

The current evidence supports release of Sentinel ML 1.0 as a
behavioural-regime scoring and analysis system.

The release must not claim:
- unique transmitter identification
- TPMS device fingerprint identification
- prospective validation of all three frozen clusters
- calibration-grade absolute DoA

The release may state:
- frozen behavioural scoring was evaluated on unseen sessions
- Cluster 1 demonstrated prospective cross-runtime recurrence
- Cluster 2 was observed naturally but remains exploratory
- Cluster 0 remains unsupported by natural prospective validation
- prospective observations are retained even when they disagree with
  intended experimental conditions

## Remaining release work

- run focused ML test suite
- add ML architecture and validation section to README
- document fresh-runtime preflight procedure
- document frozen-model limitations
- create release manifest
- final git status and provenance verification
- tag sentinel-ml-v1.0 if release checks pass
