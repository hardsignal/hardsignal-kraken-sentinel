"""Deterministic interpretation of a Sentinel AI evidence bundle."""

from ai.schemas import validate_evidence_bundle


REGIME_LABELS = {
    0: "variable / multipath-heavy behavioural regime",
    1: "coherent behavioural regime",
    2: "directionally stable but weaker / broader behavioural regime",
}


def analyse_bundle(bundle):
    bundle = validate_evidence_bundle(bundle)

    core = bundle["core"]
    ml = bundle["ml"]

    bursts = core["bursts"]
    tracks = core["track_events"]

    total = bursts.get("total", 0)
    stable = bursts.get("STABLE", 0)
    multipath = bursts.get("MULTIPATH", 0)
    low_quality = bursts.get("LOW_QUALITY", 0)

    cluster = ml["assigned_cluster"]
    novelty = ml["novelty"]

    evidence = [
        f"{stable}/{total} bursts classified STABLE",
        f"{multipath}/{total} bursts classified MULTIPATH",
        f"{low_quality}/{total} bursts classified LOW_QUALITY",
        f"track acquisitions: {tracks.get('TRACK_ACQUIRED', 0)}",
        f"track degradations: {tracks.get('TRACK_DEGRADED', 0)}",
        f"track losses: {tracks.get('TRACK_LOST', 0)}",
        f"confirmed shifts: {tracks.get('TRACK_SHIFT_CONFIRMED', 0)}",
        f"nearest centroid distance: {ml['nearest_distance']:.4f}",
        f"distance/training-max ratio: {ml['distance_vs_training_max']:.4f}",
        f"novelty status: {novelty}",
    ]

    warnings = []

    if core["missing_logs"]:
        warnings.append(
            "Core summary reports missing source logs: "
            + ", ".join(core["missing_logs"])
        )

    if novelty != "WITHIN_OBSERVED_TRAINING_RANGE":
        warnings.append(
            "Session lies outside the observed training-distance envelope."
        )

    regime = REGIME_LABELS.get(
        cluster,
        "unlabelled behavioural regime",
    )

    interpretation = (
        f"Session is assigned to Cluster {cluster}, interpreted as a "
        f"{regime}. "
    )

    if novelty == "WITHIN_OBSERVED_TRAINING_RANGE":
        interpretation += (
            "Its frozen-model distance is within the observed training range."
        )
    else:
        interpretation += (
            "Its frozen-model distance is outside the observed training range, "
            "so the assignment should be treated cautiously."
        )

    return {
        "analysis_version": "0.1",
        "session_id": bundle["session_id"],
        "assigned_cluster": cluster,
        "regime_label": regime,
        "novelty": novelty,
        "evidence": evidence,
        "warnings": warnings,
        "interpretation": interpretation,
        "boundary": (
            "This is RF/DoA behavioural-regime evidence. "
            "It does not establish transmitter identity or "
            "calibration-grade absolute direction."
        ),
    }


def format_analysis(analysis):
    lines = [
        f"Session: {analysis['session_id']}",
        f"Behavioural regime: C{analysis['assigned_cluster']}",
        f"Regime description: {analysis['regime_label']}",
        f"Novelty: {analysis['novelty']}",
        "",
        "Evidence:",
    ]

    lines.extend(f"- {item}" for item in analysis["evidence"])

    if analysis["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {item}" for item in analysis["warnings"])

    lines.extend([
        "",
        "Interpretation:",
        analysis["interpretation"],
        "",
        "Boundary:",
        analysis["boundary"],
    ])

    return "\n".join(lines)
