# Kraken Wider-IQ Acquisition V1

## Status

PRE-REGISTERED — NO V1 DATA COLLECTED

## Motivation

The existing TPMS feature-development chain used Kraken VFO IQ recorded at
25,000 complex samples/s.

Architecture review established that this representation is produced from
the synchronized 2.4 MS/s Kraken stream by VFO filtering and 96x
decimation.

Episode Features V1, Episode Features V2, and Waveform Structure V1 did not
identify a feature satisfying their respective advancement criteria for
S1/S2 device discrimination.

Wider-IQ Acquisition V1 therefore tests a new acquisition representation
rather than another post-hoc feature search over the same 25 kS/s evidence.

## Research question

Does a wider synchronized RF representation preserve repeatable
device-dependent structure that is absent or insufficiently represented
after the existing 25 kS/s VFO channelization?

## Null interpretation

Wider bandwidth is not assumed to improve device discrimination.

If no stable between-device structure is observed, the result is negative
or inconclusive according to the criteria below.

## Baseline

The existing characterized baseline remains:

- target VFO frequency: 433.868160 MHz
- VFO bandwidth: 25 kHz
- recorded VFO rate: 25 kS/s complex IQ
- squelch mode: Manual
- squelch threshold: -45 dB
- global DSP decimation: 1
- firmware decimation ratio: 1

Existing captures are not reclassified as wider-IQ captures.

## Acquisition representation

The exact V1 wider-IQ acquisition mechanism is NOT YET SELECTED.

It must satisfy all of the following before V1 collection begins:

1. It must preserve more RF information than the existing 25 kS/s VFO
   recordings.
2. Its effective sample rate and usable bandwidth must be measured or
   established from the implementation.
3. It must not attach a competing consumer to the live
   `delay_sync_iq` FIFO handshake.
4. It must not run a second RTL-SDR acquisition process while Kraken owns
   the tuners.
5. It must not silently modify the existing characterized baseline.
6. The exact acquisition implementation must be documented and frozen
   before experimental sensor captures.

Until those conditions are satisfied, V1 RF collection must not begin.

## Sensors

Development comparison:

- S1
- S2

S3 remains reserved from this V1 development analysis.

S3 has been used by earlier independent work and is therefore not described
as globally untouched.

## Geometry

S1 and S2 must be tested under the same controlled geometry.

The following must remain fixed during a comparison session:

- Kraken antenna-array position and orientation;
- sensor activation position;
- sensor orientation;
- approximate sensor-to-array distance;
- target frequency configuration;
- receiver gain configuration;
- acquisition representation and sample rate.

Any intentional geometry change creates a separate experimental condition.

## Activation plan

Target:

- 8 deliberate activations for S1;
- 8 deliberate activations for S2.

Each activation must receive an operator marker.

Operator markers represent trigger-action timestamps, not exact RF emission
timestamps.

## Provenance

Every acquisition session must record:

- capture/session identifier;
- sensor label;
- acquisition start and finish timestamps;
- Git HEAD;
- acquisition implementation/version;
- relevant configuration snapshot;
- sample rate;
- usable bandwidth or filter bandwidth;
- center/target frequency;
- file names;
- file sizes;
- SHA-256 hashes;
- operator activation log.

Raw IQ must remain outside Git.

## Development order

The intended development order is:

1. collect S1 wider-IQ evidence;
2. independently repeat S1 if required to establish within-device
   repeatability;
3. collect S2 under the same controlled condition;
4. compare within-S1 variation against S1/S2 variation;
5. select candidate features only from S1/S2 development evidence;
6. freeze any advancing feature before inspecting S3 with that feature.

## Primary comparison

The primary question is not whether any individual metric differs between
S1 and S2.

A candidate feature must show:

1. repeatability within S1;
2. repeatability within S2 when sufficient data exist;
3. S1/S2 separation larger than ordinary within-device variation;
4. no dependence on a single extreme event;
5. a physically interpretable relationship to the wider-IQ signal
   representation.

Absolute received power and DoA are contextual measurements and are not
treated as device-identity features.

## Advancement rule

A feature may advance to S3 validation only if, using S1/S2 development
data alone:

- the feature definition is deterministic;
- extraction parameters are frozen;
- within-device repeatability is demonstrated;
- between-device separation exceeds observed within-device variation;
- the result is not driven by one event or one capture;
- the direction of the expected S3 comparison is pre-declared.

If no feature satisfies all conditions, no feature advances.

