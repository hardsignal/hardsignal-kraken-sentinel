#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import numpy as np

FS = 25_000.0
DTYPE = np.complex128
FORMAT = "HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V1"


def strongest_non_dc_offset(iq):
    if iq.size < 2:
        raise ValueError("fragment too short")

    x = iq - np.mean(iq)
    window = np.hanning(iq.size)

    spectrum = np.fft.fftshift(np.fft.fft(x * window))
    power = np.abs(spectrum) ** 2
    freq = np.fft.fftshift(
        np.fft.fftfreq(iq.size, d=1.0 / FS)
    )

    dc = int(np.argmin(np.abs(freq)))
    power[dc] = -np.inf

    return float(freq[int(np.argmax(power))])


def analyse_fragment(entry):
    path = Path(entry["path"])
    size = path.stat().st_size

    if size != entry["size_bytes"]:
        raise RuntimeError(
            f"size mismatch: {path.name}: "
            f"expected {entry['size_bytes']}, got {size}"
        )

    if size % np.dtype(DTYPE).itemsize != 0:
        raise RuntimeError(
            f"invalid complex128 file size: {path.name}"
        )

    iq = np.fromfile(path, dtype=DTYPE)

    if iq.size == 0:
        raise RuntimeError(f"empty IQ file: {path}")

    mag = np.abs(iq)

    result = {
        "path": str(path),
        "size_bytes": int(size),
        "samples": int(iq.size),
        "duration_seconds": float(iq.size / FS),
        "rms_magnitude": float(np.sqrt(np.mean(mag ** 2))),
        "mean_magnitude": float(np.mean(mag)),
        "median_magnitude": float(np.median(mag)),
        "peak_magnitude": float(np.max(mag)),
        "strongest_component_offset_hz":
            strongest_non_dc_offset(iq),
    }

    return result, mag


def analyse_episode(ep):
    fragments = []
    magnitude_blocks = []

    for entry in ep["files"]:
        result, mag = analyse_fragment(entry)
        fragments.append(result)
        magnitude_blocks.append(mag)

    total_samples = sum(f["samples"] for f in fragments)

    if total_samples == 0:
        raise RuntimeError("episode contains zero samples")

    durations = np.array(
        [f["duration_seconds"] for f in fragments],
        dtype=float,
    )

    offsets = np.array(
        [f["strongest_component_offset_hz"] for f in fragments],
        dtype=float,
    )

    sum_abs = sum(float(np.sum(x)) for x in magnitude_blocks)
    sum_abs2 = sum(float(np.sum(x ** 2)) for x in magnitude_blocks)
    peak = max(float(np.max(x)) for x in magnitude_blocks)

    # This array is used only for the sample-level magnitude median.
    # Fragment IQ is never treated as a continuous time-domain signal.
    magnitudes = np.concatenate(magnitude_blocks)

    return {
        "episode": int(ep["episode"]),
        "fragment_count": len(fragments),
        "filesystem_span_seconds": float(ep["span_seconds"]),
        "preceding_gap_seconds": ep["preceding_gap_seconds"],
        "total_samples": int(total_samples),
        "total_iq_duration_seconds":
            float(total_samples / FS),
        "min_fragment_duration_seconds":
            float(np.min(durations)),
        "max_fragment_duration_seconds":
            float(np.max(durations)),
        "median_fragment_duration_seconds":
            float(np.median(durations)),
        "rms_magnitude":
            float(np.sqrt(sum_abs2 / total_samples)),
        "mean_magnitude":
            float(sum_abs / total_samples),
        "median_magnitude":
            float(np.median(magnitudes)),
        "peak_magnitude":
            peak,
        "median_strongest_component_offset_hz":
            float(np.median(offsets)),
        "min_strongest_component_offset_hz":
            float(np.min(offsets)),
        "max_strongest_component_offset_hz":
            float(np.max(offsets)),
        "strongest_component_offset_spread_hz":
            float(np.max(offsets) - np.min(offsets)),
        "fragments": fragments,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Kraken Episode Features V1"
    )
    parser.add_argument(
        "capture_dir",
        help="capture directory containing episodes.json",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write episode-features-v1.json",
    )
    args = parser.parse_args()

    capture = Path(args.capture_dir)
    episodes_path = capture / "episodes.json"

    data = json.loads(episodes_path.read_text())

    if data.get("format") != "HARDSIGNAL_KRAKEN_EPISODES_V1":
        raise RuntimeError(
            f"unexpected format: {data.get('format')}"
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
        "episode_count": len(results),
        "episodes": results,
    }

    print("KRAKEN EPISODE FEATURES V1")
    print("==========================")
    print(f"Capture:  {data['capture_id']}")
    print(f"Episodes: {len(results)}")
    print()

    print(
        "EP  FILES   IQ_s      RMS       MEAN      "
        "MEDIAN    PEAK      SPEC_MED_Hz  SPREAD_Hz"
    )

    for r in results:
        print(
            f"E{r['episode']:02d} "
            f"{r['fragment_count']:6d} "
            f"{r['total_iq_duration_seconds']:7.3f} "
            f"{r['rms_magnitude']:9.6f} "
            f"{r['mean_magnitude']:9.6f} "
            f"{r['median_magnitude']:9.6f} "
            f"{r['peak_magnitude']:9.6f} "
            f"{r['median_strongest_component_offset_hz']:12.3f} "
            f"{r['strongest_component_offset_spread_hz']:10.3f}"
        )

    if args.write:
        output_path = capture / "episode-features-v1.json"
        output_path.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n"
        )
        print()
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
