import argparse
import json
from pathlib import Path

if __package__:
    from watcher.episode_report import (
        build_episode_report,
        format_episode_report,
        load_episode_events,
    )
else:
    from episode_report import (
        build_episode_report,
        format_episode_report,
        load_episode_events,
    )


DEFAULT_LOG = Path.home() / "kraken_episode_events.jsonl"


def build_parser():
    parser = argparse.ArgumentParser(
        description="Summarize Kraken RF Sentinel source episodes."
    )

    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help=f"Episode JSONL log (default: {DEFAULT_LOG})",
    )

    parser.add_argument(
        "--session",
        help="Only include one session_id.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit report as JSON instead of text.",
    )

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    events = load_episode_events(
        args.log,
        session_id=args.session,
    )

    if not events:
        print("No episode events found.")
        print(f"log: {args.log}")

        if args.session is not None:
            print(f"session: {args.session}")

        return 0

    report = build_episode_report(events)

    if args.json:
        print(
            json.dumps(
                report,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(format_episode_report(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
