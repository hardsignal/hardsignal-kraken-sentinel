#!/usr/bin/env python3

"""
Sentinel ML prospective-session workflow.

Uses the frozen behavioural model without refitting.

Commands:
    check
        Verify frozen-model provenance and Kraken reference configuration.

    finalize --session SESSION_ID
        Build a one-session feature record, score it against the frozen
        behavioural model, save a JSON result, and append the natural
        prospective ledger.

This tool describes RF/DoA behavioural regimes.
It does not establish transmitter identity.
"""

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd

from ml.dataset_builder import build_dataset


MODEL_PATH = Path(
    "results/ml/sentinel_behaviour_model_v001.joblib"
)

MANIFEST_PATH = Path(
    "results/ml/sentinel_behaviour_model_v001_manifest.json"
)

TRAINING_DATASET = Path(
    "results/ml/rf_behaviour_dataset_v001.csv"
)

RESULT_DIR = Path(
    "results/ml/prospective"
)

LEDGER_PATH = Path(
    "results/ml/natural_prospective_ledger_v001.csv"
)

KRAKEN_SETTINGS_URL = (
    "http://127.0.0.1:8042/settings"
)

KRAKEN_STATUS_PATH = Path.home() / "krakensdr_doa/_share/status.json"
KRAKEN_MYDATA_PATH = Path.home() / "krakensdr_doa/mydata.csv"

REFERENCE_SETTINGS = {
    "vfo_freq_0": 433868160,
    "vfo_squelch_mode_0": "Manual",
    "vfo_squelch_0": -45,
    "doa_method": "MUSIC",
    "doa_decorrelation_method": "Off",
    "ant_arrangement": "UCA",
    "ant_spacing_meters": 0.21,
}

LEDGER_COLUMNS = [
    "time",
    "session_id",
    "model_version",
    "training_dataset_sha256",
    "assigned_cluster",
    "nearest_distance",
    "second_nearest_distance",
    "separation_ratio",
    "distance_vs_training_max",
    "novelty",
]


def sha256_file(path):
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(65536),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_manifest():
    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


def verify_provenance():
    manifest = load_manifest()

    expected = manifest[
        "training_dataset_sha256"
    ]

    actual = sha256_file(
        TRAINING_DATASET
    )

    if actual != expected:
        raise RuntimeError(
            "Frozen training dataset SHA256 mismatch:\n"
            f"expected={expected}\n"
            f"actual={actual}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    model_hash = model[
        "training_dataset_sha256"
    ]

    if model_hash != expected:
        raise RuntimeError(
            "Frozen model provenance mismatch:\n"
            f"manifest={expected}\n"
            f"model={model_hash}"
        )

    return manifest, model


def get_kraken_settings():
    with urlopen(
        KRAKEN_SETTINGS_URL,
        timeout=5,
    ) as response:
        return json.load(response)


def compare_settings(settings):
    mismatches = []

    for key, expected in (
        REFERENCE_SETTINGS.items()
    ):
        actual = settings.get(key)

        if isinstance(expected, float):
            try:
                equal = (
                    abs(
                        float(actual)
                        - expected
                    )
                    < 1e-9
                )
            except (TypeError, ValueError):
                equal = False
        else:
            equal = actual == expected

        if not equal:
            mismatches.append(
                (key, expected, actual)
            )

    return mismatches


def score_row(row, model):
    features = model["features"]

    matrix = pd.DataFrame(
        [[
            row.get(feature)
            for feature in features
        ]],
        columns=features,
    )

    X = model["imputer"].transform(
        matrix
    )

    X = model["scaler"].transform(
        X
    )[0]

    distances = {}

    for cluster_id, centroid in (
        model["centroids"].items()
    ):
        distances[int(cluster_id)] = (
            float(
                np.linalg.norm(
                    X - centroid
                )
            )
        )

    ordered = sorted(
        distances.items(),
        key=lambda item: item[1],
    )

    assigned = ordered[0][0]
    nearest = ordered[0][1]
    second = ordered[1][1]

    reference = model[
        "distance_reference"
    ][assigned]

    training_max = reference["max"]

    ratio = (
        nearest / training_max
        if training_max > 0
        else float("inf")
    )

    separation = (
        second / nearest
        if nearest > 0
        else float("inf")
    )

    novelty = (
        "WITHIN_OBSERVED_TRAINING_RANGE"
        if ratio <= 1.0
        else "OUTSIDE_OBSERVED_TRAINING_RANGE"
    )

    return {
        "assigned_cluster": assigned,
        "nearest_distance": nearest,
        "second_nearest_distance": second,
        "separation_ratio": separation,
        "distance_vs_training_max": ratio,
        "novelty": novelty,
        "distances": {
            str(k): v
            for k, v in ordered
        },
    }



