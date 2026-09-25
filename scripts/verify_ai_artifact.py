#!/usr/bin/env python3
"""Offline, read-only verifier for any Sentinel AI v1.0 artifact."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai.v1_artifact import verify_v1_artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--source-dir", type=Path, help="Also verify the recorded ML JSON sources against this directory")
    args = parser.parse_args(argv)
    try:
        artifact = verify_v1_artifact(args.artifact, source_dir=args.source_dir)
    except (ValueError, OSError, UnicodeError, RecursionError) as exc:
        print(f"FAIL Sentinel AI v1 artifact: {exc}", file=sys.stderr)
        return 1
    scope = "embedded + current sources" if args.source_dir is not None else "embedded sources only"
    print(f"PASS Sentinel AI v1 artifact ({artifact['mode']}; {scope})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
