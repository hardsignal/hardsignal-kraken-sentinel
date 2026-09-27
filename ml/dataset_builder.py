#!/usr/bin/env python3

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from ml.feature_schema import CSV_COLUMNS, DATASET_VERSION


QUALITY_VALUES = {"STABLE", "MULTIPATH", "LOW_QUALITY"}

TRACK_EVENTS = {
    "TRACK_ACQUIRED",
    "TRACK_REACQUIRED",
    "TRACK_SHIFT_CONFIRMED",
    "TRACK_DEGRADED",
    "TRACK_LOST",
    "TRACK_RECOVERED",
}


def parse_kv_line(line):
    """Parse comma-separated key=value Sentinel record."""
    result = {}

    for part in line.strip().split(","):
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        result[key.strip()] = value.strip()

    return result


def float_or_none(value):
    if value is None:
        return None

    value = str(value).strip()

    if value.upper() in {"NA", "NONE", ""}:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def std(values):
    values = [v for v in values if v is not None]

    if len(values) < 2:
        return 0.0 if values else None

    return statistics.stdev(values)


def circular_summary_deg(values):
    values = [v for v in values if v is not None]

    if not values:
        return None, None

    radians = [math.radians(v) for v in values]

    mean_sin = statistics.mean(math.sin(v) for v in radians)
    mean_cos = statistics.mean(math.cos(v) for v in radians)

    angle = math.degrees(math.atan2(mean_sin, mean_cos)) % 360.0

    r = math.hypot(mean_sin, mean_cos)

    if r <= 1e-12:
        circ_std = 180.0
    else:
        r = min(1.0, r)
        circ_std = math.degrees(math.sqrt(max(0.0, -2.0 * math.log(r))))

    return angle, circ_std


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def load_bursts(path):
    sessions = defaultdict(list)

    path = Path(path)

    if not path.exists():
        return sessions

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = parse_kv_line(line)

            session_id = record.get("session_id")
            quality = record.get("quality")

            # Ignore SESSION_START markers and legacy/non-classified records.
            if not session_id or quality not in QUALITY_VALUES:
                continue

            sessions[session_id].append(record)

    return sessions


def load_track_events(path):
    sessions = defaultdict(Counter)

    path = Path(path)

    if not path.exists():
        return sessions

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = parse_kv_line(line)

            session_id = record.get("session_id")
            event = record.get("event")

            if not session_id or event not in TRACK_EVENTS:
                continue

            sessions[session_id][event] += 1

    return sessions


def load_episode_events(path):
    sessions = defaultdict(Counter)

    path = Path(path)

    if not path.exists():
        return sessions

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: malformed JSON: {exc}"
                ) from exc

            session_id = record.get("session_id")
            event = record.get("event")

            if not session_id or not event:
                continue

            sessions[session_id][event] += 1

    return sessions


