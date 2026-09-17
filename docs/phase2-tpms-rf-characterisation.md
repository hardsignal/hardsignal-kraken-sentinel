# Phase 2 — TPMS RF Characterisation

Controlled KrakenSDR DoA experiment using four TPMS sensors at 433.868160 MHz.

## Experimental conditions

- KrakenSDR UCA array remained fixed.
- Each sensor was placed in the same physical position.
- Sensors were triggered individually using the Autel TS508WF.
- Quiet baseline was recorded before sensor activation.
- Raw Kraken observations were retained.

## Results

| Sensor | Observations | Mean DoA | DoA SD | Mean Power |
|---|---:|---:|---:|---:|
| Sensor 1 | 21 | 205.00° | 2.07° | -34.24 dB |
| Sensor 2 | 17 | 190.82° | 1.25° | -36.79 dB |
| Sensor 3 | 20 | 213.35° | 3.88° | -31.35 dB |
| Sensor 4 | 19 main-cluster | 226.89° | 2.07° | -36.61 dB |

Sensor 4 produced one isolated 135° observation. The remaining
observations formed a stable 210–240° cluster, so the outlier was
retained in the raw data but excluded from the main-cluster stability
calculation.

## Baseline

With all four TPMS sensors inactive, no observations above the
-45 dB threshold were detected at 433.868160 MHz.

## Interpretation

All four sensors produced repeatable strong observations with distinct
main DoA clusters under the same physical setup.

The DoA separation is promising for controlled RF characterisation,
but it is not by itself proof of a unique RF fingerprint. Further
measurements should test repeatability across multiple trigger sessions
and examine additional RF features.

## Status

**Phase 2A — Controlled TPMS DoA characterisation: COMPLETE**

Next: repeat-session validation and RF feature comparison.

---

# Phase 2B — TPMS IQ Feature Characterisation

Date: 17 September 2026

Phase 2B extended the controlled TPMS experiment from DoA metadata to
recorded channelised IQ. The objective was to test whether candidate RF
features were repeatable within a sensor and whether they discriminated
Sensor 1 from Sensor 2.

The Phase 2A DoA measurements above and the Phase 2B IQ experiment are
retained as separate experimental datasets. Equivalence of their exact
sensor geometry was not established, so their absolute DoA values are
not directly combined.

## Acquisition

KrakenSDR VFO0 configuration:

- RF centre frequency: 433.868160 MHz
- VFO bandwidth: 25 kHz
- DAQ input sample rate: 2.400 MS/s
- VFO decimation factor: 96
- Saved IQ sample rate: 25,000 complex samples/s
- Saved IQ format: headerless NumPy complex128
- Manual squelch: -45 dB
- IQ recording: enabled

The KrakenSDR array remained fixed during the Sensor 1 / Sensor 2
comparison. Sensors were tested at the same marked experimental
position and orientation.

## Frozen extractor

The controlled recordings were analysed with:

`fingerprinting/tpms_iq_features.py`

Extractor SHA-256:

`5aa9e6e0452895a355880316bf884758fbc2811f11aac8c9f8f3e9f715509c84`

Frozen analysis parameters:

- envelope threshold: 0.05
- event join gap: 25 samples
- minimum event length: 5 samples
- spectral padding: 25 samples
- FFT size: 16384
- centre exclusion: +/-100 Hz
- separated spectral-peak distance: 300 Hz
- candidate short-event window: 4.50–5.40 ms

The extractor and its parameters were established using Sensor 2
recordings before Sensor 1 IQ was analysed. The extractor was not
modified after observing Sensor 1 results.

## Controlled capture results

| Capture | Short events | Duration median | P1/P2 spacing median |
|---|---:|---:|---:|
| Sensor 2 A | 5 | 4.600 ms | 12085.0 Hz |
| Sensor 2 B | 8 | 5.000 ms | 12086.5 Hz |
| Sensor 2 C | 5 | 4.600 ms | 12089.5 Hz |
| Sensor 1 A | 5 | 4.600 ms | 12088.0 Hz |
| Sensor 1 B | 7 | 4.640 ms | 12088.0 Hz |

Sensor 2 capture-median spectral spacing ranged from 12085.0 Hz to
12089.5 Hz. Both Sensor 1 capture medians were 12088.0 Hz.

Short-event duration also overlapped strongly between the two sensors.

## Spectral topology

Across Sensor 1 and Sensor 2 recordings, short events repeatedly showed
a dominant spectral component near -2.85 to -2.87 kHz relative to the
VFO centre and a recurring secondary component near +9.2 kHz. This
produced the frequently observed relative separation of approximately
12.09 kHz.

Additional spectral components repeatedly appeared in several regions,
including approximately +10.0/+10.6 kHz, +4.2/+4.4 kHz, and negative
components around -8.6 to -10 kHz.

The rank of secondary peaks was not stable in every event. A blind
P1/P2 rule sometimes selected a different spectral component, producing
alternate spacing measurements. These measurements are retained in the
structured results rather than removed as outliers.

One Sensor 1 event produced a 325 Hz P1/P2 spacing because two nearby
negative-frequency components occupied the first two amplitude ranks;
the recurring +9.2 kHz component remained present lower in the ranked
peak list. This demonstrates that second-highest FFT peak selection is
not, by itself, a robust fingerprint feature.

## Identity-feature interpretation

Candidate features tested in this experiment:

- short-event duration
- relative P1/P2 spectral spacing
- descriptive multi-component spectral topology

Explicitly excluded from identity scoring:

- absolute carrier offset
- received power
- DoA

Absolute carrier position and DoA remain useful descriptive
measurements, but were not used to force Sensor 1 / Sensor 2
discrimination.

## Result

Under the controlled geometry and frozen extraction method, Sensor 1
and Sensor 2 exhibited highly similar short-event duration and
approximately 12.09 kHz relative spectral-spacing structure.

The tested V1 timing and naive P1/P2 spectral-spacing features were
repeatable but did not provide useful Sensor 1 / Sensor 2
discrimination under these experimental conditions.

The experiment therefore establishes a negative discrimination result
for these specific candidate features rather than evidence of unique
device identity.

## Evidence

Structured measurements:

- `fingerprinting/results/tpms_s2_capture_a.json`
- `fingerprinting/results/tpms_s2_capture_b.json`
- `fingerprinting/results/tpms_s2_capture_c.json`
- `fingerprinting/results/tpms_s1_capture_a.json`
- `fingerprinting/results/tpms_s1_capture_b.json`

Extractor and structured results were frozen in Git commit:

`f3d6062` — `Add controlled TPMS IQ feature extraction`

## Status

**Phase 2B — Controlled TPMS IQ feature characterisation: COMPLETE**

Next work should treat any improved spectral-topology method as a
separate experiment rather than modifying the frozen V1 method to
produce Sensor 1 / Sensor 2 separation.
