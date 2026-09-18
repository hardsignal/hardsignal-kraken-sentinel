#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


FS = 25_000.0
DTYPE = np.complex128

FORMAT = "HARDSIGNAL_KRAKEN_WAVEFORM_STRUCTURE_V1_DEVELOPMENT"

STFT_WINDOW = 512
STFT_HOP = 256
STFT_NFFT = 2048

IF_BLOCK = 512
IF_HOP = 256

ENVELOPE_BLOCK = 512
ENVELOPE_HOP = 256

ACTIVE_THRESHOLD = 1.50


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def summary(values):
    a = np.asarray(values, dtype=float)

    if a.size == 0:
        return None

    q25, q75 = np.percentile(a, [25, 75])
    med = float(np.median(a))
    mad = float(np.median(np.abs(a - med)))

    return {
        "count": int(a.size),
        "median": med,
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "range": float(np.max(a) - np.min(a)),
        "mad": mad,
        "q25": float(q25),
        "q75": float(q75),
        "iqr": float(q75 - q25),
    }


def load_iq(entry):
    path = Path(entry["path"])

    if not path.exists():
        raise RuntimeError(f"missing IQ file: {path}")

    stat_size = path.stat().st_size
    expected_size = int(entry["size_bytes"])

    if stat_size != expected_size:
        raise RuntimeError(
            f"size mismatch: {path}: "
            f"expected {expected_size}, got {stat_size}"
        )

    expected_sha = entry.get("sha256")
    if not expected_sha:
        raise RuntimeError(f"missing SHA-256 in episodes record: {path}")

    actual_sha = sha256_file(path)

    if actual_sha != expected_sha:
        raise RuntimeError(
            f"SHA-256 mismatch: {path}: "
            f"expected {expected_sha}, got {actual_sha}"
        )

    if stat_size % np.dtype(DTYPE).itemsize != 0:
        raise RuntimeError(f"unaligned complex128 file: {path}")

    iq = np.fromfile(path, dtype=DTYPE)

    if iq.size < STFT_WINDOW:
        raise RuntimeError(
            f"fragment shorter than analysis window: {path}: {iq.size}"
        )

    return path, iq


def frame_starts(n, window, hop):
    if n < window:
        return []

    return list(range(0, n - window + 1, hop))


def instantaneous_frequency(iq):
    phase_step = np.angle(iq[1:] * np.conj(iq[:-1]))
    return phase_step * FS / (2.0 * np.pi)


def analyse_if(iq):
    inst = instantaneous_frequency(iq)

    starts = frame_starts(len(inst), IF_BLOCK, IF_HOP)
    block_medians = []
    block_mads = []

    for start in starts:
        x = inst[start:start + IF_BLOCK]

        med = float(np.median(x))
        mad = float(np.median(np.abs(x - med)))

        block_medians.append(med)
        block_mads.append(mad)

    changes = np.diff(block_medians) if len(block_medians) >= 2 else []

    return {
        "sample_summary_hz": summary(inst),
        "block_count": len(block_medians),
        "block_median_frequency_hz": summary(block_medians),
        "block_mad_frequency_hz": summary(block_mads),
        "block_to_block_change_hz": summary(changes),
    }


def analyse_stft(iq):
    starts = frame_starts(len(iq), STFT_WINDOW, STFT_HOP)

    window = np.hanning(STFT_WINDOW)
    freqs = np.fft.fftshift(
        np.fft.fftfreq(STFT_NFFT, d=1.0 / FS)
    )

    dominant = []

    for start in starts:
        x = iq[start:start + STFT_WINDOW]
        x = x - np.mean(x)
        spec = np.fft.fftshift(
            np.fft.fft(x * window, n=STFT_NFFT)
        )
        power = np.abs(spec) ** 2

        dc = int(np.argmin(np.abs(freqs)))
        power[dc] = -np.inf

        idx = int(np.argmax(power))
        dominant.append(float(freqs[idx]))

    steps = np.diff(dominant) if len(dominant) >= 2 else []

    rounded_states = [
        round(v / (FS / STFT_NFFT)) * (FS / STFT_NFFT)
        for v in dominant
    ]

    unique_states = sorted(set(rounded_states))

    state_spacings = (
        np.diff(unique_states)
        if len(unique_states) >= 2
        else []
    )

    return {
        "window_count": len(dominant),
        "dominant_frequency_hz": summary(dominant),
        "dominant_step_hz": summary(steps),
        "occupied_frequency_bin_count": len(unique_states),
        "occupied_frequency_bin_spacing_hz": summary(state_spacings),
    }


