#!/usr/bin/env python3

import argparse
import json
from datetime import datetime
from pathlib import Path

EPISODE_GAP_SECONDS = 4.000
FORMAT = "HARDSIGNAL_KRAKEN_EPISODES_V1"


def load_manifest(capture_dir):
    path = capture_dir / "manifest.json"
    if not path.is_file():
        raise SystemExit(f"ERROR: manifest not found: {path}")

    data = json.loads(path.read_text())

    if data.get("format") != "HARDSIGNAL_KRAKEN_CAPTURE_MANIFEST_V1":
        raise SystemExit(
            f"ERROR: unsupported manifest format: {data.get('format')}"
        )

    return data


def collect_files(manifest):
    rows = []

    for item in manifest["files"]:
        path = Path(item["path"])

        if not path.is_file():
            raise SystemExit(f"ERROR: IQ file missing: {path}")

        stat = path.stat()

        rows.append({
            "path": str(path),
            "name": path.name,
            "mtime_ns": stat.st_mtime_ns,
            "size_bytes": item["size_bytes"],
            "sha256": item["sha256"],
        })

    rows.sort(key=lambda x: (x["mtime_ns"], x["name"]))
    return rows


def group_files(rows):
    episodes = []

    for row in rows:
        if not episodes:
            episodes.append([row])
            continue

        previous = episodes[-1][-1]
        gap = (row["mtime_ns"] - previous["mtime_ns"]) / 1e9

        if gap > EPISODE_GAP_SECONDS:
            episodes.append([row])
        else:
            episodes[-1].append(row)

    return episodes


def iso_from_ns(ns):
    return datetime.fromtimestamp(ns / 1e9).astimezone().isoformat()


def build_output(manifest, episodes):
    result = {
        "format": FORMAT,
        "capture_id": manifest["capture_id"],
        "source_manifest_format": manifest["format"],
        "episode_gap_seconds": EPISODE_GAP_SECONDS,
        "comparison": ">",
        "episode_count": len(episodes),
        "file_count": sum(len(ep) for ep in episodes),
        "episodes": [],
    }

    previous_episode_last_ns = None

    for number, files in enumerate(episodes, 1):
        first_ns = files[0]["mtime_ns"]
        last_ns = files[-1]["mtime_ns"]

        if previous_episode_last_ns is None:
            preceding_gap = None
        else:
            preceding_gap = (
                first_ns - previous_episode_last_ns
            ) / 1e9

        episode = {
            "episode": number,
            "file_count": len(files),
            "start_time": iso_from_ns(first_ns),
            "end_time": iso_from_ns(last_ns),
            "span_seconds": (last_ns - first_ns) / 1e9,
            "preceding_gap_seconds": preceding_gap,
            "files": files,
        }

        result["episodes"].append(episode)
        previous_episode_last_ns = last_ns

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Group provenance-recorded Kraken IQ files into temporal episodes."
    )
    parser.add_argument(
        "capture_dir",
        type=Path,
        help="Capture bundle directory containing manifest.json",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write episodes.json into the capture bundle",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.capture_dir)
    rows = collect_files(manifest)
    episodes = group_files(rows)
    result = build_output(manifest, episodes)

    print(f"Capture:       {result['capture_id']}")
    print(f"Files:         {result['file_count']}")
    print(f"Threshold:     > {EPISODE_GAP_SECONDS:.3f} s")
    print(f"Episodes:      {result['episode_count']}")
    print()

    for ep in result["episodes"]:
        gap = ep["preceding_gap_seconds"]
        gap_text = "START" if gap is None else f"{gap:.3f} s"

        print(
            f"E{ep['episode']:02d}  "
            f"files={ep['file_count']:2d}  "
            f"span={ep['span_seconds']:.3f} s  "
            f"preceding_gap={gap_text}"
        )

    if args.write:
        output = args.capture_dir / "episodes.json"
        output.write_text(json.dumps(result, indent=2) + "\n")
        print()
        print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
