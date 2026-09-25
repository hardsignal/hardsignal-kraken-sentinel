import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_ai_release as verifier


class VerifyAIReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in verifier.REQUIRED_FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(verifier.ROOT / name, target)
        self.artifact_path = self.root / verifier.REFERENCE
        self.original_artifact = self.artifact_path.read_bytes()
        patcher = patch.object(verifier.subprocess, "run")
        self.run = patcher.start()
        self.addCleanup(patcher.stop)
        self.run.side_effect = self.command_result
        self.tag_exists = True
        self.commit = verifier.RELEASE_COMMIT
        self.suite_result = subprocess.CompletedProcess([], 0, "", "Ran 41 tests in 0.01s\n\nOK\n")

    def command_result(self, command, **kwargs):
        if command[0] != "git":
            if isinstance(self.suite_result, Exception):
                raise self.suite_result
            return self.suite_result
        if command[1] == "show-ref":
            return subprocess.CompletedProcess(command, 0 if self.tag_exists else 1, "", "")
        return subprocess.CompletedProcess(command, 0, self.commit + "\n", "")

    def verify(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = verifier.verify(self.root)
        return status, output.getvalue()

    def assert_failure(self, label):
        status, output = self.verify()
        self.assertEqual(status, 1, output)
        self.assertIn(f"FAIL {label}", output)

    def test_success_command_and_read_only(self):
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob("*") if p.is_file()}
        status, output = self.verify()
        self.assertEqual(status, 0, output)
        self.assertNotIn("FAIL", output)
        self.run.assert_any_call(
            [sys.executable, "-B", "-m", "unittest", "discover",
             "-s", "tests/ai", "-p", "test_*.py"],
            cwd=self.root, capture_output=True, text=True, timeout=300,
        )
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_each_required_file_missing(self):
        for name in verifier.REQUIRED_FILES:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.unlink()
                self.assert_failure("required files")
                path.write_bytes(original)
        self.assertTrue(all(call.args[0][0] == "git" for call in self.run.call_args_list))

    def test_each_corrupted_artifact_hash(self):
        for field in ("experiment_prompt", "experiment_suggestion", "report", "evidence_bundle"):
            with self.subTest(field=field):
                artifact = json.loads(self.original_artifact)
                artifact[field + "_sha256"] = "0" * 64
                self.artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
                self.assert_failure("reference artifact provenance")

    def test_wrong_code_model_digest(self):
        path = self.root / "ai/llm_client.py"
        path.write_text(path.read_text().replace(verifier.MODEL_DIGEST, "wrong"))
        self.assert_failure("frozen model constants")

    def test_wrong_artifact_metadata(self):
        for field in ("model_digest", "model", "report_mode", "ai_scope"):
            with self.subTest(field=field):
                artifact = json.loads(self.original_artifact)
                artifact[field] = "wrong"
                self.artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
                self.assert_failure("reference artifact provenance")

    def test_malformed_artifact(self):
        for content in (b"{", b"\xff", b"[]", b"null", b"{}"):
            with self.subTest(content=content):
                self.artifact_path.write_bytes(content)
                self.assert_failure("reference artifact provenance")

    def test_malformed_artifact_fields(self):
        for field in ("experiment_prompt", "experiment_suggestion", "report", "evidence_bundle"):
            with self.subTest(field=field):
                artifact = json.loads(self.original_artifact)
                artifact[field] = None
                self.artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
                self.assert_failure("reference artifact provenance")

    def test_ai_suite_failure(self):
        self.suite_result = subprocess.CompletedProcess([], 1, "", "failure details\n")
        status, output = self.verify()
        self.assertEqual(status, 1)
        self.assertIn("FAIL tests/ai: exit code 1", output)
        self.assertIn("failure details", output)

    def test_ai_suite_launch_failure_and_timeout(self):
        for error in (OSError("cannot launch"), subprocess.TimeoutExpired("tests", 300)):
            with self.subTest(error=error):
                self.suite_result = error
                self.assert_failure("tests/ai")

    def test_nested_syntax_failure(self):
        path = self.root / "ai/nested/broken.py"
        path.parent.mkdir()
        path.write_text("def broken(:", encoding="utf-8")
        self.assert_failure("AI Python compilation")

    def test_wrong_tag_commit(self):
        self.commit = "0" * 40
        self.assert_failure("Sentinel AI release tag")

    def test_missing_tag_is_explicitly_skipped(self):
        self.tag_exists = False
        status, output = self.verify()
        self.assertEqual(status, 0, output)
        self.assertIn("not available locally; skipped", output)

    def test_git_errors_are_failures(self):
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 128, "", "not a repository")
        self.assert_failure("Sentinel AI release tag")


if __name__ == "__main__":
    unittest.main()