def assert_session_not_recorded(session_id):
    if not LEDGER_PATH.exists():
        return

    with LEDGER_PATH.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        existing = csv.DictReader(handle)

        if any(
            row["session_id"] == session_id
            for row in existing
        ):
            raise RuntimeError(
                "Session already exists in "
                f"{LEDGER_PATH}: "
                f"{session_id}"
            )


def append_ledger(record):
    LEDGER_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    exists = LEDGER_PATH.exists()

    if exists:
        with LEDGER_PATH.open(
            newline="",
            encoding="utf-8",
        ) as handle:
            existing = list(
                csv.DictReader(handle)
            )

        if any(
            row["session_id"]
            == record["session_id"]
            for row in existing
        ):
            raise RuntimeError(
                "Session already exists in "
                f"{LEDGER_PATH}: "
                f"{record['session_id']}"
            )

    with LEDGER_PATH.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=LEDGER_COLUMNS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow({
            key: record[key]
            for key in LEDGER_COLUMNS
        })



def check_daq_health():
    if not KRAKEN_STATUS_PATH.exists():
        raise RuntimeError(
            f"Kraken status file missing: {KRAKEN_STATUS_PATH}"
        )

    status = json.loads(
        KRAKEN_STATUS_PATH.read_text(encoding="utf-8")
    )

    daq = status.get("daq_status", {})

    checks = {
        "frame_sync": daq.get("frame_sync"),
        "sample_delay_sync": daq.get("sample_delay_sync"),
        "iq_sync": daq.get("iq_sync"),
        "adc_overdrive": daq.get("adc_overdrive"),
        "daq_ok": status.get("daq_ok"),
        "dropped_frames": status.get("daq_num_dropped_frames"),
    }

    failures = []

    if checks["frame_sync"] is not True:
        failures.append("frame_sync")
    if checks["sample_delay_sync"] is not True:
        failures.append("sample_delay_sync")
    if checks["iq_sync"] is not True:
        failures.append("iq_sync")
    if checks["adc_overdrive"] is not False:
        failures.append("adc_overdrive")
    if checks["daq_ok"] is not True:
        failures.append("daq_ok")
    if checks["dropped_frames"] != 0:
        failures.append("dropped_frames")

    return checks, failures


def get_mydata_state():
    if not KRAKEN_MYDATA_PATH.exists():
        raise RuntimeError(
            f"Kraken data file missing: {KRAKEN_MYDATA_PATH}"
        )

    stat = KRAKEN_MYDATA_PATH.stat()

    return {
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }



def command_recorder_check(wait_seconds):
    before = get_mydata_state()

    print("=" * 70)
    print("HARDSIGNAL LABS — KRAKEN RECORDER CHECK")
    print("=" * 70)
    print(f"path={KRAKEN_MYDATA_PATH}")
    print(f"before_size={before['size']}")
    print(f"before_mtime_ns={before['mtime_ns']}")
    print()
    print(
        f"Trigger the controlled RF source once now. "
        f"Waiting {wait_seconds:.1f} seconds..."
    )

    time.sleep(wait_seconds)

    after = get_mydata_state()

    size_delta = after["size"] - before["size"]
    mtime_changed = after["mtime_ns"] > before["mtime_ns"]

    print()
    print(f"after_size={after['size']}")
    print(f"after_mtime_ns={after['mtime_ns']}")
    print(f"size_delta={size_delta}")
    print(f"mtime_changed={mtime_changed}")

    if size_delta <= 0 or not mtime_changed:
        print("recorder_active=FAIL")
        raise SystemExit(4)

    print("recorder_active=OK")


def command_check():
    manifest, _ = verify_provenance()

    settings = get_kraken_settings()
    mismatches = compare_settings(
        settings
    )

    daq_checks, daq_failures = check_daq_health()
    mydata = get_mydata_state()

    print("=" * 70)
    print(
        "HARDSIGNAL LABS — "
        "PROSPECTIVE SESSION CHECK"
    )
    print("=" * 70)

    print(
        "training_dataset_sha256="
        f"{manifest['training_dataset_sha256']}"
    )

    print(
        "model_provenance=OK"
    )

    print()
    print("KRAKEN REFERENCE SETTINGS")

    for key, expected in (
        REFERENCE_SETTINGS.items()
    ):
        print(
            f"{key}={settings.get(key)} "
            f"(expected {expected})"
        )

    print()

    if mismatches:
        print("kraken_reference=FAIL")

        for key, expected, actual in mismatches:
            print(
                f"mismatch {key}: "
                f"expected={expected} "
                f"actual={actual}"
            )

        raise SystemExit(2)

    print("kraken_reference=OK")

    print()
    print("KRAKEN DAQ HEALTH")

    for key, value in daq_checks.items():
        print(f"{key}={value}")

    if daq_failures:
        print("daq_health=FAIL")
        print("failed=" + ",".join(daq_failures))
        raise SystemExit(3)

    print("daq_health=OK")

    print()
    print("KRAKEN DATA FILE")
    print(f"path={KRAKEN_MYDATA_PATH}")
    print(f"size={mydata['size']}")
    print(f"mtime_ns={mydata['mtime_ns']}")


