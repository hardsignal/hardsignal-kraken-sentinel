#!/usr/bin/env python3

"""
Sentinel ML — Cross-Time Evaluation v0.1

Evaluates natural prospective sessions in preregistered runtime blocks.

This analysis uses only frozen-model prospective outputs.
It does not refit the behavioural model.
"""

import csv
import re
from collections import Counter
from pathlib import Path

import pandas as pd


LEDGER = Path(
    "results/ml/natural_prospective_ledger_v001.csv"
)

OUT_CSV = Path(
    "results/ml/cross_time_evaluation_v001.csv"
)

OUT_MD = Path(
    "results/ml/cross_time_evaluation_v001.md"
)

BLOCKS = {
    "A_same_runtime": {5, 6, 7},
    "B_fresh_runtime": {8, 9, 10},
    "C_fresh_runtime": {11, 12, 13},
}


def natural_number(session_id):
    match = re.match(
        r"TPMS-NATURAL-(\d+)-",
        session_id,
    )

    if not match:
        return None

    return int(match.group(1))


def load_natural_rows():
    with LEDGER.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    rows = [
        row for row in rows
        if row["session_id"].startswith(
            "TPMS-NATURAL-"
        )
    ]

    for row in rows:
        row["natural_number"] = natural_number(
            row["session_id"]
        )

        row["assigned_cluster"] = int(
            row["assigned_cluster"]
        )

        for key in [
            "nearest_distance",
            "second_nearest_distance",
            "separation_ratio",
            "distance_vs_training_max",
        ]:
            row[key] = float(row[key])

    return rows


def block_for_number(number):
    for name, numbers in BLOCKS.items():
        if number in numbers:
            return name

    return None


