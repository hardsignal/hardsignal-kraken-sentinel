# Hardsignal Kraken Sentinel

Hardsignal Kraken Sentinel is an RF sensing, direction-finding, event-analysis, and controlled RF-characterisation platform built around KrakenSDR.

The project combines:

- RF event monitoring
- Direction-of-arrival analysis
- Session and recurrence tracking
- Automated reporting
- IQ capture and feature extraction
- Controlled RF fingerprint research
- Same-device repeatability validation

The current research scope uses owned, controlled, authorised, or consented RF sources.

## Current status

Work through 2026-09-19 includes the platform and same-device studies in
Stages 1–34, followed by controlled TPMS acquisition and descriptive
between-device testing:

- Capture manifests, configuration records, and IQ size/SHA-256 provenance verification.
- Acquisition-completeness validation using a fixed activation-to-recorder observation window.
- Frozen Episode Grouping V1 and Episode Features V1 analysis.
- Between-Device Discrimination V1 held-out testing and an independent replication.

The September 19 captures passed capture provenance verification and showed
descriptive capture-level separation under the tested conditions. The earlier
negative held-out result remains part of the evidence. Replication episode E07
was retained without post-hoc outlier removal.

See the [stage history](docs/stages.md),
[held-out result](notes/BETWEEN-DEVICE-V1/between_device_v1.md),
[replication](notes/BETWEEN-DEVICE-V1/between_device_replication_v1.md), and
[replication acquisition completeness](captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/acquisition-completeness-v1.md).

## Roadmap

- Stages 1–22: platform bring-up
- Stages 23–32: measurement integrity and DoA methodology
- Stage 33: RF feature construction
- Stage 34: same-device repeatability validation
- Stage 35: controlled TPMS acquisition and between-device descriptive testing, including replication
- Further work: independent validation across sources and sessions
- Stage 60: Kraken RF Sentinel v1

## Project structure

- `watcher/` — RF event monitoring and aggregation
- `reporting/` — session, persistence, and DoA analysis
- `fingerprinting/` — RF feature extraction and baselines
- `capture/` — acquisition provenance, verification, activation logging, and episode grouping
- `analysis/` — versioned episode and passband analysis
- `captures/` and `notes/` — provenance bundles and recorded research results; raw IQ remains external
- `docs/` — architecture, methodology, validation, and stage history
- `examples/` — example outputs and usage

## Research note

These results do not establish unique device identification, production
fingerprinting, or a universal same-device/different-device discrimination
threshold. Between-Device Discrimination V1 defines no numerical discrimination
PASS/FAIL threshold. Frozen methods and historical results are retained;
methodological changes require a new version.
