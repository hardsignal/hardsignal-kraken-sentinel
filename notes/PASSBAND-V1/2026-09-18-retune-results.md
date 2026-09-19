# PASSBAND-V1 — RF Retune / Cross-Instrument Validation

Date: 2026-09-18
Project: Hardsignal Labs — PASSBAND-V1

## Hardware topology

### HackRF path
HackRF One → antenna → workstation

### Conducted measurement path
ZS-407 / TinySA → attenuator → RTL-SDR → workstation

The two paths were not connected through a splitter.

## HackRF configuration

Sample rate: 2 MS/s
Baseband filter: 1.75 MHz
LNA: 32 dB
VGA: 32 dB
AMP: OFF
Antenna power: OFF

## Initial baseline

Centre: 433.468160 MHz

10 s capture:
`hackrf_433468160_baseline_10s.cs8`

A separate 20 s capture was subsequently recorded as:
`minus400_long10s.cs8`

Measured centre-region result:
- Peak offset: 0 Hz
- Carrier-band: 60.61 dB
- Noise-band: 59.07 dB
- SNR: 1.55 dB

## -400 kHz investigation

Initial analysis showed a persistent spectral component around:

+399.75 kHz relative to 433.468160 MHz

corresponding to approximately:

433.86791 MHz RF

A retune test was performed at 433.867910 MHz.

Result:
- Strongest component: +132.0705 kHz
- Strongest RF: 433.9999805 MHz
- Centre-region peak: 0 Hz
- +400 kHz region: +397.8081 kHz

A further retune was performed at 434.000000 MHz.

Result:
- Strongest component: -500.0076 kHz
- Strongest RF: 433.4999924 MHz
- Centre-region peak: 0 Hz
- +132 kHz region: +136.8599 kHz

## ZS-407 / RTL cross-check

A wider ZS-407/RTL observation covered the 433.400–433.550 MHz region.

A later narrowed ZS-407 observation covered approximately 433.515–433.545 MHz.

Marker levels varied approximately:
- -55 dBm to -62 dBm

Observed features included approximately:
- 433.430 MHz region in the wider-span observation
- 433.520 MHz region
- 433.540 MHz region

The HackRF sweep independently showed nearby spectral structure, including:
- 433.431067 MHz
- 433.520978 MHz
- 433.540957 MHz

These observations establish cross-instrument agreement on RF structure, but do not identify a transmitter.

## Conclusion

The HackRF retune experiment did not establish a fixed external carrier corresponding to the initially observed +400 kHz component.

Spectral maxima changed relative to the HackRF centre frequency across the retune tests.

Therefore the observed maxima must not be interpreted as a confirmed transmitter without further controlled-source/reference testing.

The ~433.430, ~433.520 and ~433.540 MHz structures were observed independently with the HackRF and ZS-407/RTL measurement paths, but their source and signal type remain unidentified.

## Evidence

Raw IQ captures remain under:

`~/hardsignal-data/hackrf/PASSBAND-V1/`

Relevant captures:
- `hackrf_433468160_baseline_10s.cs8`
- `minus400_long10s.cs8`
- `test_433867910_10s.cs8`
- `test_434000000_10s.cs8`
- `target_433510987_10s.cs8`

The large CS8 captures should remain outside Git unless deliberately archived elsewhere.
