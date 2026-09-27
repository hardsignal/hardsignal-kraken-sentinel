#!/usr/bin/env python3
"""Read-only Sentinel ML 1.0 verification. Run with the ML Python environment."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA256 = {
    "results/ml/rf_behaviour_dataset_v001.csv":
        "e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51",
    "results/ml/sentinel_behaviour_model_v001.joblib":
        "a4ab69ea6db1864a23f8b6e4e6435a18f02f335effe8e5609a985a16f1662a60",
    "results/ml/sentinel_behaviour_model_v001_manifest.json":
        "9fa35379507a65498a3c6b4f48f676204e0470c4d0ff6a2117fbb56ff1decb61",
}
MANIFEST = "results/ml/sentinel_behaviour_model_v001_manifest.json"
REQUIRED_FILES = tuple(FROZEN_SHA256) + (
    "results/ml/sentinel_ml_v1_release_manifest.md",
    "results/ml/rf_behaviour_dataset_prospective_v001.csv",
    "ml/__init__.py",
    "ml/dataset_builder.py",
    "ml/feature_schema.py",
    "ml/prospective_session.py",
    "ml/score_frozen_model.py",
    "tests/ml/__init__.py",
    "tests/ml/test_dataset_builder.py",
    "tests/ml/test_prospective_session.py",
    "tests/ml/test_verify_ml_release.py",
)


def verify(root=ROOT):
    """Report all checks and return a process exit code (0 only on success)."""
    root = Path(root).resolve()
    failures = []

    def report(label, error=None):
        print(f"{'FAIL' if error else 'PASS'} {label}"
              + (f": {error}" if error else ""), flush=True)
        if error:
            failures.append(label)

    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    report("required files", ", ".join(missing) if missing else None)

    for name, expected in FROZEN_SHA256.items():
        try:
            with (root / name).open("rb") as handle:
                actual = hashlib.file_digest(handle, "sha256").hexdigest()
            if actual != expected:
                raise ValueError(f"expected {expected}, got {actual}")
        except (OSError, ValueError) as exc:
            report(f"SHA256 {name}", str(exc))
        else:
            report(f"SHA256 {name}")

    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        dataset = "results/ml/rf_behaviour_dataset_v001.csv"
        if (manifest.get("training_dataset") != dataset
                or manifest.get("training_dataset_sha256") != FROZEN_SHA256[dataset]):
            raise ValueError("manifest training dataset provenance mismatch")
    except (OSError, ValueError) as exc:
        report("model manifest readable and provenance matches", str(exc))
    else:
        report("model manifest readable and provenance matches")

    try:
        modules = sorted((root / "ml").rglob("*.py"))
        if not modules:
            raise ValueError("no ML Python modules found")
        for module in modules:
            # Compile in memory: no imports, experiment execution, or .pyc writes.
            compile(module.read_bytes(), str(module), "exec")
    except (OSError, SyntaxError, ValueError) as exc:
        report("ML Python compilation", str(exc))
    else:
        report(f"ML Python compilation ({len(modules)} modules)")

    if failures:
        # The focused tests deserialize the model. Only run after provenance passes.
        report("tests/ml", "not run because prerequisite checks failed")
    else:
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "discover",
                 "-s", "tests/ml", "-p", "test_*.py", "-v"],
                cwd=root, capture_output=True, text=True, timeout=300,
            )
            if result.returncode:
                print(result.stdout + result.stderr, end="", flush=True)
                report("tests/ml", f"exit code {result.returncode}")
            else:
                report("tests/ml")
        except (OSError, subprocess.TimeoutExpired) as exc:
            report("tests/ml", str(exc))

    report("Sentinel ML 1.0 release verification",
           f"{len(failures)} failed checks" if failures else None)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(verify())
