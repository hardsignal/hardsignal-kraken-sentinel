#!/usr/bin/env python3

"""
Hardsignal Labs — HackRF Capture Provenance V1

Owns a deterministic receive-only HackRF acquisition and records its
provenance.

Initial implementation is deliberately restricted to engineering-only
validation. Experimental V1 collection must not be enabled until this
implementation has itself been validated and committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


FORMAT = "HARDSIGNAL_HACKRF_CAPTURE_MANIFEST_V1"

FREQ_HZ = 433_868_160
SAMPLE_RATE = 2_000_000
BASEBAND_FILTER_HZ = 1_750_000
RF_AMP = 0
ANTENNA_POWER = 0
LNA_DB = 32
VGA_DB = 32
BYTES_PER_COMPLEX_SAMPLE = 2

CAPTURE_ROOT = Path("captures/hackrf")
RAW_ROOT = Path.home() / "hardsignal-data/hackrf"


def wall_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def run_text(command: list[str]) -> str:
    try:
        return subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        return exc.output
    except Exception as exc:
        return f"ERROR: {exc}\n"


def write_activation_header(
    path: Path,
    capture_id: str,
    sensor_label: str,
    count: int,
    quiet_seconds: float,
) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write("FORMAT | HARDSIGNAL_OPERATOR_ACTIVATIONS_V1\n")
        handle.write(f"CAPTURE_ID | {capture_id}\n")
        handle.write(f"SENSOR_LABEL | {sensor_label}\n")
        handle.write(f"COUNT | {count}\n")
        handle.write(f"QUIET_SECONDS | {quiet_seconds:.3f}\n")
        handle.flush()


def append_activation(path: Path, label: str) -> None:
    wall = wall_utc()
    mono = time.monotonic_ns()

    line = (
        f"{label} | wall={wall} | "
        f"monotonic_ns={mono}\n"
    )

    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()

    print(line.rstrip(), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_id")
    parser.add_argument("--sensor", required=True)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--activations", type=int, default=0)
    parser.add_argument("--quiet", type=float, default=5.0)
    parser.add_argument(
        "--post-roll",
        type=float,
        default=2.0,
        help="Seconds to record after final controlled activation.",
    )
    parser.add_argument(
        "--engineering-only",
        action="store_true",
        help="Required by this implementation version.",
    )
    args = parser.parse_args()

    if not args.engineering_only:
        raise SystemExit(
            "ERROR: this implementation is locked to --engineering-only"
        )

    if args.seconds <= 0:
        raise SystemExit("ERROR: --seconds must be > 0")

    if args.activations < 0:
        raise SystemExit("ERROR: --activations must be >= 0")

    if args.quiet < 0:
        raise SystemExit("ERROR: --quiet must be >= 0")

    if args.post_roll < 0:
        raise SystemExit("ERROR: --post-roll must be >= 0")

    controlled_mode = args.activations > 0

    expected_samples_float = SAMPLE_RATE * args.seconds

    if not expected_samples_float.is_integer():
        raise SystemExit(
            "ERROR: duration must produce an integer complex-sample count"
        )

    expected_samples = int(expected_samples_float)
    expected_bytes = expected_samples * BYTES_PER_COMPLEX_SAMPLE

    bundle = CAPTURE_ROOT / args.capture_id
    raw_dir = RAW_ROOT / args.capture_id

    if bundle.exists():
        raise SystemExit(f"ERROR: bundle already exists: {bundle}")

    if raw_dir.exists():
        raise SystemExit(f"ERROR: raw directory already exists: {raw_dir}")

    bundle.mkdir(parents=True)
    raw_dir.mkdir(parents=True)

    raw_file = raw_dir / f"{args.capture_id}.cs8"
    activation_log = bundle / "activation.log"
    transfer_log = bundle / "hackrf_transfer.log"
    receiver_log = bundle / "hackrf_info.log"
    manifest_path = bundle / "manifest.json"
    hashes_path = bundle / "files.sha256"
    notes_path = bundle / "notes.md"

    write_activation_header(
        activation_log,
        args.capture_id,
        args.sensor,
        args.activations,
        args.quiet,
    )

    receiver_text = run_text(["hackrf_info"])
    receiver_log.write_text(receiver_text, encoding="utf-8")

    git_start = git_head()
    start_wall = wall_utc()
    start_mono = time.monotonic_ns()

    command = [
        "hackrf_transfer",
        "-r", str(raw_file),
        "-f", str(FREQ_HZ),
        "-s", str(SAMPLE_RATE),
        "-b", str(BASEBAND_FILTER_HZ),
    ]

    if expected_samples is not None:
        command += ["-n", str(expected_samples)]

    command += [
        "-a", str(RF_AMP),
        "-p", str(ANTENNA_POWER),
        "-l", str(LNA_DB),
        "-g", str(VGA_DB),
    ]

    print("=== HACKRF ENGINEERING CAPTURE ===")
    print("Capture ID:", args.capture_id)
    print("Sensor:", args.sensor)
    print("Engineering only: True")
    print("Raw:", raw_file)
    print("Expected complex samples:", expected_samples)
    print("Expected bytes:", expected_bytes)
    print()
    print("Command:")
    print(" ".join(command))
    print()

    transfer_launch_wall = None
    transfer_launch_mono = None
    transfer_exit_wall = None
    transfer_exit_mono = None

    with transfer_log.open("x", encoding="utf-8") as log:
        transfer_launch_wall = wall_utc()
        transfer_launch_mono = time.monotonic_ns()

        proc = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            if controlled_mode:
                print("CONTROLLED MODE ARMED", flush=True)
                print(
                    "Prepare the trigger now. Recording has started.",
                    flush=True,
                )

                # Allow the receiver to enter streaming state.
                time.sleep(1.0)

                for index in range(1, args.activations + 1):
                    if proc.poll() is not None:
                        raise RuntimeError(
                            "HackRF capture ended before controlled activation "
                            f"A{index}"
                        )

                    input(
                        f"A{index} READY — press ENTER and trigger "
                        f"{args.sensor} now: "
                    )

                    if proc.poll() is not None:
                        raise RuntimeError(
                            "HackRF capture ended while waiting for controlled "
                            f"activation A{index}"
                        )

                    append_activation(
                        activation_log,
                        f"A{index}",
                    )

                    if index != args.activations and args.quiet:
                        print(
                            f"QUIET {args.quiet:.3f} seconds...",
                            flush=True,
                        )
                        time.sleep(args.quiet)
                        if proc.poll() is not None:
                            raise RuntimeError(
                                "HackRF capture ended during required quiet interval"
                            )
                        print("QUIET COMPLETE", flush=True)

                if args.post_roll:
                    print(
                        f"POST-ROLL {args.post_roll:.3f} seconds...",
                        flush=True,
                    )
                    time.sleep(args.post_roll)
                    if proc.poll() is not None:
                        raise RuntimeError(
                            "HackRF capture ended during required post-roll"
                        )

            transfer_exit = proc.wait()

            transfer_exit_mono = time.monotonic_ns()
            transfer_exit_wall = wall_utc()

        except BaseException:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            raise

    finish_mono = time.monotonic_ns()
    finish_wall = wall_utc()
    git_finish = git_head()

    actual_bytes = raw_file.stat().st_size if raw_file.exists() else None
    raw_sha256 = sha256_file(raw_file) if raw_file.exists() else None

    hackrf_transfer_version = run_text(
        ["hackrf_transfer"]
    ).splitlines()[:3]

    manifest = {
        "format": FORMAT,
        "capture_id": args.capture_id,
        "sensor_label": args.sensor,
        "engineering_only": True,
        "started_wall_utc": start_wall,
        "finished_wall_utc": finish_wall,
        "started_monotonic_ns": start_mono,
        "finished_monotonic_ns": finish_mono,
        "controlled_mode": controlled_mode,
        "transfer_launch_wall_utc": transfer_launch_wall,
        "transfer_launch_monotonic_ns": transfer_launch_mono,
        "transfer_exit_wall_utc": transfer_exit_wall,
        "transfer_exit_monotonic_ns": transfer_exit_mono,
        "git_head_at_start": git_start,
        "git_head_at_finish": git_finish,
        "receiver": {
            "hackrf_info_log": str(receiver_log.resolve()),
        },
        "acquisition": {
            "center_frequency_hz": FREQ_HZ,
            "sample_rate_complex_sps": SAMPLE_RATE,
            "baseband_filter_hz": BASEBAND_FILTER_HZ,
            "representation": "CS8_INTERLEAVED_SIGNED_INT8_IQ",
            "rf_amp": RF_AMP,
            "antenna_power": ANTENNA_POWER,
            "lna_db": LNA_DB,
            "vga_db": VGA_DB,
        },
        "tool_versions": {
            "hackrf_transfer_header": hackrf_transfer_version,
        },
        "command": command,
        "transfer_exit_code": transfer_exit,
        "expected_complex_samples": expected_samples,
        "expected_size_bytes": expected_bytes,
        "actual_size_bytes": actual_bytes,
        "sha256": raw_sha256,
        "raw_file": str(raw_file.resolve()),
        "activation_log": str(activation_log.resolve()),
        "transfer_log": str(transfer_log.resolve()),
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    notes_path.write_text(
        f"# HackRF Capture {args.capture_id}\n\n"
        f"- Sensor label: {args.sensor}\n"
        f"- Engineering only: true\n"
        f"- Started: {start_wall}\n"
        f"- Finished: {finish_wall}\n"
        f"- Expected complex samples: {expected_samples}\n"
        f"- Expected bytes: {expected_bytes}\n"
        f"- Actual bytes: {actual_bytes}\n"
        f"- Transfer exit code: {transfer_exit}\n\n"
        "## Interpretation\n\n"
        "Engineering provenance validation only.\n",
        encoding="utf-8",
    )

    sidecars = [
        activation_log,
        transfer_log,
        receiver_log,
        manifest_path,
        notes_path,
    ]

    with hashes_path.open("x", encoding="utf-8") as handle:
        if raw_file.exists():
            handle.write(
                f"{raw_sha256}  {raw_file.resolve()}\n"
            )

        for path in sidecars:
            handle.write(
                f"{sha256_file(path)}  {path.resolve()}\n"
            )

    print()
    print("=== COMPLETED ===")
    print("transfer_exit_code =", transfer_exit)
    print("actual_bytes =", actual_bytes)
    print("sha256 =", raw_sha256)
    print("manifest =", manifest_path)
    print("activation_log =", activation_log)
    print("transfer_log =", transfer_log)

    valid = (
        transfer_exit == 0
        and actual_bytes == expected_bytes
        and raw_sha256 is not None
    )

    if not valid:
        print("CAPTURE PROVENANCE PRECHECK: FAIL")
        return 1

    print("CAPTURE PROVENANCE PRECHECK: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