def build_session_row(session_id, bursts, track_events, episode_events):
    qualities = Counter(b["quality"] for b in bursts)

    bearings = [float_or_none(b.get("bearing")) for b in bursts]
    bearing_mean, bearing_std = circular_summary_deg(bearings)

    times = [parse_time(b.get("time")) for b in bursts]
    times = [t for t in times if t is not None]

    if times:
        start_time = min(times)
        end_time = max(times)
        duration_s = (end_time - start_time).total_seconds()
        start_text = start_time.isoformat()
        end_text = end_time.isoformat()
    else:
        start_text = ""
        end_text = ""
        duration_s = None

    burst_count = len(bursts)

    stable_count = qualities["STABLE"]
    multipath_count = qualities["MULTIPATH"]
    low_quality_count = qualities["LOW_QUALITY"]

    track = track_events.get(session_id, Counter())
    episode = episode_events.get(session_id, Counter())

    episode_event_count = sum(episode.values())

    return {
        "session_id": session_id,
        "start_time": start_text,
        "end_time": end_text,
        "duration_s": duration_s,

        "burst_count": burst_count,

        "stable_count": stable_count,
        "multipath_count": multipath_count,
        "low_quality_count": low_quality_count,

        "stable_ratio": stable_count / burst_count,
        "multipath_ratio": multipath_count / burst_count,
        "low_quality_ratio": low_quality_count / burst_count,

        "bearing_circular_mean_deg": bearing_mean,
        "bearing_circular_std_deg": bearing_std,

        "peak_power_mean_db": mean(
            [float_or_none(b.get("peak_power")) for b in bursts]
        ),
        "peak_power_std_db": std(
            [float_or_none(b.get("peak_power")) for b in bursts]
        ),

        "max_confidence_mean": mean(
            [float_or_none(b.get("max_confidence")) for b in bursts]
        ),
        "median_confidence_mean": mean(
            [float_or_none(b.get("median_confidence")) for b in bursts]
        ),

        "doa_width_mean_deg": mean(
            [float_or_none(b.get("doa_width")) for b in bursts]
        ),
        "doa_width_std_deg": std(
            [float_or_none(b.get("doa_width")) for b in bursts]
        ),

        "median_doa_peaks_mean": mean(
            [float_or_none(b.get("median_doa_peaks")) for b in bursts]
        ),
        "bearing_spread_mean_deg": mean(
            [float_or_none(b.get("bearing_spread")) for b in bursts]
        ),
        "single_peak_ratio_mean": mean(
            [float_or_none(b.get("single_peak_ratio")) for b in bursts]
        ),
        "samples_mean": mean(
            [float_or_none(b.get("samples")) for b in bursts]
        ),

        "track_event_count": sum(track.values()),
        "track_acquired_count": track["TRACK_ACQUIRED"],
        "track_reacquired_count": track["TRACK_REACQUIRED"],
        "track_shift_confirmed_count": track["TRACK_SHIFT_CONFIRMED"],
        "track_degraded_count": track["TRACK_DEGRADED"],
        "track_lost_count": track["TRACK_LOST"],
        "track_recovered_count": track["TRACK_RECOVERED"],

        "episode_event_count": episode_event_count,
        "episode_started_count": episode["EPISODE_STARTED"],
        "episode_closed_count": episode["EPISODE_CLOSED"],
    }


def build_dataset(burst_log, track_log, episode_log, min_bursts=1):
    burst_sessions = load_bursts(burst_log)
    track_sessions = load_track_events(track_log)
    episode_sessions = load_episode_events(episode_log)

    rows = []

    for session_id in sorted(burst_sessions):
        bursts = burst_sessions[session_id]

        if len(bursts) < min_bursts:
            continue

        rows.append(
            build_session_row(
                session_id,
                bursts,
                track_sessions,
                episode_sessions,
            )
        )

    return rows


def write_csv(rows, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Build Kraken RF Sentinel ML session dataset."
    )

    parser.add_argument(
        "--burst-log",
        default=str(Path.home() / "kraken_bursts.log"),
    )

    parser.add_argument(
        "--track-log",
        default=str(Path.home() / "kraken_track_events.log"),
    )

    parser.add_argument(
        "--episode-log",
        default=str(Path.home() / "kraken_episode_events.jsonl"),
    )

    parser.add_argument(
        "--output",
        default="results/ml/rf_behaviour_dataset_v001.csv",
    )

    parser.add_argument(
        "--min-bursts",
        type=int,
        default=2,
    )

    args = parser.parse_args()

    rows = build_dataset(
        args.burst_log,
        args.track_log,
        args.episode_log,
        args.min_bursts,
    )

    write_csv(rows, args.output)

    print("HARDSIGNAL LABS — SENTINEL ML DATASET BUILDER")
    print(f"dataset_version={DATASET_VERSION}")
    print(f"sessions={len(rows)}")
    print(f"output={args.output}")

    if not Path(args.episode_log).exists():
        print("episode_log=missing (episode features set to zero)")


if __name__ == "__main__":
    main()
