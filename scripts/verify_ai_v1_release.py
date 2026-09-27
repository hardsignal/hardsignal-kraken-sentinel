#!/usr/bin/env python3
"""Separate offline candidate/release gate; never creates tags or references."""

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ai.v1_artifact import strict_json_loads, verify_v1_artifact
from scripts.verify_ml_release import FROZEN_SHA256


def contained(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("release paths must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("release path escapes repository")
    return path


def check_frozen_ml(root):
    for relative, expected in FROZEN_SHA256.items():
        actual = hashlib.sha256(contained(root, relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen ML SHA256 mismatch: {relative}")


def check_release_manifest(root, manifest_path):
    root = Path(root).resolve()
    manifest = strict_json_loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "tag", "references"}:
        raise ValueError("invalid v1 release manifest fields")
    if manifest["schema_version"] != "sentinel-ai-release/1.0" or manifest["tag"] != "sentinel-ai-v1.0":
        raise ValueError("unsupported release version/tag")
    references = manifest["references"]
    if not isinstance(references, dict) or not references:
        raise ValueError("release requires pinned v1 references")
    modes = set()
    for relative, expected in references.items():
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("invalid reference SHA256")
        path = contained(root, relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"reference SHA256 mismatch: {relative}")
        artifact = verify_v1_artifact(path, source_dir=root / "results/ml/prospective")
        modes.add(artifact["mode"])
    if modes != {"normal", "history"}:
        raise ValueError("release references must cover normal and history modes")
    tag_result = subprocess.run(
        ["git", "rev-parse", "--verify", "refs/tags/sentinel-ai-v1.0^{commit}"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    if tag_result.returncode:
        raise ValueError("sentinel-ai-v1.0 tag missing")

    head_result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    if head_result.returncode:
        raise ValueError("cannot resolve HEAD")

    if tag_result.stdout.strip() != head_result.stdout.strip():
        raise ValueError("release tag does not point to HEAD")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                            capture_output=True, text=True, timeout=30)
    if status.returncode or status.stdout.strip():
        raise ValueError("release checkout must be clean")


def run_candidate_checks(root):
    check_frozen_ml(root)
    for path in sorted((root / "ai").rglob("*.py")):
        compile(path.read_bytes(), str(path), "exec")
    result = subprocess.run([sys.executable, "-B", "tests/readiness/test_ai_v1_readiness.py"],
                            cwd=root, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise ValueError("v1 readiness gate failed:\n" + result.stdout + result.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--candidate", action="store_true", help="Readiness and frozen ML hashes; not a tagged release PASS")
    choice.add_argument("--manifest", type=Path, help="Pinned release manifest; requires the eventual v1 tag and clean matching checkout")
    args = parser.parse_args(argv)
    try:
        if args.manifest is not None:
            check_release_manifest(ROOT, args.manifest)
        run_candidate_checks(ROOT)
    except (OSError, ValueError, SyntaxError, UnicodeError, RecursionError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL Sentinel AI v1 gate: {exc}", file=sys.stderr)
        return 1
    label = "candidate checks (not tagged release verification)" if args.candidate else "release verification"
    print(f"PASS Sentinel AI v1 {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
