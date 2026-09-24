#!/usr/bin/env python3

"""
Sentinel ML Experiment 005

Leave-one-feature-family-out robustness study.
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
OUT = Path("results/ml")

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

FAMILIES = {
    "bearing_dynamics": [
        "bearing_circular_std_deg",
        "bearing_spread_mean_deg",
    ],

    "power": [
        "peak_power_mean_db",
        "peak_power_std_db",
    ],

    "confidence": [
        "max_confidence_mean",
        "median_confidence_mean",
    ],

    "doa_width": [
        "doa_width_mean_deg",
        "doa_width_std_deg",
    ],

    "peak_structure": [
        "median_doa_peaks_mean",
        "single_peak_ratio_mean",
    ],

    "sampling": [
        "samples_mean",
    ],
}

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


def align(reference, candidate):
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

    return np.array([
        mapping[label]
        for label in candidate
    ])


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET)

    baseline = cluster(
        prepare(df, FEATURES)
    )

    summary_rows = []
    membership_rows = []

    for family, dropped_features in FAMILIES.items():

        remaining = [
            feature
            for feature in FEATURES
            if feature not in dropped_features
        ]

        candidate = cluster(
            prepare(df, remaining)
        )

        ari = adjusted_rand_score(
            baseline,
            candidate,
        )

        aligned = align(
            baseline,
            candidate,
        )

        retained = (
            aligned == baseline
        ).astype(int)

        cluster_scores = {}

        for cluster_id in range(N_CLUSTERS):
            mask = baseline == cluster_id

            cluster_scores[cluster_id] = (
                retained[mask].mean()
                if mask.any()
                else np.nan
            )

        summary_rows.append({
            "dropped_family": family,
            "dropped_features": "|".join(dropped_features),
            "remaining_features": len(remaining),
            "adjusted_rand_index": ari,
            "overall_retention": retained.mean(),
            "cluster_0_retention": cluster_scores[0],
            "cluster_1_retention": cluster_scores[1],
            "cluster_2_retention": cluster_scores[2],
        })

        for session_id, base, new, kept in zip(
            df["session_id"],
            baseline,
            aligned,
            retained,
        ):
            membership_rows.append({
                "dropped_family": family,
                "session_id": session_id,
                "baseline_cluster": int(base),
                "ablation_cluster": int(new),
                "membership_retained": bool(kept),
            })

    summary = pd.DataFrame(summary_rows).sort_values(
        "adjusted_rand_index"
    )

    membership = pd.DataFrame(membership_rows)

    summary.to_csv(
        OUT / "experiment_005_family_ablation.csv",
        index=False,
    )

    membership.to_csv(
        OUT / "experiment_005_family_membership.csv",
        index=False,
    )

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL ML EXPERIMENT 005")
    print("=" * 70)

    for _, row in summary.iterrows():
        print(
            f"drop={row['dropped_family']:18} "
            f"ARI={row['adjusted_rand_index']:.4f} "
            f"retention={row['overall_retention']:.3f} "
            f"C0={row['cluster_0_retention']:.3f} "
            f"C1={row['cluster_1_retention']:.3f} "
            f"C2={row['cluster_2_retention']:.3f}"
        )

    print()
    print("SESSION RETENTION")

    stability = (
        membership
        .groupby("session_id")
        ["membership_retained"]
        .mean()
        .sort_values()
    )

    for session_id, score in stability.items():
        print(
            f"retention={score:.3f} "
            f"{session_id}"
        )


if __name__ == "__main__":
    main()
