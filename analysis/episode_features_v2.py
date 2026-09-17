#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import numpy as np


FS = 25_000.0
DTYPE = np.complex128
FORMAT = "HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V2_DEVELOPMENT"

# Fixed deterministic spectral-analysis parameters.
NFFT = 16384
PEAK_COUNT = 5
MIN_PEAK_SEPARATION_BINS = 3
OCCUPIED_FRACTION = 0.90


def median_abs_deviation(values):
    x = np.asarray(values, dtype=float)
    med = np.median(x)
    return float(np.median(np.abs(x - med)))


def iqr(values):
    x = np.asarray(values, dtype=float)
    q25, q75 = np.percentile(x, [25.0, 75.0])
    return float(q75 - q25)


def load_iq(entry):
    path = Path(entry["path"])

    if not path.is_file():
        raise RuntimeError(f"IQ file missing: {path}")

    size = path.stat().st_size

    if size != entry["size_bytes"]:
        raise RuntimeError(
            f"size mismatch: {path.name}: "
            f"expected {entry['size_bytes']}, got {size}"
        )

    itemsize = np.dtype(DTYPE).itemsize

    if size % itemsize != 0:
        raise RuntimeError(
            f"invalid complex128 file size: {path.name}"
        )

    iq = np.fromfile(path, dtype=DTYPE)

    if iq.size < 2:
        raise RuntimeError(f"IQ fragment too short: {path}")

    return path, iq


def local_peaks(power):
    if power.size < 3:
        return np.array([], dtype=int)

    idx = np.where(
        (power[1:-1] > power[:-2]) &
        (power[1:-1] >= power[2:])
    )[0] + 1

    return idx


def select_peaks(power, count, min_separation_bins):
    candidates = local_peaks(power)

    if candidates.size == 0:
        return []

    ordered = sorted(
        candidates.tolist(),
        key=lambda i: (-float(power[i]), int(i)),
    )

    selected = []

    for idx in ordered:
        if all(
            abs(idx - existing) >= min_separation_bins
            for existing in selected
        ):
            selected.append(idx)

        if len(selected) >= count:
            break

    return selected


def occupied_width(freq, probability, fraction):
    order = np.argsort(freq)
    f = freq[order]
    p = probability[order]

    cumulative = np.cumsum(p)
    lower_mass = (1.0 - fraction) / 2.0
    upper_mass = 1.0 - lower_mass

    lo = int(np.searchsorted(cumulative, lower_mass, side="left"))
    hi = int(np.searchsorted(cumulative, upper_mass, side="left"))

    lo = min(lo, len(f) - 1)
    hi = min(hi, len(f) - 1)

    return float(f[hi] - f[lo])


def analyse_spectrum(iq):
    # Same basic preparation principle as V1:
    # remove complex mean and apply Hann window.
    x = iq - np.mean(iq)
    window = np.hanning(iq.size)

    spectrum = np.fft.fftshift(
        np.fft.fft(x * window, n=NFFT)
    )
    power = np.abs(spectrum) ** 2
    freq = np.fft.fftshift(
        np.fft.fftfreq(NFFT, d=1.0 / FS)
    )

    # Exclude the exact DC bin from peak selection.
    dc = int(np.argmin(np.abs(freq)))
    peak_power = power.copy()
    peak_power[dc] = -np.inf

    finite_power = np.maximum(power, 0.0)
    total_power = float(np.sum(finite_power))

    if not np.isfinite(total_power) or total_power <= 0.0:
        raise RuntimeError("invalid spectral power")

    probability = finite_power / total_power

    centroid = float(np.sum(freq * probability))
    spread = float(
        np.sqrt(
            np.sum(
                ((freq - centroid) ** 2) * probability
            )
        )
    )

    positive_probability = probability[probability > 0.0]
    entropy = float(
        -np.sum(
            positive_probability *
            np.log2(positive_probability)
        ) / np.log2(probability.size)
    )

    width90 = occupied_width(
        freq,
        probability,
        OCCUPIED_FRACTION,
    )

    selected = select_peaks(
        peak_power,
        PEAK_COUNT,
        MIN_PEAK_SEPARATION_BINS,
    )

    peaks = [
        {
            "frequency_hz": float(freq[idx]),
            "normalized_power":
                float(finite_power[idx] / total_power),
        }
        for idx in selected
    ]

    strongest_frequency = (
        peaks[0]["frequency_hz"] if peaks else None
    )
    strongest_norm_power = (
        peaks[0]["normalized_power"] if peaks else None
    )

    relative_offsets = []
    adjacent_spacings = []

    if strongest_frequency is not None:
        relative_offsets = sorted(
            float(p["frequency_hz"] - strongest_frequency)
            for p in peaks
            if p["frequency_hz"] != strongest_frequency
        )

        ordered_freqs = sorted(
            float(p["frequency_hz"])
            for p in peaks
        )

        adjacent_spacings = [
            float(b - a)
            for a, b in zip(
                ordered_freqs[:-1],
                ordered_freqs[1:],
            )
        ]

    return {
        "nfft": NFFT,
        "spectral_centroid_hz": centroid,
        "spectral_spread_hz": spread,
        "normalized_spectral_entropy": entropy,
        "occupied_width_90_hz": width90,
        "selected_peak_count": len(peaks),
        "strongest_peak_frequency_hz":
            strongest_frequency,
        "strongest_peak_normalized_power":
            strongest_norm_power,
        "relative_peak_offsets_hz":
            relative_offsets,
        "adjacent_peak_spacings_hz":
            adjacent_spacings,
        "peaks": peaks,
    }


