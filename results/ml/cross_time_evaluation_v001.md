# Sentinel ML — Cross-Time Evaluation v0.1

Frozen behavioural model v0.1; no prospective data were used for refitting.

## Runtime blocks

### A_same_runtime

- Sessions: 3
- Sequence: C2 → C2 → C1
- Cluster counts: {1: 1, 2: 2}
- Within training envelope: 1
- Outside training envelope: 2
- Mean nearest distance: 2.6101
- Mean separation ratio: 1.6330
- Mean training-max ratio: 1.0613

### B_fresh_runtime

- Sessions: 3
- Sequence: C1 → C1 → C1
- Cluster counts: {1: 3}
- Within training envelope: 3
- Outside training envelope: 0
- Mean nearest distance: 2.7519
- Mean separation ratio: 1.3688
- Mean training-max ratio: 0.8238

### C_fresh_runtime

- Sessions: 3
- Sequence: C1 → C1 → C1
- Cluster counts: {1: 3}
- Within training envelope: 3
- Outside training envelope: 0
- Mean nearest distance: 2.0545
- Mean separation ratio: 2.0618
- Mean training-max ratio: 0.6150

### D_fresh_runtime

- Sessions: 3
- Sequence: C1 → C1 → C1
- Cluster counts: {1: 3}
- Within training envelope: 3
- Outside training envelope: 0
- Mean nearest distance: 2.2556
- Mean separation ratio: 1.8502
- Mean training-max ratio: 0.6753

## Cross-block recurrence

- Clusters observed in both blocks: C1
- Clusters observed overall: C1, C2

## Session sequence

- Natural 005: C2 | distance=2.6662 | separation=1.4264 | training-max ratio=1.1939 | OUTSIDE_OBSERVED_TRAINING_RANGE
- Natural 006: C2 | distance=2.9926 | separation=1.5172 | training-max ratio=1.3400 | OUTSIDE_OBSERVED_TRAINING_RANGE
- Natural 007: C1 | distance=2.1715 | separation=1.9555 | training-max ratio=0.6501 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 008: C1 | distance=2.8323 | separation=1.2725 | training-max ratio=0.8479 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 009: C1 | distance=2.7638 | separation=1.3731 | training-max ratio=0.8274 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 010: C1 | distance=2.6595 | separation=1.4607 | training-max ratio=0.7962 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 011: C1 | distance=2.1191 | separation=1.9254 | training-max ratio=0.6344 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 012: C1 | distance=1.8110 | separation=2.5707 | training-max ratio=0.5422 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 013: C1 | distance=2.2334 | separation=1.6891 | training-max ratio=0.6686 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 015: C1 | distance=1.8149 | separation=2.1600 | training-max ratio=0.5433 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 016: C1 | distance=2.6379 | separation=1.6506 | training-max ratio=0.7897 | WITHIN_OBSERVED_TRAINING_RANGE
- Natural 017: C1 | distance=2.3140 | separation=1.7401 | training-max ratio=0.6927 | WITHIN_OBSERVED_TRAINING_RANGE

## Observed transitions

- C1 → C1: 9
- C2 → C1: 1
- C2 → C2: 1

## Interpretation

- Cluster 1 recurred across the runtime boundary.
- Cluster 2 has not yet been observed after the fresh-runtime boundary.
- The result supports cross-runtime recurrence for observed Cluster 1 behaviour.
- It does not yet demonstrate cross-runtime recurrence for every frozen behavioural regime.
- Cluster assignments describe RF/DoA behaviour, not transmitter identity.

