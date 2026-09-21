"""Launch safety tests: committed artifacts, tiny fixtures and mocked workers only."""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import copy
import inspect
import io
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
import episode_component_tracking_v2_draft2_full_matrix_exact as m


class LaunchIntegrationTests(unittest.TestCase):
    def test_160_unique_cartesian_arms_and_order(self):
        arms = m.canonical()
        self.assertEqual(len(arms), 160)
        self.assertEqual(len({a['arm_id'] for a in arms}), 160)
        self.assertEqual([(a['representation'], a['width_hz'], a['association']) for a in arms],
                         list(itertools.product(m.REPRESENTATIONS, m.WIDTHS, m.ASSOCIATIONS)))
        self.assertEqual(arms, m.historical.arms())

    def test_scientific_configuration_and_frozen_limits(self):
        self.assertEqual(m.REPRESENTATIONS, m.historical.REPRESENTATIONS)
        self.assertEqual(m.WIDTHS, m.historical.WIDTHS)
        self.assertEqual(m.ASSOCIATIONS, m.historical.ASSOCIATIONS)
        old = m.corrected.read_plan()
        self.assertEqual(m.COUNT_LIMITS, old['count_limits'])
        self.assertEqual(m.LIMITS['query'], old['query_limits'])
        self.assertEqual(m.LIMITS['family_construction_seconds'], 60)
        self.assertEqual(m.LIMITS['worker_timeout_seconds'], 400)
        self.assertEqual(m.LIMITS['worker_rss_kib'], 524288)
        self.assertEqual(m.MAX_WORKERS, 1)
        self.assertEqual(m.verify_plan()['limits'], m.LIMITS)

    def test_no_arguments_and_unauthorized_launch_rejected(self):
        with redirect_stderr(io.StringIO()), patch.object(m, 'run_batch') as launch:
            for args in ([], ['--arm', m.canonical()[0]['arm_id']], ['--execute-full-matrix']):
                with self.assertRaises(SystemExit):
                    m.main(args)
            launch.assert_not_called()

    def test_wrong_plan_hash_and_source_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Wrong frozen plan hash'):
            m.verify_plan(expected_hash='0' * 64)
        real = m.sc.sha
        target = 'analysis/episode_component_tracking_v2_draft2_exact_solver.py'
        def sha(path):
            return '0' * 64 if Path(path) == ROOT / target else real(path)
        with patch.object(m.sc, 'sha', side_effect=sha):
            with self.assertRaisesRegex(ValueError, 'source hash drift'):
                m.verify_plan()

    def test_changed_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'arms.json'
            original = m.read(m.CANONICAL)
            for edit in ('duplicate', 'missing', 'representation', 'width', 'association'):
                data = copy.deepcopy(original)
                if edit == 'duplicate':
                    data['arms'][0] = data['arms'][1]
                elif edit == 'missing':
                    data['arms'].pop()
                else:
                    data['arms'][0]['width_hz' if edit == 'width' else edit] = 'changed'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    m.canonical(path)

    def test_plan_only_never_executes_science_or_writes_results(self):
        with ExitStack() as stack:
            for obj, name in [(m.historical, 'load_inputs'), (m.historical, 'detect'),
                              (m.historical, 'represent'), (m.historical, 'association'),
                              (m, 'association'), (m, 'execute_arm'), (m, 'run_batch'),
                              (m, 'write'), (m.corrected, 'count_exact'),
                              (m.corrected.limited, 'construct')]:
                stack.enter_context(patch.object(obj, name, side_effect=AssertionError(name)))
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(m.main(['--plan-only']), 0)
            self.assertFalse(json.loads(output.getvalue())['scientific_execution'])

    def test_selection_and_checkpoint_deterministic(self):
        arms = m.canonical()
        self.assertEqual(m.select(arms, [arms[7]['arm_id']]), [arms[7]])
        ids = [arms[7]['arm_id'], arms[0]['arm_id']]
        selected = m.select(arms, ids)
        self.assertEqual(selected, [arms[0], arms[7]])
        self.assertEqual(m.checkpoint('hash', selected, {}), m.checkpoint('hash', m.select(arms, ids[::-1]), {}))
        for invalid in ([], ['unknown'], [ids[0], ids[0]]):
            with self.assertRaises(ValueError):
                m.select(arms, invalid)

    def test_dispatch_accepts_no_case_identity_or_expected_outcome(self):
        self.assertEqual(list(inspect.signature(m.association).parameters),
                         ['fragments', 'setting', 'directory', 'context', 'sources'])
        self.assertEqual(list(inspect.signature(m.corrected.count_exact).parameters), ['family', 'budget'])
        source = inspect.getsource(m.association)
        self.assertIn('corrected.count_exact(family, budget)', source)
        self.assertIn('corrected.queries.integrate', source)
        self.assertNotIn('selected', source)
        self.assertNotIn("setting == 'paths_margin", source)
        self.assertNotIn('expected_count', source)
        # The general counter has one composed V3->V2 fallback route, not labels.
        counter = inspect.getsource(m.corrected.count_exact)
        self.assertIn('counter.count(family,budget)', counter)
        self.assertIn('cutoff.compose', counter)
        for forbidden in ('TPMS', 'REPL', 'capture', 'episode_id', 'device_id', 'arm_id', '5788836'):
            self.assertNotIn(forbidden, counter)

    def test_connected_and_compact_roundtrip_tiny_fixture(self):
        fs = m.historical.make_fragments([[(3000, 'A', 12)], [(3007, 'A', 12)]])
        plan = m.verify_plan()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            for setting in m.ASSOCIATIONS:
                directory = Path(tmp) / setting
                directory.mkdir()
                with patch.object(m.historical, 'solve_group', side_effect=AssertionError('expanded solver')):
                    result = m.association(fs, setting, directory, m.staged.git_context(ROOT), plan['sources'])
                if setting == 'connected':
                    for key, value in m.historical.association(fs, setting).items():
                        if key not in ('hypotheses', 'retained_hypothesis_count'):
                            self.assertEqual(result['association'][key], value)
                    self.assertFalse((directory / 'family.json').exists())
                    self.assertFalse((directory / 'cardinality.json').exists())
                else:
                    self.assertEqual(result['cardinality']['state'], 'EXACT')
                    self.assertEqual(result['states']['exact_queries']['state'], 'EXACT')
                    self.assertTrue((directory / 'cardinality.json').exists())
                self.assertEqual(m.read(directory / 'reload.json')['state'], 'BYTE_IDENTICAL')
                self.assertEqual(result['metrics']['original_fragment_count'], 2)

    def test_no_historical_output_collision_or_path_escape(self):
        for arm in m.canonical():
            path = m.batch_directory('test') / arm['arm_id']
            self.assertTrue(path.is_relative_to(m.OUTPUT))
            self.assertFalse(path.exists())
        for bad in ('../old', '/tmp/out', '.', '..', ''):
            with self.assertRaises(ValueError):
                m.batch_directory(bad)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            output = Path(tmp) / 'link'
            output.symlink_to(ROOT / 'results', target_is_directory=True)
            with patch.object(m, 'OUTPUT', output), self.assertRaises(ValueError):
                m.batch_directory('test')

    def test_completed_results_verified_never_overwritten_failure_never_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            m.write(directory / 'result.json', {'value': 1})
            receipt = dict(state='COMPLETE', files={'result.json': m.sc.sha(directory / 'result.json')})
            m.write(directory / 'receipt.json', receipt)
            m.verify_receipt(directory)
            with self.assertRaises(FileExistsError):
                m.write(directory / 'result.json', {'value': 2})
            (directory / 'result.json').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'hash drift'):
                m.verify_receipt(directory)
            receipt['files']['result.json'] = m.sc.sha(directory / 'result.json')
            receipt['state'] = 'COMPUTATION_UNRESOLVED'
            (directory / 'receipt.json').write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'automatic retry prohibited'):
                m.verify_receipt(directory)

    def test_manifest_list_cannot_silently_authorize_full_matrix(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(io.StringIO()):
            path = Path(tmp) / 'list.json'
            path.write_text(json.dumps([a['arm_id'] for a in m.canonical()]))
            with patch.object(m, 'run_batch') as launch, self.assertRaises(SystemExit):
                m.main(['--arm-list', str(path), '--confirm-frozen-plan', m.sc.sha(m.PLAN), '--batch', 'test'])
            launch.assert_not_called()

    def test_no_limit_escalation_or_retry_interface(self):
        with redirect_stderr(io.StringIO()):
            for option in ('--workers', '--max-states', '--timeout', '--retry', '--force'):
                with self.assertRaises(SystemExit):
                    m.main(['--plan-only', option, '999999'])
        source = inspect.getsource(m.launch_arm)
        self.assertEqual(source.count('subprocess.Popen('), 1)
        self.assertNotIn('retry', source)

    def test_structural_dispatch_invariant_under_identity_relabeling(self):
        fs = m.historical.make_fragments([[(3000, 'A', 12), (3007, 'B', 12)]] * 3)
        def count(fragments):
            family = m.corrected.limited.construct(fragments, 1, 60)
            return m.corrected.count_exact(family, m.corrected.previous.Budget(**m.COUNT_LIMITS))
        original = count(fs)
        renamed = copy.deepcopy(fs)
        for i, fragment in enumerate(renamed):
            for j, candidate in enumerate(fragment['components']):
                candidate.update(candidate_id=f'unrelated-{i:03d}-{j:03d}',
                                 capture_id='invented', episode_id=987, device_id='other')
        other = count(renamed)
        self.assertEqual(original['count'], other['count'])
        self.assertEqual(original['method'], other['method'])
        self.assertEqual(original['dispatch'], other['dispatch'])

    def test_mocked_controller_resume_and_failure_preservation(self):
        selected = m.canonical()[:2]
        digest = m.sc.sha(m.PLAN)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            output = Path(tmp) / 'output'
            def finish(batch, arm, plan_hash):
                directory = batch.parent / arm['arm_id']
                directory.mkdir()
                m.write(directory / 'receipt.json', dict(state='COMPLETE', files={}))
                return True
            with patch.object(m, 'OUTPUT', output), patch.object(m, 'verify_plan'), \
                    patch.object(m, 'launch_arm', side_effect=finish) as launch:
                self.assertEqual(m.run_batch('batch', selected, digest), 0)
                self.assertEqual(launch.call_count, 2)
                self.assertEqual(m.run_batch('batch', selected, digest, resume=True), 0)
                self.assertEqual(launch.call_count, 2)
                with self.assertRaises(ValueError):
                    m.run_batch('batch', selected[:1], digest, resume=True)
                with self.assertRaises(FileExistsError):
                    m.run_batch('batch', selected, digest)
            def fail(batch, arm, plan_hash):
                (batch.parent / arm['arm_id']).mkdir()
                return False
            with patch.object(m, 'OUTPUT', output), patch.object(m, 'verify_plan'), \
                    patch.object(m, 'launch_arm', side_effect=fail) as launch:
                self.assertEqual(m.run_batch('failed', selected, digest), 1)
                self.assertEqual(launch.call_count, 1)
                with self.assertRaises(FileNotFoundError):
                    m.run_batch('failed', selected, digest, resume=True)
                self.assertEqual(launch.call_count, 1)

    def test_historical_functions_bound_in_worker_without_detection(self):
        # Inspect the adapter, never execute detector/candidate generation.
        source = inspect.getsource(m.execute_arm)
        for call in ('historical.load_inputs()', 'historical.detect(', 'historical.apply_width(',
                     'historical.fragment_metrics('):
            self.assertIn(call, source)
        self.assertNotIn('solve_group(', source)
        self.assertNotIn('historical.run(', source)
        self.assertIn("usable_spectrum=meta['usable_spectrum']", source)
        self.assertIn("meta['fragment_index']", source)

    def test_resource_ceiling_kills_mock_worker_without_retry(self):
        class Process:
            pid = 123
            returncode = None
            def poll(self):
                return self.returncode
            def kill(self):
                self.returncode = -9
            def wait(self):
                return self.returncode
        for rss, times, reason in [(524289, [0, 1], 'RSS'), (1, [0, 401, 402], 'timeout')]:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                arm = m.canonical()[0]
                with patch.object(m.subprocess, 'Popen', return_value=Process()) as popen, \
                        patch.object(m.corrected, 'memory', return_value={'VmRSS': rss}), \
                        patch.object(m.time, 'monotonic', side_effect=times):
                    self.assertFalse(m.launch_arm(directory / 'batch.json', arm, 'hash'))
                    self.assertEqual(popen.call_count, 1)
                audit = m.read(directory / arm['arm_id'] / 'worker-audit.json')
                self.assertIn(reason, audit['reason'])
                self.assertEqual(audit['limits'], m.LIMITS)
                with self.assertRaises(ValueError):
                    m.verify_receipt(directory / arm['arm_id'])

    def test_changed_frozen_limit_rejected_even_with_new_plan_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'
            plan = m.read(m.PLAN)
            plan['limits']['count']['max_states'] += 1
            path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'configuration mismatch'):
                m.verify_plan(path, m.sc.sha(path))

    def test_historical_evidence_hashes_still_match(self):
        plan = m.verify_plan()
        rows = m.read(m.CANONICAL)['arms']
        self.assertEqual(sum(r['historical_execution_state'] == 'COMPLETE' for r in rows), 1)
        self.assertEqual(sum(r['historical_execution_state'] == 'COMPUTATION_UNRESOLVED' for r in rows), 1)
        self.assertEqual(sum(r['historical_execution_state'] == 'NOT_RUN' for r in rows), 158)
        for row in rows:
            if row['historical_result']:
                ref = row['historical_result']
                self.assertEqual(plan['sources'][ref['path']], ref['sha256'])

    def test_committed_control_parity_without_recount(self):
        base = ROOT / 'results/episode-component-tracking-v2-draft2-six-capture-corrected-regression'
        expected = {('C1-E02', 'margin-1'): '5788836', ('C6-E02', 'margin-1'): '217075',
                    ('C6-E03', 'margin-0.25'): '349149', ('C6-E03', 'margin-1'): '378536340',
                    ('C6-E05', 'margin-1'): '697122', ('C4-E08', 'margin-0'): '2',
                    ('C4-E08', 'margin-0.25'): '17067800502243',
                    ('C4-E08', 'margin-1'): '378038954451765697490'}
        for (label, arm), count in expected.items():
            saved = m.read(base / label / arm / 'count-outcome.json')
            self.assertEqual(saved['count_state'], 'EXACT')
            self.assertEqual(saved['exact_count_decimal'], count)
            self.assertEqual(saved['details']['dispatch']['certificate_backend'], m.corrected.counter.VERSION)
            self.assertEqual(saved['details']['dispatch']['composition_backend'], m.corrected.cutoff.VERSION)


if __name__ == '__main__':
    unittest.main()
