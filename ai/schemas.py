"""Schema checks for Sentinel AI evidence bundles."""

EVIDENCE_BUNDLE_VERSION = "0.1"

CORE_KEYS = {
    "session_id",
    "version",
    "bursts",
    "track_events",
    "episodes",
    "missing_logs",
}

ML_KEYS = {
    "model_version",
    "record_version",
    "assigned_cluster",
    "distances",
    "nearest_distance",
    "second_nearest_distance",
    "separation_ratio",
    "distance_vs_training_max",
    "novelty",
    "scientific_scope",
    "feature_row",
    "training_dataset_sha256",
}


def validate_evidence_bundle(bundle):
    if bundle.get("schema_version") != EVIDENCE_BUNDLE_VERSION:
        raise ValueError("unsupported evidence bundle schema_version")

    session_id = bundle.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("missing session_id")

    core = bundle.get("core")
    if not isinstance(core, dict):
        raise ValueError("core must be an object")

    missing_core = CORE_KEYS - core.keys()
    if missing_core:
        raise ValueError(
            f"core missing fields: {sorted(missing_core)}"
        )

    if core.get("session_id") != session_id:
        raise ValueError("Core session_id does not match bundle session_id")

    ml = bundle.get("ml")
    if not isinstance(ml, dict):
        raise ValueError("ml must be an object")

    missing_ml = ML_KEYS - ml.keys()
    if missing_ml:
        raise ValueError(
            f"ml missing fields: {sorted(missing_ml)}"
        )

    if ml.get("session_id") not in (None, session_id):
        raise ValueError("ML session_id does not match bundle session_id")

    provenance = bundle.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("provenance must be an object")

    for field in ("ml_result_path", "ml_result_sha256"):
        if not provenance.get(field):
            raise ValueError(f"provenance missing {field}")

    return bundle