The advancement rule must not be weakened after seeing the data.

## Inconclusive criteria

The V1 experiment is inconclusive if any of the following prevents a valid
comparison:

- insufficient successful activations;
- acquisition loss or corruption;
- provenance failure;
- uncontrolled geometry change;
- configuration change between S1 and S2;
- inadequate sample-rate/bandwidth characterization;
- failure to associate captured evidence with the intended controlled
  activation sequence.

An inconclusive run is retained and documented rather than silently
discarded.

## Negative-result criterion

If acquisition and provenance are valid but no candidate feature satisfies
the advancement rule, the result is recorded as a negative V1 development
result.

No additional feature family is selected merely to obtain separation.

## Claims explicitly excluded

Wider-IQ Acquisition V1 does not by itself establish:

- unique device fingerprinting;
- transmitter identity;
- decoded TPMS identity;
- physical transmitter location;
- universal TPMS discrimination;
- production-class classifier performance;
- superiority of wider bandwidth before experimental validation.

## Next prerequisite

Before collecting V1 sensor data, select and validate a non-interfering
wider-IQ acquisition mechanism.

That mechanism becomes part of the frozen V1 protocol before the first
development capture.

## Acquisition mechanism selection

The V1 acquisition mechanism was selected prospectively after engineering
validation and before collection of S1 or S2 Wider-IQ V1 development data.

Selected receiver:

- independent HackRF One;
- HackRF operates independently of the running KrakenSDR acquisition chain;
- KrakenSDR remains unchanged and continues to provide the characterized
  25 kS/s baseline path.

Selected wider-IQ settings:

- center frequency: 433.868160 MHz;
- complex sample rate: 2,000,000 samples/s;
- baseband filter bandwidth: 1,750,000 Hz;
- representation: interleaved signed 8-bit I,Q (CS8);
- RF amplifier: OFF;
- RX LNA gain: 32 dB;
- RX VGA gain: 32 dB.

The selected HackRF sample rate is 80 times the sample rate of the existing
25 kS/s VFO-IQ representation. This ratio describes sample rates only and
does not imply an 80-fold increase in usable information or discrimination
performance.

## Engineering validation supporting selection

The mechanism was validated before S1/S2 V1 collection.

A 2 MS/s receive-only transport test produced exactly 4,000,000 complex
samples over 2 seconds, represented by exactly 8,000,000 CS8 bytes.

An explicit-filter ambient gain comparison tested:

- LNA/VGA 16/16 dB;
- LNA/VGA 24/24 dB;
- LNA/VGA 32/32 dB.

The 32/32 dB configuration increased ADC-code utilization without observed
full-scale clipping in that engineering comparison.

A subsequent 10-second controlled engineering capture used S4 only, which
is outside the S1/S2 V1 development comparison and the reserved S3 V1
validation stage.

That capture produced:

- 20,000,000 complex samples;
- 40,000,000 bytes;
- zero observed full-scale clipped I/Q values;
- substantial remaining ADC headroom.

A controlled S4 activation was attempted during the capture. Because no
activation timestamp was recorded for that engineering run, individual
signal peaks are not attributed to S4.

These engineering captures are not Wider-IQ V1 development evidence.

## Hardware provenance note

The HackRF used for V1 reports:

- Board ID: HackRF One;
- hardware revision: r9;
- firmware: v2.0.1, API 1.08.

The installed HackRF utility additionally reports that the hardware does
not appear to have been manufactured by Great Scott Gadgets.

This observation is retained as acquisition provenance and does not by
itself invalidate the engineering captures.

## Frozen acquisition boundary

For Wider-IQ Acquisition V1, the settings above are frozen before the first
S1 development activation.

Do not alter center frequency, sample rate, baseband filter, RF-amplifier
state, LNA gain, VGA gain, sample representation, or receiver hardware
between S1 and S2 development captures.

If a required acquisition-setting change is discovered after V1 data
collection begins, stop the current V1 comparison and document the change
rather than silently combining incompatible captures.

The existing Kraken 25 kS/s acquisition configuration remains unchanged.

## Next prerequisite after mechanism selection

Before the first S1 Wider-IQ V1 capture, implement and validate provenance
for the new HackRF CS8 acquisition path.

That provenance must record the frozen receiver settings, timestamps,
sensor label, Git HEAD, acquisition-tool version, output size, SHA-256,
and operator activation log.

No S1 or S2 Wider-IQ V1 development capture may begin until that provenance
path has been validated.
