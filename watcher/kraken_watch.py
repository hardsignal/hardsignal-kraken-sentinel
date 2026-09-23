import csv
import time
import statistics
from math import sin, cos, atan2, radians, degrees, sqrt, log as math_log
from datetime import datetime
from pathlib import Path
from collections import deque

from kraken_project import (
    PROJECT_LAB,
    PROJECT_NAME,
    PROJECT_PHASE,
    INSTRUMENT,
)

LOG_PATH = Path.home() / "kraken_bursts.log"
TRACK_EVENT_LOG_PATH = Path.home() / "kraken_track_events.log"
CSV_PATH = Path.home() / "krakensdr_doa" / "mydata.csv"

POWER_THRESHOLD = -45.0
POLL_INTERVAL = 1.0
EVENT_GAP = 3.0

TRACK_WINDOW = 5
TRACK_STABLE_SPREAD_MAX = 5.0
TRACK_SHIFTING_SPREAD_MIN = 12.0

last_size = None
event_rows = []
last_event_time = None
event_active = False

stable_burst_bearings = deque(maxlen=TRACK_WINDOW)

previous_track_state = "INSUFFICIENT_DATA"
last_stable_track_mean = None


def classify_track(bearings):
    if len(bearings) < TRACK_WINDOW:
        return "INSUFFICIENT_DATA", None, None

    x = statistics.mean(cos(radians(b)) for b in bearings)
    y = statistics.mean(sin(radians(b)) for b in bearings)

    mean_bearing = degrees(atan2(y, x)) % 360

    circular_r = sqrt(x * x + y * y)
    circular_r = min(1.0, max(circular_r, 1e-12))
    circular_std = degrees(sqrt(-2.0 * math_log(circular_r)))

    if circular_std <= TRACK_STABLE_SPREAD_MAX:
        state = "TRACK_STABLE"
    elif circular_std >= TRACK_SHIFTING_SPREAD_MIN:
        state = "TRACK_SHIFTING"
    else:
        state = "TRACK_VARIABLE"

    return state, mean_bearing, circular_std


def classify_quality(
    sample_count,
    circular_std,
    median_confidence,
    median_doa_width,
    single_peak_ratio,
):
    # Strong indicators that the DoA solution is being distorted
    # by multiple paths / competing peaks.
    if (
        circular_std >= 12.0
        or median_doa_width >= 80.0
        or single_peak_ratio < 0.75
    ):
        return "MULTIPATH"

    # Clean, repeatable solution.
    if (
        sample_count >= 3
        and circular_std <= 7.0
        and median_confidence >= 3.5
        and median_doa_width <= 70.0
        and single_peak_ratio >= 0.75
    ):
        return "STABLE"

    return "LOW_QUALITY"


def get_session_id():
    if not LOG_PATH.exists():
        return "NO_SESSION"

    session_id = "NO_SESSION"

    with LOG_PATH.open("r", errors="ignore") as log:
        for line in log:
            if line.startswith("SESSION_START"):
                parts = [x.strip() for x in line.strip().split("|")]
                for part in parts:
                    if part.startswith("id="):
                        session_id = part.split("=", 1)[1]

    return session_id


SESSION_ID = __import__("os").environ.get(
    "KRAKEN_SESSION_ID",
    get_session_id()
)

print("=" * 62)
print(PROJECT_LAB)
print(PROJECT_NAME)
print(PROJECT_PHASE)
print("=" * 62)
print("Researcher:       Maciej Duranczyk")
print("Role:             Cyber-Physical Security Researcher")
print(f"Instrument:       {INSTRUMENT}")
print(f"Watching:         {CSV_PATH}")
print(f"Alert threshold:  {POWER_THRESHOLD} dB")
print(f"Session ID:       {SESSION_ID}")
print("=" * 62)

