import json


EPISODE_SUMMARY_VERSION = 1
EPISODE_EVENT_VERSION = 1

REQUIRED_FIELDS = (
    "episode_id",
    "status",
    "start_index",
    "end_index",
    "end_reason",
    "start_mean",
    "latest_mean",
    "max_support",
    "degraded_seen",
)


def build_episode_summary(episode):
    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in episode
    ]

    if missing:
        raise ValueError(
            "missing episode fields: " + ", ".join(missing)
        )

    return {
        "version": EPISODE_SUMMARY_VERSION,
        "episode_id": int(episode["episode_id"]),
        "status": episode["status"],
        "start_index": int(episode["start_index"]),
        "end_index": (
            None
            if episode["end_index"] is None
            else int(episode["end_index"])
        ),
        "end_reason": episode["end_reason"],
        "start_mean": round(float(episode["start_mean"]), 1),
        "latest_mean": round(float(episode["latest_mean"]), 1),
        "max_support": int(episode["max_support"]),
        "degraded_seen": bool(episode["degraded_seen"]),
    }


def episode_summary_json(episode):
    return json.dumps(
        build_episode_summary(episode),
        sort_keys=True,
        separators=(",", ":"),
    )


def build_episode_event_record(
    event,
    episode,
    *,
    session_id,
    timestamp,
    project_name,
):
    event_name = event.get("event")

    if event_name not in (
        "EPISODE_STARTED",
        "EPISODE_CLOSED",
    ):
        raise ValueError(
            "unsupported episode event: "
            + str(event_name)
        )

    return {
        "version": EPISODE_EVENT_VERSION,
        "timestamp": timestamp,
        "project": project_name,
        "session_id": session_id,
        "event": event_name,
        "episode_id": int(event["episode_id"]),
        "observation_index": int(
            event["observation_index"]
        ),
        "reason": event.get("reason"),
        "summary": build_episode_summary(episode),
    }


def episode_event_json(
    event,
    episode,
    *,
    session_id,
    timestamp,
    project_name,
):
    return json.dumps(
        build_episode_event_record(
            event,
            episode,
            session_id=session_id,
            timestamp=timestamp,
            project_name=project_name,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
