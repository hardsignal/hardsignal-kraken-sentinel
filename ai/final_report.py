"""Compose a Sentinel AI report from authoritative evidence."""

from ai.analyst import analyse_bundle


def compose_final_report(bundle, experiment):
    analysis = analyse_bundle(bundle)

    lines = [
        "**Summary**",
        (
            f"Session {analysis['session_id']} is assigned to "
            f"Cluster {analysis['assigned_cluster']} "
            f"({analysis['regime_label']}). "
            f"Novelty status: {analysis['novelty']}."
        ),
        "",
        "**Evidence**",
    ]

    lines.extend(
        f"- {item}"
        for item in analysis["evidence"]
    )

    lines.extend([
        "",
        "**Interpretation**",
        analysis["interpretation"],
        "",
        "**Uncertainty**",
    ])

    if analysis["warnings"]:
        lines.extend(
            f"- {item}"
            for item in analysis["warnings"]
        )
    else:
        lines.append(
            "No additional deterministic warning was raised. "
            "The evidence remains limited to RF/DoA behavioural-regime "
            "analysis."
        )

    lines.extend([
        "",
        "**Next controlled experiment**",
        experiment.strip(),
        "",
        "**Scientific boundary**",
        analysis["boundary"],
    ])

    return "\n".join(lines)
