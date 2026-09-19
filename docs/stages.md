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

## Stage 35 — Controlled TPMS acquisition and between-device descriptive testing

Work recorded through 2026-09-19 extends the earlier same-device studies with
capture provenance, frozen episode analysis, acquisition-completeness validation,
and held-out between-device testing. These are descriptive research milestones;
completion of a capture or replication does not establish a validated identity
classifier.

- **Capture provenance and frozen analysis:** Kraken capture manifests record
  acquisition boundaries, configuration, Git HEAD, IQ sizes, and SHA-256 hashes.
  `capture/verify_capture.py` checks capture provenance. The September 19
  between-device reports record verification PASS. Both runs used unchanged
  [Episode Grouping V1](kraken-episode-grouping-v1.md) and
  [Episode Features V1](kraken-episode-features-v1.md).
- **Acquisition completeness:** The [V1 protocol](kraken-acquisition-completeness-v1.md)
  evaluates recorder-file timestamps independently of episode grouping using
  `marker time < IQ file mtime <= marker time + 10.000 seconds`.
  [Capture 006](../captures/PIPELINE-TPMS-006-20260918-001713/acquisition-completeness-v1.md)
  records the initial validation result. A further
  [ACQ-COMPLETE-V1 capture](../captures/ACQ-COMPLETE-V1-20260919-021641/notes.md)
  was recorded on September 19; its bundle does not yet contain a scored result report.
- **Held-out descriptive testing:** The
  [Between-Device Discrimination V1 protocol](kraken-between-device-discrimination-v1.md)
  compares capture-level summaries of the frozen spectral feature against prior
  same-source measurements. The
  [September 18 S2 result](../captures/PIPELINE-TPMS-008-20260918-003900/between-device-discrimination-v1.md)
  did not show useful separation and remains part of the historical evidence.
  The [September 19 held-out report](../notes/BETWEEN-DEVICE-V1/between_device_v1.md)
  records descriptive separation under its tested conditions.
- **Independent replication, 2026-09-19:** The
  [replication report](../notes/BETWEEN-DEVICE-V1/between_device_replication_v1.md)
  records a further acquisition using the frozen methodology, with provenance
  verification PASS and descriptive capture-level separation from the prior
  same-source captures. E07 was retained without post-hoc outlier removal.
  The two September 19 capture-level medians also differed, demonstrating
  between-acquisition variation.
- **Replication acquisition completeness:** The
  [recorded timing analysis](../captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/acquisition-completeness-v1.md)
  reports 7/8 activations ACQUIRED and A1 NOT OBSERVED under the fixed temporal
  criterion. A recorder file in-window does not establish source identity;
  NOT OBSERVED does not establish that the sensor failed to transmit.

Between-Device Discrimination V1 defines no numerical discrimination PASS/FAIL
threshold. No universal same-device or different-device threshold, unique
device identification, or production fingerprint has been established.
Further independent validation is needed before stronger claims.

Related engineering work includes Episode Features V2 and Waveform Structure V1
development, plus independent HackRF wider-IQ provenance and PASSBAND-V1
characterization. These remain separate from the frozen Episode Features V1
results; [Wider-IQ V1](kraken-wider-iq-acquisition-v1.md) S1/S2 acquisition remains
locked pending its documented prerequisites.

## Stage 60 — Kraken RF Sentinel v1
Target: a lab-ready RF research platform with validated sensing, DoA, IQ analysis, and controlled-source characterization.