while True:
    if not CSV_PATH.exists():
        time.sleep(POLL_INTERVAL)
        continue

    with CSV_PATH.open("r", errors="ignore") as f:
        rows = list(csv.reader(f))

    if last_size is None:
        last_size = len(rows)
        time.sleep(POLL_INTERVAL)
        continue

    if len(rows) > last_size:
        for row in rows[last_size:]:
            try:
                bearing = float(row[1])
                confidence = float(row[2])
                power = float(row[3])
                frequency = float(row[4])

                doa_array = [float(x) for x in row[17:]]
                if len(doa_array) != 360:
                    continue

                half_max = max(doa_array) * 0.5
                doa_width = sum(v >= half_max for v in doa_array)

                doa_peaks = sum(
                    doa_array[i] >= half_max
                    and doa_array[i] > doa_array[(i - 1) % 360]
                    and doa_array[i] >= doa_array[(i + 1) % 360]
                    for i in range(360)
                )

                if power > POWER_THRESHOLD:
                    event_rows.append(
                        (bearing, power, confidence, frequency, doa_width, doa_peaks)
                    )
                    last_event_time = time.time()
                    event_active = True

            except (ValueError, IndexError):
                pass

        last_size = len(rows)

    if event_active and time.time() - last_event_time >= EVENT_GAP:
        bearings = [r[0] for r in event_rows]

        x = statistics.mean(cos(radians(b)) for b in bearings)
        y = statistics.mean(sin(radians(b)) for b in bearings)
        mean_bearing = degrees(atan2(y, x)) % 360

        circular_r = sqrt(x * x + y * y)
        circular_r = min(1.0, max(circular_r, 1e-12))
        circular_std = degrees(sqrt(-2.0 * math_log(circular_r)))

        powers = [r[1] for r in event_rows]
        peak_power = max(powers)

        confidences = [r[2] for r in event_rows]
        max_confidence = max(confidences)
        median_confidence = statistics.median(confidences)

        frequencies = [r[3] for r in event_rows]
        mean_frequency = statistics.mean(frequencies)

        doa_widths = [r[4] for r in event_rows]
        median_doa_width = statistics.median(doa_widths)

        doa_peaks = [r[5] for r in event_rows]
        median_doa_peaks = statistics.median(doa_peaks)

        single_peak_ratio = (
            sum(1 for p in doa_peaks if p == 1) / len(doa_peaks)
        )

        quality = classify_quality(
            sample_count=len(event_rows),
            circular_std=circular_std,
            median_confidence=median_confidence,
            median_doa_width=median_doa_width,
            single_peak_ratio=single_peak_ratio,
        )

        # Only high-quality individual bursts contribute to source tracking.
        if quality == "STABLE":
            stable_burst_bearings.append(mean_bearing)

        track_state, track_mean, track_spread = classify_track(
            stable_burst_bearings
        )

        track_count = len(stable_burst_bearings)
        track_mean_text = (
            "NA" if track_mean is None else f"{track_mean:.1f}"
        )
        track_spread_text = (
            "NA" if track_spread is None else f"{track_spread:.1f}"
        )

        track_event = None

        if track_state != previous_track_state:
            if (
                track_state == "TRACK_STABLE"
                and previous_track_state == "INSUFFICIENT_DATA"
            ):
                track_event = "TRACK_ACQUIRED"

            elif (
                track_state == "TRACK_STABLE"
                and previous_track_state in ("TRACK_SHIFTING", "TRACK_VARIABLE")
            ):
                track_event = "TRACK_REACQUIRED"

            elif (
                track_state == "TRACK_SHIFTING"
                and last_stable_track_mean is not None
            ):
                track_event = "TRACK_SHIFT_DETECTED"

            elif (
                track_state == "TRACK_VARIABLE"
                and previous_track_state == "TRACK_STABLE"
            ):
                track_event = "TRACK_DEGRADED"

        old_track_mean_text = (
            "NA"
            if last_stable_track_mean is None
            else f"{last_stable_track_mean:.1f}"
        )

        timestamp = datetime.now().isoformat(timespec="seconds")

        print(
            f"{timestamp} | "
            f"PROJECT={PROJECT_NAME} | "
            f"SESSION={SESSION_ID} | "
            f"RF BURST | "
            f"freq={mean_frequency/1e6:.6f} MHz | "
            f"bearing={mean_bearing:.1f}° | "
            f"peak_power={peak_power:.1f} dB | "
            f"max_confidence={max_confidence:.2f} | "
            f"doa_width={median_doa_width:.1f}° | "
            f"median_doa_peaks={median_doa_peaks:.1f} | "
            f"bearing_spread={circular_std:.1f}° | "
            f"median_confidence={median_confidence:.2f} | "
            f"single_peak_ratio={single_peak_ratio:.2f} | "
            f"quality={quality} | "
            f"track_state={track_state} | "
            f"track_mean={track_mean_text}° | "
            f"track_spread={track_spread_text}° | "
            f"track_count={track_count} | "
            f"samples={len(event_rows)}"
        )

        with LOG_PATH.open("a") as log:
            log.write(
                f"time={timestamp},"
                f"project={PROJECT_NAME},"
                f"phase={PROJECT_PHASE},"
                f"instrument={INSTRUMENT},"
                f"session_id={SESSION_ID},"
                f"frequency_mhz={mean_frequency/1e6:.6f},"
                f"bearing={mean_bearing:.1f},"
                f"peak_power={peak_power:.1f},"
                f"max_confidence={max_confidence:.2f},"
                f"doa_width={median_doa_width:.1f},"
                f"median_doa_peaks={median_doa_peaks:.1f},"
                f"bearing_spread={circular_std:.1f},"
                f"median_confidence={median_confidence:.2f},"
                f"single_peak_ratio={single_peak_ratio:.2f},"
                f"quality={quality},"
                f"track_state={track_state},"
                f"track_mean={track_mean_text},"
                f"track_spread={track_spread_text},"
                f"track_count={track_count},"
                f"samples={len(event_rows)}\n"
            )

        if track_event is not None:
            print(
                f"{timestamp} | "
                f"PROJECT={PROJECT_NAME} | "
                f"SESSION={SESSION_ID} | "
                f"{track_event} | "
                f"previous_state={previous_track_state} | "
                f"current_state={track_state} | "
                f"old_track_mean={old_track_mean_text}° | "
                f"current_bearing={mean_bearing:.1f}° | "
                f"track_mean={track_mean_text}° | "
                f"track_spread={track_spread_text}° | "
                f"track_count={track_count}"
            )

            with TRACK_EVENT_LOG_PATH.open("a") as event_log:
                event_log.write(
                    f"time={timestamp},"
                    f"project={PROJECT_NAME},"
                    f"session_id={SESSION_ID},"
                    f"event={track_event},"
                    f"previous_state={previous_track_state},"
                    f"current_state={track_state},"
                    f"old_track_mean={old_track_mean_text},"
                    f"current_bearing={mean_bearing:.1f},"
                    f"track_mean={track_mean_text},"
                    f"track_spread={track_spread_text},"
                    f"track_count={track_count}\n"
                )

        previous_track_state = track_state

        if track_state == "TRACK_STABLE" and track_mean is not None:
            last_stable_track_mean = track_mean

        event_active = False
        event_rows = []

    time.sleep(POLL_INTERVAL)
