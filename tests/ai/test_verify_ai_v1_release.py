"""Release pins are separate from arbitrary-artifact validation."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from ai.v1_artifact import save_v1_artifact
from scripts import verify_ai_v1_release as release
import test_v1_artifact as fixtures


class V1ReleaseTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.V1ArtifactTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        shutil.copytree(fixture.sources, self.root / "results/ml/prospective")
        self.manifest = {
            "schema_version": "sentinel-ai-release/1.0", "tag": "sentinel-ai-v1.0",
            "commit": "a" * 40, "references": {},
        }
        for a in fixture.artifacts.values():
            path = save_v1_artifact(a, output_dir=self.root / "references")
            self.manifest["references"][str(path.relative_to(self.root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.path = self.root / "release.json"
        self.write(self.manifest)
        patcher = patch.object(release.subprocess, "run", side_effect=self.git_result)
        self.run = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def git_result(self, command, **kwargs):
        return subprocess.CompletedProcess(command, 0, "" if command[1] == "status" else "a" * 40 + "\n", "")

    def test_pinned_both_modes_and_matching_tag_pass(self):
        release.check_release_manifest(self.root, self.path)
        self.run.assert_any_call(["git", "rev-parse", "--verify", "refs/tags/sentinel-ai-v1.0^{commit}"],
                                 cwd=self.root, capture_output=True, text=True, timeout=30)

    def test_pin_corruption_and_missing_mode_fail(self):
        for change in ("hash", "mode"):
            with self.subTest(change=change):
                m = copy.deepcopy(self.manifest)
                key = next(iter(m["references"]))
                if change == "hash":
                    m["references"][key] = "0" * 64
                else:
                    del m["references"][key]
                self.write(m)
                with self.assertRaises(ValueError):
                    release.check_release_manifest(self.root, self.path)

    def test_wrong_missing_tag_and_dirty_checkout_fail(self):
        for result in (subprocess.CompletedProcess([], 1, "", "missing"),
                       subprocess.CompletedProcess([], 0, "b" * 40, "")):
            self.run.side_effect = None
            self.run.return_value = result
            with self.assertRaises(ValueError):
                release.check_release_manifest(self.root, self.path)
        self.run.side_effect = lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, " M file" if command[1] == "status" else "a" * 40, "")
        with self.assertRaisesRegex(ValueError, "clean"):
            release.check_release_manifest(self.root, self.path)

    def test_path_escape_and_invalid_manifest_fail(self):
        for value in ([], {}, {**self.manifest, "tag": "sentinel-ai-v0.2"},
                      {**self.manifest, "references": {"../escape": "0" * 64}}):
            self.write(value)
            with self.assertRaises(ValueError):
                release.check_release_manifest(self.root, self.path)

    def test_ml_asset_hash_check_is_read_only(self):
        path = self.root / "asset"
        path.write_bytes(b"frozen test asset")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with patch.object(release, "FROZEN_SHA256", {"asset": digest}):
            release.check_frozen_ml(self.root)
            self.assertEqual(path.read_bytes(), b"frozen test asset")
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "frozen ML"):
                release.check_frozen_ml(self.root)
