"""Sentinel AI artifact contract 1.0: builders and read-only validation.

Legacy constructors remain in artifact.py/history_artifact.py. This contract
binds supplied evidence, not authorship, raw RF logs or empirical model validity.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

from ai.artifact import canonical_sha256, text_sha256
from ai.experiment import build_experiment_prompt
from ai.experiment_guard import validate_normal_experiment_suggestion
from ai.final_report import compose_final_report
from ai.history import HistoryEvidenceSnapshot, require_history_snapshot
from ai.history_report import build_history_report
from ai.history_experiment import build_history_experiment_prompt
from ai.history_experiment_guard import validate_history_experiment
from ai.llm_client import DEFAULT_MODEL, EXPECTED_MODEL_DIGEST
from ai.schemas import validate_evidence_bundle

VERSION = "1.0"
SCHEMA = "sentinel-ai-artifact/1.0"
POLICY_VERSION = "sentinel-ai-scientific-policy/1.0"
DERIVATION_VERSION = "sentinel-ai-deterministic/1.0"
TRAINING_SHA256 = "e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51"
LINEAGE = {
    "model_version": "0.1", "record_version": "0.1",
    "training_dataset_sha256": TRAINING_SHA256,
}
MODES = {
    "normal": ("deterministic_with_ai_experiment", "next_controlled_experiment_only"),
    "history": ("deterministic_history_with_ai_experiment", "historical_next_controlled_experiment_only"),
}
COMMON_FIELDS = {
    "artifact_version", "schema_version", "created_at", "mode", "session_id",
    "report_mode", "ai_scope", "model", "model_digest", "scientific_policy_version",
    "derivation_version", "ml_lineage", "source_records_json", "source_record_sha256",
    "source_record_manifest_sha256", "experiment_prompt", "experiment_prompt_sha256",
    "experiment_suggestion", "experiment_suggestion_sha256", "artifact_sha256",
}
MODE_FIELDS = {
    "normal": {"evidence_bundle", "evidence_bundle_sha256", "deterministic_report",
               "deterministic_report_sha256", "report", "report_sha256", "core_evidence_scope"},
    "history": {"history_bundle", "history_bundle_sha256", "history_report", "history_report_sha256"},
}
SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,199}")
HASH_RE = re.compile(r"[0-9a-f]{64}")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"non-finite JSON value: {value}")


def _json_types(value):
    if isinstance(value, dict):
        for key, item in value.items():
            _require(type(key) is str, "JSON keys must be strings")
            _json_types(item)
    elif isinstance(value, list):
        for item in value:
            _json_types(item)
    elif type(value) is float:
        _require(math.isfinite(value), "non-finite JSON number")
    else:
        _require(type(value) in (str, int, bool, type(None)), "unsupported JSON type")


def strict_json_loads(text):
    value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    _json_types(value)
    return value


def _session(value):
    _require(isinstance(value, str) and SESSION_RE.fullmatch(value), "invalid session_id")


def _number(value, label, *, nonnegative=False, integer=False):
    _require(type(value) in ((int,) if integer else (int, float)), f"{label} must be numeric")
    _require(math.isfinite(value), f"{label} must be finite")
    if nonnegative:
        _require(value >= 0, f"{label} must be nonnegative")


def _ml(record, session):
    _require(type(record) is dict, "ML source must be an object")
    _require(record.get("session_id") == session, "ML source session_id mismatch")
    for key, expected in LINEAGE.items():
        _require(record.get(key) == expected, f"ML {key} lineage mismatch")
    _require(type(record.get("assigned_cluster")) is int and record["assigned_cluster"] in (0, 1, 2),
             "invalid assigned_cluster")
    _require(record.get("novelty") in ("WITHIN_OBSERVED_TRAINING_RANGE", "OUTSIDE_OBSERVED_TRAINING_RANGE"),
             "invalid novelty")
    _require(record.get("scientific_scope") == "RF/DoA behavioural regime assignment; not transmitter identity",
             "ML scientific_scope mismatch")
    features = record.get("feature_row")
    _require(type(features) is dict and features.get("session_id") == session, "feature_row session_id mismatch")
    from ai.history import HISTORY_FEATURES
    for key in HISTORY_FEATURES:
        _number(features.get(key), key, integer=key == "burst_count", nonnegative=key != "peak_power_mean_db")
    distances = record.get("distances")
    _require(type(distances) is dict and set(distances) == {"0", "1", "2"}, "invalid ML distances")
    for value in distances.values():
        _number(value, "distance", nonnegative=True)
    for key in ("nearest_distance", "second_nearest_distance", "separation_ratio", "distance_vs_training_max"):
        _number(record.get(key), key, nonnegative=True)
    ordered = sorted(distances.values())
    _require(record["nearest_distance"] == ordered[0] and record["second_nearest_distance"] == ordered[1],
             "ML distance ordering mismatch")
    _require(distances[str(record["assigned_cluster"])] == ordered[0], "ML assignment/distance mismatch")


def _core(core, session):
    _require(type(core) is dict and core.get("session_id") == session, "Core session_id mismatch")
    _require(type(core.get("version")) is int and core["version"] == 1, "unsupported Core version")
    for key in ("bursts", "track_events", "episodes"):
        _require(type(core.get(key)) is dict, f"Core {key} must be an object")
    missing = core.get("missing_logs")
    _require(type(missing) is list and all(type(item) is str for item in missing), "invalid missing_logs")
    bursts = core["bursts"]
    _require(set(bursts) == {"total", "STABLE", "MULTIPATH", "LOW_QUALITY"}, "invalid Core bursts")
    for key, value in bursts.items():
        _number(value, key, nonnegative=True, integer=True)
    _require(bursts["total"] == sum(bursts[key] for key in ("STABLE", "MULTIPATH", "LOW_QUALITY")),
             "Core burst total mismatch")
    from watcher.session_summary import TRACK_EVENTS
    _require(set(core["track_events"]) == set(TRACK_EVENTS), "invalid Core track events")
    for value in core["track_events"].values():
        _number(value, "track count", nonnegative=True, integer=True)
    episodes = core["episodes"]
    for key in ("event_count", "episodes_started", "episodes_closed", "shift_boundaries",
                "track_losses", "degraded_closed_episodes"):
        _number(episodes.get(key), key, nonnegative=True, integer=True)
    _require(type(episodes.get("active_episode_ids")) is list, "invalid active_episode_ids")
    for value in episodes["active_episode_ids"]:
        _number(value, "episode id", integer=True)
    _require(type(episodes.get("closed_episodes")) is list, "invalid closed_episodes")
    for episode in episodes["closed_episodes"]:
        _require(type(episode) is dict, "closed episode must be an object")
        for key in ("episode_id", "start_index", "end_index", "max_support"):
            _number(episode.get(key), key, integer=True)
        for key in ("start_mean", "latest_mean"):
            _number(episode.get(key), key)
        _require(type(episode.get("degraded_seen")) is bool, "invalid degraded_seen")
        _require(type(episode.get("end_reason")) is str, "invalid end_reason")


def envelope_sha256(artifact):
    return canonical_sha256({key: value for key, value in artifact.items() if key != "artifact_sha256"})


def _base(mode, session, sources, prompt, suggestion, model, digest):
    hashes = {key: text_sha256(value) for key, value in sources.items()}
    report_mode, scope = MODES[mode]
    return {
        "artifact_version": VERSION, "schema_version": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(), "mode": mode,
        "session_id": session, "report_mode": report_mode, "ai_scope": scope,
        "model": model, "model_digest": digest,
        "scientific_policy_version": POLICY_VERSION, "derivation_version": DERIVATION_VERSION,
        "ml_lineage": dict(LINEAGE), "source_records_json": sources,
        "source_record_sha256": hashes, "source_record_manifest_sha256": canonical_sha256(hashes),
        "experiment_prompt": prompt, "experiment_prompt_sha256": text_sha256(prompt),
        "experiment_suggestion": suggestion, "experiment_suggestion_sha256": text_sha256(suggestion),
    }


def build_v1_report_artifact(*, session_id, evidence_bundle, experiment_prompt,
                             experiment_suggestion, report, model=DEFAULT_MODEL, model_digest=None):
    bundle = strict_json_loads(json.dumps(evidence_bundle, allow_nan=False))
    source = bundle["provenance"].pop("ml_result_json", None)
    _require(type(source) is str, "normal v1 artifact requires captured ML source bytes")
    artifact = _base("normal", session_id, {session_id: source}, experiment_prompt,
                     experiment_suggestion, model, model_digest)
    artifact.update({
        "evidence_bundle": bundle, "evidence_bundle_sha256": canonical_sha256(bundle),
        "core_evidence_scope": "embedded_deterministic_summary",
        "deterministic_report": compose_final_report(bundle, ""),
        "report": report,
    })
    for key in ("deterministic_report", "report"):
        artifact[key + "_sha256"] = text_sha256(artifact[key])
    artifact["artifact_sha256"] = envelope_sha256(artifact)
    validate_v1_artifact(artifact)
    return artifact


def build_v1_history_artifact(*, target_session_id, history_bundle, history_report,
                              experiment_prompt, experiment_suggestion, model_digest,
                              model=DEFAULT_MODEL, snapshot=None):
    snapshot = require_history_snapshot(snapshot, target_session_id)
    sources = {key: data.decode("utf-8") for key, data in snapshot.sources}
    artifact = _base("history", target_session_id, sources, experiment_prompt,
                     experiment_suggestion, model, model_digest)
    artifact.update({
        "history_bundle": strict_json_loads(json.dumps(history_bundle, allow_nan=False)),
        "history_bundle_sha256": canonical_sha256(history_bundle),
        "history_report": history_report, "history_report_sha256": text_sha256(history_report),
    })
    artifact["artifact_sha256"] = envelope_sha256(artifact)
    validate_v1_artifact(artifact)
    return artifact


def validate_v1_artifact(artifact, *, source_dir=None):
    """Validate arbitrary v1 content; source_dir opts into current-file checks.

    Never follow artifact-supplied paths. Never generate AI text, load model assets,
    write files, or reinterpret a historical artifact as v1.
    """
    try:
        _validate_v1_artifact(artifact, source_dir=source_dir)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError(f"malformed v1 artifact: {exc}") from exc
    return artifact


def _validate_v1_artifact(a, *, source_dir):
    _json_types(a)
    _require(type(a) is dict, "artifact must be a JSON object")
    mode = a.get("mode")
    _require(type(mode) is str and mode in MODES, "unsupported artifact mode")
    _require(set(a) == COMMON_FIELDS | MODE_FIELDS[mode], "missing or unexpected artifact fields")
    for key, value in {
        "artifact_version": VERSION, "schema_version": SCHEMA, "model": DEFAULT_MODEL,
        "model_digest": EXPECTED_MODEL_DIGEST, "scientific_policy_version": POLICY_VERSION,
        "derivation_version": DERIVATION_VERSION, "ml_lineage": LINEAGE,
        "report_mode": MODES[mode][0], "ai_scope": MODES[mode][1],
    }.items():
        _require(a[key] == value, f"{key} mismatch")
    _require(type(a["created_at"]) is str, "created_at must be text")
    timestamp = datetime.fromisoformat(a["created_at"])
    _require(timestamp.tzinfo is not None and timestamp.utcoffset().total_seconds() == 0,
             "created_at must be UTC")
    _session(a["session_id"])
    for key, value in a.items():
        if key.endswith("_sha256") and key != "source_record_sha256":
            _require(type(value) is str and HASH_RE.fullmatch(value), f"invalid {key}")
    _require(envelope_sha256(a) == a["artifact_sha256"], "artifact_sha256 mismatch")
    for field in ("experiment_prompt", "experiment_suggestion"):
        _require(type(a[field]) is str and a[field].strip(), f"{field} must be nonempty text")
        _require(text_sha256(a[field]) == a[field + "_sha256"], f"{field} hash mismatch")
    sources, hashes = a["source_records_json"], a["source_record_sha256"]
    _require(type(sources) is dict and type(hashes) is dict and sources and set(sources) == set(hashes),
             "source manifest membership mismatch")
    records = {}
    for session, text in sources.items():
        _session(session)
        _require(type(text) is str, "source record must be exact UTF-8 JSON text")
        _require(type(hashes[session]) is str and HASH_RE.fullmatch(hashes[session]), "invalid source digest")
        _require(text_sha256(text) == hashes[session], "source record hash mismatch")
        records[session] = strict_json_loads(text)
        _ml(records[session], session)
    _require(canonical_sha256(hashes) == a["source_record_manifest_sha256"], "source manifest hash mismatch")
    session = a["session_id"]
    if mode == "history":
        snapshot = HistoryEvidenceSnapshot(session, tuple((key, text.encode("utf-8")) for key, text in sorted(sources.items())))
        expected = build_history_report(session, snapshot=snapshot)
        _require(canonical_sha256(a["history_bundle"]) == canonical_sha256(expected["history"]), "history bundle semantic mismatch")
        _require(canonical_sha256(a["history_bundle"]) == a["history_bundle_sha256"], "history bundle hash mismatch")
        _require(a["history_report"] == expected["text"], "history report semantic mismatch")
        _require(text_sha256(a["history_report"]) == a["history_report_sha256"], "history report hash mismatch")
        _require(a["experiment_prompt"] == build_history_experiment_prompt(session, snapshot=snapshot), "history prompt mismatch")
        validate_history_experiment(a["experiment_suggestion"], history_report=expected["text"])
    else:
        _require(set(sources) == {session}, "normal source manifest must contain only the target")
        _require(a["core_evidence_scope"] == "embedded_deterministic_summary", "unsupported Core evidence scope")
        bundle = a["evidence_bundle"]
        _require(type(bundle) is dict, "evidence bundle must be an object")
        validate_evidence_bundle(bundle)
        _require(bundle["session_id"] == session, "evidence session_id mismatch")
        _require(bundle["ml"] == records[session], "embedded ML/source mismatch")
        _core(bundle["core"], session)
        provenance = bundle["provenance"]
        _require(set(provenance) == {"ml_result_path", "ml_result_sha256"}, "invalid normal provenance fields")
        _require(type(provenance["ml_result_path"]) is str, "ML path must be text")
        _require(Path(provenance["ml_result_path"]).name == f"{session}.json", "ML path/session mismatch")
        _require(provenance["ml_result_sha256"] == hashes[session], "normal ML provenance mismatch")
        _require(canonical_sha256(bundle) == a["evidence_bundle_sha256"], "evidence bundle hash mismatch")
        _require(a["deterministic_report"] == compose_final_report(bundle, ""), "deterministic report mismatch")
        _require(a["report"] == compose_final_report(bundle, a["experiment_suggestion"]), "final report mismatch")
        for field in ("deterministic_report", "report"):
            _require(text_sha256(a[field]) == a[field + "_sha256"], f"{field} hash mismatch")
        _require(a["experiment_prompt"] == build_experiment_prompt(bundle), "normal prompt mismatch")
        validate_normal_experiment_suggestion(a["experiment_suggestion"])
    if source_dir is not None:
        root = Path(source_dir).resolve()
        for session, expected_hash in hashes.items():
            path = (root / f"{session}.json").resolve()
            _require(path.is_relative_to(root), "source path escapes source directory")
            _require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash,
                     f"current source SHA256 mismatch: {session}")


def verify_v1_artifact(path, *, source_dir=None):
    return validate_v1_artifact(strict_json_loads(Path(path).read_text(encoding="utf-8")), source_dir=source_dir)


def save_v1_artifact(artifact, *, output_dir=Path("results/ai")):
    validate_v1_artifact(artifact)
    root = Path(output_dir)
    if artifact["mode"] == "history":
        root /= "history"
    root /= artifact["session_id"]
    root.mkdir(parents=True, exist_ok=True)
    stamp = artifact["created_at"].replace(":", "").replace("+", "_")
    path = root / f"sentinel_ai_v1_{stamp}.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return path
