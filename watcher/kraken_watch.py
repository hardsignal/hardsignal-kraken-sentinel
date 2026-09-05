import csv
import time
import statistics
from math import sin, cos, atan2, radians, degrees
from datetime import datetime
from pathlib import Path

from kraken_project import (
    PROJECT_LAB,
    PROJECT_NAME,
    PROJECT_PHASE,
    INSTRUMENT,
)

LOG_PATH = Path.home() / "kraken_bursts.log"
CSV_PATH = Path.home() / "krakensdr_doa" / "mydata.csv"

POWER_THRESHOLD = -45.0
POLL_INTERVAL = 1.0
EVENT_GAP = 3.0

last_size = None
event_rows = []
last_event_time = None
event_active = False


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

        powers = [r[1] for r in event_rows]
        peak_power = max(powers)

        confidences = [r[2] for r in event_rows]
        max_confidence = max(confidences)

        frequencies = [r[3] for r in event_rows]
        mean_frequency = statistics.mean(frequencies)

        doa_widths = [r[4] for r in event_rows]
        median_doa_width = statistics.median(doa_widths)

        doa_peaks = [r[5] for r in event_rows]
        median_doa_peaks = statistics.median(doa_peaks)

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
                f"samples={len(event_rows)}\n"
            )

        event_active = False
        event_rows = []

    time.sleep(POLL_INTERVAL)
