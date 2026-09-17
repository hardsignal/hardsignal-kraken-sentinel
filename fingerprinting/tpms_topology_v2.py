#!/usr/bin/env python3
"""
Hardsignal Labs — TPMS Spectral Topology V2

Derives relative spectral-topology measurements from frozen V1 JSON
results. It does not reprocess IQ and does not modify the V1 extractor.

Pre-registered hypothesis:
    docs/tpms-topology-v2-hypothesis.md

Development data:
    Sensor 1 A/B
    Sensor 2 A/B/C

Sensor 3/4 are reserved for later validation.

This script is descriptive. It does not claim device identity.
"""

import argparse
import hashlib
import json
import statistics
from itertools import combinations
from pathlib import Path


FORMAT = "HARDSIGNAL_TPMS_TOPOLOGY_V2"

EXPECTED_V1_FORMAT = "HARDSIGNAL_TPMS_IQ_FEATURES_V1"

SHORT_MIN_MS = 4.50
SHORT_MAX_MS = 5.40
EXPECTED_PEAKS = 8


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def median_or_none(values):
    return statistics.median(values) if values else None


def topology_from_event(event):
    peaks = event.get("spectral_peaks", [])

    if len(peaks) < 2:
        return None

    peaks = sorted(peaks, key=lambda p: p["rank"])

    reference = peaks[0]
    f_ref = float(reference["frequency_hz"])

    components = []
    for peak in peaks:
        f = float(peak["frequency_hz"])
        components.append({
            "rank": int(peak["rank"]),
            "frequency_hz_diagnostic": f,
            "relative_db": float(peak["relative_db"]),
            "offset_from_dominant_hz": f - f_ref,
        })

    pairwise = []
    for a, b in combinations(peaks, 2):
        fa = float(a["frequency_hz"])
        fb = float(b["frequency_hz"])

        pairwise.append({
            "rank_a": int(a["rank"]),
            "rank_b": int(b["rank"]),
            "signed_difference_hz": fb - fa,
            "absolute_difference_hz": abs(fb - fa),
        })

    return {
        "event": event.get("event"),
        "duration_ms": float(event["duration_ms"]),
        "dominant_frequency_hz_diagnostic": f_ref,
        "component_count": len(peaks),
        "components": components,
        "pairwise_differences": pairwise,
    }


def process_v1(path):
    data = json.loads(path.read_text())

    if data.get("format") != EXPECTED_V1_FORMAT:
        raise ValueError(
            f"{path}: unexpected format {data.get('format')!r}; "
            f"expected {EXPECTED_V1_FORMAT!r}"
        )

    output_files = []
    all_events = []

    for file_record in data.get("files", []):
        events = []

        for event in file_record.get("events", []):
            duration = event.get("duration_ms")

            if duration is None:
                continue

            if not event.get("short_event_candidate", False):
                continue

            if not (SHORT_MIN_MS <= float(duration) <= SHORT_MAX_MS):
                continue

            topology = topology_from_event(event)
            if topology is None:
                continue

            events.append(topology)
            all_events.append(topology)

        output_files.append({
            "file": file_record.get("file"),
            "events": events,
        })

    durations = [e["duration_ms"] for e in all_events]
    component_counts = [e["component_count"] for e in all_events]

    return {
        "source": str(path),
        "source_sha256": sha256_file(path),
        "short_event_count": len(all_events),
        "duration_ms": {
            "median": median_or_none(durations),
            "min": min(durations) if durations else None,
            "max": max(durations) if durations else None,
        },
        "component_count": {
            "median": median_or_none(component_counts),
            "min": min(component_counts) if component_counts else None,
            "max": max(component_counts) if component_counts else None,
        },
        "files": output_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Derive TPMS relative spectral topology from frozen V1 JSON."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Frozen HARDSIGNAL_TPMS_IQ_FEATURES_V1 JSON files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output V2 JSON",
    )

    args = parser.parse_args()

    captures = [process_v1(path) for path in args.inputs]

    result = {
        "format": FORMAT,
        "method": {
            "input": "frozen V1 structured results",
            "short_event_min_ms": SHORT_MIN_MS,
            "short_event_max_ms": SHORT_MAX_MS,
            "expected_peak_count": EXPECTED_PEAKS,
            "reference_component": "rank_1_dominant",
            "features": [
                "signed_offsets_from_dominant",
                "relative_peak_amplitudes",
                "all_pairwise_frequency_differences",
            ],
            "excluded_identity_features": [
                "absolute_carrier_offset",
                "received_power",
                "doa",
                "absolute_physical_position",
            ],
        },
        "captures": captures,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")

    print(f"Wrote: {args.output}")
    print(f"Captures: {len(captures)}")
    print(
        "Short events:",
        sum(c["short_event_count"] for c in captures)
    )


if __name__ == "__main__":
    main()
