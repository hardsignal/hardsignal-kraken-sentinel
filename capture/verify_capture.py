#!/usr/bin/env python3

"""
Hardsignal Labs — Kraken Capture Verifier

Verifies the integrity and provenance of a completed Kraken capture
manifest without modifying any source IQ files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


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

    capture_dir = args.capture_dir
    manifest_path = capture_dir / "manifest.json"

    errors = []
    warnings = []

    if not manifest_path.is_file():
        print(f"ERROR: missing manifest: {manifest_path}")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot parse manifest: {exc}")
        return 1

    print("=== CAPTURE ===")
    print("ID:       ", manifest.get("capture_id"))
    print("Format:   ", manifest.get("format"))
    print("Started:  ", manifest.get("started_at"))
    print("Finished: ", manifest.get("finished_at"))

    if manifest.get("format") != "HARDSIGNAL_KRAKEN_CAPTURE_MANIFEST_V1":
        errors.append("Unexpected manifest format")

    files = manifest.get("files", [])

    print()
    print("=== BOUNDARY ===")
    print("IQ before: ", manifest.get("iq_count_before"))
    print("IQ after:  ", manifest.get("iq_count_after"))
    print("New files: ", manifest.get("new_iq_file_count"))

    if manifest.get("new_iq_file_count") != len(files):
        errors.append(
            "new_iq_file_count does not equal number of manifest file records"
        )

    changed = manifest.get("changed_preexisting_iq_files", [])

    print("Changed pre-existing:", len(changed))

    if changed:
        errors.append(
            f"{len(changed)} pre-existing IQ file(s) changed during capture"
        )

    print()
    print("=== CONFIGURATION ===")

    start_settings = manifest.get("settings_at_start")
    finish_settings = manifest.get("settings_at_finish")

    settings_unchanged = start_settings == finish_settings

    print("Settings unchanged:", settings_unchanged)

    if not settings_unchanged:
        errors.append("Kraken settings changed during capture")

    git_start = manifest.get("git_head_at_start")
    git_finish = manifest.get("git_head_at_finish")

    print("Git start: ", git_start)
    print("Git finish:", git_finish)

    if git_start != git_finish:
        warnings.append("Git HEAD changed during capture")

    print()
    print("=== IQ INTEGRITY ===")

    if not files:
        print("No IQ files recorded in this capture.")

    for item in files:
        path = Path(item["path"])
        expected_size = item.get("size_bytes")
        expected_hash = item.get("sha256")

        if not path.is_file():
            errors.append(f"Missing IQ file: {path}")
            print(f"MISSING  {path}")
            continue

        actual_size = path.stat().st_size

        if actual_size != expected_size:
            errors.append(
                f"Size mismatch: {path} "
                f"(expected {expected_size}, got {actual_size})"
            )
            print(f"SIZE-FAIL {path}")
            continue

        actual_hash = sha256_file(path)

        if actual_hash != expected_hash:
            errors.append(f"SHA256 mismatch: {path}")
            print(f"HASH-FAIL {path}")
            continue

        print(
            f"OK  {path.name}  "
            f"{actual_size} bytes  "
            f"{actual_hash[:16]}..."
        )

    hashes_path = capture_dir / "files.sha256"

    if not hashes_path.is_file():
        errors.append("files.sha256 is missing")
    else:
        expected_lines = [
            f"{item['sha256']}  {item['path']}"
            for item in files
        ]

        actual_lines = hashes_path.read_text(
            encoding="utf-8"
        ).splitlines()

        if actual_lines != expected_lines:
            errors.append("files.sha256 does not match manifest")
        else:
            print()
            print("files.sha256: OK")

    print()
    print("=== RESULT ===")

    for warning in warnings:
        print(f"WARNING: {warning}")

    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("VERIFICATION: FAIL")
        return 1

    print("VERIFICATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
