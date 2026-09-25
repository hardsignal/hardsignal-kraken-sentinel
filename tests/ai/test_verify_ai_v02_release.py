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

from scripts import verify_ai_v02_release as verifier


class VerifyAIV02ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)

        self.root = Path(temporary.name)

        for name in verifier.REQUIRED_FILES:
            source = verifier.ROOT / name
            target = self.root / name

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copyfile(
                source,
                target,
            )

        self.artifact_path = (
            self.root / verifier.REFERENCE
        )

        self.original_artifact = (
            self.artifact_path.read_bytes()
        )

        patcher = patch.object(
            verifier.subprocess,
            "run",
        )
        self.run = patcher.start()
        self.addCleanup(patcher.stop)

        self.run.side_effect = self.command_result

        self.tag_exists = True
        self.commit = verifier.RELEASE_COMMIT

        self.suite_result = subprocess.CompletedProcess(
            [],
            0,
            "",
            "Ran 90 tests in 0.01s\n\nOK\n",
        )

    def command_result(self, command, **kwargs):
        if command[0] != "git":
            if isinstance(
                self.suite_result,
                Exception,
            ):
                raise self.suite_result

            return self.suite_result

        if command[1] == "show-ref":
            return subprocess.CompletedProcess(
                command,
                0 if self.tag_exists else 1,
                "",
                "",
            )

        return subprocess.CompletedProcess(
            command,
            0,
            self.commit + "\n",
            "",
        )

    def verify(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = verifier.verify(
                self.root
            )

        return status, output.getvalue()

    def assert_failure(self, label):
        status, output = self.verify()

        self.assertEqual(
            status,
            1,
            output,
        )
        self.assertIn(
            f"FAIL {label}",
            output,
        )

    def refresh_reference_hash(self):
        digest = hashlib.sha256(
            self.artifact_path.read_bytes()
        ).hexdigest()

        return patch.object(
            verifier,
            "REFERENCE_SHA256",
            digest,
        )

    def load_artifact(self):
        return json.loads(
            self.artifact_path.read_text(
                encoding="utf-8"
            )
        )

    def write_artifact(self, artifact):
        self.artifact_path.write_text(
            json.dumps(
                artifact,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def test_success_command_and_read_only(self):
        before = {
            str(path.relative_to(self.root)):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        status, output = self.verify()

        self.assertEqual(
            status,
            0,
            output,
        )
        self.assertNotIn(
            "FAIL",
            output,
        )

        self.run.assert_any_call(
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
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=300,
        )

        after = {
            str(path.relative_to(self.root)):
            hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(
            before,
            after,
        )

    def test_each_required_file_missing(self):
        for name in verifier.REQUIRED_FILES:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()

                path.unlink()

                self.assert_failure(
                    "required files"
                )

                path.write_bytes(original)

    def test_reference_artifact_file_hash(self):
        data = bytearray(
            self.artifact_path.read_bytes()
        )

        data[-2] ^= 1

        self.artifact_path.write_bytes(
            bytes(data)
        )

        self.assert_failure(
            "reference history artifact file SHA256"
        )

    def test_each_internal_artifact_hash(self):
        fields = (
            "history_bundle",
            "history_report",
            "experiment_prompt",
            "experiment_suggestion",
        )

        for field in fields:
            with self.subTest(field=field):
                artifact = self.load_artifact()

                artifact[
                    f"{field}_sha256"
                ] = "0" * 64

                self.write_artifact(artifact)

                with self.refresh_reference_hash():
                    self.assert_failure(
                        "reference history artifact provenance"
                    )

                self.artifact_path.write_bytes(
                    self.original_artifact
                )

    def test_source_manifest_hash_corruption(self):
        artifact = self.load_artifact()

        artifact[
            "source_record_manifest_sha256"
        ] = "0" * 64

        self.write_artifact(artifact)

        with self.refresh_reference_hash():
            self.assert_failure(
                "reference history artifact provenance"
            )

    def test_wrong_artifact_metadata(self):
        fields = (
            "artifact_version",
            "report_mode",
            "ai_scope",
            "target_session_id",
            "model",
            "model_digest",
        )

        for field in fields:
            with self.subTest(field=field):
                artifact = self.load_artifact()
                artifact[field] = "wrong"

                self.write_artifact(artifact)

                with self.refresh_reference_hash():
                    self.assert_failure(
                        "reference history artifact provenance"
                    )

                self.artifact_path.write_bytes(
                    self.original_artifact
                )

    def test_future_session_in_manifest_fails(self):
        artifact = self.load_artifact()

        artifact["source_record_sha256"][
            "TPMS-NATURAL-016-20260925-021130"
        ] = "0" * 64

        artifact[
            "source_record_manifest_sha256"
        ] = verifier.canonical_sha256(
            artifact["source_record_sha256"]
        )

        self.write_artifact(artifact)

        with self.refresh_reference_hash():
            self.assert_failure(
                "reference history artifact provenance"
            )

    def test_missing_prior_session_fails(self):
        artifact = self.load_artifact()

        del artifact["source_record_sha256"][
            verifier.SOURCE_SESSIONS[0]
        ]

        artifact[
            "source_record_manifest_sha256"
        ] = verifier.canonical_sha256(
            artifact["source_record_sha256"]
        )

        self.write_artifact(artifact)

        with self.refresh_reference_hash():
            self.assert_failure(
                "reference history artifact provenance"
            )

    def test_source_record_corruption_fails(self):
        session = verifier.SOURCE_SESSIONS[0]

        path = (
            self.root
            / "results/ml/prospective"
            / f"{session}.json"
        )

        path.write_bytes(
            path.read_bytes() + b"\n"
        )

        self.assert_failure(
            "reference history artifact provenance"
        )

    def test_history_contract_corruption(self):
        artifact = self.load_artifact()

        artifact["history_bundle"][
            "prior_formal_session_count"
        ] = 10

        artifact[
            "history_bundle_sha256"
        ] = verifier.canonical_sha256(
            artifact["history_bundle"]
        )

        self.write_artifact(artifact)

        with self.refresh_reference_hash():
            self.assert_failure(
                "reference history artifact provenance"
            )

    def test_wrong_code_model_digest(self):
        path = self.root / "ai/llm_client.py"

        path.write_text(
            path.read_text().replace(
                verifier.MODEL_DIGEST,
                "wrong",
            ),
            encoding="utf-8",
        )

        self.assert_failure(
            "frozen model constants"
        )

    def test_malformed_artifact(self):
        for content in (
            b"{",
            b"\xff",
            b"[]",
            b"null",
            b"{}",
        ):
            with self.subTest(content=content):
                self.artifact_path.write_bytes(
                    content
                )

                with self.refresh_reference_hash():
                    self.assert_failure(
                        "reference history artifact provenance"
                    )

                self.artifact_path.write_bytes(
                    self.original_artifact
                )

    def test_nested_syntax_failure(self):
        path = (
            self.root
            / "ai/nested/broken.py"
        )

        path.parent.mkdir()

        path.write_text(
            "def broken(:",
            encoding="utf-8",
        )

        self.assert_failure(
            "AI Python compilation"
        )

    def test_ai_suite_failure(self):
        self.suite_result = (
            subprocess.CompletedProcess(
                [],
                1,
                "",
                "failure details\n",
            )
        )

        status, output = self.verify()

        self.assertEqual(
            status,
            1,
        )
        self.assertIn(
            "FAIL tests/ai: exit code 1",
            output,
        )
        self.assertIn(
            "failure details",
            output,
        )

    def test_ai_suite_launch_failure_and_timeout(self):
        errors = (
            OSError("cannot launch"),
            subprocess.TimeoutExpired(
                "tests",
                300,
            ),
        )

        for error in errors:
            with self.subTest(error=error):
                self.suite_result = error

                self.assert_failure(
                    "tests/ai"
                )

    def test_wrong_tag_commit(self):
        self.commit = "0" * 40

        self.assert_failure(
            "Sentinel AI v0.2 release tag"
        )

    def test_missing_tag_is_explicitly_skipped(self):
        self.tag_exists = False

        status, output = self.verify()

        self.assertEqual(
            status,
            0,
            output,
        )
        self.assertIn(
            "not available locally; skipped",
            output,
        )

    def test_git_errors_are_failures(self):
        self.run.side_effect = None

        self.run.return_value = (
            subprocess.CompletedProcess(
                [],
                128,
                "",
                "not a repository",
            )
        )

        self.assert_failure(
            "Sentinel AI v0.2 release tag"
        )


if __name__ == "__main__":
    unittest.main()
