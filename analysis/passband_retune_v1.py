#!/usr/bin/env python3
"""Offline PASSBAND-V1 grid reconstruction; never opens RF hardware.

See docs/hackrf-passband-characterization-v1.md for the pre-registered rules
and notes/PASSBAND-V1/2026-09-18-retune-results.md for interpretation limits.
"""

import argparse
import csv
import hashlib
import re
from pathlib import Path

import numpy as np


SAMPLE_RATE = 2_000_000
EXPECTED_SAMPLES = 4_000_000
NFFT = 262_144
FREQUENCY_TOLERANCE_HZ = 5_000
MIN_RELATIVE_DB = -3.0
MAX_REPEAT_DIFFERENCE_DB = 1.0
OFFSETS = tuple(k * 1000 for k in range(-900, 901, 100) if k)
REFERENCE_OFFSETS_HZ = (-100_000, 100_000)
EXPECTED_KEYS = {(p, offset) for p in (1, 2) for offset in OFFSETS}
NAME = re.compile(r"pass([12])_(minus|plus)([1-9]00)k\.cs8")


def parse_filename(name):
    """Return (pass, signed offset in Hz); reject supplemental repeats."""
    match = NAME.fullmatch(Path(name).name)
    if not match:
        raise ValueError(f"Not a primary grid filename: {name}")
    pass_number, sign, khz = match.groups()
    return int(pass_number), int(khz) * 1000 * (-1 if sign == "minus" else 1)


def discover_grid(directory):
    files = {}
    excluded = []
    for path in sorted(directory.glob("*.cs8")):
        try:
            key = parse_filename(path.name)
        except ValueError:
            excluded.append(path.name)
            continue
        files[key] = path
    if set(files) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(files))
        raise ValueError(f"Expected exactly 36 primary grid measurements; missing {missing}")
    return files, excluded


def measure(path, pass_number, offset):
    raw = path.read_bytes()
    if len(raw) != EXPECTED_SAMPLES * 2:
        raise ValueError(f"{path.name}: expected 8000000 CS8 bytes, got {len(raw)}")
    codes = np.frombuffer(raw, dtype=np.int8)
    clipped = int(np.count_nonzero((codes == -128) | (codes == 127)))
    iq = codes[0::2].astype(np.float64) + 1j * codes[1::2]
    window = np.hanning(NFFT)
    spectrum = np.zeros(NFFT)
    blocks = len(iq) // NFFT
    for start in range(0, blocks * NFFT, NFFT):
        spectrum += np.abs(np.fft.fft(iq[start:start + NFFT] * window)) ** 2
    # Integrated spectrum is mean-square complex amplitude in ADC-code units.
    spectrum /= blocks * NFFT * np.sum(window ** 2)
    frequencies = np.fft.fftfreq(NFFT, 1 / SAMPLE_RATE)
    candidates = np.flatnonzero(np.abs(frequencies - offset) <= FREQUENCY_TOLERANCE_HZ)
    peak = int(candidates[np.argmax(spectrum[candidates])])
    measured = float(frequencies[peak])
    power = float(np.sum(spectrum[(peak + np.arange(-2, 3)) % NFFT]))
    if power <= 0 or not np.isfinite(power):
        raise ValueError(f"{path.name}: no finite positive candidate tone power")
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "pass": pass_number,
        "offset_hz": offset,
        "samples": len(iq),
        "endpoint_clipped_values": clipped,
        "clipped_fraction": clipped / len(codes),
        "measured_offset_hz": measured,
        "frequency_error_hz": measured - offset,
        "tone_power_db_adc2": float(10 * np.log10(power)),
        "frequency_within_tolerance": abs(measured - offset) <= FREQUENCY_TOLERANCE_HZ,
    }


def summarize_grid(rows):
    keys = [(r["pass"], r["offset_hz"]) for r in rows]
    if len(keys) != 36 or set(keys) != EXPECTED_KEYS:
        raise ValueError("Expected 36 unique measurements: two passes of the 18-point grid")
    reference = float(np.mean([
        r["tone_power_db_adc2"] for r in rows
        if r["offset_hz"] in REFERENCE_OFFSETS_HZ
    ]))
    groups = {}
    for offset in OFFSETS:
        pair = sorted((r for r in rows if r["offset_hz"] == offset), key=lambda r: r["pass"])
        mean = float(np.mean([r["tone_power_db_adc2"] for r in pair]))
        difference = abs(pair[1]["tone_power_db_adc2"] - pair[0]["tone_power_db_adc2"])
        relative = mean - reference
        flags = {
            "clipping_ok": all(r["endpoint_clipped_values"] == 0 for r in pair),
            "frequency_ok": all(r["frequency_within_tolerance"] for r in pair),
            "response_ok": relative >= MIN_RELATIVE_DB,
            "repeat_difference_ok": difference <= MAX_REPEAT_DIFFERENCE_DB,
        }
        groups[offset] = {
            "mean_power_db_adc2": mean,
            "relative_response_db": relative,
            "between_pass_difference_db": difference,
            **flags,
            "numerical_rules_pass": all(flags.values()),
        }
        for row in pair:
            row.update(groups[offset])
            row["reference_power_db_adc2"] = reference
            row["controlled_amplitude_repeatability_established"] = False
    edges = []
    for sign in (-1, 1):
        edge = 0
        for magnitude in range(100_000, 900_001, 100_000):
            if not groups[sign * magnitude]["numerical_rules_pass"]:
                break
            edge = magnitude
        edges.append(sign * edge)
    return reference, groups, edges