def analyse_envelope(iq):
    mag = np.abs(iq)

    med = float(np.median(mag))

    if not math.isfinite(med) or med <= 0.0:
        raise RuntimeError("invalid median magnitude")

    norm = mag / med

    starts = frame_starts(len(norm), ENVELOPE_BLOCK, ENVELOPE_HOP)

    block_medians = []
    active_fraction = []

    for start in starts:
        x = norm[start:start + ENVELOPE_BLOCK]

        block_medians.append(float(np.median(x)))
        active_fraction.append(
            float(np.mean(x >= ACTIVE_THRESHOLD))
        )

    transitions = 0
    if len(active_fraction) >= 2:
        states = [
            1 if x >= 0.5 else 0
            for x in active_fraction
        ]
        transitions = sum(
            a != b for a, b in zip(states, states[1:])
        )

    mean = float(np.mean(norm))
    std = float(np.std(norm))

    cv = std / mean if mean > 0.0 else float("nan")

    return {
        "normalization": "fragment_median_magnitude",
        "active_threshold_normalized": ACTIVE_THRESHOLD,
        "sample_summary_normalized": summary(norm),
        "coefficient_of_variation": cv,
        "block_count": len(block_medians),
        "block_median_normalized": summary(block_medians),
        "block_active_fraction": summary(active_fraction),
        "active_state_transition_count": int(transitions),
    }


def analyse_fragment(entry):
    path, iq = load_iq(entry)

    return {
        "path": str(path),
        "size_bytes": int(entry["size_bytes"]),
        "sha256": entry["sha256"],
        "samples": int(iq.size),
        "duration_seconds": float(iq.size / FS),
        "instantaneous_frequency": analyse_if(iq),
        "time_frequency": analyse_stft(iq),
        "envelope": analyse_envelope(iq),
    }


def collect_fragment_metric(fragments, getter):
    vals = []

    for frag in fragments:
        value = getter(frag)

        if value is not None and math.isfinite(float(value)):
            vals.append(float(value))

    return summary(vals)


