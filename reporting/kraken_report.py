from pathlib import Path
from datetime import datetime
from statistics import median
from math import sin, cos, atan2, radians, degrees, sqrt
from collections import defaultdict
import math
import subprocess
import sys

from kraken_project import (
    PROJECT_LAB,
    PROJECT_NAME,
    PROJECT_PHASE,
    RESEARCHER,
    ROLE,
    INSTRUMENT,
    ANALYSIS,
    INTERPRETATION,
)

LOG_PATH = Path.home() / "kraken_bursts.log"

all_rows = []

with LOG_PATH.open() as f:
    for line in f:
        line = line.strip()

        if line.startswith("SESSION_START"):
            continue

        try:
            d = dict(x.split("=", 1) for x in line.split(","))

            d["time"] = datetime.fromisoformat(d["time"])
            d["bearing"] = float(d["bearing"]) % 360
            d["confidence"] = float(d["max_confidence"])
            d["power"] = float(d["peak_power"])
            d["samples"] = int(d["samples"])
            d["frequency_mhz"] = float(d["frequency_mhz"])
            d["doa_width"] = (
                float(d["doa_width"])
                if "doa_width" in d
                else None
            )
            d["median_doa_peaks"] = (
                float(d["median_doa_peaks"])
                if "median_doa_peaks" in d
                else None
            )

            all_rows.append(d)

        except (ValueError, KeyError):
            pass

if not all_rows:
    print("No valid RF records found.")
    raise SystemExit

# Find the latest session marker.
current_session_id = None

with LOG_PATH.open() as f:
    for line in f:
        if line.startswith("SESSION_START"):
            parts = [x.strip() for x in line.strip().split("|")]

            for part in parts:
                if part.startswith("id="):
                    current_session_id = part.split("=", 1)[1]

if current_session_id is None:
    print("No SESSION_START marker found.")
    raise SystemExit

session_rows = [
    r for r in all_rows
    if r.get("session_id") == current_session_id
]

qualified = [
    r for r in session_rows
    if r["confidence"] >= 3.0
    and r["samples"] >= 3
]

report_time = datetime.now().astimezone()

session_start_time = None
session_end_time = None

with LOG_PATH.open("r", errors="ignore") as f:
    for line in f:
        if line.startswith("SESSION_START"):
            parts = [x.strip() for x in line.strip().split("|")]

            marker_id = None
            marker_time = None

            for part in parts:
                if part.startswith("id="):
                    marker_id = part.split("=", 1)[1]
                elif part.startswith("time="):
                    try:
                        marker_time = datetime.fromisoformat(
                            part.split("=", 1)[1]
                        )
                    except ValueError:
                        pass

            if marker_id == current_session_id:
                session_start_time = marker_time

        elif line.startswith("SESSION_END"):
            parts = [x.strip() for x in line.strip().split("|")]

            marker_id = None
            marker_time = None

            for part in parts:
                if part.startswith("id="):
                    marker_id = part.split("=", 1)[1]
                elif part.startswith("time="):
                    try:
                        marker_time = datetime.fromisoformat(
                            part.split("=", 1)[1]
                        )
                    except ValueError:
                        pass

            if marker_id == current_session_id:
                session_end_time = marker_time

print("=" * 72)
print(PROJECT_LAB)
print(PROJECT_NAME)
print("CURRENT SESSION ANALYSIS")
print("=" * 72)
print()
print(f"Researcher:          {RESEARCHER}")
print(f"Role:                {ROLE}")
print(f"Phase:               {PROJECT_PHASE}")
print(f"Instrument:          {INSTRUMENT}")
print(f"Analysis:            {ANALYSIS}")
print()
print(f"Report date:         {report_time:%Y-%m-%d}")
print(f"Report time:         {report_time:%H:%M:%S}")
print(f"Session ID:          {current_session_id}")
if session_end_time:
    print("Session status:       COMPLETED")
else:
    print("Session status:       ACTIVE")


if session_start_time:
    print(
        f"Session started:     "
        f"{session_start_time:%Y-%m-%d %H:%M:%S}"
    )
    if session_end_time:
        print(
            f"Session ended:       "
            f"{session_end_time:%Y-%m-%d %H:%M:%S}"
        )

