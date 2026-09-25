"""Deterministic cross-session history for Sentinel AI v0.2."""

import json
import math
import re
from pathlib import Path


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

SESSION_NUMBER_RE = re.compile(
    r"^TPMS-NATURAL-(\d+)-"
)


def session_number(session_id):
    match = SESSION_NUMBER_RE.match(session_id)

    if not match:
        raise ValueError(
            f"unsupported natural session id: {session_id}"
        )

    return int(match.group(1))


def load_formal_history(
    results_dir=Path("results/ml/prospective"),
):
    records = []

    for path in sorted(
        Path(results_dir).glob("TPMS-NATURAL-*.json")
    ):
        record = json.loads(
            path.read_text(encoding="utf-8")
        )

        number = session_number(record["session_id"])

        if number not in FORMAL_SESSION_NUMBERS:
            continue

        records.append(record)

    return records


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
):
    records = load_formal_history(results_dir)

    by_id = {
        record["session_id"]: record
        for record in records
    }

    if target_session_id not in by_id:
        raise ValueError(
            "target session is not in the formal prospective set"
        )

    target = by_id[target_session_id]
    target_number = session_number(target_session_id)

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
        "target_session_id": target_session_id,
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