def analyse_episode(ep):
    fragments = [
        analyse_fragment(entry)
        for entry in ep["files"]
    ]

    return {
        "episode": int(ep["episode"]),
        "fragment_count": len(fragments),

        # Recorder structure/context only.
        "filesystem_span_seconds": float(ep["span_seconds"]),
        "preceding_gap_seconds": ep["preceding_gap_seconds"],
        "total_iq_samples": int(
            sum(f["samples"] for f in fragments)
        ),
        "total_iq_duration_seconds": float(
            sum(f["duration_seconds"] for f in fragments)
        ),

        "if_block_median_frequency_hz": collect_fragment_metric(
            fragments,
            lambda f:
                f["instantaneous_frequency"]
                 ["block_median_frequency_hz"]["median"]
            if f["instantaneous_frequency"]
                ["block_median_frequency_hz"] is not None
            else None
        ),

        "if_block_mad_frequency_hz": collect_fragment_metric(
            fragments,
            lambda f:
                f["instantaneous_frequency"]
                 ["block_mad_frequency_hz"]["median"]
            if f["instantaneous_frequency"]
                ["block_mad_frequency_hz"] is not None
            else None
        ),

        "stft_dominant_frequency_hz": collect_fragment_metric(
            fragments,
            lambda f:
                f["time_frequency"]
                 ["dominant_frequency_hz"]["median"]
            if f["time_frequency"]
                ["dominant_frequency_hz"] is not None
            else None
        ),

        "stft_dominant_step_hz": collect_fragment_metric(
            fragments,
            lambda f:
                f["time_frequency"]
                 ["dominant_step_hz"]["median"]
            if f["time_frequency"]
                ["dominant_step_hz"] is not None
            else None
        ),

        "stft_occupied_frequency_bin_count":
            collect_fragment_metric(
                fragments,
                lambda f:
                    f["time_frequency"]
                     ["occupied_frequency_bin_count"]
            ),

        "envelope_coefficient_of_variation":
            collect_fragment_metric(
                fragments,
                lambda f:
                    f["envelope"]
                     ["coefficient_of_variation"]
            ),

        "envelope_block_active_fraction":
            collect_fragment_metric(
                fragments,
                lambda f:
                    f["envelope"]
                     ["block_active_fraction"]["median"]
                if f["envelope"]
                    ["block_active_fraction"] is not None
                else None
            ),

        "envelope_active_state_transition_count":
            collect_fragment_metric(
                fragments,
                lambda f:
                    f["envelope"]
                     ["active_state_transition_count"]
            ),

        "fragments": fragments,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    capture_dir = Path(args.capture_dir)
    episodes_path = capture_dir / "episodes.json"

    if not episodes_path.exists():
        raise SystemExit(f"missing {episodes_path}")

    data = json.loads(episodes_path.read_text())

    if data.get("format") != "HARDSIGNAL_KRAKEN_EPISODES_V1":
        raise SystemExit(
            "unsupported episode format: "
            f"{data.get('format')}"
        )

    episodes = [
        analyse_episode(ep)
        for ep in data["episodes"]
    ]

    out = {
        "format": FORMAT,
        "capture_id": data["capture_id"],
        "sample_rate_hz": FS,
        "iq_dtype": "complex128",

        "parameters": {
            "stft_window_samples": STFT_WINDOW,
            "stft_hop_samples": STFT_HOP,
            "stft_nfft": STFT_NFFT,
            "stft_window_function": "hann",
            "instantaneous_frequency_method":
                "angle(x[n] * conj(x[n-1]))",
            "if_block_samples": IF_BLOCK,
            "if_hop_samples": IF_HOP,
            "envelope_normalization":
                "fragment_median_magnitude",
            "envelope_block_samples": ENVELOPE_BLOCK,
            "envelope_hop_samples": ENVELOPE_HOP,
            "active_threshold_normalized": ACTIVE_THRESHOLD,
            "fragments_concatenated": False,
            "iq_sha256_verified": True,
        },

        "episode_count": len(episodes),
        "episodes": episodes,
    }

    print("KRAKEN WAVEFORM STRUCTURE V1 — DEVELOPMENT")
    print("==========================================")
    print(f"Capture:  {data['capture_id']}")
    print(f"Episodes: {len(episodes)}")
    print()

    print(
        "EP  FILES   IF_MED_HZ   IF_MAD_HZ  "
        "STFT_MED_HZ  STFT_STEP  BINS  ENV_CV  ACTIVE  TRANS"
    )

    for ep in episodes:
        def med(name):
            x = ep[name]
            return float("nan") if x is None else x["median"]

        print(
            f"E{ep['episode']:02d} "
            f"{ep['fragment_count']:6d} "
            f"{med('if_block_median_frequency_hz'):11.3f} "
            f"{med('if_block_mad_frequency_hz'):11.3f} "
            f"{med('stft_dominant_frequency_hz'):12.3f} "
            f"{med('stft_dominant_step_hz'):10.3f} "
            f"{med('stft_occupied_frequency_bin_count'):5.1f} "
            f"{med('envelope_coefficient_of_variation'):7.4f} "
            f"{med('envelope_block_active_fraction'):7.4f} "
            f"{med('envelope_active_state_transition_count'):5.1f}"
        )

    if args.write:
        output = capture_dir / "waveform-structure-v1.json"

        output.write_text(
            json.dumps(
                out,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            ) + "\n"
        )

        print()
        print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
