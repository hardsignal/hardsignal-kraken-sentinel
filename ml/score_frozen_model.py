#!/usr/bin/env python3

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


DEFAULT_MODEL = Path(
    "results/ml/sentinel_behaviour_model_v001.joblib"
)


def main():
    parser = argparse.ArgumentParser(
        description="Score an unseen Sentinel session against the frozen ML model."
    )

    parser.add_argument(
        "--dataset",
        required=True,
    )

    parser.add_argument(
        "--session",
        required=True,
    )

    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
    )

    args = parser.parse_args()

    artifact = joblib.load(args.model)
    data = pd.read_csv(args.dataset)

    rows = data[
        data["session_id"] == args.session
    ]

    if len(rows) != 1:
        raise SystemExit(
            f"Expected exactly one row for {args.session}, found {len(rows)}"
        )

    features = artifact["features"]

    X = artifact["imputer"].transform(
        rows[features]
    )

    X = artifact["scaler"].transform(X)[0]

    distances = {}

    for cluster_id, centroid in artifact["centroids"].items():
        distances[int(cluster_id)] = float(
            np.linalg.norm(X - centroid)
        )

    assigned = min(
        distances,
        key=distances.get,
    )

    nearest_distance = distances[assigned]
    reference = artifact["distance_reference"][assigned]

    ratio_to_training_max = (
        nearest_distance / reference["max"]
        if reference["max"] > 0
        else float("inf")
    )

    ordered = sorted(
        distances.items(),
        key=lambda item: item[1],
    )

    second_distance = (
        ordered[1][1]
        if len(ordered) > 1
        else float("nan")
    )

    separation_ratio = (
        second_distance / nearest_distance
        if nearest_distance > 0
        else float("inf")
    )

    print("=" * 70)
    print("HARDSIGNAL LABS — FROZEN SENTINEL BEHAVIOUR SCORE")
    print("=" * 70)

    print(f"session={args.session}")
    print(f"model_version={artifact['model_version']}")
    print(f"assigned_cluster={assigned}")
    print(f"nearest_distance={nearest_distance:.4f}")
    print(f"second_nearest_distance={second_distance:.4f}")
    print(f"separation_ratio={separation_ratio:.4f}")

    print()
    print("DISTANCES")

    for cluster_id, distance in ordered:
        print(
            f"cluster={cluster_id} "
            f"distance={distance:.4f}"
        )

    print()
    print("TRAINING REFERENCE")

    print(
        f"cluster_training_count={reference['count']}"
    )
    print(
        f"cluster_distance_mean={reference['mean']:.4f}"
    )
    print(
        f"cluster_distance_median={reference['median']:.4f}"
    )
    print(
        f"cluster_distance_max={reference['max']:.4f}"
    )
    print(
        f"distance_vs_training_max={ratio_to_training_max:.4f}"
    )

    print()
    if ratio_to_training_max <= 1.0:
        print("novelty=WITHIN_OBSERVED_TRAINING_RANGE")
    else:
        print("novelty=OUTSIDE_OBSERVED_TRAINING_RANGE")

    print()
    print(
        "NOTE: cluster assignment describes RF/DoA behaviour, "
        "not transmitter identity."
    )


if __name__ == "__main__":
    main()
