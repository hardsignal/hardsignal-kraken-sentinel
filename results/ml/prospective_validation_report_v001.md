# Sentinel ML v0.1 — Prospective Validation Report

## Frozen model

- Model version: 0.1
- Frozen model commit: `49d5661`
- Training sessions: 21
- Features: 11
- Training dataset SHA256:
  `e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51`
- Model type: nearest frozen behavioural centroid
- Scope: RF/DoA behavioural regimes, not transmitter identity

The model was not refit during prospective validation.

## Results

| Test | Preregistered target | Assigned | Distance | Separation | Training-max ratio | Interpretation |
|---|---|---:|---:|---:|---:|---|
| 001 | coherent reference | 1 | 2.2061 | 1.6457 | 0.6604 | Successful coherent-regime prospective result |
| 002 | mixed / multipath, Cluster 0 | 1 | 1.8078 | 2.2901 | 0.5412 | Target physical regime was not successfully induced |
| 003 | broad, directionally stable, Cluster 2 | 1 | 1.7904 | 2.5841 | 0.5360 | Broad DoA appeared, but signal remained too coherent/high-confidence |
| 004 | weak, broad, stable multipath, Cluster 2 | 1 | 2.6762 | 1.4493 | 0.8012 | Partial Cluster-2 signature; overall feature vector remained closer to Cluster 1 |

All four sessions were within the observed training-distance envelope of
their assigned cluster.

## Main observations

1. Prospective Test 001 provided the first unseen-session validation of the
   frozen behavioural model and was assigned to the coherent Cluster 1 regime.

2. Tests 002–004 did not validate Clusters 0 or 2 because the attempted
   physical manipulations did not reproduce the corresponding frozen feature
   regimes.

3. The frozen model did not simply follow the intended experimental condition.
   It followed the measured multivariate RF/DoA feature vector.

4. Test 004 demonstrated a hybrid state:
   - bearing stability, power variation, and DoA width were closer to Cluster 2;
   - confidence, peak count, single-peak ratio, mean power, and DoA-width
     variation were closer to Cluster 1.

5. Further engineered attempts to force a particular frozen cluster should be
   avoided in this validation phase to reduce the risk of tuning against the
   validation set.

## Current interpretation

The prospective evidence supports the ability of the frozen Sentinel ML model
to classify unseen RF/DoA behaviour into its previously learned behavioural
space.

It does not yet establish generalization across all three behavioural regimes,
and it does not establish unique transmitter identification.

## Next phase

Collect naturally occurring unseen sessions under the restored reference
configuration:

- MUSIC
- decorrelation Off
- UCA radius 0.21 m
- 433.868160 MHz

Each new session should be scored against the frozen model without refitting.
The growing prospective dataset can later be used to evaluate regime
recurrence, novelty, and eventual out-of-sample performance.
