#!/usr/bin/env python3

"""
Sentinel ML Experiment 006

Freeze the Experiment 002 behavioural model for prospective validation.

This model describes RF/DoA behavioural regimes.
It is not a device-identity model.
"""

from pathlib import Path
import hashlib
import json

import joblib
import numpy as np
import pandas as pd
import sklearn

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


DATASET = Path("results/ml/rf_behaviour_dataset_v001.csv")
ASSIGNMENTS = Path("results/ml/experiment_002_assignments.csv")

MODEL_PATH = Path("results/ml/sentinel_behaviour_model_v001.joblib")
MANIFEST_PATH = Path("results/ml/sentinel_behaviour_model_v001_manifest.json")

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


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    data = pd.read_csv(DATASET)
    assignments = pd.read_csv(ASSIGNMENTS)

    training = data.merge(
        assignments[["session_id", "cluster"]],
        on="session_id",
        how="inner",
        validate="one_to_one",
    )

    if len(training) != 21:
        raise SystemExit(
            f"Expected 21 frozen training sessions, got {len(training)}"
        )

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_imputed = imputer.fit_transform(training[FEATURES])
    X = scaler.fit_transform(X_imputed)

    labels = training["cluster"].to_numpy(dtype=int)

    centroids = {}
    distance_reference = {}

    for cluster_id in sorted(np.unique(labels)):
        mask = labels == cluster_id
        members = X[mask]

        centroid = members.mean(axis=0)
        distances = np.linalg.norm(
            members - centroid,
            axis=1,
        )

        centroids[int(cluster_id)] = centroid

        distance_reference[int(cluster_id)] = {
            "count": int(len(distances)),
            "mean": float(np.mean(distances)),
            "median": float(np.median(distances)),
            "max": float(np.max(distances)),
        }

    artifact = {
        "model_version": "0.1",
        "model_type": "nearest_frozen_behaviour_centroid",
        "features": FEATURES,
        "imputer": imputer,
        "scaler": scaler,
        "centroids": centroids,
        "distance_reference": distance_reference,
        "training_session_ids": training["session_id"].tolist(),
        "training_clusters": labels.tolist(),
        "training_dataset_sha256": sha256_file(DATASET),
        "sklearn_version": sklearn.__version__,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH)

    manifest = {
        "model_version": artifact["model_version"],
        "model_type": artifact["model_type"],
        "training_sessions": len(training),
        "features": FEATURES,
        "cluster_counts": {
            str(int(cluster_id)): int((labels == cluster_id).sum())
            for cluster_id in sorted(np.unique(labels))
        },
        "distance_reference": {
            str(k): v
            for k, v in distance_reference.items()
        },
        "training_dataset": str(DATASET),
        "training_dataset_sha256": artifact["training_dataset_sha256"],
        "assignment_source": str(ASSIGNMENTS),
        "sklearn_version": sklearn.__version__,
        "scientific_scope": (
            "RF/DoA behavioural regime model; "
            "not evidence of unique transmitter identity"
        ),
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL ML EXPERIMENT 006")
    print("=" * 70)
    print(f"training_sessions={len(training)}")
    print(f"features={len(FEATURES)}")
    print(f"dataset_sha256={artifact['training_dataset_sha256']}")

    print()
    print("FROZEN CLUSTERS")

    for cluster_id in sorted(centroids):
        ref = distance_reference[cluster_id]

        print(
            f"cluster={cluster_id} "
            f"sessions={ref['count']} "
            f"distance_mean={ref['mean']:.4f} "
            f"distance_median={ref['median']:.4f} "
            f"distance_max={ref['max']:.4f}"
        )

    print()
    print(f"model={MODEL_PATH}")
    print(f"manifest={MANIFEST_PATH}")
    print()
    print("MODEL IS NOW FROZEN — DO NOT REFIT FOR PROSPECTIVE TESTS")


if __name__ == "__main__":
    main()
