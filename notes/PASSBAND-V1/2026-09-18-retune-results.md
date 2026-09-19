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

## Two-pass grid analysis and timing limitation

The primary 36-measurement grid consists of `pass1_minus900k.cs8` through
`pass1_plus900k.cs8` and the corresponding `pass2_...` files, excluding zero.
`pass2_minus900k_repeat.cs8` is supplemental and does not replace the primary
measurement. Centre, repeat, baseline and retune captures are not grid points.

Pass 1 was recorded 04:07–04:36 and Pass 2 14:00–14:32 on 2026-09-18.
These are recorded clock times; no timezone conversion is inferred here.
The passes were separated by ~10 hours and cannot establish controlled
amplitude repeatability. Frequency accuracy relative to commanded offsets
and between-pass amplitude differences must be reported separately.
Frequency agreement does not validate amplitude stability or calibrated
absolute receiver frequency accuracy.

Reproduce the grid calculations from the repository root (Python 3 and NumPy):

```sh
python3 analysis/passband_retune_v1.py /path/to/PASSBAND-V1 --output-dir notes/PASSBAND-V1
python3 -m unittest discover -s tests -p 'test_passband_retune_v1.py'
```

The analyzer opens CS8 inputs read-only and writes `passband_retune_v1.csv`
and `passband_retune_v1.md` to the output directory. The CSV contains 36 rows,
input hashes, frequency errors, endpoint clipping, offset means, the shared
four-measurement ±100000 Hz reference, relative responses and absolute
between-pass dB differences. The Markdown records the estimator and exclusions.

Review of Git history found the method pre-registration in `f59e75b` and
the retune narrative in `1073d33`, but no committed grid-analysis script or
exact historical FFT parameters. The existing `analysis/episode_features_*`
and `analysis/waveform_structure_v1.py` analyze Kraken evidence, not this CS8
grid. The new analyzer is an explicitly documented reconstruction, not a
claim of bit-for-bit reproduction of an unpreserved ad hoc estimator.

All pre-registered thresholds and the reference/contiguous-edge rules remain
unchanged. Numerical rule checks are diagnostic: a peak selected inside a
±5 kHz search is not independent proof of source-tone detection. No new SNR
threshold is introduced. The timing limitation and unresolved DC exclusion
prevent this analysis from freezing a usable passband or unlocking S1/S2.