def command_finalize(session_id):
    manifest, model = verify_provenance()

    # Reject duplicates before scoring or writing any result artifact.
    assert_session_not_recorded(session_id)

    rows = build_dataset(
        Path.home() / "kraken_bursts.log",
        Path.home()
        / "kraken_track_events.log",
        Path.home()
        / "kraken_episode_events.jsonl",
        min_bursts=2,
    )

    matches = [
        row
        for row in rows
        if row["session_id"]
        == session_id
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one dataset "
            f"row for {session_id}; "
            f"found {len(matches)}"
        )

    row = matches[0]
    score = score_row(
        row,
        model,
    )

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = {
        "record_version": "0.1",
        "time": datetime.now().astimezone().isoformat(),
        "session_id": session_id,
        "model_version": model["model_version"],
        "training_dataset_sha256": (
            manifest[
                "training_dataset_sha256"
            ]
        ),
        "feature_row": row,
        **score,
        "scientific_scope": (
            "RF/DoA behavioural regime "
            "assignment; not transmitter identity"
        ),
    }

    output = (
        RESULT_DIR
        / f"{session_id}.json"
    )

    output.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    ledger_record = {
        "time": result["time"],
        "session_id": session_id,
        "model_version": (
            result["model_version"]
        ),
        "training_dataset_sha256": (
            result[
                "training_dataset_sha256"
            ]
        ),
        "assigned_cluster": (
            score["assigned_cluster"]
        ),
        "nearest_distance": (
            f"{score['nearest_distance']:.6f}"
        ),
        "second_nearest_distance": (
            f"{score['second_nearest_distance']:.6f}"
        ),
        "separation_ratio": (
            f"{score['separation_ratio']:.6f}"
        ),
        "distance_vs_training_max": (
            f"{score['distance_vs_training_max']:.6f}"
        ),
        "novelty": score["novelty"],
    }

    append_ledger(
        ledger_record
    )

    print("=" * 70)
    print(
        "HARDSIGNAL LABS — "
        "PROSPECTIVE SESSION FINALIZED"
    )
    print("=" * 70)

    print(f"session={session_id}")
    print(
        "assigned_cluster="
        f"{score['assigned_cluster']}"
    )
    print(
        "nearest_distance="
        f"{score['nearest_distance']:.4f}"
    )
    print(
        "second_nearest_distance="
        f"{score['second_nearest_distance']:.4f}"
    )
    print(
        "separation_ratio="
        f"{score['separation_ratio']:.4f}"
    )
    print(
        "distance_vs_training_max="
        f"{score['distance_vs_training_max']:.4f}"
    )
    print(
        f"novelty={score['novelty']}"
    )

    print()
    print("DISTANCES")

    for cluster_id, distance in (
        sorted(
            score["distances"].items(),
            key=lambda item: item[1],
        )
    ):
        print(
            f"cluster={cluster_id} "
            f"distance={distance:.4f}"
        )

    print()
    print(f"result={output}")
    print(f"ledger={LEDGER_PATH}")


def main():
    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "check",
        help=(
            "Verify frozen provenance, Kraken reference settings, "
            "DAQ health, and data-file presence."
        ),
    )

    recorder = sub.add_parser(
        "recorder-check",
        help=(
            "Actively verify that mydata.csv advances after "
            "a controlled RF activation."
        ),
    )

    recorder.add_argument(
        "--wait",
        type=float,
        default=8.0,
    )

    finalize = sub.add_parser(
        "finalize",
        help=(
            "Score and record an "
            "existing prospective session."
        ),
    )

    finalize.add_argument(
        "--session",
        required=True,
    )

    args = parser.parse_args()

    if args.command == "check":
        command_check()

    elif args.command == "recorder-check":
        command_recorder_check(
            args.wait
        )

    elif args.command == "finalize":
        command_finalize(
            args.session
        )


if __name__ == "__main__":
    main()
