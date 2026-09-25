"""Command-line interface for Sentinel AI."""

import argparse
import sys

from ai.artifact import build_report_artifact, save_report_artifact
from ai.evidence_bundle import build_evidence_bundle
from ai.llm_client import SentinelLLMError, verify_model_digest
from ai.experiment import (
    build_experiment_prompt,
    suggest_experiment_from_prompt,
)
from ai.experiment_guard import SentinelExperimentGuardError
from ai.final_report import compose_final_report
from ai.history_artifact import (
    build_history_artifact,
    save_history_artifact,
)
from ai.history_experiment import (
    build_history_experiment_prompt,
    suggest_history_experiment_from_prompt,
)
from ai.history_report import build_history_report


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a grounded Sentinel AI session report."
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Recorded Sentinel session ID",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save an auditable JSON report artifact",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Run Sentinel AI v0.2 prior-session historical reasoning",
    )
    parser.add_argument(
        "--output-dir",
        default="results/ai",
        help="Artifact output directory",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        if args.history:
            model_digest = verify_model_digest()

            historical = build_history_report(
                args.session
            )
            history_prompt = build_history_experiment_prompt(
                args.session
            )
            experiment = suggest_history_experiment_from_prompt(
                history_prompt
            )

            print("=" * 70)
            print("HARDSIGNAL LABS — SENTINEL AI v0.2 HISTORY")
            print("=" * 70)
            print(historical["text"])
            print()
            print("Next controlled experiment:")
            print(experiment)

            if args.save:
                artifact = build_history_artifact(
                    target_session_id=args.session,
                    history_bundle=historical["history"],
                    history_report=historical["text"],
                    experiment_prompt=history_prompt,
                    experiment_suggestion=experiment,
                    model_digest=model_digest,
                )
                path = save_history_artifact(
                    artifact,
                    output_dir=args.output_dir,
                )

                print()
                print(f"Saved: {path}")

            return 0

        bundle = build_evidence_bundle(args.session)
        model_digest = verify_model_digest()
        experiment_prompt = build_experiment_prompt(bundle)
        experiment = suggest_experiment_from_prompt(experiment_prompt)
        report = compose_final_report(bundle, experiment)

    except FileNotFoundError as exc:
        print(f"SENTINEL_AI_ERROR: {exc}", file=sys.stderr)
        return 2

    except SentinelLLMError as exc:
        print(f"SENTINEL_AI_LLM_ERROR: {exc}", file=sys.stderr)
        return 4

    except SentinelExperimentGuardError as exc:
        print(
            f"SENTINEL_AI_EXPERIMENT_REJECT: {exc}",
            file=sys.stderr,
        )
        return 6

    except ValueError as exc:
        print(f"SENTINEL_AI_EVIDENCE_ERROR: {exc}", file=sys.stderr)
        return 5

    print("=" * 70)
    print("HARDSIGNAL LABS — SENTINEL AI v0.1")
    print("=" * 70)
    print(f"Session: {args.session}")
    print()
    print(report)

    if args.save:
        artifact = build_report_artifact(
            session_id=args.session,
            evidence_bundle=bundle,
            experiment_prompt=experiment_prompt,
            experiment_suggestion=experiment,
            report=report,
            model_digest=model_digest,
        )
        path = save_report_artifact(
            artifact,
            output_dir=args.output_dir,
        )
        print()
        print(f"Saved: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
