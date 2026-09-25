# Hardsignal Kraken RF Sentinel

An RF sensing, direction-finding, and event-analysis platform built around KrakenSDR, with a separate controlled RF fingerprint research programme.

## v1.0.0 — Core Analysis Stack

v1.0.0 establishes the core path from live KrakenSDR bursts to quality-aware tracking, source episodes, and session reporting. Live RF and offline bearing/quality replay share the same `TrackerEngine`, with a retained real-RF regression fixture validating state transitions. This release validates the core analysis stack; it does not establish unique device identification or calibration-grade absolute DoA.

## Architecture

```text
KrakenSDR
  -> burst/event processing
  -> DoA quality classification
  -> TrackerEngine
  -> SourceEpisodeEngine
  -> episode JSONL
  -> episode/session reporting

saved real RF (bearing + quality)
  -> TrackerEngine
  -> regression verification
```

## Key capabilities

- KrakenSDR burst ingestion and event grouping.
- DoA quality classification: `STABLE`, `MULTIPATH`, `LOW_QUALITY`.
- Shared `TrackerEngine` for live RF and true offline replay from bearing + quality.
- Track lifecycle: `BUILDING`, `ESTABLISHED`, `MATURE`; track health: `HEALTHY`, `DEGRADED`, `LOST`.
- Directional shift hysteresis: an established track requires 5 coherent candidate observations; a mature track requires 7.
- `SourceEpisodeEngine`, deterministic episode summaries, and live episode JSONL logging.
- Episode reporting CLI and unified session-summary CLI.
- Real TPMS RF regression fixture covering tracking and episode behaviour.

## Real-RF validation

A controlled TPMS source at **433.868160 MHz** demonstrated directional shift hysteresis: the active track held around **286°** while a clean candidate cluster accumulated around **145° / 144° / 144° / 143°**. The fifth coherent candidate confirmed the transition, establishing a new track around **144°**. This real session is retained in the [regression inputs](tests/fixtures/tpms_hysteresis_clean_v1_inputs.csv) and [recorded expectations](tests/fixtures/tpms_hysteresis_clean_v1.log).

This is repeatability and state-machine validation. Replay recomputes transitions from bearing + quality through the same engine used live. It does **not** validate absolute indoor bearing accuracy: indoor multipath can produce reflected or biased directions, including coherent clusters. No calibration-grade absolute DoA claim is made.

## Testing

**45/45 focused tests passed at the v1.0.0 release checkpoint:**

| Area | Tests |
| --- | ---: |
| Session summary | 12 |
| Tracker | 15 |
| Source episode | 4 |
| Episode summary/event | 6 |
| Episode report/CLI | 8 |

This is the focused core release checkpoint, not a claim about the entire research test suite.

## Sentinel ML 1.0 — Behavioural Regime Analysis

**Status: Sentinel ML 1.0 release.**

Sentinel ML adds a machine-learning layer above the deterministic Kraken RF
Sentinel stack. It scores session-level RF/DoA behavioural regimes; it does
not identify physical transmitters.

### Architecture

KrakenSDR
→ deterministic burst / quality / tracking pipeline
→ session-level feature dataset
→ frozen preprocessing
→ frozen behavioural model
→ cluster assignment + distance
→ novelty / training-envelope analysis
→ prospective validation history

### Frozen model

- 21 historical training sessions
- 11 continuous RF/DoA features
- 3 exploratory behavioural clusters
- Frozen model commit: `49d5661`
- Frozen dataset SHA-256:
  `e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51`
- Prospective sessions are never used to refit model v0.1.

### Validation

Model development includes:

- PCA and agglomerative behavioural clustering
- 1,000-run perturbation / feature-subsampling stability analysis
- single-feature ablation
- feature-family ablation
- frozen-model regression scoring
- provenance locking

Formal natural prospective validation currently contains 12 valid sessions
across four runtime blocks:

Block A: C2 -> C2 -> C1
Block B: C1 -> C1 -> C1
Block C: C1 -> C1 -> C1
Block D: C1 -> C1 -> C1

Cluster status:

- **C1:** prospectively supported; 10/12 formal natural sessions and recurrence
  across fresh Kraken runtimes.
- **C2:** exploratory; 2 natural observations, both outside its original
  training-distance envelope; cross-runtime recurrence not demonstrated.
- **C0:** not prospectively validated.

Natural 014 is retained as evidence but excluded from formal Block D because
the DAQ preflight reported `adc_overdrive=True`.

### Prospective workflow

Fresh-runtime validation sequence:

start Kraken
-> wait for DAQ synchronization
-> run prospective-session check
-> enable Kraken Local Data Recording
-> run recorder-check
-> collect natural session
-> finalize against frozen model

Reference configuration:

- Frequency: 433.868160 MHz
- DoA method: MUSIC
- Decorrelation: Off
- Array: UCA
- Radius: 0.21 m
- Squelch: Manual / -45 dB

Useful commands:

    python -m ml.prospective_session check
    python -m ml.prospective_session recorder-check --wait 10
    python -m ml.prospective_session finalize --session SESSION_ID
    python -m ml.prospective_report
    python -m ml.cross_time_evaluation