print("Comparison:          Historical RF Baseline")
print()

print("SESSION INTEGRITY")
print()
print(f"Session marker:        VALID")
print(f"Tagged observations:   {len(session_rows)}")
raw_session_count = 0

with LOG_PATH.open(errors="ignore") as f:
    for line in f:
        if f"session_id={current_session_id}," in line:
            raw_session_count += 1

print(
    f"Observation count:     "
    f"{'VALID' if raw_session_count == len(session_rows) else 'CHECK'}"
)

known_session_ids = set()

with LOG_PATH.open(errors="ignore") as f:
    for line in f:
        if line.startswith("SESSION_START"):
            for part in line.strip().split("|"):
                if part.strip().startswith("id="):
                    known_session_ids.add(
                        part.strip().split("=", 1)[1]
                    )

record_session_ids = {
    r.get("session_id")
    for r in all_rows
    if r.get("session_id")
}

unmatched_ids = record_session_ids - known_session_ids

print(f"Record ownership:      {"VALID" if not unmatched_ids else "CHECK"}")
print(f"Unmatched session IDs: {len(unmatched_ids)}")
print(f"End marker:            {"PRESENT" if session_end_time else "NOT PRESENT"}")
print()

print("SESSION OBSERVATION STATUS")
print()
print(f"Raw RF bursts:        {len(session_rows)}")
print(f"Qualified detections: {len(qualified)}")
print()

if not qualified:
    if session_rows:
        print("STATUS: OBSERVING — no qualified candidates yet.")
        print("Raw observations are being retained for analysis.")
    else:
        print("STATUS: WAITING — no RF bursts recorded in this session yet.")

    print()
    print("INTERPRETATION")
    print()
    print(INTERPRETATION)
    print()
    print("=" * 72)
    raise SystemExit

# ----------------------------------------------------------------------
# Group qualified detections by frequency.
#
# The frequency values produced by KrakenSDR are rounded to 6 decimal
# MHz places in the log, so use that logged value as the grouping key.
# ----------------------------------------------------------------------

frequency_groups = defaultdict(list)

for r in qualified:
    frequency_groups[r["frequency_mhz"]].append(r)

print("SESSION SUMMARY")
print()
if session_rows:
    observation_start = min(r["time"] for r in session_rows)
    observation_end = max(r["time"] for r in session_rows)
    observation_span = observation_end - observation_start
    print(f"Observation span:     {observation_span}")
else:
    print("Observation span:     0:00:00")


if session_start_time:
    duration = (session_end_time or report_time) - session_start_time
    print(f"Session duration:     {str(duration).split('.')[0]}")
else:
    print("Session duration:     unknown")

print(f"Raw RF bursts:        {len(session_rows)}")
print(f"Qualified detections: {len(qualified)}")

if qualified:
    frequencies = sorted({
        round(r["frequency_mhz"], 6)
        for r in qualified
    })
    print(f"Frequencies observed: {len(frequencies)}")
    print(f"Strongest power:      {max(r["power"] for r in qualified):.1f} dB")
else:
    print("Frequencies observed: 0")
    print("Strongest power:      n/a")

print()

print("FREQUENCY GROUPS")
print()

