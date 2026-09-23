"""Command-line entry point for offline Session Summary v1."""

import argparse
import json
from pathlib import Path
import sys

if __package__:
    from watcher.session_summary import build_session_summary, format_session_summary
else:
    from session_summary import build_session_summary, format_session_summary


def build_parser():
    parser = argparse.ArgumentParser(description="Summarize a Kraken RF Sentinel session offline.")
    parser.add_argument("--session", required=True, help="Session ID to include.")
    for option, filename in (("bursts", "kraken_bursts.log"),
                             ("track", "kraken_track_events.log"),
                             ("episode", "kraken_episode_events.jsonl")):
        default = Path.home() / filename
        parser.add_argument(f"--{option}-log", type=Path, default=default,
                            help=f"Input log (default: {default})")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = build_session_summary(
            args.session, bursts_log=args.bursts_log,
            track_log=args.track_log, episode_log=args.episode_log,
        )
    except (OSError, ValueError) as exc:
        print(f"session summary: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
          if args.json else format_session_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
