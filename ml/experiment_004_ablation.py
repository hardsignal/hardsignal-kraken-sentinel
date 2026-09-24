#!/usr/bin/env python3

"""
Sentinel ML Experiment 004

Leave-one-feature-out ablation study.

Question:
    Does the three-cluster behavioural structure survive when each
    measurement feature is removed individually?

Outputs:
    - experiment_004_feature_ablation.csv
    - experiment_004_membership_ablation.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from scipy.optimize import linear_sum_assignment

from sklearn.cluster import AgglomerativeClustering
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler


DATASET = Path("results/ml/rf_behaviour_dataset_v001.csv")
OUT_DIR = Path("results/ml")

FEATURES = [
    "bearing_circular_std_deg",
    "peak_power_mean_db",
    "peak_power_std_db",
    "max_confidence_mean",
    "median_confidence_mean",
    "doa_width_mean_deg",
    "doa_width_std_deg",
    "median_doa_peaks_mean",
    "bearing_spread_mean_deg",
    "single_peak_ratio_mean",
    "samples_mean",
]

N_CLUSTERS = 3


def prepare(df, features):
    X = SimpleImputer(
        strategy="median"
    ).fit_transform(df[features])

    return StandardScaler().fit_transform(X)


def cluster(X):
    return AgglomerativeClustering(
        n_clusters=N_CLUSTERS,
        linkage="ward",
    ).fit_predict(X)


def align_labels(reference, candidate):
    matrix = np.zeros(
        (N_CLUSTERS, N_CLUSTERS),
        dtype=int,
    )

    for ref, cand in zip(reference, candidate):
        matrix[ref, cand] += 1

    rows, cols = linear_sum_assignment(-matrix)

    mapping = {
        cand: ref
        for ref, cand in zip(rows, cols)
    }

    return np.array([mapping[x] for x in candidate])


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET)

    baseline_X = prepare(df, FEATURES)
    baseline = cluster(baseline_X)

    summary_rows = []
    membership_rows = []

    for dropped in FEATURES:
        remaining = [
            feature
            for feature in FEATURES
            if feature != dropped
        ]

        X = prepare(df, remaining)
        labels = cluster(X)

        ari = adjusted_rand_score(
            baseline,
            labels,
        )

        aligned = align_labels(
            baseline,
            labels,
        )

        retention = (
            aligned == baseline
        ).astype(int)

        overall_retention = retention.mean()

        cluster_retention = {}

        for cluster_id in range(N_CLUSTERS):
            mask = baseline == cluster_id

            cluster_retention[cluster_id] = (
                retention[mask].mean()
                if mask.any()
                else np.nan
            )

        summary_rows.append({
            "dropped_feature": dropped,
            "remaining_features": len(remaining),
            "adjusted_rand_index": ari,
            "overall_membership_retention": overall_retention,
            "cluster_0_retention": cluster_retention[0],
            "cluster_1_retention": cluster_retention[1],
            "cluster_2_retention": cluster_retention[2],
        })

        for session_id, base, new, kept in zip(
            df["session_id"],
            baseline,
            aligned,
            retention,
        ):
            membership_rows.append({
                "dropped_feature": dropped,
                "session_id": session_id,
                "baseline_cluster": int(base),
                "ablation_cluster": int(new),
                "membership_retained": bool(kept),
            })

    summary = pd.DataFrame(summary_rows)

    summary = summary.sort_values(
        "adjusted_rand_index",
        ascending=True,
    )

    membership = pd.DataFrame(
        membership_rows
    )

    summary.to_csv(
        OUT_DIR / "experiment_004_feature_ablation.csv",
        index=False,
    )

    membership.to_csv(
        OUT_DIR / "experiment_004_membership_ablation.csv",
        index=False,
    )

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL ML EXPERIMENT 004")
    print("=" * 70)

    print(f"sessions={len(df)}")
    print(f"baseline_features={len(FEATURES)}")
    print(f"clusters={N_CLUSTERS}")

    print()
    print("LEAVE-ONE-FEATURE-OUT RESULTS")
    print()

    for _, row in summary.iterrows():
        print(
            f"drop={row['dropped_feature']:30} "
            f"ARI={row['adjusted_rand_index']:.4f} "
            f"retention={row['overall_membership_retention']:.3f} "
            f"C0={row['cluster_0_retention']:.3f} "
            f"C1={row['cluster_1_retention']:.3f} "
            f"C2={row['cluster_2_retention']:.3f}"
        )

    print()
    print("MOST SENSITIVE FEATURE")

    worst = summary.iloc[0]

    print(
        f"{worst['dropped_feature']} "
        f"ARI={worst['adjusted_rand_index']:.4f}"
    )

    print()
    print("MOST ROBUST REMOVAL")

    best = summary.iloc[-1]

    print(
        f"{best['dropped_feature']} "
        f"ARI={best['adjusted_rand_index']:.4f}"
    )

    print()
    print("SESSION INSTABILITY")

    instability = (
        membership
        .groupby("session_id")
        ["membership_retained"]
        .mean()
        .sort_values()
    )

    for session_id, score in instability.items():
        print(
            f"retention={score:.3f} "
            f"{session_id}"
        )

    print()
    print("outputs:")
    print("  results/ml/experiment_004_feature_ablation.csv")
    print("  results/ml/experiment_004_membership_ablation.csv")


if __name__ == "__main__":
    main()