def main():
    rows = load_natural_rows()

    selected = []

    for row in rows:
        block = block_for_number(
            row["natural_number"]
        )

        if block is None:
            continue

        row = dict(row)
        row["block"] = block
        selected.append(row)

    expected = set().union(
        *BLOCKS.values()
    )

    observed = {
        row["natural_number"]
        for row in selected
    }

    missing = sorted(
        expected - observed
    )

    if missing:
        raise SystemExit(
            f"Missing expected natural sessions: {missing}"
        )

    df = pd.DataFrame(selected).sort_values(
        "natural_number"
    )

    detail_columns = [
        "block",
        "natural_number",
        "session_id",
        "assigned_cluster",
        "nearest_distance",
        "second_nearest_distance",
        "separation_ratio",
        "distance_vs_training_max",
        "novelty",
    ]

    df[detail_columns].to_csv(
        OUT_CSV,
        index=False,
    )

    summaries = []

    for block_name in BLOCKS:
        block = df[
            df["block"] == block_name
        ]

        counts = Counter(
            block["assigned_cluster"]
        )

        summaries.append({
            "block": block_name,
            "sessions": len(block),
            "sequence": " → ".join(
                f"C{x}"
                for x in block[
                    "assigned_cluster"
                ]
            ),
            "cluster_counts": dict(
                sorted(counts.items())
            ),
            "within": int(
                (
                    block["novelty"]
                    == "WITHIN_OBSERVED_TRAINING_RANGE"
                ).sum()
            ),
            "outside": int(
                (
                    block["novelty"]
                    == "OUTSIDE_OBSERVED_TRAINING_RANGE"
                ).sum()
            ),
            "mean_distance": float(
                block[
                    "nearest_distance"
                ].mean()
            ),
            "mean_separation": float(
                block[
                    "separation_ratio"
                ].mean()
            ),
            "mean_training_ratio": float(
                block[
                    "distance_vs_training_max"
                ].mean()
            ),
        })

    clusters_by_block = {
        block_name: set(
            df.loc[
                df["block"] == block_name,
                "assigned_cluster",
            ]
        )
        for block_name in BLOCKS
    }

    common_clusters = set.intersection(
        *clusters_by_block.values()
    )

    all_clusters = set.union(
        *clusters_by_block.values()
    )

    transitions = Counter()

    ordered = df.sort_values(
        "natural_number"
    )

    labels = ordered[
        "assigned_cluster"
    ].tolist()

    for before, after in zip(
        labels,
        labels[1:],
    ):
        transitions[
            (before, after)
        ] += 1

    lines = []

    lines.append(
        "# Sentinel ML — Cross-Time Evaluation v0.1"
    )
    lines.append("")
    lines.append(
        "Frozen behavioural model v0.1; "
        "no prospective data were used for refitting."
    )
    lines.append("")

    lines.append("## Runtime blocks")
    lines.append("")

    for summary in summaries:
        lines.append(
            f"### {summary['block']}"
        )
        lines.append("")
        lines.append(
            f"- Sessions: {summary['sessions']}"
        )
        lines.append(
            f"- Sequence: {summary['sequence']}"
        )
        lines.append(
            f"- Cluster counts: "
            f"{summary['cluster_counts']}"
        )
        lines.append(
            f"- Within training envelope: "
            f"{summary['within']}"
        )
        lines.append(
            f"- Outside training envelope: "
            f"{summary['outside']}"
        )
        lines.append(
            f"- Mean nearest distance: "
            f"{summary['mean_distance']:.4f}"
        )
        lines.append(
            f"- Mean separation ratio: "
            f"{summary['mean_separation']:.4f}"
        )
        lines.append(
            f"- Mean training-max ratio: "
            f"{summary['mean_training_ratio']:.4f}"
        )
        lines.append("")

    lines.append("## Cross-block recurrence")
    lines.append("")

    lines.append(
        "- Clusters observed in both blocks: "
        + (
            ", ".join(
                f"C{x}"
                for x in sorted(
                    common_clusters
                )
            )
            if common_clusters
            else "none"
        )
    )

    lines.append(
        "- Clusters observed overall: "
        + ", ".join(
            f"C{x}"
            for x in sorted(
                all_clusters
            )
        )
    )

    lines.append("")

    lines.append("## Session sequence")
    lines.append("")

    for _, row in ordered.iterrows():
        lines.append(
            f"- Natural {int(row['natural_number']):03d}: "
            f"C{int(row['assigned_cluster'])} | "
            f"distance={row['nearest_distance']:.4f} | "
            f"separation={row['separation_ratio']:.4f} | "
            f"training-max ratio="
            f"{row['distance_vs_training_max']:.4f} | "
            f"{row['novelty']}"
        )

    lines.append("")
    lines.append("## Observed transitions")
    lines.append("")

    for (
        before,
        after,
    ), count in sorted(
        transitions.items()
    ):
        lines.append(
            f"- C{before} → C{after}: {count}"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")

    if 1 in common_clusters:
        lines.append(
            "- Cluster 1 recurred across the runtime boundary."
        )

    if 2 not in common_clusters:
        lines.append(
            "- Cluster 2 has not yet been observed "
            "after the fresh-runtime boundary."
        )

    lines.append(
        "- The result supports cross-runtime recurrence "
        "for observed Cluster 1 behaviour."
    )

    lines.append(
        "- It does not yet demonstrate cross-runtime "
        "recurrence for every frozen behavioural regime."
    )

    lines.append(
        "- Cluster assignments describe RF/DoA behaviour, "
        "not transmitter identity."
    )

    lines.append("")

    OUT_MD.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print(
        "HARDSIGNAL LABS — "
        "CROSS-TIME EVALUATION v0.1"
    )
    print("=" * 70)

    for summary in summaries:
        print(
            f"{summary['block']}: "
            f"{summary['sequence']}"
        )

    print(
        "common_clusters="
        + ",".join(
            f"C{x}"
            for x in sorted(
                common_clusters
            )
        )
    )

    print(
        f"output_csv={OUT_CSV}"
    )
    print(
        f"output_report={OUT_MD}"
    )


if __name__ == "__main__":
    main()
