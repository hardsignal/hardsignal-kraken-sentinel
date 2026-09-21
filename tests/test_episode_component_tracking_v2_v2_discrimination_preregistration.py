"""Read-only design contract checks; no scientific imports, IQ or execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-v2-discrimination-preregistration'
PARENT = '4d61b04867e479187a3ae5c6914df98e382fc18b'
JSON_PATH = ROOT / 'results' / (STEM + '.json')
DOC_PATH = ROOT / 'docs' / (STEM + '.md')
JSON_SHA256 = 'dd9a1694c5d0bc7a47ad2f0bfa917816cc66325f5325e4718b95a7bb9780a7b6'
DOC_SHA256 = 'f28d4d168a2475c6a755b21c521270e8f2de269a12e67227f24116137321b7c7'
EXPECTED = {
    'A': {'representation': 'grid_sigma5', 'width_hz': 350, 'association': 'connected'},
    'B': {'representation': 'grid_sigma10', 'width_hz': 350, 'association': 'connected'},
}
INTENDED = {'docs/' + STEM + '.md', 'results/' + STEM + '.json',
            'tests/test_episode_component_tracking_v2_v2_discrimination_preregistration.py'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(document):
    """Validate a design object only; not a runner or parameter interface."""
    if document['candidates'] != EXPECTED:
        raise ValueError('Confirmatory comparison changed')
    encoded = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    if sha(encoded) != JSON_SHA256:
        raise ValueError('Frozen preregistration changed')


class DiscriminationPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(JSON_PATH.read_bytes())

    def test_frozen_payload_and_document(self):
        validate(self.design)
        self.assertEqual(sha(JSON_PATH.read_bytes()), JSON_SHA256)
        self.assertEqual(sha(DOC_PATH.read_bytes()), DOC_SHA256)
        self.assertIn(self.design['decision'], DOC_PATH.read_text())

    def test_exact_two_candidates(self):
        self.assertEqual(self.design['candidates'], EXPECTED)
        self.assertEqual(len(self.design['candidates']), 2)

    def test_reject_expanded_or_changed_comparison(self):
        mutations = []
        for field, value in [('representation', 'native'), ('representation', 'grid_sigma20'),
                             ('width_hz', 325), ('width_hz', None),
                             ('association', 'paths_margin0')]:
            d = copy.deepcopy(self.design)
            d['candidates']['A'][field] = value
            mutations.append(d)
        d = copy.deepcopy(self.design)
        d['candidates']['C'] = dict(EXPECTED['A'])
        mutations.append(d)
        for d in mutations:
            with self.assertRaises(ValueError):
                validate(d)

    def test_parent_deferred_and_provenance(self):
        d = self.design
        self.assertEqual(d['parent_checkpoint'], '4d61b04')
        self.assertEqual(d['parent_commit'], PARENT)
        self.assertEqual(d['parent_decision'], 'STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED')
        old = json.loads((ROOT / 'results/episode-component-tracking-v2-stage37-configuration-selection.json').read_bytes())
        self.assertEqual(old['decision'], d['parent_decision'])
        self.assertIsNone(old['selected_configuration'])
        subprocess.run(['git', 'merge-base', '--is-ancestor', PARENT, 'HEAD'], cwd=ROOT, check=True)
        self.assertEqual(d['provenance_requirements']['branch'], 'codex/v2-discrimination-design')
        for path, digest in d['provenance_requirements']['bound_files_sha256'].items():
            with self.subTest(path=path):
                self.assertEqual(sha((ROOT / path).read_bytes()), digest)
                self.assertEqual(sha(subprocess.check_output(['git', 'show', PARENT + ':' + path], cwd=ROOT)), digest)

    def test_all_parent_tracked_files_unchanged(self):
        # Covers tracked V1 evidence, reviews, raw inventories and scientific code.
        # Git diff includes staged + unstaged changes and checks deleted files too.
        changed = set(subprocess.check_output(['git', 'diff', '--name-only', PARENT], cwd=ROOT, text=True).splitlines())
        self.assertFalse(changed - INTENDED, changed - INTENDED)
        parent_files = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', PARENT], cwd=ROOT, text=True).splitlines())
        self.assertFalse(changed & parent_files)

    def test_inherited_constants_and_width_override(self):
        tree = ast.parse((ROOT / 'analysis/episode_component_tracking_v2_draft1.py').read_text())
        params = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'PARAMETERS' for t in n.targets))
        self.assertEqual(params.pop('maximum_component_width_hz'), 200.0)
        expected = dict(params, maximum_component_width_hz=350)
        self.assertEqual(self.design['fixed_parameters']['inherited_detector_and_tracking'], expected)
        self.assertFalse(self.design['execution_ready'])
        self.assertTrue(self.design['fixed_parameters']['not_established_by_committed_evidence'])
        self.assertIn('before first V2 capture', self.design['fixed_parameters']['pre_acquisition_lock'])

    def test_membership_endpoint_locked_before_execution(self):
        p = self.design['primary_endpoint']
        self.assertTrue(p['defined_before_execution'])
        self.assertEqual(p['frequency_match_tolerance_hz'], 25)
        self.assertEqual(p['minimum_mean_advantage'], 0.10)
        self.assertEqual(p['winner_minimum_mean_score'], 0.80)
        self.assertIn('score=0 (including two null primaries)', p['pair_score'])
        self.assertIn('ordinal', p['membership_mapping'])
        self.assertIn('all eight', p['inference'])
        self.assertFalse(self.design['execution_performed'])

    def test_balanced_paired_new_capture_design(self):
        a = self.design['acquisition_plan']
        self.assertTrue(a['new_data_only'])
        self.assertEqual((a['sessions'], a['controlled_sources'], a['repeats_per_source_per_session']), (8, 2, 3))
        self.assertEqual(a['captures'], 8 * 2 * 3)
        self.assertEqual(a['planned_activation_slots'], 48 * 6)
        self.assertEqual(a['repeat_comparisons'], 8 * 2 * 6 * 3)
        self.assertIn('byte-identical', a['pairing'])
        self.assertIn('not optimized using Stage36 effects', a['sample_size_rationale'])

    def test_deferred_and_critical_gates_remain_possible(self):
        self.assertEqual(self.design['possible_outcomes'], ['A_SELECTED', 'B_SELECTED', 'DEFERRED'])
        rule = self.design['decision_rule']
        self.assertEqual(rule['default'], 'DEFERRED')
        self.assertIn('Any tie', rule['DEFERRED'])
        self.assertEqual(len(rule['all_required']), 5)
        self.assertEqual(len(self.design['secondary_endpoints']), 4)
        self.assertTrue(all(s['critical_gate'] for s in self.design['secondary_endpoints']))

    def test_anomalies_and_missing_observations_cannot_disappear(self):
        a = self.design['anomaly_policy']
        self.assertTrue(a['retain_all'])
        self.assertFalse(a['post_hoc_exclusion_allowed'])
        self.assertIn('All scheduled slots', a['primary'])
        self.assertIn('cannot rescue', a['sensitivity'])
        self.assertIn('E07', a['interpretation'])
        self.assertFalse(self.design['missing_data_policy']['replacement'])
        self.assertIn('DEFERRED', self.design['missing_data_policy']['policy'])

    def test_mandatory_controls_and_claim_boundaries(self):
        n = self.design['negative_controls']
        self.assertTrue(n['mandatory'])
        self.assertTrue(n['separate_from_real_data'])
        self.assertIn('1/100', n['noise_gate'])
        self.assertIn('Zero crossing', n['crossing_gate'])
        self.assertIn('cannot distinguish sigma', n['scope'])
        self.assertEqual(set(self.design['claims_boundary']['forbidden']),
                         {'RF transmitter identity', 'carrier identity', 'device fingerprint identity',
                          'device identity', 'universal thresholds', 'universally correct source association'})

    def test_no_execution_or_tuning_interface(self):
        self.assertTrue(self.design['design_only'])
        self.assertFalse(self.design['prohibition_on_post_hoc_tuning']['allowed'])
        f = self.design['computational_failure_policy']
        self.assertFalse(f['automatic_retries'])
        self.assertFalse(f['relaxed_limits'])
        interface = self.design['provenance_requirements']['planned_runner_interface']
        self.assertFalse(interface['implemented'])
        self.assertIn('No representation, width, association, threshold, budget override, retry or tuning arguments', interface['contract'])
        # This module only uses stdlib document/Git readers, never a science import.
        tree = ast.parse(Path(__file__).read_text())
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        modules |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertLessEqual(modules, {'ast', 'copy', 'hashlib', 'json', 'pathlib', 'subprocess', 'unittest'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess':
                self.assertIsInstance(node.args[0], ast.List)
                self.assertEqual(ast.literal_eval(node.args[0].elts[0]), 'git')

    def test_reject_post_hoc_changes_to_all_core_gates(self):
        for path, replacement in [
            (('primary_endpoint', 'frequency_match_tolerance_hz'), 50),
            (('primary_endpoint', 'defined_before_execution'), False),
            (('negative_controls', 'mandatory'), False),
            (('anomaly_policy', 'retain_all'), False),
            (('decision_rule', 'default'), 'A_SELECTED'),
            (('prohibition_on_post_hoc_tuning', 'allowed'), True),
            (('parent_decision',), 'A_SELECTED'),
            (('claims_boundary', 'forbidden'), []),
        ]:
            d = copy.deepcopy(self.design)
            target = d
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = replacement
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate(d)


if __name__ == '__main__':
    unittest.main()