for frequency in sorted(frequency_groups):
    group = frequency_groups[frequency]
    count = len(group)

    session_frequency_rows = [
        r for r in session_rows
        if round(r["frequency_mhz"], 6) == round(frequency, 6)
    ]

    if count == 1:
        persistence = "ISOLATED"
    elif count <= 4:
        persistence = "SPARSE"
    elif count <= 19:
        persistence = "REPEATED"
    else:
        persistence = "PERSISTENT"

    historical_count = sum(
        1 for r in all_rows
        if round(r["frequency_mhz"], 6) == round(frequency, 6)
    )

    if historical_count == 1:
        historical_persistence = "ISOLATED"
    elif historical_count <= 4:
        historical_persistence = "SPARSE"
    elif historical_count <= 19:
        historical_persistence = "REPEATED"
    else:
        historical_persistence = "PERSISTENT"

    tagged_sessions = {
        r["session_id"]
        for r in all_rows
        if r.get("session_id")
        and round(r["frequency_mhz"], 6) == round(frequency, 6)
    }

    historical_bearings = [
        r["bearing"]
        for r in all_rows
        if round(r["frequency_mhz"], 6) == round(frequency, 6)
    ]

    x = sum(cos(radians(v)) for v in historical_bearings) / len(historical_bearings)
    y = sum(sin(radians(v)) for v in historical_bearings) / len(historical_bearings)

    circular_mean = degrees(atan2(y, x)) % 360
    concentration = sqrt(x*x + y*y)
    if len(historical_bearings) < 5:
        directional_class = "INSUFFICIENT DATA"
    elif concentration < 0.25:
        directional_class = "DIFFUSE"
    elif concentration < 0.50:
        directional_class = "WEAKLY CLUSTERED"
    elif concentration < 0.75:
        directional_class = "CLUSTERED"
    else:
        directional_class = "TIGHTLY CLUSTERED"
    historical_rows = [
        r for r in all_rows
        if round(r["frequency_mhz"], 6) == round(frequency, 6)
    ]

    window_groups = {}
    for r in historical_rows:
        t = r["time"]
        bucket = t.replace(minute=(t.minute // 10) * 10, second=0, microsecond=0)
        window_groups.setdefault(bucket, []).append(r["bearing"])

    reliable_means = []
    for bucket in sorted(window_groups):
        values = window_groups[bucket]
        if len(values) < 5:
            continue

        wx = sum(cos(radians(v)) for v in values) / len(values)
        wy = sum(sin(radians(v)) for v in values) / len(values)
        reliable_means.append(degrees(atan2(wy, wx)) % 360)

    doa_shift = 0.0
    if len(reliable_means) >= 2:
        doa_shift = abs((reliable_means[-1] - reliable_means[0] + 180) % 360 - 180)

    if (
        historical_persistence == "PERSISTENT"
        and directional_class in ("CLUSTERED", "TIGHTLY CLUSTERED")
        and doa_shift >= 30.0
    ):
        candidate_quality = "STRONG TEMPORAL CANDIDATE — EVOLVING DoA"
    elif historical_persistence == "PERSISTENT" and directional_class in ("CLUSTERED", "TIGHTLY CLUSTERED"):
        candidate_quality = "STRONG CANDIDATE"
    elif historical_persistence == "PERSISTENT" and directional_class in ("DIFFUSE", "WEAKLY CLUSTERED"):
        candidate_quality = "RECURRING / UNSTABLE DoA"
    elif historical_persistence == "REPEATED" and directional_class in ("CLUSTERED", "TIGHTLY CLUSTERED"):
        candidate_quality = "DEVELOPING CANDIDATE"
    else:
        candidate_quality = "INSUFFICIENT EVIDENCE"

    historical_times = sorted(
        r["time"]
        for r in all_rows
        if round(r["frequency_mhz"], 6) == round(frequency, 6)
    )

    historical_span = historical_times[-1] - historical_times[0]

    if len(historical_times) >= 2:
        gaps = [
            (b - a).total_seconds()
            for a, b in zip(historical_times, historical_times[1:])
        ]
        median_gap = f"{median(gaps):.1f}s"
        max_gap = f"{max(gaps):.1f}s"
    else:
        median_gap = "n/a"
        max_gap = "n/a"

    print(
        f"{frequency:.6f} MHz"
        f" | current={count} ({persistence})"
        f" | historical={historical_count} ({historical_persistence})"
        f" | tagged_sessions={len(tagged_sessions)}"
    )
    print(
        f"  temporal: span={historical_span}"
        f" | median_gap={median_gap}"
        f" | max_gap={max_gap}"
    )
    width_values = [
        r["doa_width"]
        for r in session_frequency_rows
        if r.get("doa_width") is not None
    ]

    print(
        f"  directional: mean={circular_mean:.1f}°"
        f" | concentration={concentration:.3f}"
        f" | class={directional_class}"
    )

    if width_values:
        print(
            f"  doa_response: median_width={median(width_values):.1f}°"
            f" | measured={len(width_values)}/{len(session_frequency_rows)}"
        )
    else:
        print(
            f"  doa_response: median_width=n/a"
            f" | measured=0/{len(session_frequency_rows)}"
        )

    peak_values = [
        r["median_doa_peaks"]
        for r in session_frequency_rows
        if r.get("median_doa_peaks") is not None
    ]

    if peak_values:
        print(
            f"  doa_ambiguity: median_peaks={median(peak_values):.1f}"
            f" | measured={len(peak_values)}/{len(session_frequency_rows)}"
        )
    else:
        print(
            f"  doa_ambiguity: median_peaks=n/a"
            f" | measured=0/{len(session_frequency_rows)}"
        )

    print(
        f"  candidate_quality: {candidate_quality}"
    )

print()
print("DIRECTIONAL ANALYSIS")
print()

total_candidates = 0
directional_states = defaultdict(list)

for frequency in sorted(frequency_groups):

    group = frequency_groups[frequency]

    print(f"FREQUENCY: {frequency:.6f} MHz")
    print("-" * 72)

    bins = [0] * 36

    for r in group:
        bins[int(r["bearing"] // 10)] += 1

    peaks = []

    for i, count in enumerate(bins):
        left = bins[(i - 1) % 36]
        right = bins[(i + 1) % 36]

        if count >= 3 and count > left and count >= right:
            peaks.append((count, i * 10))

    peaks.sort(reverse=True)

    if not peaks:
        print("No directional peaks meeting the minimum threshold.")
        print()
        continue

    for count, centre in peaks:

        nearby = [
            r for r in group
            if min(
                abs(r["bearing"] - centre),
                360 - abs(r["bearing"] - centre)
            ) <= 10
        ]

        if not nearby:
            continue

        angles = [
            math.radians(r["bearing"])
            for r in nearby
        ]

        sin_mean = sum(math.sin(a) for a in angles)
        cos_mean = sum(math.cos(a) for a in angles)

        mean_bearing = math.degrees(
            math.atan2(sin_mean, cos_mean)
        ) % 360

        avg_conf = (
            sum(r["confidence"] for r in nearby)
            / len(nearby)
        )

        strongest = max(
            r["power"]
            for r in nearby
        )

        nearby_widths = [
            r["doa_width"]
            for r in nearby
            if r.get("doa_width") is not None
        ]

        nearby_peaks = [
            r["median_doa_peaks"]
            for r in nearby
            if r.get("median_doa_peaks") is not None
        ]

        windows = {
            r["time"].replace(
                minute=(r["time"].minute // 10) * 10,
                second=0,
                microsecond=0
            )
            for r in nearby
        }

        start = min(r["time"] for r in nearby)
        end = max(r["time"] for r in nearby)

        duration = (
            end - start
        ).total_seconds()

        if len(windows) >= 4:
            status = "PERSISTENT"
        elif len(windows) >= 2:
            status = "REPEATED"
        else:
            status = "TRANSIENT"

        total_candidates += 1

        width_text = (
            f"{median(nearby_widths):.1f}°"
            if nearby_widths
            else "n/a"
        )

        peaks_text = (
            f"{median(nearby_peaks):.1f}"
            if nearby_peaks
            else "n/a"
        )

        state_width = median(nearby_widths) if nearby_widths else None
        state_peaks = median(nearby_peaks) if nearby_peaks else None

        directional_states[frequency].append({
            "bearing": mean_bearing,
            "hits": len(nearby),
            "width": state_width,
            "peaks": state_peaks,
            "quality": (
                "COHERENT"
                if state_peaks is not None and state_peaks <= 1.0
                else "AMBIGUOUS"
            ),
        })

        print(
            f"{status:10s} | "
            f"{mean_bearing:6.1f}° | "
            f"hits={len(nearby):3d} | "
            f"windows={len(windows):2d} | "
            f"confidence={avg_conf:.2f} | "
            f"peak={strongest:.1f} dB | "
            f"width={width_text} | "
            f"peaks={peaks_text} | "
            f"span={duration:.0f}s"
        )

    print()

print(f"Candidates classified: {total_candidates}")
print()

print("DIRECTIONAL STATES")
print()

for frequency in sorted(directional_states):
    print(f"FREQUENCY: {frequency:.6f} MHz")

    for i, state in enumerate(directional_states[frequency], 1):
        width = f"{state['width']:.1f}°" if state["width"] is not None else "n/a"
        peaks = f"{state['peaks']:.1f}" if state["peaks"] is not None else "n/a"

        print(f"  State {i}")
        print(f"    centroid:     {state['bearing']:.1f}°")
        print(f"    hits:         {state['hits']}")
        print(f"    median width: {width}")
        print(f"    median peaks: {peaks}")
        print(f"    quality:      {state['quality']}")

    raw_group = [
        r for r in session_rows
        if r["frequency_mhz"] == frequency
    ]

    multi_peak = [
        r for r in raw_group
        if r.get("median_doa_peaks") is not None
        and r["median_doa_peaks"] > 1.0
    ]

    multi_peak_fraction = (
        100.0 * len(multi_peak) / len(raw_group)
        if raw_group else 0.0
    )

    ambiguity_windows = []
    recovery_summaries = []

    for r in sorted(multi_peak, key=lambda x: x["time"]):
        if (
            not ambiguity_windows
            or (r["time"] - ambiguity_windows[-1][-1]["time"]).total_seconds() > 60
        ):
            ambiguity_windows.append([r])
        else:
            ambiguity_windows[-1].append(r)

    print("  Ambiguity diagnostics")
    print(f"    raw observations:        {len(raw_group)}")
    print(f"    multi-peak observations: {len(multi_peak)}")
    print(f"    multi-peak fraction:     {multi_peak_fraction:.1f}%")

    for i, window in enumerate(ambiguity_windows, 1):
        start = window[0]["time"]
        end = window[-1]["time"]
        duration = (end - start).total_seconds()

        max_peaks = max(r["median_doa_peaks"] for r in window)
        max_width = max(
            r["doa_width"] for r in window
            if r.get("doa_width") is not None
        )
        min_conf = min(r["confidence"] for r in window)

        next_start = (
            ambiguity_windows[i][0]["time"]
            if i < len(ambiguity_windows)
            else None
        )

        recovery_rows = [
            r for r in sorted(raw_group, key=lambda x: x["time"])
            if r["time"] > end
            and (next_start is None or r["time"] < next_start)
            and r["confidence"] >= 3.0
            and r["samples"] >= 3
            and r.get("median_doa_peaks") is not None
            and r["median_doa_peaks"] <= 1.0
        ]

        print(f"    window {i}:")
        print(f"      start:          {start:%H:%M:%S}")
        print(f"      end:            {end:%H:%M:%S}")
        print(f"      duration:       {duration:.0f}s")
        print(f"      observations:   {len(window)}")
        print(f"      max peaks:      {max_peaks:.1f}")
        print(f"      max width:      {max_width:.1f}°")
        print(f"      min confidence: {min_conf:.2f}")

        if recovery_rows:
            first_recovery = recovery_rows[0]
            recovery_delay = (
                first_recovery["time"] - end
            ).total_seconds()

            angles = [
                math.radians(r["bearing"])
                for r in recovery_rows
            ]

            recovery_bearing = math.degrees(
                math.atan2(
                    sum(math.sin(a) for a in angles),
                    sum(math.cos(a) for a in angles)
                )
            ) % 360

            print("      recovery:")
            print(f"        coherent resumed:   {first_recovery['time']:%H:%M:%S}")
            print(f"        recovery delay:     {recovery_delay:.0f}s")
            print(f"        coherent samples:   {len(recovery_rows)}")
            print(f"        recovered centroid: {recovery_bearing:.1f}°")

            transition_duration = (
                first_recovery["time"] - start
            ).total_seconds()

            recovery_summaries.append({
                "delay": recovery_delay,
                "bearing": recovery_bearing,
                "samples": len(recovery_rows),
                "time": first_recovery["time"],
            })

            print("      state transitions:")
            print(f"        COHERENT -> AMBIGUOUS: {start:%H:%M:%S}")
            print(
                f"        AMBIGUOUS -> COHERENT: "
                f"{first_recovery['time']:%H:%M:%S}"
            )
            print(
                f"        time to confirmed recovery: "
                f"{transition_duration:.0f}s"
            )
        else:
            print("      recovery:             not observed")
            print("      state transitions:")
            print(f"        COHERENT -> AMBIGUOUS: {start:%H:%M:%S}")
            print("        AMBIGUOUS -> COHERENT: not observed")

    states = directional_states[frequency]
    dominant_state = (
        max(states, key=lambda x: x["hits"])
        if states else None
    )

    single_peak_count = len(raw_group) - len(multi_peak)

    print("  DoA stability")
    print(f"    single-peak observations: {single_peak_count}/{len(raw_group)}")
    print(f"    multi-peak fraction:      {multi_peak_fraction:.1f}%")

    if dominant_state is not None:
        print(f"    dominant state:           {dominant_state['bearing']:.1f}°")
        print(f"    dominant state hits:      {dominant_state['hits']}")

    if ambiguity_windows:
        print(
            f"    recoveries observed:      "
            f"{len(recovery_summaries)}/{len(ambiguity_windows)}"
        )
    else:
        print("    recoveries observed:      n/a")

    if recovery_summaries and dominant_state is not None:
        latest_recovery = recovery_summaries[-1]

        centroid_error = abs(
            (
                latest_recovery["bearing"]
                - dominant_state["bearing"]
                + 180.0
            ) % 360.0 - 180.0
        )

        print(f"    recovery delay:           {latest_recovery['delay']:.0f}s")
        print(f"    recovered centroid:       {latest_recovery['bearing']:.1f}°")
        print(f"    centroid error:           {centroid_error:.1f}°")

        if centroid_error <= 10.0:
            stability_class = "MIXED / RECOVERING"
        else:
            stability_class = "MIXED / SHIFTED"

    elif ambiguity_windows:
        stability_class = "MIXED / UNRESOLVED"

    elif dominant_state is not None:
        stability_class = "STABLE / NO AMBIGUITY"

    else:
        stability_class = "INSUFFICIENT DATA"

    print(f"    classification:           {stability_class}")
    print()

def extract_directional_states(rows):
    """
    Reproduce the session directional-state classifier for an arbitrary
    historical group without changing the main classifier.
    """

    qualified_rows = [
        r for r in rows
        if r["confidence"] >= 3.0
        and r["samples"] >= 3
    ]

    if not qualified_rows:
        return []

    bins = [0] * 36

    for r in qualified_rows:
        bins[int(r["bearing"] // 10)] += 1

    peaks = []

    for i, count in enumerate(bins):
        left = bins[(i - 1) % 36]
        right = bins[(i + 1) % 36]

        if count >= 3 and count > left and count >= right:
            peaks.append((count, i * 10))

    peaks.sort(reverse=True)

    states = []

    for count, centre in peaks:
        nearby = [
            r for r in qualified_rows
            if min(
                abs(r["bearing"] - centre),
                360 - abs(r["bearing"] - centre)
            ) <= 10
        ]

        if not nearby:
            continue

        angles = [
            math.radians(r["bearing"])
            for r in nearby
        ]

        mean_bearing = math.degrees(
            math.atan2(
                sum(math.sin(a) for a in angles),
                sum(math.cos(a) for a in angles)
            )
        ) % 360

        widths = [
            r["doa_width"]
            for r in nearby
            if r.get("doa_width") is not None
        ]

        peak_counts = [
            r["median_doa_peaks"]
            for r in nearby
            if r.get("median_doa_peaks") is not None
        ]

        states.append({
            "bearing": mean_bearing,
            "hits": len(nearby),
            "width": median(widths) if widths else None,
            "peaks": median(peak_counts) if peak_counts else None,
        })

    return states


print("CROSS-SESSION ANALYSIS")
print()

for frequency in sorted({
    round(r["frequency_mhz"], 6)
    for r in all_rows
}):
    session_groups = {}

    for r in all_rows:
        if round(r["frequency_mhz"], 6) != frequency:
            continue

        sid = r.get("session_id")
        if not sid:
            continue

        session_groups.setdefault(sid, []).append(r)

    tagged_sessions = len(session_groups)
    qualifying_sessions = sum(
        1 for rows in session_groups.values()
        if len(rows) >= 5
    )

    if tagged_sessions >= 2:
        rf_recurrence = "YES"
    else:
        rf_recurrence = "NOT YET"

    qualifying_centroids = []

    for rows in session_groups.values():
        if len(rows) < 5:
            continue

        bearings = [r["bearing"] for r in rows]
        x = sum(cos(radians(v)) for v in bearings) / len(bearings)
        y = sum(sin(radians(v)) for v in bearings) / len(bearings)
        qualifying_centroids.append(degrees(atan2(y, x)) % 360)

    if qualifying_sessions >= 2:
        centroid_shifts = []
        for i in range(len(qualifying_centroids)):
            for j in range(i + 1, len(qualifying_centroids)):
                shift = abs(
                    (qualifying_centroids[j] - qualifying_centroids[i] + 180)
                    % 360 - 180
                )
                centroid_shifts.append(shift)

        max_centroid_shift = max(centroid_shifts)
        doa_recurrence = "READY FOR VALIDATION"
    elif tagged_sessions >= 2:
        max_centroid_shift = None
        doa_recurrence = "PRELIMINARY"
    else:
        max_centroid_shift = None
        doa_recurrence = "INSUFFICIENT DATA"

    print(f"{frequency:.6f} MHz")
    print(f"  tagged_sessions: {tagged_sessions}")
    print(f"  qualifying_sessions: {qualifying_sessions}")
    print(f"  RF recurrence: {rf_recurrence}")
    print(f"  DoA recurrence: {doa_recurrence}")

    if max_centroid_shift is not None:
        print(f"  qualifying centroid max shift: {max_centroid_shift:.1f}°")

    for sid in sorted(session_groups):
        rows = session_groups[sid]
        bearings = [r["bearing"] for r in rows]

        x = sum(cos(radians(v)) for v in bearings) / len(bearings)
        y = sum(sin(radians(v)) for v in bearings) / len(bearings)

        mean_bearing = degrees(atan2(y, x)) % 360
        concentration = sqrt(x*x + y*y)

        evidence = "QUALIFYING" if len(rows) >= 5 else "LOW-SAMPLE"

        print(
            f"  session {sid}: n={len(rows)}"
            f" | mean={mean_bearing:.1f}°"
            f" | concentration={concentration:.3f}"
            f" | {evidence}"
        )

    print()

print("CROSS-SESSION DIRECTIONAL STATES")
print()

for frequency in sorted({
    round(r["frequency_mhz"], 6)
    for r in all_rows
}):
    session_groups = {}

    for r in all_rows:
        if round(r["frequency_mhz"], 6) != frequency:
            continue

        sid = r.get("session_id")
        if not sid:
            continue

        session_groups.setdefault(sid, []).append(r)

    matched_sessions = []

    for sid in sorted(session_groups):
        states = extract_directional_states(session_groups[sid])

        if not states:
            continue

        dominant = max(states, key=lambda x: x["hits"])

        matched_sessions.append({
            "session_id": sid,
            "bearing": dominant["bearing"],
            "hits": dominant["hits"],
            "width": dominant["width"],
            "peaks": dominant["peaks"],
        })

    if len(matched_sessions) < 2:
        continue

    print(f"{frequency:.6f} MHz")

    for state in matched_sessions:
        width_text = (
            f"{state['width']:.1f}°"
            if state["width"] is not None
            else "n/a"
        )

        peaks_text = (
            f"{state['peaks']:.1f}"
            if state["peaks"] is not None
            else "n/a"
        )

        print(
            f"  session {state['session_id']}: "
            f"dominant={state['bearing']:.1f}°"
            f" | hits={state['hits']}"
            f" | width={width_text}"
            f" | peaks={peaks_text}"
        )

    print("  consecutive state shifts:")

    for previous, current in zip(
        matched_sessions,
        matched_sessions[1:]
    ):
        shift = abs(
            (
                current["bearing"]
                - previous["bearing"]
                + 180.0
            ) % 360.0 - 180.0
        )

        print(
            f"    {previous['session_id']} -> "
            f"{current['session_id']}: "
            f"{shift:.1f}°"
        )

    first_state = matched_sessions[0]
    last_state = matched_sessions[-1]

    return_error = abs(
        (
            last_state["bearing"]
            - first_state["bearing"]
            + 180.0
        ) % 360.0 - 180.0
    )

    print(f"  first -> last state error: {return_error:.1f}°")

    if len(matched_sessions) >= 3:
        if return_error <= 10.0:
            return_match = "YES"
        else:
            return_match = "NO"

        print(f"  return-state match: {return_match}")

    print()

print("HISTORICAL CANDIDATE OVERVIEW")
print()
for frequency in sorted({
    round(r["frequency_mhz"], 6)
    for r in all_rows
}):
    rows = [
        r for r in all_rows
        if round(r["frequency_mhz"], 6) == frequency
    ]

    count = len(rows)
    bearings = [r["bearing"] for r in rows]

    powers = [r["power"] for r in rows]
    confidences = [r["confidence"] for r in rows]

    median_power = median(powers)
    median_confidence = median(confidences)

    x = sum(cos(radians(v)) for v in bearings) / count
    y = sum(sin(radians(v)) for v in bearings) / count
    concentration = sqrt(x*x + y*y)

    if count == 1:
        persistence = "ISOLATED"
    elif count < 5:
        persistence = "SPARSE"
    elif count < 20:
        persistence = "REPEATED"
    else:
        persistence = "PERSISTENT"

    if count < 5:
        direction = "INSUFFICIENT DATA"
    elif concentration < 0.25:
        direction = "DIFFUSE"
    elif concentration < 0.50:
        direction = "WEAKLY CLUSTERED"
    elif concentration < 0.75:
        direction = "CLUSTERED"
    else:
        direction = "TIGHTLY CLUSTERED"

    window_groups = {}
    for r in rows:
        t = r["time"]
        bucket = t.replace(minute=(t.minute // 10) * 10, second=0, microsecond=0)
        window_groups.setdefault(bucket, []).append(r["bearing"])

    reliable_means = []
    for bucket in sorted(window_groups):
        values = window_groups[bucket]
        if len(values) < 5:
            continue

        wx = sum(cos(radians(v)) for v in values) / len(values)
        wy = sum(sin(radians(v)) for v in values) / len(values)
        reliable_means.append(degrees(atan2(wy, wx)) % 360)

    doa_shift = 0.0
    if len(reliable_means) >= 2:
        doa_shift = abs((reliable_means[-1] - reliable_means[0] + 180) % 360 - 180)

    if (
        persistence == "PERSISTENT"
        and direction in ("CLUSTERED", "TIGHTLY CLUSTERED")
        and doa_shift >= 30.0
    ):
        quality = "STRONG TEMPORAL CANDIDATE — EVOLVING DoA"
    elif persistence == "PERSISTENT" and direction in ("CLUSTERED", "TIGHTLY CLUSTERED"):
        quality = "STRONG CANDIDATE"
    elif persistence == "PERSISTENT" and direction in ("DIFFUSE", "WEAKLY CLUSTERED"):
        quality = "RECURRING / UNSTABLE DoA"
    elif persistence == "REPEATED" and direction in ("CLUSTERED", "TIGHTLY CLUSTERED"):
        quality = "DEVELOPING CANDIDATE"
    else:
        quality = "INSUFFICIENT EVIDENCE"

    print(
        f"{frequency:.6f} MHz | observations={count}"
        f" | persistence={persistence}"
    )
    print(
        f"  signal: power={median_power:.1f} dB"
        f" | confidence={median_confidence:.3f}"
    )
    print(
        f"  directional: concentration={concentration:.3f}"
        f" | class={direction}"
    )
    print(
        f"  quality: {quality}"
    )
    print()

print("INTERPRETATION")
print()
print(INTERPRETATION)
print()
print("CURRENT vs HISTORICAL")
print()

result = subprocess.run(
    [sys.executable, str(Path.home() / "kraken_compare.py")],
    capture_output=True,
    text=True
)

for line in result.stdout.splitlines():
    if "MATCHED |" in line or "NEW DIRECTION |" in line or "NEW FREQUENCY |" in line:
        print(line)

print()
print("=" * 72)
