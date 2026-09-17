#!/usr/bin/env python3

"""
Hardsignal Labs — TPMS Component Families V3

Rank-independent development analysis of TPMS spectral-spacing families.

Methodological rules were frozen before this implementation:
  family tolerance:             +/- 50 Hz
  within-sensor repeatability:  >= 60% in every capture
  opposite-sensor recurrence:   < 40% in every capture

Development sensors:
  S1: captures A, B
  S2: captures A, B, C

Sensor 3 / Sensor 4 are reserved unseen validation data.

This implementation consumes frozen V1 JSON results only. It does not
modify V1 segmentation, FFT processing, peak detection, or V2 results.

Absolute carrier offset, received power, DoA and absolute physical
position are excluded from identity scoring.
"""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path
from statistics import median


FORMAT = "HARDSIGNAL_TPMS_COMPONENT_FAMILIES_V3"

TOLERANCE_HZ = 50.0
WITHIN_SENSOR_MIN = 0.60
OPPOSITE_SENSOR_MAX = 0.40

EXPECTED_FORMAT = "HARDSIGNAL_TPMS_IQ_FEATURES_V1"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_capture(label, sensor, path):
    data = json.loads(path.read_text())

    if data.get("format") != EXPECTED_FORMAT:
        raise ValueError(
            f"{path}: expected {EXPECTED_FORMAT}, "
            f"got {data.get('format')!r}"
        )

    events = []

    for file_entry in data["files"]:
        source_file = file_entry.get("file")

        for event in file_entry["events"]:
            if not event.get("short_event_candidate"):
                continue

            peaks = event.get("spectral_peaks", [])

            if len(peaks) < 2:
                continue

            freqs = sorted(
                float(p["frequency_hz"])
                for p in peaks
            )

            spacings = sorted(
                abs(b - a)
                for a, b in combinations(freqs, 2)
            )

            events.append({
                "source_file": source_file,
                "event": event.get("event"),
                "duration_ms": float(event["duration_ms"]),
                "pairwise_spacings_hz": spacings,
            })

    if not events:
        raise ValueError(f"{path}: no candidate short events")

    return {
        "label": label,
        "sensor": sensor,
        "source": str(path),
        "source_sha256": sha256_file(path),
        "event_count": len(events),
        "events": events,
    }


def candidate_centres(captures):
    """
    Deterministic candidate centres.

    Every observed development spacing is a candidate centre.

    This deliberately avoids single-linkage clustering. Family
    membership is always evaluated directly against the fixed centre
    using +/- TOLERANCE_HZ.
    """
    values = set()

    for capture in captures:
        for event in capture["events"]:
            for spacing in event["pairwise_spacings_hz"]:
                values.add(float(spacing))

    return sorted(values)


def event_hits(event, centre):
    return any(
        abs(spacing - centre) <= TOLERANCE_HZ
        for spacing in event["pairwise_spacings_hz"]
    )


def recurrence(capture, centre):
    hits = sum(
        event_hits(event, centre)
        for event in capture["events"]
    )

    total = capture["event_count"]

    return {
        "hits": hits,
        "events": total,
        "fraction": hits / total,
        "percent": 100.0 * hits / total,
    }


def classify_family(captures, centre):
    by_capture = {
        capture["label"]: recurrence(capture, centre)
        for capture in captures
    }

    by_sensor = {}

    for sensor in sorted({c["sensor"] for c in captures}):
        sensor_caps = [
            c for c in captures
            if c["sensor"] == sensor
        ]

        repeatable = all(
            by_capture[c["label"]]["fraction"] >= WITHIN_SENSOR_MIN
            for c in sensor_caps
        )

        by_sensor[sensor] = {
            "repeatable_in_every_capture": repeatable,
            "captures": [c["label"] for c in sensor_caps],
        }

    s1_repeatable = by_sensor["S1"]["repeatable_in_every_capture"]
    s2_repeatable = by_sensor["S2"]["repeatable_in_every_capture"]

    s1_caps = [c for c in captures if c["sensor"] == "S1"]
    s2_caps = [c for c in captures if c["sensor"] == "S2"]

    s1_low_in_every_capture = all(
        by_capture[c["label"]]["fraction"] < OPPOSITE_SENSOR_MAX
        for c in s1_caps
    )

    s2_low_in_every_capture = all(
        by_capture[c["label"]]["fraction"] < OPPOSITE_SENSOR_MAX
        for c in s2_caps
    )

    if s1_repeatable and s2_repeatable:
        classification = "shared_signal_structure"
    elif s1_repeatable and s2_low_in_every_capture:
        classification = "candidate_s1_discriminating"
    elif s2_repeatable and s1_low_in_every_capture:
        classification = "candidate_s2_discriminating"
    else:
        classification = "insufficient_or_overlapping"

    return {
        "centre_hz": centre,
        "tolerance_hz": TOLERANCE_HZ,
        "capture_recurrence": by_capture,
        "sensor_repeatability": by_sensor,
        "classification": classification,
    }


