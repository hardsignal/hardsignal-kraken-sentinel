#!/usr/bin/env python3

"""
Sentinel ML Experiment 003

Tests stability of Experiment 002's three-cluster solution under:
  1. small standardized measurement perturbations
  2. random feature subsampling

This is an exploratory robustness test, not statistical proof.
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
OUTPUT = Path("results/ml")

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
TRIALS = 1000
NOISE_SIGMA = 0.10
FEATURE_KEEP_FRACTION = 0.80
RANDOM_SEED = 42


def cluster(X):
    return AgglomerativeClustering(
        n_clusters=N_CLUSTERS,
        linkage="ward",
    ).fit_predict(X)


def align_labels(reference, candidate):
    """
    Map arbitrary candidate cluster numbers onto reference cluster numbers
    using maximum-overlap assignment.
    """
    matrix = np.zeros(
        (N_CLUSTERS, N_CLUSTERS),
        dtype=int,
    )

    for ref, cand in zip(reference, candidate):
        matrix[ref, cand] += 1

    rows, cols = linear_sum_assignment(-matrix)

    mapping = {
        candidate_label: reference_label
        for reference_label, candidate_label in zip(rows, cols)
    }

    return np.array([mapping[x] for x in candidate])


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET)

    X_raw = df[FEATURES]

    X = SimpleImputer(
        strategy="median"
    ).fit_transform(X_raw)

    X = StandardScaler().fit_transform(X)

    baseline = cluster(X)

    rng = np.random.default_rng(RANDOM_SEED)

    ari_scores = []
    retention = np.zeros(len(df), dtype=float)

    feature_count = max(
        2,
        round(len(FEATURES) * FEATURE_KEEP_FRACTION),
    )

    for _ in range(TRIALS):

        selected = np.sort(
            rng.choice(
                len(FEATURES),
                size=feature_count,
                replace=False,
            )
        )

        X_trial = X[:, selected].copy()

        noise = rng.normal(
            loc=0.0,
            scale=NOISE_SIGMA,
            size=X_trial.shape,
        )

        X_trial += noise

        labels = cluster(X_trial)

        ari_scores.append(
            adjusted_rand_score(baseline, labels)
        )

        aligned = align_labels(baseline, labels)

        retention += (aligned == baseline)

    retention /= TRIALS

    ari_scores = np.asarray(ari_scores)

    result = pd.DataFrame({
        "session_id": df["session_id"],
        "baseline_cluster": baseline,
        "membership_retention": retention,
    })

    result = result.sort_values(
        ["baseline_cluster", "membership_retention"],
        ascending=[True, True],
    )

    result.to_csv(
        OUTPUT / "experiment_003_membership_stability.csv",
        index=False,
    )

    summary = pd.DataFrame({
        "metric": [
            "trials",
            "features_total",
            "features_per_trial",
            "noise_sigma",
            "ari_mean",
            "ari_median",
            "ari_p10",
            "ari_p90",
            "ari_min",
            "ari_max",
        ],
        "value": [
            TRIALS,
            len(FEATURES),
            feature_count,
            NOISE_SIGMA,
            ari_scores.mean(),
            np.median(ari_scores),
            np.quantile(ari_scores, 0.10),
            np.quantile(ari_scores, 0.90),
            ari_scores.min(),
            ari_scores.max(),
        ],
    })

    summary.to_csv(
        OUTPUT / "experiment_003_stability_summary.csv",
        index=False,
    )

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL ML EXPERIMENT 003")
    print("=" * 70)

    print(f"sessions={len(df)}")
    print(f"trials={TRIALS}")
    print(f"features_total={len(FEATURES)}")
    print(f"features_per_trial={feature_count}")
    print(f"noise_sigma={NOISE_SIGMA}")

    print()
    print("ADJUSTED RAND INDEX")
    print(f"mean   ={ari_scores.mean():.4f}")
    print(f"median ={np.median(ari_scores):.4f}")
    print(f"p10    ={np.quantile(ari_scores, 0.10):.4f}")
    print(f"p90    ={np.quantile(ari_scores, 0.90):.4f}")
    print(f"min    ={ari_scores.min():.4f}")
    print(f"max    ={ari_scores.max():.4f}")

    print()
    print("MEMBERSHIP RETENTION")

    for _, row in result.iterrows():
        print(
            f"cluster={int(row['baseline_cluster'])} "
            f"retention={row['membership_retention']:.3f} "
            f"{row['session_id']}"
        )

    print()
    print("CLUSTER MEAN RETENTION")

    cluster_retention = (
        result.groupby("baseline_cluster")
        ["membership_retention"]
        .mean()
    )

    for cluster_id, score in cluster_retention.items():
        print(
            f"cluster={cluster_id} "
            f"mean_retention={score:.3f}"
        )

    print()
    print("outputs:")
    print("  results/ml/experiment_003_membership_stability.csv")
    print("  results/ml/experiment_003_stability_summary.csv")


if __name__ == "__main__":
    main()
