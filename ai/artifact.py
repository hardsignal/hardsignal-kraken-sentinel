"""Versioned Sentinel AI report artifacts."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ai.llm_client import DEFAULT_MODEL


ARTIFACT_VERSION = "0.1"


def canonical_sha256(value):
    data = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_report_artifact(
    *,
    session_id,
    evidence_bundle,
    experiment_prompt,
    experiment_suggestion,
    report,
    model=DEFAULT_MODEL,
    model_digest=None,
):
    return {
        "artifact_version": ARTIFACT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "model": model,
        "model_digest": model_digest,
        "assigned_cluster": evidence_bundle["ml"]["assigned_cluster"],
        "novelty": evidence_bundle["ml"]["novelty"],
        "training_dataset_sha256": (
            evidence_bundle["ml"]["training_dataset_sha256"]
        ),
        "ml_result_sha256": (
            evidence_bundle["provenance"]["ml_result_sha256"]
        ),
        "evidence_bundle_sha256": canonical_sha256(evidence_bundle),
        "report_mode": "deterministic_with_ai_experiment",
        "ai_scope": "next_controlled_experiment_only",
        "experiment_prompt": experiment_prompt,
        "experiment_prompt_sha256": text_sha256(experiment_prompt),
        "experiment_suggestion": experiment_suggestion,
        "experiment_suggestion_sha256": text_sha256(experiment_suggestion),
        "report_sha256": text_sha256(report),
        "evidence_bundle": evidence_bundle,
        "report": report,
    }


def save_report_artifact(
    artifact,
    *,
    output_dir=Path("results/ai"),
):
    output_dir = Path(output_dir) / artifact["session_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = (
        artifact["created_at"]
        .replace(":", "")
        .replace("+", "_")
    )

    path = output_dir / f"sentinel_ai_v01_{stamp}.json"

    path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path
