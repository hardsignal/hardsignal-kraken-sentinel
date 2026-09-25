#!/usr/bin/env python3

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


DEFAULT_LEDGER = Path(
    "results/ml/natural_prospective_ledger_v001.csv"
)

DEFAULT_OUTPUT = Path(
    "results/ml/natural_prospective_report_v001.md"
)


def load_rows(path):
    with Path(path).open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return list(csv.DictReader(handle))


def build_report(rows):
    clusters = Counter(
        int(row["assigned_cluster"])
        for row in rows
    )

    novelty = Counter(
        row["novelty"]
        for row in rows
    )

    transitions = Counter()

    for previous, current in zip(
        rows,
        rows[1:],
    ):
        key = (
            int(previous["assigned_cluster"]),
            int(current["assigned_cluster"]),
        )
        transitions[key] += 1

    lines = []

    lines.append(
        "# Sentinel ML — Natural Prospective Validation"
    )
    lines.append("")

    lines.append(
        "Frozen behavioural model v0.1; "
        "no prospective session is used for refitting."
    )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Natural prospective sessions: {len(rows)}"
    )

    for cluster_id in sorted(clusters):
        lines.append(
            f"- Cluster {cluster_id}: "
            f"{clusters[cluster_id]} sessions"
        )

    lines.append(
        "- Within training envelope: "
        f"{novelty['WITHIN_OBSERVED_TRAINING_RANGE']}"
    )

    lines.append(
        "- Outside training envelope: "
        f"{novelty['OUTSIDE_OBSERVED_TRAINING_RANGE']}"
    )

    lines.append("")
    lines.append("## Sessions")
    lines.append("")

    lines.append(
        "| Session | Cluster | Distance | "
        "Separation | Training-max ratio | Novelty |"
    )

    lines.append(
        "|---|---:|---:|---:|---:|---|"
    )

    for row in rows:
        lines.append(
            f"| {row['session_id']} "
            f"| {row['assigned_cluster']} "
            f"| {float(row['nearest_distance']):.4f} "
            f"| {float(row['separation_ratio']):.4f} "
            f"| {float(row['distance_vs_training_max']):.4f} "
            f"| {row['novelty']} |"
        )

    lines.append("")
    lines.append("## Observed cluster transitions")
    lines.append("")

    if transitions:
        for (
            previous_cluster,
            current_cluster,
        ), count in sorted(
            transitions.items()
        ):
            lines.append(
                f"- C{previous_cluster} → "
                f"C{current_cluster}: {count}"
            )
    else:
        lines.append(
            "- Not enough sessions for transitions."
        )

    lines.append("")
    lines.append("## Interpretation constraints")
    lines.append("")
    lines.append(
        "- Cluster assignment describes RF/DoA behaviour, "
        "not transmitter identity."
    )
    lines.append(
        "- Outside-range observations are nearest-regime "
        "assignments, not confirmed members of that regime."
    )
    lines.append(
        "- Same-runtime recurrence is not equivalent to "
        "cross-time or cross-runtime generalization."
    )
    lines.append(
        "- The frozen model must not be refit during this "
        "prospective validation phase."
    )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ledger",
        default=str(DEFAULT_LEDGER),
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
    )

    args = parser.parse_args()

    rows = load_rows(args.ledger)

    if not rows:
        raise SystemExit(
            "Prospective ledger contains no sessions."
        )

    report = build_report(rows)

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        report + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print(
        "HARDSIGNAL LABS — "
        "NATURAL PROSPECTIVE REPORT"
    )
    print("=" * 70)

    print(f"sessions={len(rows)}")

    for cluster_id, count in sorted(
        Counter(
            int(row["assigned_cluster"])
            for row in rows
        ).items()
    ):
        print(
            f"cluster={cluster_id} "
            f"sessions={count}"
        )

    print(
        "outside_training_range="
        f"{sum(
            row['novelty']
            == 'OUTSIDE_OBSERVED_TRAINING_RANGE'
            for row in rows
        )}"
    )

    print(f"output={output}")


if __name__ == "__main__":
    main()
