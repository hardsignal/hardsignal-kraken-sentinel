# HackRF Passband Characterization V1

Status: PRE-REGISTERED ENGINEERING METHOD

## Purpose

Empirically characterize the usable analysis passband of the frozen
HackRF Wider-IQ V1 receive configuration before any S1/S2 acquisition.

This is engineering characterization only. No S1, S2, or S3 device
observations are used.

## Frozen receiver configuration

- Center frequency: 433.868160 MHz
- Complex sample rate: 2.000000 MS/s
- Baseband filter setting: 1.750000 MHz
- RF amplifier: OFF
- Antenna power: OFF
- LNA gain: 32 dB
- VGA gain: 32 dB
- Sample format: CS8 interleaved signed I/Q
- Capture duration per measurement: 2 s
- Samples per measurement: 4,000,000 complex samples

Receiver settings remain unchanged throughout characterization.

## Stimulus and geometry

- Source: tinySA Ultra+ signal generator, sine output
- Generator level: -18.5 dBm
- Coupling: radiated antenna-to-antenna
- Source and HackRF antennas remain stationary throughout the sweep
- No direct coax connection is used
- Sweep mode remains OFF
- Only generator frequency changes between measurements
- The generator is disabled while changing frequency

Because the stimulus is radiated rather than a calibrated conducted
injection, this experiment characterizes the response of the frozen
measurement arrangement. It is not an absolute calibrated measurement
of HackRF receiver gain.

## Predeclared tone offsets

Offsets are relative to the frozen HackRF center frequency of
433.868160 MHz.

Measurements shall be made at:

- -900 kHz
- -800 kHz
- -700 kHz
- -600 kHz
- -500 kHz
- -400 kHz
- -300 kHz
- -200 kHz
- -100 kHz
- +100 kHz
- +200 kHz
- +300 kHz
- +400 kHz
- +500 kHz
- +600 kHz
- +700 kHz
- +800 kHz
- +900 kHz

A 0 Hz measurement is excluded from passband-response estimation
because a center-frequency CW tone overlaps the HackRF direct-conversion
DC component.

Each non-zero offset shall be measured in two independent captures.
The complete negative-to-positive grid is measured once and then
repeated as a second pass.

No tone offset may be added, removed, or repositioned in response to
the observed amplitude results.

## Tone measurement

For each capture:

1. Decode CS8 as interleaved signed int8 complex I/Q.
2. Verify the expected sample count and check for ADC endpoint clipping.
3. Estimate the received tone frequency by searching within +/-5 kHz
   of the commanded non-zero offset.
4. Measure tone power using the same FFT length, window, and
   normalization for every capture.
5. Record the measured tone offset and amplitude.
6. Do not use the 0 Hz/DC bin as a response reference.

The analysis implementation and parameters shall be identical for all
offsets and both passes.

## Relative-response reference

For each offset, combine the two independent measurements using their
arithmetic mean in dB.

The reference level is the arithmetic mean of the four measurements at
-100 kHz and +100 kHz.

Each offset response is expressed in dB relative to this fixed
near-center reference.

## Usable-passband rule

An offset is accepted only when:

- neither capture contains ADC endpoint clipping;
- the expected tone is detected within +/-5 kHz of its commanded
  offset;
- the mean relative response is no more than 3.0 dB below the
  near-center reference; and
- the two repeated amplitude measurements differ by no more than
  1.0 dB.

The final usable edge on each side is the outermost accepted offset for
which every tested offset between it and +/-100 kHz also passes.

The final analysis passband is symmetric about 0 Hz and uses the
smaller absolute value of the accepted negative and positive edges.

No isolated passing point beyond a failing point may extend the usable
passband.

## DC treatment

The center-frequency result is not estimated from this radiated CW
test because the injected center tone is inseparable from the
receiver's direct-conversion DC component.

This characterization therefore does not by itself define the final
DC-exclusion width. DC exclusion shall be characterized separately
and frozen before S1/S2 acquisition.

## Decision discipline

The -3.0 dB response threshold, 1.0 dB repeatability threshold,
frequency tolerance, tone grid, reference definition, and symmetric
edge rule are fixed before collection of the characterization sweep.

They shall not be changed after inspecting the sweep results.
