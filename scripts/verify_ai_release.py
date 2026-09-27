#!/usr/bin/env python3
"""Read-only, offline Sentinel AI v0.1 verification (Python 3.12)."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RELEASE_COMMIT = "b11760688cd8f9bbb3f8eacde5261f5223712ac1"
MODEL = "qwen3:14b"
MODEL_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"
REFERENCE = (
    "results/ai/TPMS-NATURAL-015-20260925-020456/"
    "sentinel_ai_v01_2026-09-25T022902.246529_0000.json"
)
REQUIRED_FILES = tuple(f"ai/{name}.py" for name in (
    "__init__", "analyst", "artifact", "cli", "evidence_bundle", "experiment",
    "experiment_guard", "final_report", "llm_client", "output_guard", "prompts",
    "report", "schemas",
)) + tuple(f"tests/ai/{name}.py" for name in (
    "__init__", "test_analyst", "test_artifact", "test_cli", "test_evidence_bundle",
    "test_experiment_guard", "test_llm_client", "test_output_guard", "test_report",
    "test_verify_ai_release",
)) + (REFERENCE,)


def check_tag(root):
    """Distinguish an absent local tag from Git errors or a wrong target."""
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/tags/sentinel-ai-v0.1"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 1:
        return " (not available locally; skipped)"
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git tag lookup failed")
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "refs/tags/sentinel-ai-v0.1^{commit}"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    if result.returncode or result.stdout.strip() != RELEASE_COMMIT:
        raise ValueError(f"expected release commit {RELEASE_COMMIT}")
    return f" ({RELEASE_COMMIT})"


def check_model(root):
    # Inspect literals without importing or executing the Ollama client.
    tree = ast.parse((root / "ai/llm_client.py").read_bytes())
    for name, expected in (("DEFAULT_MODEL", MODEL), ("EXPECTED_MODEL_DIGEST", MODEL_DIGEST)):
        values = [ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == name
                          for target in node.targets)]
        if values != [expected]:
            raise ValueError(f"{name} must equal {expected}")


def check_artifact(root):
    artifact = json.loads((root / REFERENCE).read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        raise ValueError("artifact must be a JSON object")
    for name, expected in (
        ("report_mode", "deterministic_with_ai_experiment"),
        ("ai_scope", "next_controlled_experiment_only"),
        ("model", MODEL), ("model_digest", MODEL_DIGEST),
    ):
        if artifact.get(name) != expected:
            raise ValueError(f"artifact {name} mismatch")
    for name in ("experiment_prompt", "experiment_suggestion", "report", "evidence_bundle"):
        value = artifact.get(name)
        if name == "evidence_bundle":
            if not isinstance(value, dict):
                raise ValueError("evidence_bundle must be a JSON object")
            encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8")
        else:
            if not isinstance(value, str):
                raise ValueError(f"{name} must be text")
            encoded = value.encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != artifact.get(f"{name}_sha256"):
            raise ValueError(f"{name}_sha256 mismatch")


def verify(root=ROOT):
    """Return zero only if all applicable checks pass; never write repository files."""
    root = Path(root).resolve()
    failures = []

    def check(label, operation):
        try:
            detail = operation() or ""
        except (OSError, ValueError, SyntaxError, TypeError, subprocess.TimeoutExpired) as exc:
            failures.append(label)
            print(f"FAIL {label}: {exc}", flush=True)
        else:
            print(f"PASS {label}{detail}", flush=True)

    def required_files():
        missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
        if missing:
            raise ValueError(", ".join(missing))

    def compile_modules():
        modules = sorted((root / "ai").rglob("*.py"))
        if not modules:
            raise ValueError("no AI Python modules found")
        for module in modules:
            compile(module.read_bytes(), str(module), "exec")
        return f" ({len(modules)} modules; in memory)"

    def run_tests():
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover",
             "-s", "tests/ai", "-p", "test_*.py"],
            cwd=root, capture_output=True, text=True, timeout=300,
        )
        output = result.stdout + result.stderr
        if result.returncode:
            print(output, end="", flush=True)
            raise ValueError(f"exit code {result.returncode}")
        summary = next((line for line in output.splitlines() if line.startswith("Ran ")), "")
        return f" ({summary})" if summary else ""

    check("required files", required_files)
    check("AI Python compilation", compile_modules)
    check("Sentinel AI release tag", lambda: check_tag(root))
    check("frozen model constants", lambda: check_model(root))
    check("reference artifact provenance (4 SHA256 hashes)", lambda: check_artifact(root))
    if failures:
        print("FAIL tests/ai: not run because prerequisite checks failed", flush=True)
    else:
        check("tests/ai", run_tests)
    print(f"{'FAIL' if failures else 'PASS'} Sentinel AI v0.1 release verification", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(verify())
