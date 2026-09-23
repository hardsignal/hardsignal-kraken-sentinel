"""Offline, session-scoped summaries of the three Sentinel logs.

Blank lines, session markers and records without session IDs are excluded.
Malformed syntax fails even outside the selected session; missing files count as empty
and are listed explicitly in the report. Only fields used by the report are
schema-validated, so additional log fields remain compatible.
"""

import json
import math
from pathlib import Path

if __package__:
    from watcher.episode_report import build_episode_report
else:
    from episode_report import build_episode_report


QUALITIES = ("STABLE", "MULTIPATH", "LOW_QUALITY")
TRACK_EVENTS = (
    "TRACK_ACQUIRED", "TRACK_REACQUIRED", "TRACK_SHIFT_CONFIRMED",
    "TRACK_DEGRADED", "TRACK_LOST", "TRACK_RECOVERED",
)


def _pairs(fields):
    record = {}
    for key, value in fields:
        if not key or key in record:
            raise ValueError(f"empty or duplicate field: {key!r}")
        record[key] = value
    return record


def _parse_fields(line):
    fields = []
    for field in line.split(","):
        if "=" not in field:
            raise ValueError(f"expected key=value, got {field!r}")
        key, value = field.split("=", 1)
        fields.append((key.strip(), value.strip()))
    return _pairs(fields)


def _reject_constant(value):
    raise ValueError(f"non-finite JSON value: {value}")


def _validate_episode(record):
    if record.get("event") not in ("EPISODE_STARTED", "EPISODE_CLOSED"):
        raise ValueError("unsupported or missing episode event")
    if type(record.get("episode_id")) is not int:
        raise ValueError("episode_id must be an integer")
    if record["event"] == "EPISODE_CLOSED":
        summary = record.get("summary")
        if not isinstance(summary, dict):
            raise ValueError("closed episode summary must be an object")
        for key in ("start_index", "end_index", "max_support"):
            if type(summary.get(key)) is not int:
                raise ValueError(f"summary.{key} must be an integer")
        for key in ("start_mean", "latest_mean"):
            value = summary.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"summary.{key} must be a finite number")
        if type(summary.get("degraded_seen")) is not bool:
            raise ValueError("summary.degraded_seen must be a boolean")
        for label, value in (("reason", record.get("reason")),
                             ("summary.end_reason", summary.get("end_reason"))):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be a nonempty string")


def _load(path, session_id, kind, missing_logs):
    path = Path(path).expanduser()
    try:
        source = path.open(encoding="utf-8")
    except FileNotFoundError:
        missing_logs.append(str(path))
        return []
    records = []
    with source:
        for number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                if kind == "episodes":
                    record = json.loads(line, object_pairs_hook=_pairs,
                                        parse_constant=_reject_constant)
                    if not isinstance(record, dict):
                        raise ValueError("episode event must be an object")
                    _validate_episode(record)
                else:
                    if line.startswith("SESSION_START |"):
                        marker = _parse_fields(",".join(line.strip().split(" | ")[1:]))
                        if not marker.get("id") or not marker.get("time"):
                            raise ValueError("session marker requires id and time")
                        continue
                    record = _parse_fields(line.strip())
                # Legacy unscoped records cannot belong to the requested session.
                if "session_id" not in record:
                    if kind == "episodes":
                        raise ValueError("missing session_id")
                    continue
                if not isinstance(record["session_id"], str) or not record["session_id"]:
                    raise ValueError("session_id must be a nonempty string")
                if record["session_id"] != session_id:
                    continue
                if kind == "bursts" and record.get("quality") not in QUALITIES:
                    raise ValueError("unsupported or missing burst quality")
                if kind == "track" and not record.get("event"):
                    raise ValueError("missing track event")
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"{path}: line {number}: {exc}") from exc
            if record["session_id"] == session_id:
                records.append(record)
    return records


def build_session_summary(session_id, *, bursts_log, track_log, episode_log):
    """Read logs without RF dependencies and return a JSON-serializable report."""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be a nonempty string")
    missing = []
    bursts = _load(bursts_log, session_id, "bursts", missing)
    tracks = _load(track_log, session_id, "track", missing)
    episodes = _load(episode_log, session_id, "episodes", missing)
    return {
        "version": 1,
        "session_id": session_id,
        "missing_logs": missing,
        "bursts": {
            "total": len(bursts),
            **{quality: sum(row["quality"] == quality for row in bursts)
               for quality in QUALITIES},
        },
        "track_events": {
            event: sum(row["event"] == event for row in tracks)
            for event in TRACK_EVENTS
        },
        "episodes": build_episode_report(episodes),
    }


def format_session_summary(report):
    bursts, tracks, episodes = (report[key] for key in
                                ("bursts", "track_events", "episodes"))
    active = ", ".join(map(str, episodes["active_episode_ids"])) or "none"
    lines = [
        "KRAKEN RF SENTINEL — SESSION SUMMARY",
        f"session: {report['session_id']}", "", "BURSTS",
        f"total: {bursts['total']}", f"stable: {bursts['STABLE']}",
        f"multipath: {bursts['MULTIPATH']}",
        f"low quality: {bursts['LOW_QUALITY']}", "", "TRACK EVENTS",
    ]
    labels = ("acquired", "reacquired", "shifts confirmed", "degraded", "lost", "recovered")
    lines.extend(f"{label}: {tracks[event]}" for label, event in zip(labels, TRACK_EVENTS))
    lines.extend([
        "", "EPISODES", f"started: {episodes['episodes_started']}",
        f"closed: {episodes['episodes_closed']}", f"active: {active}",
        f"shift boundaries: {episodes['shift_boundaries']}",
        f"track losses: {episodes['track_losses']}",
        f"degraded closed episodes: {episodes['degraded_closed_episodes']}",
    ])
    if report["missing_logs"]:
        lines.extend(["", "Missing logs (counted as empty):", *report["missing_logs"]])
    return "\n".join(lines)
