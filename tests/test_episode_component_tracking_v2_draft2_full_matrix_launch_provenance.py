"""Freeze-binding checks; no scientific execution or historical artifact writes."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_full_matrix_exact as m


class LaunchProvenanceTests(unittest.TestCase):
    def test_real_integrated_descendant_and_historical_truth(self):
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=m.ROOT, text=True).strip()
        self.assertNotEqual(head, m.LAUNCH_INTEGRATION_BASE)
        self.assertEqual(subprocess.run(['git', 'merge-base', '--is-ancestor',
                         m.LAUNCH_INTEGRATION_BASE, head], cwd=m.ROOT).returncode, 0)
        self.assertNotEqual(subprocess.run(['git', 'cat-file', '-e',
                            m.LAUNCH_INTEGRATION_BASE + ':' + m.RUNNER],
                            cwd=m.ROOT, capture_output=True).returncode, 0)
        self.assertEqual(len(m.verify_plan()['arms']), 160)

    def test_non_descendant_rejected(self):
        root = subprocess.check_output(['git', 'rev-list', '--max-parents=0', 'HEAD'],
                                       cwd=m.ROOT, text=True).splitlines()[0]
        with patch.object(m.subprocess, 'check_output', return_value=root):
            with self.assertRaisesRegex(ValueError, 'not a descendant'):
                m.verify_plan()

    def test_source_drift_rejected(self):
        paths = [m.RUNNER, str(Path(m.historical.__file__).relative_to(m.ROOT)),
                 str(Path(m.corrected.__file__).relative_to(m.ROOT)),
                 str(Path(m.corrected.counter.__file__).relative_to(m.ROOT)),
                 str(Path(m.corrected.queries.__file__).relative_to(m.ROOT))]
        real_sha = m.sc.sha
        for target in paths:
            with self.subTest(target=target):
                with patch.object(m.sc, 'sha', side_effect=lambda p:
                                  '0' * 64 if Path(p) == m.ROOT / target else real_sha(p)):
                    with self.assertRaisesRegex(ValueError, 'source hash drift'):
                        m.verify_plan()

    def test_plan_mutation_even_with_supplied_matching_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'
            plan = m.read(m.PLAN)
            plan['authorization'] = 'changed'
            path.write_text(json.dumps(plan))
            for expected in (None, m.sc.sha(path)):
                with self.assertRaisesRegex(ValueError, 'plan hash drift'):
                    m.verify_plan(path, expected)

    def test_binding_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'binding.json'
            original = m.read(m.BINDING)
            for key in original:
                binding = dict(original, **{key: 'changed'})
                path.write_text(json.dumps(binding))
                with patch.object(m, 'BINDING', path):
                    with self.assertRaisesRegex(ValueError, 'Launch binding'):
                        m.verify_plan()

    def test_runtime_limit_drift_rejected(self):
        limits = copy.deepcopy(m.LIMITS)
        limits['worker_timeout_seconds'] += 1
        with patch.object(m, 'LIMITS', limits):
            with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
                m.verify_plan()

    def test_historical_namespace_rejected(self):
        with patch.object(m, 'OUTPUT', m.ROOT / 'results'):
            with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
                m.verify_plan()

    def test_output_symlink_collision_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'results').mkdir()
            output = root / m.OUTPUT.relative_to(m.ROOT)
            output.symlink_to(m.ROOT / 'results', target_is_directory=True)
            real_sha = m.sc.sha
            with patch.object(m, 'ROOT', root), patch.object(m, 'OUTPUT', output), \
                    patch.object(m.sc, 'sha', side_effect=lambda p: real_sha(
                        m_path if (m_path := Path(p)).is_absolute() and not m_path.is_relative_to(root)
                        else Path(__file__).resolve().parents[1] / m_path.relative_to(root))), \
                    patch.object(m.subprocess, 'check_output', return_value='descendant'), \
                    patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
                with self.assertRaisesRegex(ValueError, 'namespace collision'):
                    m.verify_plan()


if __name__ == '__main__':
    unittest.main()
