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

## Controlled Array Orientation Validation

A later controlled experiment investigated a recurrent directional candidate at:

**433.999392 MHz**

The antenna array was tested using an A → B → A configuration while preserving
the measurement setup and RF processing parameters.

### Orientation A — Original Array Position

Session `20260910-034827` produced:

- 27 observations at 433.999392 MHz
- circular mean: **228.2°**
- directional concentration: **0.999**
- dominant classified state: **227.7°**
- 22 classified hits

### Orientation B — 90° Clockwise Array Rotation

The complete antenna array was rotated approximately 90° clockwise without
changing antenna spacing, channel assignments, cabling, or receiver settings.

Session `20260910-040627` produced:

- circular mean: **115.4°**
- directional concentration: **0.982**
- classified state: **99.4°** (7 hits)
- classified state: **122.8°** (18 hits)

The directional response therefore changed substantially after changing the
physical orientation of the array.

### Orientation A' — Original Position Restored

The array was then rotated approximately 90° counter-clockwise to restore the
original orientation.

Session `20260910-041951` produced a dominant coherent state of:

- bearing: **221.0°**
- classified hits: **13**
- median DoA width: **46°**
- median peak count: **1**

The restored dominant coherent state was within **6.7°** of the original
classified state (**227.7° → 221.0°**).

### Automated Cross-Session State Matching

The reporting pipeline was extended to extract dominant directional states from
historical sessions using the same qualification, 10° binning, local-peak, and
±10° neighbourhood rules used by the session directional classifier.

For 433.999392 MHz, the automated comparison recovered:

- Session `20260910-034827`: **227.7°**, 22 hits, median width 44°, median peaks 1
- Session `20260910-040627`: **122.8°**, 18 hits, median width 36°, median peaks 1
- Session `20260910-041951`: **221.0°**, 13 hits, median width 46°, median peaks 1

The automatically calculated state changes were:

- first → second session: **104.8°**
- second → third session: **98.2°**
- first → final state error: **6.7°**
- return-state match: **YES**

The comparison operates on classified directional states rather than forcing
low-sample sessions into the analysis.

### Ambiguity, Recovery, and Stability

The restored-orientation session also contained a temporary period of
multi-peak directional ambiguity.

The reporter identified:

- raw observations: **19**
- multi-peak observations: **9**
- multi-peak fraction: **47.4%**
- ambiguity window: **04:21:14–04:24:00**
- ambiguity-window duration: **166 s**
- maximum observed peak count: **3**
- maximum DoA width: **144.5°**
- minimum confidence: **1.70**

A coherent solution subsequently resumed at **04:24:13**, giving:

- recovery delay after the final multi-peak observation: **13 s**
- coherent recovery samples: **7**
- recovered centroid: **220.9°**
- dominant classified state: **221.0°**
- recovery centroid error: **0.1°**

The state-transition sequence was therefore:

**COHERENT → AMBIGUOUS → COHERENT**

The interval from the beginning of the ambiguity window to confirmed coherent
recovery was **179 s**. The session-level stability classifier reported
**MIXED / RECOVERING**.

### Interpretation

The A → B → A experiment demonstrated a repeatable orientation-dependent DoA
response. Rotating the array moved the dominant directional solution away from
the original ~220–230° sector, while restoring the array returned the dominant
coherent solution to approximately that sector.

The measured angular change was not a simple 1:1 transformation of the physical
array rotation. Indoor multipath, reflections, antenna geometry, placement, and
other environmental effects therefore remain important factors.

These measurements demonstrate repeatability of the KrakenSDR directional
response under controlled geometry changes. They do **not** establish the
identity or physical location of the observed transmitter.

## Phase 1 Conclusion

Phase 1 established a repeatable passive RF/DoA observation baseline around
433.868160 MHz and subsequently produced a controlled directional-validation
candidate at 433.999392 MHz.

For the 433.999392 MHz candidate, the A → B → A' experiment demonstrated that
changing array orientation produced a substantial change in the dominant
classified DoA state, while restoring the original orientation returned the
dominant state to within 6.7° of its original value.

The analysis pipeline also demonstrated that a single aggregate bearing can
hide meaningful behaviour. Directional-state extraction exposed coherent
states, multi-peak ambiguity, state transitions, recovery latency, and
cross-session return-state matching.

These results establish repeatability of the measured KrakenSDR directional
response under the tested conditions. They do not establish transmitter
identity or physical transmitter location, and the non-ideal response to array
rotation remains consistent with significant environmental and multipath
influence.

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
