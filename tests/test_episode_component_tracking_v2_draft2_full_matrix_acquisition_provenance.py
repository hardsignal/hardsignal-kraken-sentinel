"""Read-only acquisition descendant regressions; no capture or scientific run."""
import ast
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from provenance import v2_acquisition_lock_v1 as p
import episode_component_tracking_v2_draft2_full_matrix_exact as launch
import test_episode_component_tracking_v2_v2_discrimination_preregistration as prereg
import test_episode_component_tracking_v2_stage37_configuration_selection as selection
from draft2_review_provenance import validate_review

ROOT = launch.ROOT


class AcquisitionProvenanceTests(unittest.TestCase):
    def test_exact_checkpoints_paths_and_frozen_bytes(self):
        manifest = p.validate(ROOT)
        self.assertEqual(len(manifest['frozen_sha256']), 5)
        self.assertEqual(p.git(ROOT, 'rev-parse', p.ACQUISITION + '^').decode().strip(), p.PARENT)
        for path, digest in p.ACQUISITION_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(p.sha(p.git(ROOT, 'show', p.ACQUISITION + ':' + path)), digest)
                current = manifest['current_sha256'].get(path, digest)
                self.assertEqual(p.sha((ROOT / path).read_bytes()), current)

    def entry_points(self):
        return (lambda: p.validate(ROOT), prereg.verify_repair,
                lambda: selection.verify_provenance(selection.read('stage37-configuration-selection')),
                launch.verify_plan, lambda: validate_review('definition'),
                lambda: validate_review('feasibility'))

    def test_every_frozen_file_mutation_rejected_at_all_entry_points(self):
        read = Path.read_bytes
        for path in p.ACQUISITION_SHA256:
            for verify in self.entry_points():
                with self.subTest(path=path, verify=verify), patch.object(
                        Path, 'read_bytes', lambda f: read(f) + b'\nmutation' if f == ROOT / path else read(f)):
                    with self.assertRaises(ValueError):
                        verify()

    def test_every_frozen_file_deletion_rejected_at_all_entry_points(self):
        read = Path.read_bytes
        for path in p.ACQUISITION_SHA256:
            def missing(f):
                if f == ROOT / path:
                    raise FileNotFoundError(path)
                return read(f)
            for verify in self.entry_points():
                with self.subTest(path=path, verify=verify), patch.object(Path, 'read_bytes', missing):
                    with self.assertRaises(FileNotFoundError):
                        verify()

    def test_sixth_tracked_or_untracked_descendant_rejected(self):
        real = subprocess.check_output
        for command in (['git', 'diff', '--name-only', '-z', p.ACQUISITION],
                        ['git', 'ls-files', '--others', '--exclude-standard', '-z']):
            def extra(cmd, **kwargs):
                raw = real(cmd, **kwargs)
                return raw + b'analysis/arbitrary_sixth.py\0' if cmd == command else raw
            for verify in self.entry_points():
                with self.subTest(command=command, verify=verify), patch.object(
                        subprocess, 'check_output', side_effect=extra):
                    with self.assertRaisesRegex(ValueError, 'unrecognized descendant'):
                        verify()

    def test_both_ancestry_edges_required(self):
        real = subprocess.run
        for earlier, later in ((p.PARENT, p.ACQUISITION), (p.ACQUISITION, 'HEAD')):
            def reject(cmd, **kwargs):
                if cmd == ['git', 'merge-base', '--is-ancestor', earlier, later]:
                    raise subprocess.CalledProcessError(1, cmd)
                return real(cmd, **kwargs)
            with self.subTest(edge=(earlier, later)), patch.object(subprocess, 'run', side_effect=reject):
                with self.assertRaises(subprocess.CalledProcessError):
                    p.validate(ROOT)

    def test_historical_five_hashes_and_validator_transitions_required(self):
        real = subprocess.check_output
        manifest = p.validate(ROOT)
        pairs = [(p.ACQUISITION, path) for path in p.ACQUISITION_SHA256]
        pairs += [(revision, path) for revision in (p.PARENT, p.ACQUISITION)
                  for path in manifest['historical_sha256'] if revision != p.PARENT or path not in p.ACQUISITION_SHA256]
        for revision, path in pairs:
            def drift(cmd, **kwargs):
                raw = real(cmd, **kwargs)
                return raw + b'drift' if cmd == ['git', 'show', revision + ':' + path] else raw
            with self.subTest(revision=revision, path=path), patch.object(
                    subprocess, 'check_output', side_effect=drift):
                with self.assertRaises(ValueError):
                    p.validate(ROOT)

    def test_manifest_cannot_expand_paths_rewrite_history_or_decisions(self):
        read = Path.read_bytes
        original = json.loads(read(ROOT / p.BINDING))
        for field in original:
            changed = dict(original)
            changed[field] = {} if isinstance(original[field], dict) else 'drift'
            with self.subTest(field=field), patch.object(Path, 'read_bytes', lambda f:
                    json.dumps(changed).encode() if f == ROOT / p.BINDING else read(f)):
                with self.assertRaises(ValueError):
                    p.validate(ROOT)

    def test_repair_code_mutations_rejected(self):
        read = Path.read_bytes
        for path in p.TRANSITIONS | p.ADDITIONS:
            with self.subTest(path=path), patch.object(Path, 'read_bytes', lambda f:
                    read(f) + b'\n# drift' if f == ROOT / path else read(f)):
                with self.assertRaises(ValueError):
                    p.validate(ROOT)

    def test_saved_historical_inventories_remain_exact(self):
        for path in (prereg.REPAIR_PATH,
                     'results/episode-component-tracking-v2-stage37-provenance-repair-v1.json',
                     str(launch.PLAN.relative_to(ROOT)), str(launch.BINDING.relative_to(ROOT))):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), p.git(ROOT, 'show', p.PARENT + ':' + path))
        plan = launch.verify_plan()
        self.assertFalse(set(p.ACQUISITION_SHA256) & set(plan['sources']))

    def test_protected_scientific_artifacts_unchanged(self):
        paths = p.git(ROOT, 'ls-tree', '-r', '--name-only', p.PARENT).decode().splitlines()
        protected = [name for name in paths if name.startswith(('docs/', 'results/'))
                     and any(tag in name for tag in ('stage36', 'stage37', 'v2-discrimination-preregistration'))]
        self.assertTrue(protected)
        for name in protected:
            with self.subTest(path=name):
                self.assertEqual((ROOT / name).read_bytes(), p.git(ROOT, 'show', p.PARENT + ':' + name))

    def test_runner_scientific_code_constants_and_interface_unchanged(self):
        path = 'analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py'
        def scientific_ast(raw):
            return [ast.dump(node) for node in ast.parse(raw).body
                    if not (isinstance(node, ast.FunctionDef) and node.name == 'verify_plan')]
        self.assertEqual(scientific_ast((ROOT / path).read_bytes()),
                         scientific_ast(p.git(ROOT, 'show', p.ACQUISITION + ':' + path)))
        helper = ast.parse((ROOT / 'analysis/provenance/v2_acquisition_lock_v1.py').read_bytes())
        imports = {node.names[0].name for node in helper.body if isinstance(node, ast.Import)}
        self.assertEqual(imports, {'hashlib', 'json', 'subprocess'})

    def test_metadata_validator_only_changes_provenance(self):
        path = 'analysis/validate_episode_component_tracking_v2_v2_acquisition_manifest.py'
        def semantics(raw):
            return [ast.dump(node) for node in ast.parse(raw).body
                    if not (isinstance(node, ast.FunctionDef) and node.name == 'verify_contract')
                    and not (isinstance(node, ast.ImportFrom) and node.module == 'provenance')]
        self.assertEqual(semantics((ROOT / path).read_bytes()),
                         semantics(p.git(ROOT, 'show', p.ACQUISITION + ':' + path)))

    def test_integration_is_read_only_and_acquisition_remains_blocked(self):
        with ExitStack() as stack:
            for obj, name in ((launch, 'run_batch'), (launch, 'execute_arm'),
                              (launch, 'worker'), (launch, 'launch_arm'),
                              (launch, 'association'), (launch.historical, 'solve_group'),
                              (launch.historical, 'detect'), (launch.historical, 'load_inputs')):
                stack.enter_context(patch.object(obj, name, side_effect=AssertionError('scientific execution')))
            for verify in self.entry_points():
                verify()
            for kind in ('definition', 'feasibility'):
                validate_review(kind)
        lock = json.loads((ROOT / 'results/episode-component-tracking-v2-v2-acquisition-lock.json').read_bytes())
        self.assertEqual(lock['decision'], p.DECISIONS['acquisition'])
        self.assertEqual(lock['state'], 'BLOCKED_PENDING_ACQUISITION_SETTINGS')
