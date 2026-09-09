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
