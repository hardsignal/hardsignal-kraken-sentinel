import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_ml_release as verifier


class VerifyMLReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in verifier.REQUIRED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        dataset = "results/ml/rf_behaviour_dataset_v001.csv"
        (self.root / verifier.MANIFEST).write_text(json.dumps({
            "training_dataset": dataset,
            "training_dataset_sha256": hashlib.sha256(b"").hexdigest(),
        }), encoding="utf-8")
        self.hashes = {
            name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
            for name in verifier.FROZEN_SHA256
        }
        patcher = patch.object(verifier, "FROZEN_SHA256", self.hashes)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(verifier.subprocess, "run")
        self.run_tests = patcher.start()
        self.addCleanup(patcher.stop)
        self.run_tests.return_value = subprocess.CompletedProcess([], 0, "", "")

    def verify(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = verifier.verify(self.root)
        return status, output.getvalue()

    def test_success_and_focused_suite_command(self):
        status, output = self.verify()
        self.assertEqual(status, 0)
        self.assertNotIn("FAIL", output)
        self.run_tests.assert_called_once_with(
            [sys.executable, "-B", "-m", "unittest", "discover",
             "-s", "tests/ml", "-p", "test_*.py", "-v"],
            cwd=self.root, capture_output=True, text=True, timeout=300,
        )
        self.assertFalse(list(self.root.rglob("*.pyc")))

    def test_each_frozen_hash_mismatch_blocks_model_loading(self):
        for name in self.hashes:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                status, output = self.verify()
                path.write_bytes(original)
                self.assertEqual(status, 1)
                self.assertIn(f"FAIL SHA256 {name}", output)
        self.run_tests.assert_not_called()

    def test_each_required_file_missing(self):
        for name in verifier.REQUIRED_FILES:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.unlink()
                status, output = self.verify()
                path.write_bytes(original)
                self.assertEqual(status, 1)
                self.assertIn("FAIL required files", output)
                self.assertIn(name, output)
        self.run_tests.assert_not_called()

    def test_manifest_invalid_json_encoding_shape_or_provenance(self):
        for content in (b"{", b"\xff", b"[]", b"{}"):
            with self.subTest(content=content):
                (self.root / verifier.MANIFEST).write_bytes(content)
                self.hashes[verifier.MANIFEST] = hashlib.sha256(content).hexdigest()
                status, output = self.verify()
                self.assertEqual(status, 1)
                self.assertIn("FAIL model manifest", output)
        self.run_tests.assert_not_called()

    def test_nested_module_syntax_error(self):
        path = self.root / "ml/nested/broken.py"
        path.parent.mkdir()
        path.write_text("def broken(:", encoding="utf-8")
        status, output = self.verify()
        self.assertEqual(status, 1)
        self.assertIn("FAIL ML Python compilation", output)
        self.run_tests.assert_not_called()

    def test_empty_module_tree_fails(self):
        for path in (self.root / "ml").rglob("*.py"):
            path.unlink()
        status, output = self.verify()
        self.assertEqual(status, 1)
        self.assertIn("no ML Python modules found", output)

    def test_focused_suite_failure_reports_diagnostics(self):
        self.run_tests.return_value = subprocess.CompletedProcess(
            [], 1, "test output\n", "failure details\n",
        )
        status, output = self.verify()
        self.assertEqual(status, 1)
        self.assertIn("FAIL tests/ml: exit code 1", output)
        self.assertIn("failure details", output)

    def test_focused_suite_launch_failure_and_timeout(self):
        for error in (OSError("cannot launch"), subprocess.TimeoutExpired("tests", 300)):
            with self.subTest(error=error):
                self.run_tests.side_effect = error
                status, output = self.verify()
                self.assertEqual(status, 1)
                self.assertIn("FAIL tests/ml", output)


if __name__ == "__main__":
    unittest.main()
