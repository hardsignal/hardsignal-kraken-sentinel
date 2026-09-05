# Hardsignal Kraken Sentinel — Stage History

## Stages 1–22 — Platform bring-up

Initial KrakenSDR setup, DoA workflow development, event monitoring, logging, and basic RF observation handling.

## Stage 23 — Session integrity
Added session IDs, ownership checks, marker validation, and record consistency.

## Stage 24 — RF persistence
Added current-session and historical persistence analysis.

## Stage 25 — Directional stability
Added circular mean and directional concentration analysis.

## Stage 26 — Candidate quality
Combined persistence and directional coherence into candidate classifications.

## Stage 27 — Power and confidence study
Separated descriptive RF quality metrics from candidate evidence.

## Stage 28 — Descriptive metrics
Added structured session and frequency measurements.

## Stage 29 — Report readability
Refined Sentinel reporting into a research-oriented format.

## Stage 30 — Temporal DoA validation
Added time-windowed DoA analysis and directional evolution checks.

## Stage 31 — Cross-session recurrence
Added tagged-session recurrence and cross-session DoA comparison.

## Stage 32 — DoA and RF quality
Validated Kraken CSV/DoA structure and separated RF quality, DoA quality, estimator diagnostics, and timing.

## Stage 32B — Watcher/report integration
Added DoA half-max width and local peak count to watcher events and reports.

## Stage 33 — RF fingerprint construction
Moved fingerprint research from DoA metadata to recorded IQ.

Validated burst segmentation, timing, recurrence, spectral analysis, and baseline storage.

## Stage 34 — Same-device repeatability
Tested candidate RF features across repeated captures from the same controlled keyfob.

Feature Vector V2 keeps:
- long-burst duration
- recurrence interval
- relative spectral spacing

Absolute carrier offset, received power, and DoA are excluded from the identity score.

## Stage 35+ — Between-device discrimination
Compare within-device and between-device feature distributions using multiple controlled transmitters.

## Stage 60 — Kraken RF Sentinel v1
Target: a lab-ready RF research platform with validated sensing, DoA, IQ analysis, and controlled-source characterization.
