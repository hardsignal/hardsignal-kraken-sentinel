#!/usr/bin/env python3

"""
Hardsignal Labs — HackRF Capture Provenance V1 Verifier
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


FORMAT = "HARDSIGNAL_HACKRF_CAPTURE_MANIFEST_V1"

FROZEN = {
    "center_frequency_hz": 433_868_160,
    "sample_rate_complex_sps": 2_000_000,
    "baseband_filter_hz": 1_750_000,
    "representation": "CS8_INTERLEAVED_SIGNED_INT8_IQ",
    "rf_amp": 0,
    "antenna_power": 0,
    "lna_db": 32,
    "vga_db": 32,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir", type=Path)
    args = parser.parse_args()

    bundle = args.capture_dir
    manifest_path = bundle / "manifest.json"

    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_path.is_file():
        print("ERROR: missing manifest:", manifest_path)
        return 1

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        print("ERROR: cannot parse manifest:", exc)
        return 1

    print("=== HACKRF CAPTURE ===")
    print("ID:", manifest.get("capture_id"))
    print("Format:", manifest.get("format"))
    print("Sensor:", manifest.get("sensor_label"))
    print("Engineering only:", manifest.get("engineering_only"))

    if manifest.get("format") != FORMAT:
        errors.append("Unexpected manifest format")

    required = [
        "started_wall_utc",
        "finished_wall_utc",
        "started_monotonic_ns",
        "finished_monotonic_ns",
        "git_head_at_start",
        "git_head_at_finish",
        "receiver",
        "acquisition",
        "tool_versions",
        "command",
        "transfer_exit_code",
        "expected_complex_samples",
        "expected_size_bytes",
        "actual_size_bytes",
        "sha256",
        "raw_file",
        "activation_log",
        "transfer_log",
    ]

    for key in required:
        if key not in manifest:
            errors.append(f"Missing manifest field: {key}")

    acquisition = manifest.get("acquisition", {})

    print()
    print("=== FROZEN SETTINGS ===")

    for key, expected in FROZEN.items():
        actual = acquisition.get(key)
        ok = actual == expected
        print(f"{key}: {actual!r} expected={expected!r} ok={ok}")

        if not ok:
            errors.append(
                f"Frozen setting mismatch: {key}"
            )

    transfer_exit = manifest.get("transfer_exit_code")
    print()
    print("transfer_exit_code =", transfer_exit)

    if transfer_exit != 0:
        errors.append("hackrf_transfer exit code is non-zero")

    expected_samples = manifest.get("expected_complex_samples")
    expected_bytes = manifest.get("expected_size_bytes")

    if not isinstance(expected_samples, int) or expected_samples <= 0:
        errors.append("expected_complex_samples must be a positive integer")

    if not isinstance(expected_bytes, int) or expected_bytes <= 0:
        errors.append("expected_size_bytes must be a positive integer")

    if (
        isinstance(expected_samples, int)
        and expected_bytes != expected_samples * 2
    ):
        errors.append(
            "Expected byte count is inconsistent with CS8 sample count"
        )

    raw_value = manifest.get("raw_file")
    raw_path = Path(raw_value) if raw_value else None

    print()
    print("=== RAW FILE ===")

    if raw_path is None or not raw_path.is_file():
        errors.append("Raw CS8 file is missing")
        print("MISSING:", raw_path)
    else:
        actual_size = raw_path.stat().st_size
        actual_hash = sha256_file(raw_path)

        print("Path:", raw_path)
        print("Size:", actual_size)
        print("SHA256:", actual_hash)

        if actual_size != expected_bytes:
            errors.append("Raw file size != expected_size_bytes")

        if actual_size != manifest.get("actual_size_bytes"):
            errors.append("Raw file size != manifest actual_size_bytes")

        if actual_hash != manifest.get("sha256"):
            errors.append("Raw file SHA256 mismatch")

    print()
    print("=== SIDECARS ===")

    activation_value = manifest.get("activation_log")
    transfer_value = manifest.get("transfer_log")

    activation_path = (
        Path(activation_value) if activation_value else None
    )
    transfer_path = (
        Path(transfer_value) if transfer_value else None
    )

    for name, path in (
        ("activation log", activation_path),
        ("transfer log", transfer_path),
    ):
        if path is None or not path.is_file():
            errors.append(f"Missing {name}")
            print("MISSING:", name)
        else:
            print("OK:", name, path)

    receiver = manifest.get("receiver", {})
    receiver_value = receiver.get("hackrf_info_log")
    receiver_path = (
        Path(receiver_value) if receiver_value else None
    )

    if receiver_path is None or not receiver_path.is_file():
        errors.append("Missing hackrf_info log")
        print("MISSING: hackrf_info log")
    else:
        print("OK: hackrf_info log", receiver_path)

    git_start = manifest.get("git_head_at_start")
    git_finish = manifest.get("git_head_at_finish")

    print()
    print("=== ACTIVATION LOG CONTENT ===")

    if activation_path is not None and activation_path.is_file():
        lines = activation_path.read_text(
            encoding="utf-8"
        ).splitlines()

        fields = {}
        markers = []

        for line in lines:
            if " | " not in line:
                continue

            key, value = line.split(" | ", 1)

            if key.startswith("A") and key[1:].isdigit():
                markers.append((key, value))
            else:
                fields[key] = value

        if fields.get("FORMAT") != "HARDSIGNAL_OPERATOR_ACTIVATIONS_V1":
            errors.append("Unexpected activation-log format")

        if fields.get("CAPTURE_ID") != manifest.get("capture_id"):
            errors.append("Activation-log capture ID mismatch")

        if fields.get("SENSOR_LABEL") != manifest.get("sensor_label"):
            errors.append("Activation-log sensor label mismatch")

        try:
            declared_count = int(fields.get("COUNT", ""))
        except ValueError:
            declared_count = None
            errors.append("Invalid activation-log COUNT")

        if (
            declared_count is not None
            and len(markers) != declared_count
        ):
            errors.append(
                "Activation marker count does not match declared COUNT"
            )

        for label, value in markers:
            if "wall=" not in value or "monotonic_ns=" not in value:
                errors.append(
                    f"Activation marker missing timing fields: {label}"
                )

        print("Declared count:", declared_count)
        print("Marker count:", len(markers))

    print()
    print("=== GIT ===")
    print("Start:", git_start)
    print("Finish:", git_finish)

    if not git_start or git_start == "UNKNOWN":
        errors.append("Missing/unknown Git HEAD at start")

    if not git_finish or git_finish == "UNKNOWN":
        errors.append("Missing/unknown Git HEAD at finish")

    if git_start != git_finish:
        warnings.append("Git HEAD changed during acquisition")

    start_mono = manifest.get("started_monotonic_ns")
    finish_mono = manifest.get("finished_monotonic_ns")

    if (
        isinstance(start_mono, int)
        and isinstance(finish_mono, int)
        and finish_mono <= start_mono
    ):
        errors.append("Monotonic finish is not after start")

    # Controlled acquisitions additionally record the exact HackRF
    # transfer interval. Activation markers must fall inside it.
    controlled_mode = bool(
        manifest.get("controlled_mode", False)
    )

    transfer_launch_mono = manifest.get(
        "transfer_launch_monotonic_ns"
    )
    transfer_exit_mono = manifest.get(
        "transfer_exit_monotonic_ns"
    )

    if controlled_mode:
        if not isinstance(transfer_launch_mono, int):
            errors.append(
                "Missing transfer_launch_monotonic_ns"
            )

        if not isinstance(transfer_exit_mono, int):
            errors.append(
                "Missing transfer_exit_monotonic_ns"
            )

        if (
            isinstance(transfer_launch_mono, int)
            and isinstance(transfer_exit_mono, int)
            and transfer_exit_mono <= transfer_launch_mono
        ):
            errors.append(
                "Transfer exit is not after transfer launch"
            )

        marker_times = []

        for label, value in markers:
            try:
                marker_mono = int(
                    value.split("monotonic_ns=", 1)[1].split()[0]
                )
            except (ValueError, IndexError):
                continue

            marker_times.append((label, marker_mono))

            if (
                isinstance(transfer_launch_mono, int)
                and marker_mono < transfer_launch_mono
            ):
                errors.append(
                    f"Activation marker before transfer launch: {label}"
                )

            if (
                isinstance(transfer_exit_mono, int)
                and marker_mono > transfer_exit_mono
            ):
                errors.append(
                    f"Activation marker after transfer exit: {label}"
                )

        for previous, current in zip(
            marker_times,
            marker_times[1:]
        ):
            if current[1] <= previous[1]:
                errors.append(
                    "Activation monotonic timestamps are not ordered"
                )

    hashes_path = bundle / "files.sha256"

    print()
    print("=== HASH LIST ===")

    if not hashes_path.is_file():
        errors.append("files.sha256 missing")
    else:
        hash_errors = 0
        entries = {}

        for line in hashes_path.read_text(
            encoding="utf-8"
        ).splitlines():
            if not line.strip():
                continue

            try:
                expected_hash, filename = line.split("  ", 1)
            except ValueError:
                errors.append("Malformed files.sha256 line")
                hash_errors += 1
                continue

            if filename in entries:
                errors.append(
                    f"Duplicate files.sha256 entry: {filename}"
                )
                hash_errors += 1
                continue

            entries[filename] = expected_hash

        expected_paths = set()

        if raw_path is not None:
            expected_paths.add(str(raw_path.resolve()))

        for path in (
            activation_path,
            transfer_path,
            receiver_path,
            manifest_path,
            bundle / "notes.md",
        ):
            if path is not None:
                expected_paths.add(str(path.resolve()))

        actual_paths = set(entries)

        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)

        for filename in missing:
            errors.append(
                f"Missing files.sha256 entry: {filename}"
            )
            hash_errors += 1

        for filename in extra:
            errors.append(
                f"Unexpected files.sha256 entry: {filename}"
            )
            hash_errors += 1

        for filename, expected_hash in entries.items():
            path = Path(filename)

            if not path.is_file():
                errors.append(
                    f"Hash-list file missing: {path}"
                )
                hash_errors += 1
                continue

            if sha256_file(path) != expected_hash:
                errors.append(
                    f"Hash-list mismatch: {path}"
                )
                hash_errors += 1

        if hash_errors == 0:
            print("files.sha256 exact set and hashes: OK")

    print()
    print("=== RESULT ===")

    for warning in warnings:
        print("WARNING:", warning)

    for error in errors:
        print("ERROR:", error)

    if errors:
        print("VERIFICATION: FAIL")
        return 1

    print("VERIFICATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
