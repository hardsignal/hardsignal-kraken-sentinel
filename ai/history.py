"""Deterministic cross-session history for Sentinel AI v0.2."""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import math
import re
from pathlib import Path
from types import MappingProxyType

from ai.artifact import canonical_sha256


FORMAL_SESSION_NUMBERS = {
    5, 6, 7,
    8, 9, 10,
    11, 12, 13,
    15, 16, 17,
}

HISTORY_FEATURES = (
    "bearing_circular_std_deg",
    "peak_power_mean_db",
    "median_confidence_mean",
    "doa_width_mean_deg",
    "single_peak_ratio_mean",
    "burst_count",
)

SESSION_NUMBER_RE = re.compile(r"^TPMS-NATURAL-([0-9]+)-")
SESSION_ID_RE = re.compile(r"TPMS-NATURAL-([0-9]{3})-([0-9]{8}-[0-9]{6})")


def session_number(session_id):
    match = SESSION_ID_RE.fullmatch(session_id) if isinstance(session_id, str) else None

    if not match:
        raise ValueError(
            f"unsupported natural session id: {session_id}"
        )

    datetime.strptime(match.group(2), "%Y%m%d-%H%M%S")
    return int(match.group(1))


def _read_formal_sources(results_dir, through_session_number):
    sources = []
    for path in sorted(Path(results_dir).glob("TPMS-NATURAL-*.json")):
        # Filter filenames before opening any future or excluded source bytes.
        prefix = SESSION_NUMBER_RE.match(path.stem)
        if prefix is None:
            raise ValueError(f"malformed natural session filename: {path.name}")
        number = int(prefix.group(1))
        if through_session_number is not None and number > through_session_number:
            continue
        if number not in FORMAL_SESSION_NUMBERS:
            continue
        session_number(path.stem)
        sources.append((path.stem, path.read_bytes()))
    return tuple(sources)


def _parse_formal_sources(sources, through_session_number):
    records = []
    seen_numbers = set()
    for filename_id, data in sources:
        number = session_number(filename_id)
        if number not in FORMAL_SESSION_NUMBERS or (
            through_session_number is not None and number > through_session_number
        ):
            raise ValueError("non-formal or future source in history snapshot")
        record = json.loads(data.decode("utf-8"))
        if not isinstance(record, dict):
            raise ValueError(f"historical record must be a JSON object: {filename_id}.json")
        identity = record.get("session_id")
        session_number(identity)
        if identity != filename_id:
            raise ValueError(f"filename/session_id mismatch: {filename_id}.json")
        if number in seen_numbers:
            raise ValueError(f"duplicate formal session identity: {number:03d}")
        seen_numbers.add(number)
        records.append(record)

    # Completeness follows validation of every consumed identity.
    if through_session_number in FORMAL_SESSION_NUMBERS:
        if through_session_number not in seen_numbers:
            raise ValueError("target session is not in the formal prospective set")
        expected = {n for n in FORMAL_SESSION_NUMBERS if n <= through_session_number}
        missing = sorted(expected - seen_numbers)
        if missing:
            raise ValueError(
                "incomplete formal session prefix; missing required sessions: "
                + ", ".join(f"{number:03d}" for number in missing)
            )
    return records


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class HistoryEvidenceSnapshot:
    """Validated, deeply immutable records and the exact bytes they came from.

    This is an in-memory capture, not an atomic filesystem transaction across
    files. Subsequent disk changes cannot alter any of its derived outputs.
    """

    target_session_id: str
    sources: tuple
    records: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        # Copy mutable input containers; bytes themselves are immutable.
        sources = tuple((identity, bytes(data)) for identity, data in self.sources)
        records = _parse_formal_sources(sources, session_number(self.target_session_id))
        if not any(record["session_id"] == self.target_session_id for record in records):
            raise ValueError("target session is not in the formal prospective set")
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "records", tuple(_freeze(record) for record in records))

    @property
    def source_record_sha256(self):
        return {identity: hashlib.sha256(data).hexdigest() for identity, data in self.sources}

    @property
    def source_record_manifest_sha256(self):
        return canonical_sha256(self.source_record_sha256)


