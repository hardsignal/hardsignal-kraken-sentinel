"""Deterministic historical comparison reporting for Sentinel AI v0.2."""

from ai.history import build_history_bundle


FEATURE_LABELS = {
    "bearing_circular_std_deg": "bearing circular std",
    "peak_power_mean_db": "peak power mean",
    "median_confidence_mean": "median confidence",
    "doa_width_mean_deg": "DoA width mean",
    "single_peak_ratio_mean": "single-peak ratio mean",
    "burst_count": "burst count",
}


def build_history_report(
    target_session_id,
    *,
    results_dir="results/ml/prospective",
):
    history = build_history_bundle(
        target_session_id,
        results_dir=results_dir,
    )

    lines = [
        f"Target session: {history['target_session_id']}",
        f"Target cluster: C{history['target_cluster']}",
        f"Target novelty: {history['target_novelty']}",
        "",
        "Historical scope:",
        (
            f"- prior formal sessions: "
            f"{history['prior_formal_session_count']}"
        ),
        (
            f"- total formal prospective sessions available: "
            f"{history['formal_session_count_total']}"
        ),
        "- excluded formal-number record: 014",
        "",
        "Prior cluster counts:",
    ]

    if history["prior_cluster_counts"]:
        for cluster, count in sorted(
            history["prior_cluster_counts"].items(),
            key=lambda item: int(item[0]),
        ):
            lines.append(f"- C{cluster}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "Nearest prior sessions:",
    ])

    if history["nearest_prior_sessions"]:
        for item in history["nearest_prior_sessions"]:
            lines.append(
                f"- {item['session_id']}: "
                f"C{item['cluster']}, "
                f"{item['novelty']}, "
                f"normalized feature distance="
                f"{item['normalized_feature_distance']:.6f}"
            )
    else:
        lines.append("- none")

    lines.extend([
        "",
        "Target vs prior same-cluster mean:",
    ])

    deltas = history["target_vs_same_cluster_prior_mean"]

    if deltas:
        for feature in FEATURE_LABELS:
            value = deltas[feature]
            lines.append(
                f"- {FEATURE_LABELS[feature]}: {value:+.6f}"
            )
    else:
        lines.append("- unavailable; no prior same-cluster sessions")

    return {
        "history": history,
        "text": "\n".join(lines),
    }
