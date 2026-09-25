#!/usr/bin/env python3
"""Read-only, offline Sentinel AI v0.2 release verification."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

TAG = "sentinel-ai-v0.2"
RELEASE_COMMIT = "4a08b8cc2b42745dd0443d4e331bb5f2fbc23806"

MODEL = "qwen3:14b"
MODEL_DIGEST = (
    "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"
)

TARGET_SESSION = "TPMS-NATURAL-015-20260925-020456"

REFERENCE = (
    "results/ai/history/"
    "TPMS-NATURAL-015-20260925-020456/"
    "sentinel_ai_history_v02_2026-09-25T030154.793526_0000.json"
)

REFERENCE_SHA256 = (
    "218d8bb67a5147bb54814175185857f773d1537237b59b3f0949e01f79a212df"
)

SOURCE_SESSIONS = (
    "TPMS-NATURAL-005-20260925-005143",
    "TPMS-NATURAL-006-20260925-005606",
    "TPMS-NATURAL-007-20260925-005956",
    "TPMS-NATURAL-008-20260925-012315",
    "TPMS-NATURAL-009-20260925-012627",
    "TPMS-NATURAL-010-20260925-012906",
    "TPMS-NATURAL-011-20260925-014556",
    "TPMS-NATURAL-012-20260925-014842",
    "TPMS-NATURAL-013-20260925-015115",
    "TPMS-NATURAL-015-20260925-020456",
)

EXCLUDED_SESSIONS = (
    "TPMS-NATURAL-014-20260925-015522",
    "TPMS-NATURAL-016-20260925-020821",
    "TPMS-NATURAL-017-20260925-021130",
)

AI_MODULES = (
    "__init__",
    "analyst",
    "artifact",
    "cli",
    "evidence_bundle",
    "experiment",
    "experiment_guard",
    "final_report",
    "history",
    "history_artifact",
    "history_experiment",
    "history_experiment_guard",
    "history_report",
    "llm_client",
    "output_guard",
    "prompts",
    "report",
    "schemas",
)

AI_TESTS = (
    "__init__",
    "test_analyst",
    "test_artifact",
    "test_cli",
    "test_evidence_bundle",
    "test_experiment_guard",
    "test_history",
    "test_history_artifact",
    "test_history_experiment",
    "test_history_experiment_guard",
    "test_history_report",
    "test_llm_client",
    "test_output_guard",
    "test_report",
    "test_verify_ai_release",
    "test_verify_ai_v02_release",
)

SOURCE_FILES = tuple(
    f"results/ml/prospective/{session}.json"
    for session in SOURCE_SESSIONS
)

REQUIRED_FILES = (
    tuple(f"ai/{name}.py" for name in AI_MODULES)
    + tuple(f"tests/ai/{name}.py" for name in AI_TESTS)
    + SOURCE_FILES
    + (
        "scripts/verify_ai_release.py",
        REFERENCE,
    )
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def canonical_sha256(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return sha256_bytes(encoded)


def text_sha256(value):
    if not isinstance(value, str):
        raise ValueError("hashed text field must be text")

    return sha256_bytes(value.encode("utf-8"))


def check_tag(root):
    """Check the frozen v0.2 tag when available locally."""

    result = subprocess.run(
        [
            "git",
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/tags/{TAG}",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode == 1:
        return " (not available locally; skipped)"

    if result.returncode:
        raise ValueError(
            result.stderr.strip() or "Git tag lookup failed"
        )

    result = subprocess.run(
        [
            "git",
            "rev-parse",
            "--verify",
            f"refs/tags/{TAG}^{{commit}}",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode:
        raise ValueError(
            result.stderr.strip() or "Git tag resolution failed"
        )

    actual = result.stdout.strip()

    if actual != RELEASE_COMMIT:
        raise ValueError(
            f"expected release commit {RELEASE_COMMIT}; got {actual}"
        )

    return f" ({RELEASE_COMMIT})"


def check_model(root):
    """Inspect frozen Ollama constants without importing the client."""

    tree = ast.parse(
        (root / "ai/llm_client.py").read_bytes()
    )

    expected_values = (
        ("DEFAULT_MODEL", MODEL),
        ("EXPECTED_MODEL_DIGEST", MODEL_DIGEST),
    )

    for name, expected in expected_values:
        values = [
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == name
                for target in node.targets
            )
        ]

        if values != [expected]:
            raise ValueError(
                f"{name} must equal {expected}"
            )


def check_reference_file_hash(root):
    actual = sha256_file(root / REFERENCE)

    if actual != REFERENCE_SHA256:
        raise ValueError(
            "reference artifact SHA256 mismatch: "
            f"expected {REFERENCE_SHA256}; got {actual}"
        )


def check_internal_hash(artifact, field, *, canonical=False):
    value = artifact.get(field)

    if canonical:
        if not isinstance(value, dict):
            raise ValueError(
                f"{field} must be a JSON object"
            )

        actual = canonical_sha256(value)
    else:
        actual = text_sha256(value)

    expected = artifact.get(f"{field}_sha256")

    if actual != expected:
        raise ValueError(
            f"{field}_sha256 mismatch"
        )


def check_source_manifest(root, artifact):
    manifest = artifact.get("source_record_sha256")

    if not isinstance(manifest, dict):
        raise ValueError(
            "source_record_sha256 must be a JSON object"
        )

    actual_sessions = tuple(sorted(manifest))
    expected_sessions = tuple(sorted(SOURCE_SESSIONS))

    if actual_sessions != expected_sessions:
        missing = sorted(
            set(expected_sessions) - set(actual_sessions)
        )
        unexpected = sorted(
            set(actual_sessions) - set(expected_sessions)
        )

        raise ValueError(
            "source session set mismatch; "
            f"missing={missing}; unexpected={unexpected}"
        )

    for excluded in EXCLUDED_SESSIONS:
        if excluded in manifest:
            raise ValueError(
                f"excluded/future session present: {excluded}"
            )

    for session in SOURCE_SESSIONS:
        expected_digest = manifest.get(session)

        if (
            not isinstance(expected_digest, str)
            or len(expected_digest) != 64
        ):
            raise ValueError(
                f"invalid source digest for {session}"
            )

        path = (
            root
            / "results/ml/prospective"
            / f"{session}.json"
        )

        actual_digest = sha256_file(path)

        if actual_digest != expected_digest:
            raise ValueError(
                f"source SHA256 mismatch for {session}"
            )

    expected_manifest_hash = artifact.get(
        "source_record_manifest_sha256"
    )
    actual_manifest_hash = canonical_sha256(manifest)

    if actual_manifest_hash != expected_manifest_hash:
        raise ValueError(
            "source_record_manifest_sha256 mismatch"
        )


def check_history_contract(artifact):
    history = artifact.get("history_bundle")

    if not isinstance(history, dict):
        raise ValueError(
            "history_bundle must be a JSON object"
        )

    if history.get("target_session_id") != TARGET_SESSION:
        raise ValueError(
            "history target_session_id mismatch"
        )

    if history.get("prior_formal_session_count") != 9:
        raise ValueError(
            "expected 9 prior formal sessions"
        )

    if history.get("formal_session_count_total") != 12:
        raise ValueError(
            "expected 12 total formal prospective sessions"
        )

    if history.get("excluded_session_numbers") != [14]:
        raise ValueError(
            "expected excluded_session_numbers=[14]"
        )


def check_artifact(root):
    path = root / REFERENCE

    artifact = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(artifact, dict):
        raise ValueError(
            "artifact must be a JSON object"
        )

    expected_metadata = (
        ("artifact_version", "0.2"),
        (
            "report_mode",
            "deterministic_history_with_ai_experiment",
        ),
        (
            "ai_scope",
            "historical_next_controlled_experiment_only",
        ),
        ("target_session_id", TARGET_SESSION),
        ("model", MODEL),
        ("model_digest", MODEL_DIGEST),
    )

    for name, expected in expected_metadata:
        if artifact.get(name) != expected:
            raise ValueError(
                f"artifact {name} mismatch"
            )

    check_internal_hash(
        artifact,
        "history_bundle",
        canonical=True,
    )
    check_internal_hash(
        artifact,
        "history_report",
    )
    check_internal_hash(
        artifact,
        "experiment_prompt",
    )
    check_internal_hash(
        artifact,
        "experiment_suggestion",
    )

    check_history_contract(artifact)
    check_source_manifest(root, artifact)


def verify(root=ROOT):
    """Run the complete read-only Sentinel AI v0.2 release gate."""

    root = Path(root).resolve()
    failures = []

    def check(label, operation):
        try:
            detail = operation() or ""
        except (
            OSError,
            ValueError,
            SyntaxError,
            TypeError,
            UnicodeError,
            json.JSONDecodeError,
            subprocess.TimeoutExpired,
        ) as exc:
            failures.append(label)
            print(
                f"FAIL {label}: {exc}",
                flush=True,
            )
        else:
            print(
                f"PASS {label}{detail}",
                flush=True,
            )

    def required_files():
        missing = [
            name
            for name in REQUIRED_FILES
            if not (root / name).is_file()
        ]

        if missing:
            raise ValueError(
                ", ".join(missing)
            )

        return f" ({len(REQUIRED_FILES)} files)"

    def compile_modules():
        modules = sorted(
            (root / "ai").rglob("*.py")
        )

        if not modules:
            raise ValueError(
                "no AI Python modules found"
            )

        for module in modules:
            compile(
                module.read_bytes(),
                str(module),
                "exec",
            )

        return (
            f" ({len(modules)} modules; in memory)"
        )

    def run_tests():
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/ai",
                "-p",
                "test_*.py",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = result.stdout + result.stderr

        if result.returncode:
            print(
                output,
                end="",
                flush=True,
            )
            raise ValueError(
                f"exit code {result.returncode}"
            )

        summary = next(
            (
                line
                for line in output.splitlines()
                if line.startswith("Ran ")
            ),
            "",
        )

        if summary:
            return f" ({summary})"

        return ""

    check(
        "required files",
        required_files,
    )
    check(
        "AI Python compilation",
        compile_modules,
    )
    check(
        "Sentinel AI v0.2 release tag",
        lambda: check_tag(root),
    )
    check(
        "frozen model constants",
        lambda: check_model(root),
    )
    check(
        "reference history artifact file SHA256",
        lambda: check_reference_file_hash(root),
    )
    check(
        "reference history artifact provenance",
        lambda: check_artifact(root),
    )

    if failures:
        print(
            "FAIL tests/ai: not run because "
            "prerequisite checks failed",
            flush=True,
        )
    else:
        check(
            "tests/ai",
            run_tests,
        )

    final = "FAIL" if failures else "PASS"

    print(
        f"{final} Sentinel AI v0.2 release verification",
        flush=True,
    )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(verify())