def markdown_summary(rows, reference, groups, edges, excluded):
    errors = np.array([r["frequency_error_hz"] for r in rows])
    lines = [
        "# PASSBAND-V1 grid reconstruction", "",
        "Engineering analysis only; S1/S2 remain locked. No usable passband is established.", "",
        "Pass 1 was recorded 04:07–04:36 and Pass 2 14:00–14:32 on 2026-09-18 "
        "(recorded clock times; no timezone conversion inferred). The passes were separated "
        "by ~10 hours and cannot establish controlled amplitude repeatability. "
        "Between-pass amplitude differences are descriptive, even where the 1.0 dB rule passes.", "",
        "## Frequency accuracy versus amplitude repeatability", "",
        f"36/36 expected captures; all contain {EXPECTED_SAMPLES:,} complex samples. "
        f"ADC endpoint values: {sum(r['endpoint_clipped_values'] for r in rows)}.", "",
        f"Frequency error (measured minus commanded): {errors.min():.3f} to "
        f"{errors.max():.3f} Hz; maximum absolute error {np.max(np.abs(errors)):.3f} Hz. "
        "These are candidate-peak errors relative to commanded offsets, not a calibrated "
        "absolute receiver accuracy measurement or evidence of amplitude repeatability. "
        "The ±5 kHz search constrains the selected peak by construction; without a "
        "predeclared detection/SNR criterion it does not prove source-tone detection.", "",
        f"Four-measurement ±100000 Hz arithmetic-dB reference: {reference:.6f} dB ADC².", "",
        "| Offset Hz | Mean dB ADC² | Relative dB | Between-pass Δ dB | Clip OK | Frequency OK | Response OK | Δ OK | Numerical rules |",
        "| ---: | ---: | ---: | ---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for offset, g in groups.items():
        flags = " | ".join("yes" if g[k] else "no" for k in (
            "clipping_ok", "frequency_ok", "response_ok", "repeat_difference_ok", "numerical_rules_pass"))
        lines.append(f"| {offset:+d} | {g['mean_power_db_adc2']:.3f} | "
                     f"{g['relative_response_db']:.3f} | {g['between_pass_difference_db']:.3f} | {flags} |")
    lines += [
        "", f"Numerical contiguous edges: {edges[0]:+d}, {edges[1]:+d} Hz; "
        f"symmetric half-width: {min(abs(e) for e in edges)} Hz "
        "(0 means no contiguous accepted interval). These are arithmetic diagnostics, "
        "not validation of controlled amplitude repeatability. DC exclusion remains unresolved.", "",
        "## Reproduction", "",
        f"CS8 signed I+jQ, {SAMPLE_RATE} samples/s; {NFFT}-point NumPy symmetric Hann "
        f"window; {EXPECTED_SAMPLES // NFFT} nonoverlapping complete blocks averaged in linear power; "
        f"last {EXPECTED_SAMPLES % NFFT} samples omitted from FFT only. "
        "Clipping counts -128 and +127 across all I/Q values. Peak search ±5000 Hz; "
        "frequency is the peak bin (no interpolation); power sums peak ±2 bins, "
        "normalized by NFFT × sum(window²). dB = 10 log10(power in ADC-code²). "
        "No DC subtraction or per-pass amplitude normalization.", "",
        "Offset means and the four-point reference are arithmetic means in dB. "
        "Thresholds remain ≥-3.0 dB relative response, ≤1.0 dB pair difference, "
        "±5000 Hz frequency tolerance, no clipping, and contiguous symmetric edges. "
        "This estimator is documented retrospectively; the Git pre-registration did "
        "not specify an FFT length, window, normalization or numerical detection criterion.", "",
        f"NumPy version: {np.__version__}. CSV records input SHA-256 hashes. "
        "Only exact primary grid filenames are included; no replacement by extra repeats.", "",
        "Excluded CS8 files: " + ", ".join(f"`{name}`" for name in excluded) + ".", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("passband_dir", type=Path, help="Directory containing pass1/2_{minus,plus}Nk.cs8")
    parser.add_argument("--output-dir", type=Path, default=Path("notes/PASSBAND-V1"))
    args = parser.parse_args()
    try:
        files, excluded = discover_grid(args.passband_dir)
        rows = [measure(path, *key) for key, path in sorted(files.items())]
        reference, groups, edges = summarize_grid(rows)
        summary = markdown_summary(rows, reference, groups, edges, excluded)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / "passband_retune_v1.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        (args.output_dir / "passband_retune_v1.md").write_text(summary, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"Wrote 36 measurements and summary to {args.output_dir}")


if __name__ == "__main__":
    main()
