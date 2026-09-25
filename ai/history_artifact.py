"""Provenance-complete Sentinel AI v0.2 historical artifacts."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ai.artifact import canonical_sha256, text_sha256
from ai.history import load_formal_history, session_number
from ai.llm_client import DEFAULT_MODEL


HISTORY_ARTIFACT_VERSION = "0.2"


def sha256_file(path):
    h = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def build_source_record_hashes(
    target_session_id,
    *,
    results_dir=Path("results/ml/prospective"),
):
    results_dir = Path(results_dir)
    target_number = session_number(target_session_id)

    records = [
        record
        for record in load_formal_history(results_dir)
        if session_number(record["session_id"]) <= target_number
    ]

    if not any(
        record["session_id"] == target_session_id
        for record in records
    ):
        raise ValueError(
            "target session is not in the formal prospective set"
        )

    hashes = {}

    for record in records:
        session_id = record["session_id"]
        path = results_dir / f"{session_id}.json"

        if not path.is_file():
            raise FileNotFoundError(path)

        hashes[session_id] = sha256_file(path)

    return hashes


def build_history_artifact(
    *,
    target_session_id,
    history_bundle,
    history_report,
    experiment_prompt,
    experiment_suggestion,
    model_digest,
    model=DEFAULT_MODEL,
    results_dir=Path("results/ml/prospective"),
):
    if history_bundle.get("target_session_id") != target_session_id:
        raise ValueError("history target_session_id mismatch")

    source_hashes = build_source_record_hashes(
        target_session_id,
        results_dir=results_dir,
    )

    return {
        "artifact_version": HISTORY_ARTIFACT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_mode": "deterministic_history_with_ai_experiment",
        "ai_scope": "historical_next_controlled_experiment_only",
        "target_session_id": target_session_id,
        "model": model,
        "model_digest": model_digest,
        "history_bundle": history_bundle,
        "history_bundle_sha256": canonical_sha256(history_bundle),
        "history_report": history_report,
        "history_report_sha256": text_sha256(history_report),
        "experiment_prompt": experiment_prompt,
        "experiment_prompt_sha256": text_sha256(experiment_prompt),
        "experiment_suggestion": experiment_suggestion,
        "experiment_suggestion_sha256": text_sha256(
            experiment_suggestion
        ),
        "source_record_sha256": source_hashes,
        "source_record_manifest_sha256": canonical_sha256(
            source_hashes
        ),
    }


def save_history_artifact(
    artifact,
    *,
    output_dir=Path("results/ai"),
):
    output_dir = (
        Path(output_dir)
        / "history"
        / artifact["target_session_id"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = (
        artifact["created_at"]
        .replace(":", "")
        .replace("+", "_")
    )

    path = output_dir / (
        f"sentinel_ai_history_v02_{stamp}.json"
    )

    path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path
