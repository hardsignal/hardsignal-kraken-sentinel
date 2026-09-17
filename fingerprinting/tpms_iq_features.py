#!/usr/bin/env python3

"""
Hardsignal Labs — TPMS IQ Feature Extractor
Stage 33: controlled RF fingerprint construction from recorded IQ.

Input:
    KrakenSDR channelized VFO IQ
    headerless NumPy complex128
    Fs = 25,000 complex samples/s

Frozen development parameters:
    envelope threshold       = 0.05
    event join gap           = 25 samples
    minimum event length     = 5 samples
    spectral padding         = 25 samples
    FFT size                 = 16384
    DC/centre exclusion      = +/-100 Hz
    spectral peak separation = 300 Hz
    short-event window       = 4.50 .. 5.40 ms

Identity-candidate features:
    short-event duration
    relative spectral spacing / spectral topology

Explicitly excluded from identity scoring:
    absolute carrier offset
    received power
    DoA

The extractor reports measurements. It does not claim transmitter identity.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import numpy as np


FS = 25_000
DTYPE = np.complex128

THRESHOLD = 0.05
JOIN_GAP = 25
MIN_SAMPLES = 5

PAD = 25
NFFT = 16_384
CENTER_IGNORE_HZ = 100
PEAK_SEPARATION_HZ = 300

SHORT_MIN_MS = 4.50
SHORT_MAX_MS = 5.40

TOP_PEAKS = 8


def detect_events(iq: np.ndarray):
    idx = np.flatnonzero(np.abs(iq) > THRESHOLD)

    if idx.size == 0:
        return []

    regions = []
    start = prev = int(idx[0])

    for value in idx[1:]:
        value = int(value)

        if value - prev <= JOIN_GAP + 1:
            prev = value
        else:
            if prev - start + 1 >= MIN_SAMPLES:
                regions.append((start, prev))
            start = prev = value

    if prev - start + 1 >= MIN_SAMPLES:
        regions.append((start, prev))

    return regions


def spectral_peaks(iq: np.ndarray, start: int, end: int):
    lo = max(0, start - PAD)
    hi = min(len(iq), end + PAD + 1)

    x = iq[lo:hi].copy()

    if len(x) < 2:
        return []

    x -= np.mean(x)
    x *= np.hanning(len(x))

    spectrum = np.abs(
        np.fft.fftshift(
            np.fft.fft(x, n=NFFT)
        )
    )

    frequencies = np.fft.fftshift(
        np.fft.fftfreq(NFFT, d=1 / FS)
    )

    spectrum[np.abs(frequencies) <= CENTER_IGNORE_HZ] = 0

    work = spectrum.copy()
    peaks = []

    for rank in range(1, TOP_PEAKS + 1):
        index = int(np.argmax(work))
        amplitude = float(work[index])

        if amplitude <= 0:
            break

        frequency = float(frequencies[index])

        if not peaks:
            reference_amplitude = amplitude

        relative_db = float(
            20 * np.log10(amplitude / reference_amplitude)
        )

        peaks.append(
            {
                "rank": rank,
                "frequency_hz": frequency,
                "relative_db": relative_db,
            }
        )

        work[
            np.abs(frequencies - frequency)
            <= PEAK_SEPARATION_HZ
        ] = 0

    return peaks


def analyse_file(filename: str):
    iq = np.fromfile(filename, dtype=DTYPE)

    if iq.size == 0:
        return {
            "file": os.path.basename(filename),
            "samples": 0,
            "recorder_span_ms": 0.0,
            "events": [],
        }

    if not (
        np.isfinite(iq.real).all()
        and np.isfinite(iq.imag).all()
    ):
        raise ValueError(
            f"Non-finite complex128 samples in {filename}"
        )

    output_events = []

    for number, (start, end) in enumerate(
        detect_events(iq), 1
    ):
        samples = end - start + 1
        duration_ms = samples / FS * 1000.0

        peaks = spectral_peaks(iq, start, end)

        spacing_p1_p2 = None

        if len(peaks) >= 2:
            spacing_p1_p2 = abs(
                peaks[1]["frequency_hz"]
                - peaks[0]["frequency_hz"]
            )

        output_events.append(
            {
                "event": number,
                "start_ms": start / FS * 1000.0,
                "end_ms": (end + 1) / FS * 1000.0,
                "duration_ms": duration_ms,
                "short_event_candidate": (
                    SHORT_MIN_MS
                    <= duration_ms
                    <= SHORT_MAX_MS
                ),
                "p1_p2_spacing_hz": spacing_p1_p2,
                "spectral_peaks": peaks,
            }
        )

    return {
        "file": os.path.basename(filename),
        "samples": int(iq.size),
        "recorder_span_ms": iq.size / FS * 1000.0,
        "events": output_events,
    }


def robust_summary(results):
    durations = []
    spacings = []

    for result in results:
        for event in result["events"]:
            if not event["short_event_candidate"]:
                continue

            durations.append(event["duration_ms"])

            spacing = event["p1_p2_spacing_hz"]
            if spacing is not None:
                spacings.append(spacing)

    summary = {
        "short_event_count": len(durations),
    }

    if durations:
        d = np.asarray(durations)

        summary["duration_ms"] = {
            "median": float(np.median(d)),
            "mean": float(np.mean(d)),
            "min": float(np.min(d)),
            "max": float(np.max(d)),
        }

    if spacings:
        s = np.asarray(spacings)
        median = float(np.median(s))

        summary["p1_p2_spacing_hz"] = {
            "median": median,
            "mean": float(np.mean(s)),
            "std": float(np.std(s)),
            "min": float(np.min(s)),
            "max": float(np.max(s)),
            "mad": float(
                np.median(np.abs(s - median))
            ),
        }

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Extract controlled TPMS IQ features."
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        help="IQ files or shell-style glob patterns",
    )

    parser.add_argument(
        "--json",
        dest="json_output",
        help="Write complete measurements to JSON",
    )

    args = parser.parse_args()

    files = []

    for item in args.inputs:
        matches = glob.glob(os.path.expanduser(item))

        if matches:
            files.extend(matches)
        elif Path(os.path.expanduser(item)).is_file():
            files.append(os.path.expanduser(item))

    files = sorted(set(files))

    if not files:
        raise SystemExit("No IQ files matched.")

    results = [analyse_file(filename) for filename in files]
    summary = robust_summary(results)

    print("HARDSIGNAL LABS — TPMS IQ FEATURE EXTRACTOR")
    print("=" * 60)
    print(f"Files                 : {len(files)}")
    print(f"Sample rate           : {FS} complex samples/s")
    print(f"Input dtype           : complex128")
    print(f"Envelope threshold    : {THRESHOLD}")
    print(
        f"Short-event window    : "
        f"{SHORT_MIN_MS:.2f} .. {SHORT_MAX_MS:.2f} ms"
    )

    print()
    print("SHORT-EVENT SUMMARY")
    print("-" * 60)
    print(
        f"Candidate events      : "
        f"{summary['short_event_count']}"
    )

    if "duration_ms" in summary:
        d = summary["duration_ms"]
        print(f"Duration median       : {d['median']:.3f} ms")
        print(
            f"Duration range        : "
            f"{d['min']:.3f} .. {d['max']:.3f} ms"
        )

    if "p1_p2_spacing_hz" in summary:
        s = summary["p1_p2_spacing_hz"]

        print(f"P1/P2 spacing median  : {s['median']:.1f} Hz")
        print(f"P1/P2 spacing mean    : {s['mean']:.1f} Hz")
        print(f"P1/P2 spacing std     : {s['std']:.1f} Hz")
        print(f"P1/P2 spacing MAD     : {s['mad']:.1f} Hz")
        print(
            f"P1/P2 spacing range   : "
            f"{s['min']:.1f} .. {s['max']:.1f} Hz"
        )

    print()
    print(
        "NOTE: P1/P2 spacing is reported as an observed "
        "candidate measurement."
    )
    print(
        "Alternate secondary spectral components are retained "
        "in the detailed output."
    )

    if args.json_output:
        payload = {
            "format": "HARDSIGNAL_TPMS_IQ_FEATURES_V1",
            "acquisition": {
                "sample_rate_complex_sps": FS,
                "dtype": "complex128",
            },
            "parameters": {
                "envelope_threshold": THRESHOLD,
                "join_gap_samples": JOIN_GAP,
                "minimum_event_samples": MIN_SAMPLES,
                "spectral_padding_samples": PAD,
                "fft_size": NFFT,
                "center_ignore_hz": CENTER_IGNORE_HZ,
                "peak_separation_hz": PEAK_SEPARATION_HZ,
                "short_event_min_ms": SHORT_MIN_MS,
                "short_event_max_ms": SHORT_MAX_MS,
            },
            "excluded_identity_features": [
                "absolute_carrier_offset_hz",
                "received_power",
                "doa",
            ],
            "summary": summary,
            "files": results,
        }

        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        print()
        print(f"JSON written          : {output}")


if __name__ == "__main__":
    main()
