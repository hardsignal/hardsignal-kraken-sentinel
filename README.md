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

Stages 1–34 complete.

Current validated work includes:

- KrakenSDR DoA observation handling
- event aggregation and logging
- session integrity checks
- RF persistence analysis
- directional stability analysis
- cross-session recurrence analysis
- IQ capture workflow
- burst timing and spectral feature extraction
- same-device feature repeatability testing
- RF Feature Vector V2

Feature Vector V2 currently uses:

- long-burst duration
- burst recurrence interval
- relative phase-state to spectral-component spacing

Absolute carrier offset, received power, and DoA are excluded from the identity score.

## Roadmap

- Stages 1–22: platform bring-up
- Stages 23–32: measurement integrity and DoA methodology
- Stage 33: RF feature construction
- Stage 34: same-device repeatability validation
- Stage 35+: between-device discrimination
- Stage 60: Kraken RF Sentinel v1

## Project structure

- `watcher/` — RF event monitoring and aggregation
- `reporting/` — session, persistence, and DoA analysis
- `fingerprinting/` — RF feature extraction and baselines
- `docs/` — architecture, methodology, validation, and stage history
- `examples/` — example outputs and usage

## Research note

RF fingerprint features are treated as experimental evidence, not assumed identifiers. Features are tested for repeatability and rejected or revised when they fail validation.
