# Sentinel ML — Natural Prospective Validation

Frozen behavioural model v0.1; no prospective session is used for refitting.

## Summary

- Natural prospective sessions: 9
- Cluster 1: 7 sessions
- Cluster 2: 2 sessions
- Within training envelope: 7
- Outside training envelope: 2

## Sessions

| Session | Cluster | Distance | Separation | Training-max ratio | Novelty |
|---|---:|---:|---:|---:|---|
| TPMS-NATURAL-005-20260925-005143 | 2 | 2.6662 | 1.4264 | 1.1939 | OUTSIDE_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-006-20260925-005606 | 2 | 2.9926 | 1.5172 | 1.3400 | OUTSIDE_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-007-20260925-005956 | 1 | 2.1715 | 1.9555 | 0.6501 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-008-20260925-012315 | 1 | 2.8323 | 1.2725 | 0.8479 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-009-20260925-012627 | 1 | 2.7638 | 1.3731 | 0.8274 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-010-20260925-012906 | 1 | 2.6595 | 1.4607 | 0.7962 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-011-20260925-014556 | 1 | 2.1191 | 1.9254 | 0.6344 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-012-20260925-014842 | 1 | 1.8110 | 2.5707 | 0.5422 | WITHIN_OBSERVED_TRAINING_RANGE |
| TPMS-NATURAL-013-20260925-015115 | 1 | 2.2334 | 1.6891 | 0.6686 | WITHIN_OBSERVED_TRAINING_RANGE |

## Observed cluster transitions

- C1 → C1: 6
- C2 → C1: 1
- C2 → C2: 1

## Interpretation constraints

- Cluster assignment describes RF/DoA behaviour, not transmitter identity.
- Outside-range observations are nearest-regime assignments, not confirmed members of that regime.
- Same-runtime recurrence is not equivalent to cross-time or cross-runtime generalization.
- The frozen model must not be refit during this prospective validation phase.

