#!/usr/bin/env python3
"""
Kraken RF Sentinel ML Experiment 001

Goal:
    Explore session-level RF/DoA behavioural structure.

Methods:
    - median imputation
    - StandardScaler
    - PCA for visualization
    - Agglomerative clustering in standardized feature space
    - silhouette-based exploratory cluster-count selection
    - Isolation Forest anomaly detection

This experiment does NOT establish device identity.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


DATASET = Path("results/ml/rf_behaviour_dataset_v001.csv")
OUT_DIR = Path("results/ml")

FEATURES = [
    "stable_ratio",
    "multipath_ratio",

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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET)

    if len(df) < 5:
        raise SystemExit("Need at least 5 sessions for Experiment 001.")

    missing = [column for column in FEATURES if column not in df.columns]
    if missing:
        raise SystemExit(f"Missing required features: {missing}")

    X_raw = df[FEATURES]

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_imputed = imputer.fit_transform(X_raw)
    X = scaler.fit_transform(X_imputed)

    # ---------------------------------------------------------
    # Select exploratory cluster count using silhouette score.
    # ---------------------------------------------------------
    silhouette_results = []

    max_k = min(5, len(df) - 1)

    for k in range(2, max_k + 1):
        model = AgglomerativeClustering(
            n_clusters=k,
            linkage="ward",
        )

        labels = model.fit_predict(X)
        score = silhouette_score(X, labels)

        silhouette_results.append({
            "k": k,
            "silhouette": score,
        })

    silhouette_df = pd.DataFrame(silhouette_results)

    best_row = silhouette_df.loc[
        silhouette_df["silhouette"].idxmax()
    ]

    best_k = int(best_row["k"])
    best_score = float(best_row["silhouette"])

    cluster_model = AgglomerativeClustering(
        n_clusters=best_k,
        linkage="ward",
    )

    clusters = cluster_model.fit_predict(X)

    # ---------------------------------------------------------
    # PCA — visualization only.
    # Clustering is performed in full standardized space.
    # ---------------------------------------------------------
    pca = PCA(n_components=2)
    points = pca.fit_transform(X)

    # ---------------------------------------------------------
    # Isolation Forest.
    # Higher exported anomaly_score = more unusual.
    # ---------------------------------------------------------
    detector = IsolationForest(
        n_estimators=500,
        contamination="auto",
        random_state=42,
    )

    detector.fit(X)

    prediction = detector.predict(X)
    decision = detector.decision_function(X)

    anomaly_score = -decision
    is_anomaly = prediction == -1

    # ---------------------------------------------------------
    # Session assignments.
    # ---------------------------------------------------------
    assignments = pd.DataFrame({
        "point_id": range(1, len(df) + 1),
        "session_id": df["session_id"],
        "pc1": points[:, 0],
        "pc2": points[:, 1],
        "cluster": clusters,
        "anomaly_score": anomaly_score,
        "is_anomaly": is_anomaly,
    })

    assignments = assignments.sort_values(
        ["cluster", "anomaly_score"],
        ascending=[True, False],
    )

    assignments.to_csv(
        OUT_DIR / "experiment_001_assignments.csv",
        index=False,
    )

    silhouette_df.to_csv(
        OUT_DIR / "experiment_001_silhouette.csv",
        index=False,
    )

    # ---------------------------------------------------------
    # PCA feature loadings.
    # ---------------------------------------------------------
    loadings = pd.DataFrame(
        pca.components_.T,
        index=FEATURES,
        columns=["PC1", "PC2"],
    )

    loadings["pc1_abs"] = loadings["PC1"].abs()
    loadings["pc2_abs"] = loadings["PC2"].abs()

    loadings.to_csv(
        OUT_DIR / "experiment_001_pca_loadings.csv"
    )

    # ---------------------------------------------------------
    # Plot.
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 8))

    for cluster in sorted(set(clusters)):
        mask = clusters == cluster

        ax.scatter(
            points[mask, 0],
            points[mask, 1],
            label=f"Cluster {cluster}",
            s=70,
        )

    for i, (x, y) in enumerate(points, start=1):
        ax.annotate(
            str(i),
            (x, y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
        )

    anomaly_mask = is_anomaly

    if anomaly_mask.any():
        ax.scatter(
            points[anomaly_mask, 0],
            points[anomaly_mask, 1],
            marker="x",
            s=130,
            linewidths=2,
            label="Isolation Forest anomaly",
        )

    ax.set_xlabel(
        f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)"
    )
    ax.set_ylabel(
        f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}% variance)"
    )
    ax.set_title(
        "Hardsignal Labs — Kraken RF Sentinel ML Experiment 001"
    )
    ax.legend()
    ax.grid(True, alpha=0.25)

    fig.tight_layout()

    fig.savefig(
        OUT_DIR / "experiment_001_pca.png",
        dpi=180,
    )

    plt.close(fig)

    # ---------------------------------------------------------
    # Console report.
    # ---------------------------------------------------------
    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL ML EXPERIMENT 001")
    print("=" * 70)

    print(f"sessions={len(df)}")
    print(f"features={len(FEATURES)}")
    print(
        "pca_variance="
        f"{pca.explained_variance_ratio_[0]:.4f},"
        f"{pca.explained_variance_ratio_[1]:.4f}"
    )

    print()
    print("SILHOUETTE SEARCH")

    for row in silhouette_results:
        print(
            f"k={row['k']} "
            f"silhouette={row['silhouette']:.4f}"
        )

    print()
    print(
        f"selected_clusters={best_k} "
        f"silhouette={best_score:.4f}"
    )

    print()
    print("CLUSTER COUNTS")

    counts = pd.Series(clusters).value_counts().sort_index()

    for cluster, count in counts.items():
        print(f"cluster={cluster} sessions={count}")

    print()
    print("ISOLATION FOREST")

    print(f"anomalies={int(is_anomaly.sum())}")

    anomaly_rows = assignments[
        assignments["is_anomaly"]
    ].sort_values(
        "anomaly_score",
        ascending=False,
    )

    for _, row in anomaly_rows.iterrows():
        print(
            f"anomaly_score={row['anomaly_score']:.4f} "
            f"session={row['session_id']}"
        )

    print()
    print("TOP PC1 LOADINGS")

    for feature, row in (
        loadings
        .sort_values("pc1_abs", ascending=False)
        .head(5)
        .iterrows()
    ):
        print(f"{feature:30} {row['PC1']:+.4f}")

    print()
    print("TOP PC2 LOADINGS")

    for feature, row in (
        loadings
        .sort_values("pc2_abs", ascending=False)
        .head(5)
        .iterrows()
    ):
        print(f"{feature:30} {row['PC2']:+.4f}")

    print()
    print("outputs:")
    print("  results/ml/experiment_001_assignments.csv")
    print("  results/ml/experiment_001_silhouette.csv")
    print("  results/ml/experiment_001_pca_loadings.csv")
    print("  results/ml/experiment_001_pca.png")


if __name__ == "__main__":
    main()
