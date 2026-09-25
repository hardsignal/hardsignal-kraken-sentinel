"""Build the factual evidence boundary consumed by Sentinel AI."""

import hashlib
import json
from pathlib import Path

from ai.schemas import (
    EVIDENCE_BUNDLE_VERSION,
    validate_evidence_bundle,
)
from watcher.session_summary import (
    build_session_summary as build_core_session_summary,
)


DEFAULT_BURSTS_LOG = Path.home() / "kraken_bursts.log"
DEFAULT_TRACK_LOG = Path.home() / "kraken_track_events.log"
DEFAULT_EPISODE_LOG = Path.home() / "kraken_episode_events.jsonl"
DEFAULT_ML_RESULTS = Path("results/ml/prospective")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ml_result(session_id, ml_results_dir=DEFAULT_ML_RESULTS):
    path = Path(ml_results_dir) / f"{session_id}.json"

    if not path.is_file():
        raise FileNotFoundError(
            f"ML result not found for session {session_id}: {path}"
        )

    record = json.loads(path.read_text(encoding="utf-8"))

    if record.get("session_id") != session_id:
        raise ValueError("ML result session_id mismatch")

    return path, record


def build_evidence_bundle(
    session_id,
    *,
    bursts_log=DEFAULT_BURSTS_LOG,
    track_log=DEFAULT_TRACK_LOG,
    episode_log=DEFAULT_EPISODE_LOG,
    ml_results_dir=DEFAULT_ML_RESULTS,
):
    core = build_core_session_summary(
        session_id,
        bursts_log=Path(bursts_log),
        track_log=Path(track_log),
        episode_log=Path(episode_log),
    )

    ml_path, ml = load_ml_result(
        session_id,
        ml_results_dir=ml_results_dir,
    )

    bundle = {
        "schema_version": EVIDENCE_BUNDLE_VERSION,
        "session_id": session_id,
        "core": core,
        "ml": ml,
        "provenance": {
            "ml_result_path": str(ml_path),
            "ml_result_sha256": sha256_file(ml_path),
        },
    }

    return validate_evidence_bundle(bundle)
