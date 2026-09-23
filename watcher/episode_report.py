import json
from pathlib import Path


def load_episode_events(path, session_id=None):
    path = Path(path)

    if not path.exists():
        return []

    events = []

    for line_number, line in enumerate(
        path.read_text().splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid JSONL at line {line_number}: {exc}"
            ) from exc

        if session_id is not None:
            if event.get("session_id") != session_id:
                continue

        events.append(event)

    return events


def build_episode_report(events):
    started = [
        event
        for event in events
        if event.get("event") == "EPISODE_STARTED"
    ]

    closed = [
        event
        for event in events
        if event.get("event") == "EPISODE_CLOSED"
    ]

    started_ids = {
        int(event["episode_id"])
        for event in started
    }

    closed_ids = {
        int(event["episode_id"])
        for event in closed
    }

    active_ids = sorted(started_ids - closed_ids)

    shift_closures = [
        event
        for event in closed
        if event.get("reason") == "SHIFT_CONFIRMED"
    ]

    lost_closures = [
        event
        for event in closed
        if event.get("reason") == "TRACK_LOST"
    ]

    degraded_closed = [
        event
        for event in closed
        if event.get("summary", {}).get("degraded_seen") is True
    ]

    closed_summaries = [
        {
            "episode_id": int(event["episode_id"]),
            "start_index": event["summary"]["start_index"],
            "end_index": event["summary"]["end_index"],
            "start_mean": event["summary"]["start_mean"],
            "latest_mean": event["summary"]["latest_mean"],
            "max_support": event["summary"]["max_support"],
            "degraded_seen": event["summary"]["degraded_seen"],
            "end_reason": event["summary"]["end_reason"],
        }
        for event in closed
    ]

    return {
        "event_count": len(events),
        "episodes_started": len(started),
        "episodes_closed": len(closed),
        "active_episode_ids": active_ids,
        "shift_boundaries": len(shift_closures),
        "track_losses": len(lost_closures),
        "degraded_closed_episodes": len(degraded_closed),
        "closed_episodes": closed_summaries,
    }


def format_episode_report(report):
    lines = [
        "KRAKEN RF SENTINEL — EPISODE REPORT",
        "=" * 44,
        f"events:                   {report['event_count']}",
        f"episodes started:         {report['episodes_started']}",
        f"episodes closed:          {report['episodes_closed']}",
        f"shift boundaries:         {report['shift_boundaries']}",
        f"track losses:             {report['track_losses']}",
        (
            "degraded closed episodes: "
            f"{report['degraded_closed_episodes']}"
        ),
        (
            "active episode ids:       "
            + (
                ",".join(
                    str(value)
                    for value in report["active_episode_ids"]
                )
                if report["active_episode_ids"]
                else "none"
            )
        ),
    ]

    for episode in report["closed_episodes"]:
        lines.extend(
            [
                "",
                f"Episode {episode['episode_id']}",
                (
                    f"  observations: "
                    f"{episode['start_index']}"
                    f" → {episode['end_index']}"
                ),
                (
                    f"  bearing:      "
                    f"{episode['start_mean']:.1f}°"
                    f" → {episode['latest_mean']:.1f}°"
                ),
                f"  max support:  {episode['max_support']}",
                (
                    "  degraded:     "
                    + (
                        "yes"
                        if episode["degraded_seen"]
                        else "no"
                    )
                ),
                f"  end reason:   {episode['end_reason']}",
            ]
        )

    return "\n".join(lines)
