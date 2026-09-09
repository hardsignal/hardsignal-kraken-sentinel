# Phase 1 — RF Observation & DoA Characterisation

## Objective

Characterise RF activity and direction-of-arrival (DoA) behaviour using a KrakenSDR array under controlled laboratory conditions.

The initial objective was to establish a repeatable RF/DoA baseline before progressing to controlled RF fingerprinting of individual TPMS transmitters.

## Instrumentation

- KrakenSDR
- Five-element V-dipole array
- Linux workstation
- 433 MHz RF observation
- Controlled TPMS transmitter experiments

## Observed RF

A repeated signal was observed at:

**433.868160 MHz**

The dataset contained 4,548 observations at this frequency during the analysed measurement period.

## DoA Results

Several repeatable directional clusters were identified.

| DoA cluster | Observations | Mean bearing | Standard deviation |
|---|---:|---:|---:|
| ~65° | 81 | 64.79° | 1.06° |
| ~123° | 16 | 123.31° | 1.26° |
| ~343° | 20 | 342.60° | 3.60° |
| ~229° | 11 | 228.82° | 3.35° |
| ~99° | 65 | 99.22° | 4.72° |
| ~20° | 18 | 19.89° | 5.35° |

## Key Observation

The strongest and most stable directional cluster was:

**64.79° ± 1.06° (N=81)**

A second highly stable cluster was:

**123.31° ± 1.26° (N=16)**

These results demonstrate repeatable DoA estimation from the array under the tested laboratory configuration.

## Environmental Effects

Measurements demonstrated that array geometry and the surrounding RF environment can substantially affect the observed DoA.

Multiple angular modes were observed for the same RF frequency. These may represent different transmitter positions, reflections, multipath propagation, array ambiguity, or other environmental effects.

Consequently, a DoA cluster is not treated as proof of a unique transmitter identity.

## Phase 1 Conclusion

Phase 1 established a repeatable RF/DoA baseline at 433.868160 MHz.

The KrakenSDR successfully produced stable directional estimates from repeated RF activity. The measurements also demonstrated the importance of controlled geometry and environmental conditions when attempting to associate RF observations with individual devices.

## Transition to Phase 2

Phase 2 will investigate controlled RF fingerprinting of individual TPMS transmitters.

The objective is to determine whether measurements such as:

- frequency
- signal strength
- temporal behaviour
- DoA
- burst characteristics
- other RF features

can be used to distinguish individual controlled transmitters.

No individual TPMS sensor identity is assigned to the DoA clusters in this Phase 1 report.

---

**Project:** Hardsignal Labs  
**Phase:** 1 — RF Observation & DoA Characterisation  
**Status:** Complete