def deduplicate_candidates(families):
    """
    Collapse overlapping candidate centres after classification.

    Candidate centres within 2*TOLERANCE_HZ of the previously retained
    centre can represent substantially overlapping membership windows.

    For each classification, retain the centre with the greatest total
    event support; ties use the lower centre.

    This is reporting consolidation only. Classification itself is
    calculated before consolidation against each fixed observed centre.
    """
    grouped = {}

    for family in families:
        grouped.setdefault(family["classification"], []).append(family)

    output = []

    for classification, group in grouped.items():
        remaining = sorted(group, key=lambda x: x["centre_hz"])

        while remaining:
            seed = remaining[0]

            neighbourhood = [
                f for f in remaining
                if abs(f["centre_hz"] - seed["centre_hz"])
                <= 2.0 * TOLERANCE_HZ
            ]

            def support(f):
                return sum(
                    r["hits"]
                    for r in f["capture_recurrence"].values()
                )

            chosen = sorted(
                neighbourhood,
                key=lambda f: (-support(f), f["centre_hz"])
            )[0]

            output.append(chosen)

            lo = chosen["centre_hz"] - 2.0 * TOLERANCE_HZ
            hi = chosen["centre_hz"] + 2.0 * TOLERANCE_HZ

            remaining = [
                f for f in remaining
                if not (lo <= f["centre_hz"] <= hi)
            ]

    return sorted(output, key=lambda x: x["centre_hz"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--capture",
        action="append",
        nargs=3,
        metavar=("LABEL", "SENSOR", "JSON"),
        required=True,
        help="Capture label, sensor label, frozen V1 JSON",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output V3 JSON",
    )
    args = parser.parse_args()

    captures = [
        load_capture(label, sensor, Path(path))
        for label, sensor, path in args.capture
    ]

    sensors = sorted({c["sensor"] for c in captures})

    if sensors != ["S1", "S2"]:
        raise ValueError(
            "V3 development implementation requires S1 and S2 only; "
            "reserved validation sensors must not be supplied"
        )

    centres = candidate_centres(captures)

    families = [
        classify_family(captures, centre)
        for centre in centres
    ]

    consolidated = deduplicate_candidates(families)

    counts = {}

    for classification in (
        "shared_signal_structure",
        "candidate_s1_discriminating",
        "candidate_s2_discriminating",
        "insufficient_or_overlapping",
    ):
        counts[classification] = sum(
            f["classification"] == classification
            for f in consolidated
        )

    result = {
        "format": FORMAT,
        "method": {
            "rank_independent": True,
            "family_tolerance_hz": TOLERANCE_HZ,
            "within_sensor_min_fraction_per_capture":
                WITHIN_SENSOR_MIN,
            "opposite_sensor_max_fraction_per_capture_exclusive":
                OPPOSITE_SENSOR_MAX,
            "pairwise_spacing": "absolute",
            "candidate_centres":
                "all observed development spacings",
            "family_membership":
                "direct distance to fixed centre; no linkage chaining",
            "excluded_identity_features": [
                "absolute_carrier_offset_hz",
                "received_power",
                "doa",
                "absolute_physical_position",
            ],
        },
        "captures": [
            {
                "label": c["label"],
                "sensor": c["sensor"],
                "source": c["source"],
                "source_sha256": c["source_sha256"],
                "event_count": c["event_count"],
                "duration_median_ms": median(
                    e["duration_ms"] for e in c["events"]
                ),
            }
            for c in captures
        ],
        "candidate_centre_count": len(centres),
        "consolidated_family_count": len(consolidated),
        "classification_counts": counts,
        "families": consolidated,
        "development_only": True,
        "validation_sensors_used": [],
        "identity_claim": False,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(result, indent=2) + "\n"
    )

    print(f"Format: {FORMAT}")
    print(f"Candidate centres: {len(centres)}")
    print(f"Consolidated families: {len(consolidated)}")

    for key, value in counts.items():
        print(f"{key}: {value}")

    print(f"Output: {output}")


if __name__ == "__main__":
    main()
