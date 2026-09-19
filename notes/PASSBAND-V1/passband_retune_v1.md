# PASSBAND-V1 grid reconstruction

Engineering analysis only; S1/S2 remain locked. No usable passband is established.

Pass 1 was recorded 04:07–04:36 and Pass 2 14:00–14:32 on 2026-09-18 (recorded clock times; no timezone conversion inferred). The passes were separated by ~10 hours and cannot establish controlled amplitude repeatability. Between-pass amplitude differences are descriptive, even where the 1.0 dB rule passes.

## Frequency accuracy versus amplitude repeatability

36/36 expected captures; all contain 4,000,000 complex samples. ADC endpoint values: 8.

Frequency error (measured minus commanded): -384.521 to -175.476 Hz; maximum absolute error 384.521 Hz. These are candidate-peak errors relative to commanded offsets, not a calibrated absolute receiver accuracy measurement or evidence of amplitude repeatability. The ±5 kHz search constrains the selected peak by construction; without a predeclared detection/SNR criterion it does not prove source-tone detection.

Four-measurement ±100000 Hz arithmetic-dB reference: 19.923649 dB ADC².

| Offset Hz | Mean dB ADC² | Relative dB | Between-pass Δ dB | Clip OK | Frequency OK | Response OK | Δ OK | Numerical rules |
| ---: | ---: | ---: | ---: | :---: | :---: | :---: | :---: | :---: |
| -900000 | 23.759 | 3.836 | 3.152 | no | yes | yes | no | no |
| -800000 | 27.136 | 7.212 | 3.867 | yes | yes | yes | no | no |
| -700000 | 27.201 | 7.277 | 2.886 | yes | yes | yes | no | no |
| -600000 | 26.354 | 6.430 | 3.915 | yes | yes | yes | no | no |
| -500000 | 24.795 | 4.872 | 8.254 | yes | yes | yes | no | no |
| -400000 | 25.105 | 5.182 | 7.970 | yes | yes | yes | no | no |
| -300000 | 22.591 | 2.667 | 7.392 | yes | yes | yes | no | no |
| -200000 | 22.672 | 2.748 | 1.993 | yes | yes | yes | no | no |
| -100000 | 20.786 | 0.863 | 5.510 | yes | yes | yes | no | no |
| +100000 | 19.061 | -0.863 | 4.048 | yes | yes | yes | no | no |
| +200000 | 19.372 | -0.552 | 3.054 | yes | yes | yes | no | no |
| +300000 | 19.243 | -0.681 | 1.035 | yes | yes | yes | no | no |
| +400000 | 18.858 | -1.066 | 2.429 | yes | yes | yes | no | no |
| +500000 | 20.137 | 0.213 | 0.611 | yes | yes | yes | yes | yes |
| +600000 | 18.214 | -1.709 | 0.238 | yes | yes | yes | yes | yes |
| +700000 | 21.537 | 1.613 | 2.695 | yes | yes | yes | no | no |
| +800000 | 23.440 | 3.517 | 7.078 | yes | yes | yes | no | no |
| +900000 | 22.792 | 2.869 | 9.896 | yes | yes | yes | no | no |

Numerical contiguous edges: +0, +0 Hz; symmetric half-width: 0 Hz (0 means no contiguous accepted interval). These are arithmetic diagnostics, not validation of controlled amplitude repeatability. DC exclusion remains unresolved.

## Reproduction

CS8 signed I+jQ, 2000000 samples/s; 262144-point NumPy symmetric Hann window; 15 nonoverlapping complete blocks averaged in linear power; last 67840 samples omitted from FFT only. Clipping counts -128 and +127 across all I/Q values. Peak search ±5000 Hz; frequency is the peak bin (no interpolation); power sums peak ±2 bins, normalized by NFFT × sum(window²). dB = 10 log10(power in ADC-code²). No DC subtraction or per-pass amplitude normalization.

Offset means and the four-point reference are arithmetic means in dB. Thresholds remain ≥-3.0 dB relative response, ≤1.0 dB pair difference, ±5000 Hz frequency tolerance, no clipping, and contiguous symmetric edges. This estimator is documented retrospectively; the Git pre-registration did not specify an FFT length, window, normalization or numerical detection criterion.

NumPy version: 1.26.4. CSV records input SHA-256 hashes. Only exact primary grid filenames are included; no replacement by extra repeats.

Excluded CS8 files: `centre_repeat1.cs8`, `centre_repeat2.cs8`, `centre_repeat3.cs8`, `hackrf_433468160_baseline_10s.cs8`, `minus400_long10s.cs8`, `minus400_repeat1.cs8`, `minus400_repeat2.cs8`, `minus400_repeat3.cs8`, `pass2_minus900k_repeat.cs8`, `target_433510987_10s.cs8`, `test_433867910_10s.cs8`, `test_434000000_10s.cs8`.
