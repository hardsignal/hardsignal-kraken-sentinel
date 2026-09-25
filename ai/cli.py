"""Command-line interface for Sentinel AI."""

import argparse
import sys

from ai.evidence_bundle import build_evidence_bundle
from ai.llm_client import SentinelLLMError
from ai.output_guard import SentinelOutputGuardError
from ai.prompts import build_analyst_prompt
from ai.report import generate_grounded_report


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a grounded Sentinel AI session report."
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Recorded Sentinel session ID",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        bundle = build_evidence_bundle(args.session)
        prompt = build_analyst_prompt(bundle)
        report = generate_grounded_report(prompt)

    except FileNotFoundError as exc:
        print(f"SENTINEL_AI_ERROR: {exc}", file=sys.stderr)
        return 2

    except SentinelOutputGuardError as exc:
        print(
            f"SENTINEL_AI_FINAL_REJECT: {exc}",
            file=sys.stderr,
        )
        return 3

    except SentinelLLMError as exc:
        print(f"SENTINEL_AI_LLM_ERROR: {exc}", file=sys.stderr)
        return 4

    except ValueError as exc:
        print(f"SENTINEL_AI_EVIDENCE_ERROR: {exc}", file=sys.stderr)
        return 5

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL AI v0.1")
    print("=" * 70)
    print(f"Session: {args.session}")
    print()
    print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
