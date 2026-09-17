#!/usr/bin/env python3

import argparse
import time
from datetime import datetime
from pathlib import Path

FORMAT = "HARDSIGNAL_OPERATOR_ACTIVATIONS_V1"


def timestamp():
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def main():
    parser = argparse.ArgumentParser(
        description="Record independent operator activation timestamps."
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output activation log",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=6,
        help="Number of controlled activations (default: 6)",
    )
    parser.add_argument(
        "--quiet",
        type=float,
        default=15.0,
        help="Quiet interval after each activation in seconds (default: 15)",
    )
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"ERROR: output already exists: {args.output}")

    with args.output.open("x") as f:
        f.write(f"FORMAT | {FORMAT}\n")
        f.write(f"COUNT | {args.count}\n")
        f.write(f"QUIET_SECONDS | {args.quiet:.3f}\n")
        f.flush()

        print()
        print("CONTROLLED ACTIVATION LOGGER")
        print("============================")
        print(f"Events: {args.count}")
        print(f"Quiet interval: {args.quiet:.3f} s")
        print()
        print("For each event:")
        print("  1. Prepare the TPMS trigger.")
        print("  2. Press ENTER at the moment you trigger it.")
        print("  3. Do not activate anything during QUIET.")
        print()

        for i in range(1, args.count + 1):
            label = f"A{i}"

            input(f"{label} READY — press ENTER and trigger now: ")

            wall = timestamp()
            mono_ns = time.monotonic_ns()

            line = (
                f"{label} | wall={wall} | "
                f"monotonic_ns={mono_ns}\n"
            )

            f.write(line)
            f.flush()

            print(line.rstrip())

            if i != args.count:
                print(f"QUIET {args.quiet:.3f} seconds...")
                time.sleep(args.quiet)
                print("QUIET COMPLETE")
                print()

        print()
        print("ALL ACTIVATIONS RECORDED")
        print(f"Log: {args.output}")


if __name__ == "__main__":
    main()
