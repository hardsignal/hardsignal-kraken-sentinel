TRACK_WINDOW = 5
TRACK_MATURE_BURSTS = 20

TRACK_DEGRADE_REJECTS = 3
TRACK_LOST_REJECTS = 5

TRACK_MATURE_DEGRADE_REJECTS = 5
TRACK_MATURE_LOST_REJECTS = 8

TRACK_ESTABLISHED_SHIFT_CONFIRM = 5
TRACK_MATURE_SHIFT_CONFIRM = 7

TRACK_CANDIDATE_SPREAD_MAX = 5.0


def maturity_and_limits(track_support_bursts):
    if track_support_bursts >= TRACK_MATURE_BURSTS:
        return (
            "MATURE",
            TRACK_MATURE_DEGRADE_REJECTS,
            TRACK_MATURE_LOST_REJECTS,
        )

    if track_support_bursts >= TRACK_WINDOW:
        return (
            "ESTABLISHED",
            TRACK_DEGRADE_REJECTS,
            TRACK_LOST_REJECTS,
        )

    return (
        "BUILDING",
        TRACK_DEGRADE_REJECTS,
        TRACK_LOST_REJECTS,
    )


def track_health_for(track_support_bursts, rejected_streak):
    maturity, degrade_limit, lost_limit = maturity_and_limits(
        track_support_bursts
    )

    # A track that has never been established cannot be degraded/lost.
    if track_support_bursts < TRACK_WINDOW:
        return "BUILDING"

    if rejected_streak >= lost_limit:
        return "LOST"

    if rejected_streak >= degrade_limit:
        return "DEGRADED"

    return "HEALTHY"


def shift_confirm_required(track_support_bursts):
    if track_support_bursts >= TRACK_MATURE_BURSTS:
        return TRACK_MATURE_SHIFT_CONFIRM

    return TRACK_ESTABLISHED_SHIFT_CONFIRM


def shift_candidate_confirmed(
    candidate_count,
    candidate_spread,
    track_support_bursts,
):
    required = shift_confirm_required(track_support_bursts)

    return (
        candidate_count >= required
        and candidate_spread <= TRACK_CANDIDATE_SPREAD_MAX
    )
