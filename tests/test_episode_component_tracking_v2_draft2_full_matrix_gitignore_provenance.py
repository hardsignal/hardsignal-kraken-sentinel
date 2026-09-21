"""Repair regressions: provenance reads only; never execute a matrix arm."""
import ast
from contextlib import ExitStack
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_full_matrix_exact as launch
from provenance import stage37_gitignore_v1 as p
from draft2_review_provenance import validate_files, validate_review

ROOT = launch.ROOT


class GitignoreRepairTests(unittest.TestCase):
    def test_versioned_repair_binding_is_pinned(self):
        self.assertEqual(p.sha((ROOT / p.BINDING).read_bytes()),
                         '085babba93c3ba981f60511d788ae4591f0fdcb2fb020b30aacb365f86ecfd86')
        self.assertEqual(p.validate_repair(ROOT, launch.sc.sha(ROOT / p.RUNNER)),
                         p.ORIGINAL_RUNNER_SHA256)

    def test_repair_binding_field_drift_rejected(self):
        original = json.loads((ROOT / p.BINDING).read_bytes())
        real_read = Path.read_bytes
        for key in original:
            changed = json.dumps(dict(original, **{key: 'drift'})).encode()
            with self.subTest(key=key), patch.object(Path, 'read_bytes', lambda path:
                    changed if path == ROOT / p.BINDING else real_read(path)):
                with self.assertRaisesRegex(ValueError, 'source hash drift'):
                    launch.verify_plan()

    def test_repair_helper_and_older_validator_drift_rejected(self):
        real_read = Path.read_bytes
        for name in (p.HELPER, p.REVIEW_VALIDATOR):
            with self.subTest(name=name), patch.object(Path, 'read_bytes', lambda path:
                    real_read(path) + b'# drift\n' if path == ROOT / name else real_read(path)):
                with self.assertRaisesRegex(ValueError, 'source hash drift'):
                    launch.verify_plan()

    def test_current_descendant_without_scientific_execution(self):
        with ExitStack() as stack:
            for name in ('run_batch', 'execute_arm', 'worker', 'launch_arm'):
                stack.enter_context(patch.object(launch, name, side_effect=AssertionError('execution')))
            self.assertEqual(len(launch.verify_plan()['arms']), 160)
            for kind in ('definition', 'feasibility'):
                self.assertGreater(validate_review(kind), 0)

    def test_historical_bytes_and_exact_transition(self):
        old = p.historical_bytes(ROOT, p.EXECUTION, '.gitignore')
        frozen = p.historical_bytes(ROOT, p.FREEZE, '.gitignore')
        self.assertEqual(p.sha(old), launch.read(launch.PLAN)['sources']['.gitignore'])
        self.assertEqual(frozen, old + p.ADDITION)
        p.validate_gitignore(ROOT, p.sha(old), frozen)
        validate_files({'.gitignore': p.sha(old)}, lambda _: frozen, {'.gitignore'})

    def test_mutation_and_rule_removal_rejected_by_both_entry_points(self):
        frozen = (ROOT / '.gitignore').read_bytes()
        for bad in (frozen + b'# drift\n', frozen.replace(p.ADDITION, b''),
                    frozen.replace(b'*.cs8', b'*.other')):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    validate_files({'.gitignore': p.HISTORICAL_SHA256},
                                   lambda _: bad, {'.gitignore'})
                real_read = Path.read_bytes
                with patch.object(Path, 'read_bytes', lambda path:
                                  bad if path == ROOT / '.gitignore' else real_read(path)):
                    with self.assertRaisesRegex(ValueError, 'source hash drift'):
                        launch.verify_plan()

    def test_historical_hash_cannot_be_replaced_with_current_hash(self):
        with self.assertRaisesRegex(ValueError, 'Historical'):
            p.validate_gitignore(ROOT, p.FROZEN_SHA256, (ROOT / '.gitignore').read_bytes())

    def test_historical_bytes_are_actually_checked(self):
        original = p.historical_bytes
        for revision in (p.EXECUTION, p.FREEZE):
            with self.subTest(revision=revision), patch.object(p, 'historical_bytes',
                    side_effect=lambda root, rev, path: b'drift' if rev == revision
                    else original(root, rev, path)):
                with self.assertRaisesRegex(ValueError, 'Historical'):
                    p.validate_gitignore(ROOT, p.HISTORICAL_SHA256,
                                        (ROOT / '.gitignore').read_bytes())

    def test_freeze_ancestry_required(self):
        import subprocess
        real_run = p.subprocess.run
        with patch.object(p.subprocess, 'run', side_effect=lambda args, **kwargs:
                          subprocess.CompletedProcess(args, 1) if args[1] == 'merge-base'
                          else real_run(args, **kwargs)):
            with self.assertRaisesRegex(ValueError, 'checkpoint'):
                p.validate_gitignore(ROOT, p.HISTORICAL_SHA256,
                                    (ROOT / '.gitignore').read_bytes())

    def test_scientific_runner_code_and_limits_unchanged(self):
        def semantics(source):
            tree = ast.parse(source)
            return [ast.dump(node) for node in tree.body
                    if not (isinstance(node, ast.ImportFrom)
                            and node.module == 'provenance.stage37_gitignore_v1')
                    and not (isinstance(node, ast.FunctionDef) and node.name == 'verify_plan')]
        self.assertEqual(semantics((ROOT / p.RUNNER).read_bytes()),
                         semantics(p.historical_bytes(ROOT, p.FREEZE, p.RUNNER)))

    def test_frozen_evidence_and_review_payloads_unchanged(self):
        paths = [launch.PLAN, launch.BINDING, launch.CANONICAL]
        paths += list((ROOT / 'results').glob('*stage36*'))
        paths += list((ROOT / 'results').glob('*stage37-*-review.json'))
        paths += list((ROOT / 'docs').glob('*stage37-*-review.md'))
        for path in paths:
            if path.is_file():
                name = str(path.relative_to(ROOT))
                with self.subTest(path=name):
                    self.assertEqual(path.read_bytes(),
                                     p.historical_bytes(ROOT, '9d9d3b1312e793da519cc08f430f821de9870078', name))
