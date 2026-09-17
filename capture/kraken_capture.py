#!/usr/bin/env python3

"""
Hardsignal Labs — Kraken Capture Manifest

Creates an evidence manifest for a controlled KrakenSDR IQ acquisition.

This tool does NOT:
- modify IQ files
- move IQ files
- delete IQ files
- analyse RF identity
- alter KrakenSDR configuration

It records acquisition boundaries and provenance so that later analysis
can be traced back to the exact source files and configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


IQ_DIR = Path.home() / "krakensdr_doa/_share/records/iq"
SETTINGS_FILE = Path.home() / "krakensdr_doa/_share/settings.json"
STATE_DIR = Path.home() / ".local/state/hardsignal-kraken-sentinel"
CAPTURE_ROOT = Path("captures")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


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


def load_settings() -> dict:
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    except Exception as exc:
        return {
            "settings_file": str(SETTINGS_FILE),
            "error": str(exc),
        }

    wanted = [
        "vfo_freq_0",
        "vfo_bw_0",
        "vfo_squelch_mode_0",
        "vfo_squelch_0",
        "vfo_iq_0",
    ]

    return {
        "settings_file": str(SETTINGS_FILE),
        "settings_sha256": sha256_file(SETTINGS_FILE),
        "values": {key: settings.get(key) for key in wanted},
    }


def list_iq_files() -> dict[str, dict]:
    result = {}

    if not IQ_DIR.exists():
        return result

    for path in sorted(IQ_DIR.glob("*.iq")):
        stat = path.stat()

        result[str(path.resolve())] = {
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }

    return result


def state_path(capture_id: str) -> Path:
    return STATE_DIR / f"{capture_id}.json"


def command_start(capture_id: str, note: str | None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    path = state_path(capture_id)

    if path.exists():
        raise SystemExit(f"Capture state already exists: {path}")

    state = {
        "format": "HARDSIGNAL_KRAKEN_CAPTURE_STATE_V1",
        "capture_id": capture_id,
        "started_at": now_iso(),
        "git_head_at_start": git_head(),
        "note": note,
        "iq_directory": str(IQ_DIR),
        "settings_at_start": load_settings(),
        "iq_files_at_start": list_iq_files(),
    }

    with path.open("x", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Capture started: {capture_id}")
    print(f"State: {path}")
    print(f"IQ files before capture: {len(state['iq_files_at_start'])}")


def command_finish(capture_id: str) -> None:
    path = state_path(capture_id)

    if not path.exists():
        raise SystemExit(f"No capture state found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        state = json.load(handle)

    before = state["iq_files_at_start"]
    after = list_iq_files()

    new_paths = sorted(set(after) - set(before))

    changed_preexisting = []

    for name, old_meta in before.items():
        if name in after and after[name] != old_meta:
            changed_preexisting.append(name)

    files = []

    for name in new_paths:
        iq_path = Path(name)

        files.append({
            "path": name,
            "name": iq_path.name,
            "size_bytes": iq_path.stat().st_size,
            "sha256": sha256_file(iq_path),
        })

    manifest = {
        "format": "HARDSIGNAL_KRAKEN_CAPTURE_MANIFEST_V1",
        "capture_id": capture_id,
        "started_at": state["started_at"],
        "finished_at": now_iso(),
        "note": state.get("note"),
        "git_head_at_start": state["git_head_at_start"],
        "git_head_at_finish": git_head(),
        "iq_directory": str(IQ_DIR),
        "iq_count_before": len(before),
        "iq_count_after": len(after),
        "new_iq_file_count": len(files),
        "settings_at_start": state["settings_at_start"],
        "settings_at_finish": load_settings(),
        "changed_preexisting_iq_files": changed_preexisting,
        "files": files,
    }

    output_dir = CAPTURE_ROOT / capture_id

    if output_dir.exists():
        raise SystemExit(f"Capture output already exists: {output_dir}")

    output_dir.mkdir(parents=True)

    manifest_path = output_dir / "manifest.json"

    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    hashes_path = output_dir / "files.sha256"

    with hashes_path.open("x", encoding="utf-8") as handle:
        for item in files:
            handle.write(f"{item['sha256']}  {item['path']}\n")

    notes_path = output_dir / "notes.md"

    with notes_path.open("x", encoding="utf-8") as handle:
        handle.write(f"# Capture {capture_id}\n\n")
        handle.write(f"- Started: {manifest['started_at']}\n")
        handle.write(f"- Finished: {manifest['finished_at']}\n")
        handle.write(f"- New IQ files: {len(files)}\n")

        if state.get("note"):
            handle.write(f"- Note: {state['note']}\n")

        handle.write("\n## Interpretation\n\n")
        handle.write("Not yet assigned.\n")

    path.unlink()

    print(f"Capture finished: {capture_id}")
    print(f"New IQ files: {len(files)}")
    print(f"Manifest: {manifest_path}")
    print(f"Hashes:   {hashes_path}")
    print(f"Notes:    {notes_path}")

    if changed_preexisting:
        print(
            f"WARNING: {len(changed_preexisting)} pre-existing IQ file(s) "
            "changed during capture.",
            file=sys.stderr,
        )


def command_status(capture_id: str) -> None:
    path = state_path(capture_id)

    if not path.exists():
        raise SystemExit(f"No active capture state: {capture_id}")

    with path.open("r", encoding="utf-8") as handle:
        state = json.load(handle)

    before = state["iq_files_at_start"]
    current = list_iq_files()
    new_paths = sorted(set(current) - set(before))

    print(f"Capture ID: {capture_id}")
    print(f"Started:    {state['started_at']}")
    print(f"IQ before:  {len(before)}")
    print(f"IQ now:     {len(current)}")
    print(f"New files:  {len(new_paths)}")

    for name in new_paths:
        print(f"  {Path(name).name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("capture_id")
    start.add_argument("--note")

    finish = sub.add_parser("finish")
    finish.add_argument("capture_id")

    status = sub.add_parser("status")
    status.add_argument("capture_id")

    args = parser.parse_args()

    if args.command == "start":
        command_start(args.capture_id, args.note)
    elif args.command == "finish":
        command_finish(args.capture_id)
    elif args.command == "status":
        command_status(args.capture_id)


if __name__ == "__main__":
    main()