def load_history_snapshot(target_session_id, *, results_dir=Path("results/ml/prospective")):
    return HistoryEvidenceSnapshot(
        target_session_id,
        _read_formal_sources(results_dir, session_number(target_session_id)),
    )


def load_formal_history(results_dir=Path("results/ml/prospective"), *, through_session_number=None):
    """Compatibility loader using the same byte parsing and membership checks."""
    return _parse_formal_sources(
        _read_formal_sources(results_dir, through_session_number), through_session_number,
    )


def require_history_snapshot(snapshot, target_session_id):
    if not isinstance(snapshot, HistoryEvidenceSnapshot):
        raise ValueError("history evidence snapshot is required")
    if snapshot.target_session_id != target_session_id:
        raise ValueError("history snapshot target_session_id mismatch")
    return snapshot


def _mean(values):
    return sum(values) / len(values)


def _population_std(values):
    if not values:
        raise ValueError("cannot calculate std of empty data")

    mean = _mean(values)

    return math.sqrt(
        sum((value - mean) ** 2 for value in values)
        / len(values)
    )


def _feature_distance(target, candidate, scales):
    total = 0.0
    used = 0

    for feature in HISTORY_FEATURES:
        scale = scales[feature]

        if scale == 0:
            continue

        delta = (
            target["feature_row"][feature]
            - candidate["feature_row"][feature]
        ) / scale

        total += delta * delta
        used += 1

    if used == 0:
        return 0.0

    return math.sqrt(total / used)


def build_history_bundle(
    target_session_id,
    *,
    results_dir=Path("results/ml/prospective"),
    snapshot=None,
):
    if snapshot is None:
        snapshot = load_history_snapshot(target_session_id, results_dir=results_dir)
    snapshot = require_history_snapshot(snapshot, target_session_id)
    target_number = session_number(target_session_id)
    records = snapshot.records

    by_id = {
        record["session_id"]: record
        for record in records
    }

    if target_session_id not in by_id:
        raise ValueError(
            "target session is not in the formal prospective set"
        )

    target = by_id[target_session_id]

    prior = [
        record
        for record in records
        if session_number(record["session_id"]) < target_number
    ]

    same_cluster = [
        record
        for record in prior
        if record["assigned_cluster"]
        == target["assigned_cluster"]
    ]

    scales = {}

    for feature in HISTORY_FEATURES:
        values = [
            record["feature_row"][feature]
            for record in prior
        ]

        scales[feature] = (
            _population_std(values)
            if values
            else 0.0
        )

    nearest = sorted(
        prior,
        key=lambda record: _feature_distance(
            target,
            record,
            scales,
        ),
    )[:3]

    same_cluster_feature_means = {}

    if same_cluster:
        for feature in HISTORY_FEATURES:
            same_cluster_feature_means[feature] = _mean([
                record["feature_row"][feature]
                for record in same_cluster
            ])

    deltas = {
        feature: (
            target["feature_row"][feature]
            - same_cluster_feature_means[feature]
        )
        for feature in HISTORY_FEATURES
    } if same_cluster_feature_means else {}

    prior_cluster_counts = {}

    for record in prior:
        cluster = str(record["assigned_cluster"])
        prior_cluster_counts[cluster] = (
            prior_cluster_counts.get(cluster, 0) + 1
        )

    return {
        "history_version": "0.1",
        "source_record_manifest_sha256": snapshot.source_record_manifest_sha256,
        "target_session_id": target_session_id,
        # Available formal records through the target, including the target.
        "formal_session_count_total": len(records),
        "prior_formal_session_count": len(prior),
        "excluded_session_numbers": [14],
        "target_cluster": target["assigned_cluster"],
        "target_novelty": target["novelty"],
        "prior_cluster_counts": prior_cluster_counts,
        "same_cluster_prior_count": len(same_cluster),
        "same_cluster_prior_feature_means": (
            same_cluster_feature_means
        ),
        "target_vs_same_cluster_prior_mean": deltas,
        "nearest_prior_sessions": [
            {
                "session_id": record["session_id"],
                "cluster": record["assigned_cluster"],
                "novelty": record["novelty"],
                "normalized_feature_distance": round(
                    _feature_distance(
                        target,
                        record,
                        scales,
                    ),
                    6,
                ),
            }
            for record in nearest
        ],
    }
