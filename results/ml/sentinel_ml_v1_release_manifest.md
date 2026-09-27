# Sentinel ML 1.0 — Release Manifest

## Release identity

- Branch: `ml-v0.1`
- Release-base commit: `a712314a9b2f542c730936b70912b71614e63ab4`
- Intended tag: `sentinel-ml-v1.0`
- The annotated release tag identifies the exact final release commit.
- Frozen-model source commit: `49d5661`
- Phase-1 checkpoint tag: `sentinel-ml-v0.1-phase1`

## Frozen artefacts

- Dataset: `results/ml/rf_behaviour_dataset_v001.csv`
- Dataset SHA-256: `e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51`
- Model: `results/ml/sentinel_behaviour_model_v001.joblib`
- Model SHA-256: `a4ab69ea6db1864a23f8b6e4e6435a18f02f335effe8e5609a985a16f1662a60`
- Model manifest: `results/ml/sentinel_behaviour_model_v001_manifest.json`
- Model manifest SHA-256: `9fa35379507a65498a3c6b4f48f676204e0470c4d0ff6a2117fbb56ff1decb61`

## Model definition

- Historical training sessions: 21
- Continuous features: 11
- Frozen behavioural clusters: 3
- Prospective refitting: prohibited

## Formal prospective validation

- Valid natural sessions: 12
- Cluster 1: 10 sessions
- Cluster 2: 2 sessions
- Cluster 0: 0 sessions
- Outside original training envelope: 2 sessions

- Block A: C2 -> C2 -> C1
- Block B: C1 -> C1 -> C1
- Block C: C1 -> C1 -> C1
- Block D: C1 -> C1 -> C1

Natural 014 is retained but excluded from formal Block D because
`adc_overdrive=True` was observed during its DAQ preflight.

## Release-candidate verification

- ML Python compilation: PASS
- Focused ML tests: 5/5 PASS
- Frozen dataset provenance: PASS
- C1 cross-runtime prospective recurrence: demonstrated
- C2 status: exploratory
- C0 status: not prospectively validated

## Scope limitations

This release does not claim:

- unique transmitter identification
- TPMS device fingerprint identification
- prospective validation of all three frozen clusters
- calibration-grade absolute DoA