def analyse_fragment(entry):
    path, iq = load_iq(entry)
    spectral = analyse_spectrum(iq)

    result = {
        "path": str(path),
        "size_bytes": int(path.stat().st_size),
        "samples": int(iq.size),
        "duration_seconds": float(iq.size / FS),
    }

    result.update(spectral)
    return result


def summarise(values):
    x = np.asarray(values, dtype=float)

    return {
        "median": float(np.median(x)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "range": float(np.max(x) - np.min(x)),
        "mad": median_abs_deviation(x),
        "iqr": iqr(x),
    }


def analyse_episode(ep):
    fragments = [
        analyse_fragment(entry)
        for entry in ep["files"]
    ]

    durations = [
        f["duration_seconds"]
        for f in fragments
    ]

    centroids = [
        f["spectral_centroid_hz"]
        for f in fragments
    ]

    spreads = [
        f["spectral_spread_hz"]
        for f in fragments
    ]

    entropies = [
        f["normalized_spectral_entropy"]
        for f in fragments
    ]

    widths = [
        f["occupied_width_90_hz"]
        for f in fragments
    ]

    prominence = [
        f["strongest_peak_normalized_power"]
        for f in fragments
        if f["strongest_peak_normalized_power"] is not None
    ]

    # Relative spectral geometry summaries use only relationships
    # internal to each fragment.
    first_relative_offsets = []
    median_adjacent_spacings = []

    for fragment in fragments:
        offsets = fragment["relative_peak_offsets_hz"]
        spacings = fragment["adjacent_peak_spacings_hz"]

        if offsets:
            nearest = min(offsets, key=lambda x: abs(x))
            first_relative_offsets.append(abs(float(nearest)))

        if spacings:
            median_adjacent_spacings.append(
                float(np.median(spacings))
            )

    mtimes = [
        int(entry["mtime_ns"])
        for entry in ep["files"]
    ]

    inter_fragment_gaps = [
        float((b - a) / 1e9)
        for a, b in zip(mtimes[:-1], mtimes[1:])
    ]

    result = {
        "episode": int(ep["episode"]),
        "fragment_count": len(fragments),
        "filesystem_span_seconds":
            float(ep["span_seconds"]),
        "preceding_gap_seconds":
            ep["preceding_gap_seconds"],
        "total_samples":
            int(sum(f["samples"] for f in fragments)),
        "total_iq_duration_seconds":
            float(sum(durations)),
        "fragment_duration_seconds":
            summarise(durations),
        "spectral_centroid_hz":
            summarise(centroids),
        "spectral_spread_hz":
            summarise(spreads),
        "normalized_spectral_entropy":
            summarise(entropies),
        "occupied_width_90_hz":
            summarise(widths),
        "strongest_peak_normalized_power":
            summarise(prominence) if prominence else None,
        "nearest_relative_peak_offset_abs_hz":
            (
                summarise(first_relative_offsets)
                if first_relative_offsets
                else None
            ),
        "median_adjacent_peak_spacing_hz":
            (
                summarise(median_adjacent_spacings)
                if median_adjacent_spacings
                else None
            ),
        "inter_fragment_gap_seconds":
            (
                summarise(inter_fragment_gaps)
                if inter_fragment_gaps
                else None
            ),
        "fragments": fragments,
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Kraken Episode Features V2 development extractor"
    )
    parser.add_argument(
        "capture_dir",
        help="capture directory containing frozen episodes.json",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write episode-features-v2.json",
    )
    args = parser.parse_args()

    capture = Path(args.capture_dir)
    episodes_path = capture / "episodes.json"

    data = json.loads(episodes_path.read_text())

    if data.get("format") != "HARDSIGNAL_KRAKEN_EPISODES_V1":
        raise RuntimeError(
            f"unexpected episode format: {data.get('format')}"
        )

    results = [
        analyse_episode(ep)
        for ep in data["episodes"]
    ]

    output = {
        "format": FORMAT,
        "capture_id": data["capture_id"],
        "sample_rate_hz": FS,
        "iq_dtype": "complex128",
        "nfft": NFFT,
        "peak_count": PEAK_COUNT,
        "minimum_peak_separation_bins":
            MIN_PEAK_SEPARATION_BINS,
        "occupied_fraction": OCCUPIED_FRACTION,
        "episode_count": len(results),
        "episodes": results,
    }

    print("KRAKEN EPISODE FEATURES V2 — DEVELOPMENT")
    print("========================================")
    print(f"Capture:  {data['capture_id']}")
    print(f"Episodes: {len(results)}")
    print()

    print(
        "EP  FILES   IQ_s    "
        "CENTROID_MED  SPREAD_MED  ENTROPY_MED  "
        "WIDTH90_MED  RELPEAK_MED"
    )

    for r in results:
        rel = r["nearest_relative_peak_offset_abs_hz"]
        rel_text = (
            f"{rel['median']:11.3f}"
            if rel is not None
            else "       NONE"
        )

        print(
            f"E{r['episode']:02d} "
            f"{r['fragment_count']:6d} "
            f"{r['total_iq_duration_seconds']:7.3f} "
            f"{r['spectral_centroid_hz']['median']:13.3f} "
            f"{r['spectral_spread_hz']['median']:11.3f} "
            f"{r['normalized_spectral_entropy']['median']:12.6f} "
            f"{r['occupied_width_90_hz']['median']:11.3f} "
            f"{rel_text}"
        )

    if args.write:
        output_path = capture / "episode-features-v2.json"
        output_path.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n"
        )
        print()
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