The recorder check requires one controlled RF activation during its wait
window and verifies that `mydata.csv` actually advances.

### Release-candidate gate

- ML Python modules compile successfully.
- Focused ML tests: **5/5 PASS**
- Frozen training dataset SHA-256 verified.
- Release-candidate working tree verified clean.

### Limitations

Sentinel ML 1.0 does not establish:

- unique transmitter identification
- TPMS device fingerprint identification
- prospective validation of all three frozen clusters
- calibration-grade absolute DoA

## Usage

Run from the repository root with Python 3.

Live watcher (requires KrakenSDR CSV output at `~/krakensdr_doa/mydata.csv`):

```bash
PYTHONPATH=. python3 watcher/kraken_watch.py
```

The watcher writes `~/kraken_bursts.log`, `~/kraken_track_events.log`, and `~/kraken_episode_events.jsonl`.

Episode report, optionally filtered to a session (replace `SESSION_ID` with a recorded session ID):

```bash
python3 -m watcher.episode_report_cli --log ~/kraken_episode_events.jsonl
python3 -m watcher.episode_report_cli --session SESSION_ID --json
```

Unified session summary from burst, track, and episode logs:

```bash
python3 -m watcher.session_summary_cli --session SESSION_ID \
  --bursts-log ~/kraken_bursts.log \
  --track-log ~/kraken_track_events.log \
  --episode-log ~/kraken_episode_events.jsonl
```

Add `--json` for structured output. These paths are also the CLI defaults.

Focused tracker tests, including true replay:

```bash
python3 -m unittest discover -s tests -p 'test_tracker*.py' -v
```

## Project structure

- `watcher/` — live burst/event processing, shared tracking, source episodes, JSONL logging, and episode/session reporting CLIs
- `ml/` — behavioural dataset construction, clustering experiments, frozen-model scoring, prospective validation, and cross-time evaluation
- `results/ml/` — frozen model artefacts, prospective evidence, validation reports, and release-readiness records
- `reporting/` — existing session, persistence, and DoA analysis
- `fingerprinting/` — experimental RF feature extraction and baselines
- `capture/` — acquisition provenance, verification, activation logging, and episode grouping
- `analysis/` — versioned episode and passband analysis
- `captures/` and `notes/` — provenance bundles and recorded research results; raw IQ remains external
- `tests/` — automated checks and real-RF regression fixtures
- `docs/` — architecture, methodology, validation, and stage history
- `examples/` — example outputs and usage

## RF fingerprint research

RF fingerprint research uses recorded IQ, feature extraction, and same-device repeatability studies. At Stage 34, candidate features were tested across repeated captures from the same controlled keyfob. **RF Feature Vector V2** retains long-burst duration, recurrence interval, and relative spectral spacing; absolute carrier offset, received power, and DoA are excluded from the experimental identity score. These features are research candidates, not proven identifiers.

Historical milestones remain part of the evidence:

- Stages 1–22: platform bring-up.
- Stages 23–32: measurement integrity and DoA methodology.
- Stage 33: RF feature construction.
- Stage 34: same-device repeatability validation.
- Stage 35: controlled TPMS acquisition and between-device descriptive testing, including replication.

Work through 2026-09-19 includes capture manifests, configuration records, IQ size/SHA-256 provenance verification, acquisition-completeness validation using a fixed activation-to-recorder observation window, frozen Episode Grouping V1 and Episode Features V1 analysis, and Between-Device Discrimination V1 held-out testing with an independent replication.

The September 19 captures passed capture provenance verification and showed descriptive capture-level separation under the tested conditions. The earlier negative held-out result remains part of the evidence. Replication episode E07 was retained without post-hoc outlier removal.

See the [stage history](docs/stages.md), [held-out result](notes/BETWEEN-DEVICE-V1/between_device_v1.md), [replication](notes/BETWEEN-DEVICE-V1/between_device_replication_v1.md), and [replication acquisition completeness](captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/acquisition-completeness-v1.md).

These results do not establish unique device identification, production fingerprinting, or a universal same-device/different-device discrimination threshold. Between-Device Discrimination V1 defines no numerical discrimination PASS/FAIL threshold. Frozen methods and historical results are retained; methodological changes require a new version.

## Scope and research ethics

Research is limited to **owned, controlled, authorised, or consented RF sources**. Acquisition, validation, and interpretation must remain within that scope.

## Roadmap

With v1.0.0 and Sentinel ML 1.0 released, possible next work includes:

- Additional natural prospective behavioural validation across independent runtimes.
- Controlled multi-sensor TPMS datasets with session-level held-out evaluation.
- Multi-session source history and source correlation.
- Persistence scoring and richer alerts.
- Controlled between-device discrimination and independent validation across sources and sessions.
- Improved controlled/outdoor DoA validation.

## Release

**v1.0.0 — Core Analysis Stack**

- Git tag: `v1.0.0`
- Release commit: `c622e71`

**Sentinel ML 1.0 — Behavioural Regime Analysis**

- Git tag: `sentinel-ml-v1.0`
- Development branch: `ml-v0.1`
- Phase-1 checkpoint tag: `sentinel-ml-v0.1-phase1`
- Frozen-model commit: `49d5661`
