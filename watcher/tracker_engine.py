from collections import deque
from math import atan2, cos, degrees, log, radians, sin, sqrt
import statistics

from watcher.tracker_policy import (
    TRACK_MATURE_SHIFT_CONFIRM,
    TRACK_WINDOW,
    maturity_and_limits,
    shift_candidate_confirmed,
    shift_confirm_required,
    track_health_for,
)


TRACK_STABLE_SPREAD_MAX = 5.0
TRACK_SHIFTING_SPREAD_MIN = 12.0

TRACK_SHIFT_CANDIDATE_MIN_DEG = 20.0
TRACK_CANDIDATE_JOIN_MAX_DEG = 12.0


def angular_distance_deg(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def circular_summary(bearings):
    if not bearings:
        return None, None

    x = statistics.mean(cos(radians(b)) for b in bearings)
    y = statistics.mean(sin(radians(b)) for b in bearings)

    mean_bearing = degrees(atan2(y, x)) % 360.0

    circular_r = sqrt(x * x + y * y)
    circular_r = min(1.0, max(circular_r, 1e-12))

    circular_std = degrees(
        sqrt(-2.0 * log(circular_r))
    )

    return mean_bearing, circular_std


def classify_track(bearings):
    if len(bearings) < TRACK_WINDOW:
        return "INSUFFICIENT_DATA", None, None

    mean_bearing, spread = circular_summary(bearings)

    if spread <= TRACK_STABLE_SPREAD_MAX:
        state = "TRACK_STABLE"
    elif spread >= TRACK_SHIFTING_SPREAD_MIN:
        state = "TRACK_SHIFTING"
    else:
        state = "TRACK_VARIABLE"

    return state, mean_bearing, spread


class TrackerEngine:
    def __init__(self):
        self.stable_burst_bearings = deque(maxlen=TRACK_WINDOW)
        self.shift_candidate_bearings = deque(
            maxlen=TRACK_MATURE_SHIFT_CONFIRM
        )

        self.previous_track_state = "INSUFFICIENT_DATA"
        self.previous_track_health = "BUILDING"

        self.last_stable_track_mean = None

        self.track_support_bursts = 0
        self.rejected_streak = 0

    def process(self, bearing, quality):
        active_track_supported = False
        shift_confirmed = False

        shift_candidate_status = "NONE"
        shift_candidate_count = len(self.shift_candidate_bearings)

        shift_candidate_required = shift_confirm_required(
            self.track_support_bursts
        )

        if quality == "STABLE":
            active_reference = self.last_stable_track_mean

            active_established = (
                active_reference is not None
                and len(self.stable_burst_bearings) >= TRACK_WINDOW
            )

            if not active_established:
                self.stable_burst_bearings.append(bearing)
                self.shift_candidate_bearings.clear()

                shift_candidate_status = "NONE"
                shift_candidate_count = 0
                active_track_supported = True

            else:
                distance_from_track = angular_distance_deg(
                    bearing,
                    active_reference,
                )

                if distance_from_track < TRACK_SHIFT_CANDIDATE_MIN_DEG:
                    self.stable_burst_bearings.append(bearing)
                    self.shift_candidate_bearings.clear()

                    shift_candidate_status = "NONE"
                    shift_candidate_count = 0
                    active_track_supported = True

                else:
                    if self.shift_candidate_bearings:
                        candidate_mean, _ = circular_summary(
                            self.shift_candidate_bearings
                        )

                        if (
                            angular_distance_deg(
                                bearing,
                                candidate_mean,
                            )
                            > TRACK_CANDIDATE_JOIN_MAX_DEG
                        ):
                            self.shift_candidate_bearings.clear()

                    self.shift_candidate_bearings.append(bearing)

                    _, candidate_spread = circular_summary(
                        self.shift_candidate_bearings
                    )

                    shift_candidate_count = len(
                        self.shift_candidate_bearings
                    )

                    shift_candidate_status = "PENDING"

                    if shift_candidate_confirmed(
                        shift_candidate_count,
                        candidate_spread,
                        self.track_support_bursts,
                    ):
                        confirmed = list(
                            self.shift_candidate_bearings
                        )

                        self.stable_burst_bearings.clear()
                        self.stable_burst_bearings.extend(
                            confirmed[-TRACK_WINDOW:]
                        )

                        shift_candidate_status = "CONFIRMED"
                        shift_confirmed = True
                        active_track_supported = True

                        self.shift_candidate_bearings.clear()

        track_state, track_mean, track_spread = classify_track(
            self.stable_burst_bearings
        )

        track_count = len(self.stable_burst_bearings)

        if quality == "STABLE":
            self.rejected_streak = 0
        else:
            self.rejected_streak += 1

        if track_state == "TRACK_STABLE":
            if shift_confirmed:
                self.track_support_bursts = TRACK_WINDOW

            elif self.previous_track_state != "TRACK_STABLE":
                self.track_support_bursts = TRACK_WINDOW

            elif active_track_supported:
                self.track_support_bursts += 1

        elif track_state in ("TRACK_SHIFTING", "TRACK_VARIABLE"):
            self.track_support_bursts = 0

        track_maturity, _, _ = maturity_and_limits(
            self.track_support_bursts
        )

        track_health = track_health_for(
            self.track_support_bursts,
            self.rejected_streak,
        )

        result = {
            "track_state": track_state,
            "track_mean": track_mean,
            "track_spread": track_spread,
            "track_count": track_count,
            "track_health": track_health,
            "track_maturity": track_maturity,
            "track_support": self.track_support_bursts,
            "rejected_streak": self.rejected_streak,
            "shift_candidate": shift_candidate_status,
            "shift_candidate_count": shift_candidate_count,
            "shift_candidate_required": shift_candidate_required,
            "shift_confirmed": shift_confirmed,
        }

        self.previous_track_state = track_state
        self.previous_track_health = track_health

        if track_state == "TRACK_STABLE" and track_mean is not None:
            self.last_stable_track_mean = track_mean

        if track_health == "LOST":
            self.stable_burst_bearings.clear()
            self.shift_candidate_bearings.clear()

            self.track_support_bursts = 0
            self.rejected_streak = 0

            self.previous_track_state = "INSUFFICIENT_DATA"

        return result
