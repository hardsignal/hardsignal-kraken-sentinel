"""Read-only design contract checks; no scientific imports, IQ or execution."""
import ast
from provenance import v2_acquisition_lock_v1 as acquisition
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

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

PREREGISTRATION = '9eda24f5a065c8763132eab1f336963d4e322d87'
AUTHORIZED_REPAIR = 'fb11e2347e38aed82824118c99e5a882069905e3'
STAGE37_TEST = 'tests/test_episode_component_tracking_v2_stage37_configuration_selection.py'
V2_TEST = 'tests/test_episode_component_tracking_v2_v2_discrimination_preregistration.py'
REPAIR_PATH = 'results/episode-component-tracking-v2-v2-preregistration-provenance-repair-v1.json'
HISTORICAL_STAGE37_SHA256 = 'e3263babc1aa5231d00f15cc0fc719a02c28f61403a8639dbd582ad27fc3bd09'
REPAIRED_STAGE37_SHA256 = 'ea5b6df9d572067c04f34a8b134df2b29cac1594e2661877d239882f0e4ce997'
HISTORICAL_V2_SHA256 = 'e3652e9025070e72101468b4aca738b403cbe762122d6e5de50140c5f9156596'
REPAIR_METADATA = {
    'schema_version': 1,
    'preregistration_checkpoint': PREREGISTRATION,
    'authorized_repair_checkpoint': AUTHORIZED_REPAIR,
    'stage37_test_path': STAGE37_TEST,
    'historical_stage37_test_sha256': HISTORICAL_STAGE37_SHA256,
    'repaired_stage37_test_sha256': REPAIRED_STAGE37_SHA256,
    'historical_v2_test_sha256': HISTORICAL_V2_SHA256,
    'frozen_v2_markdown_sha256': DOC_SHA256,
    'frozen_v2_json_sha256': JSON_SHA256,
    'authorized_v2_paths': sorted(INTENDED),
    'parent_decision': 'STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED',
    'v2_decision': 'V2_DISCRIMINATION_EXPERIMENT_PREREGISTERED',
    'scope': 'Provenance validation only. The original V2 test and fb11e23 Stage 37 '
             'validator mutually pin historical bytes. Both validators now read this '
             'versioned artifact; current_validation_sha256 binds their final bytes. '
             'The artifact is separately committed, avoiding self-embedded hashes. '
             'No scientific execution, protocol changes or tuning interface.',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(document):
    """Validate a design object only; not a runner or parameter interface."""
    if document['candidates'] != EXPECTED:
        raise ValueError('Confirmatory comparison changed')
    encoded = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    if sha(encoded) != JSON_SHA256:
        raise ValueError('Frozen preregistration changed')


def git_bytes(checkpoint, path):
    return subprocess.check_output(['git', 'show', checkpoint + ':' + path], cwd=ROOT)


def require_hash(raw, expected, label):
    if sha(raw) != expected:
        raise ValueError('provenance drift: ' + label)


def verify_repair():
    """Read-only, versioned transition; never executes scientific code."""
    raw = (ROOT / REPAIR_PATH).read_bytes()
    artifact = json.loads(raw)
    metadata = {k: v for k, v in artifact.items() if k != 'current_validation_sha256'}
    if metadata != REPAIR_METADATA:
        raise ValueError('repair metadata drift')
    transition = acquisition.validate(ROOT)
    current = artifact['current_validation_sha256']
    if set(current) != {STAGE37_TEST, V2_TEST}:
        raise ValueError('validation path drift')
    for earlier, later in ((PARENT, PREREGISTRATION),
                           (PREREGISTRATION, AUTHORIZED_REPAIR),
                           (AUTHORIZED_REPAIR, 'HEAD')):
        subprocess.run(['git', 'merge-base', '--is-ancestor', earlier, later],
                       cwd=ROOT, check=True)
    for checkpoint, path, expected in (
            (PREREGISTRATION, STAGE37_TEST, HISTORICAL_STAGE37_SHA256),
            (AUTHORIZED_REPAIR, STAGE37_TEST, REPAIRED_STAGE37_SHA256),
            (PREREGISTRATION, V2_TEST, HISTORICAL_V2_SHA256),
            (AUTHORIZED_REPAIR, V2_TEST, HISTORICAL_V2_SHA256)):
        require_hash(git_bytes(checkpoint, path), expected, checkpoint + ':' + path)
    changed_at_repair = subprocess.check_output(
        ['git', 'diff', '--name-only', PREREGISTRATION, AUTHORIZED_REPAIR],
        cwd=ROOT, text=True).splitlines()
    if changed_at_repair != [STAGE37_TEST]:
        raise ValueError('authorized repair scope drift')
    for path, expected in current.items():
        require_hash(git_bytes(acquisition.ACQUISITION, path), expected, path)
        if transition['historical_sha256'][path] != expected:
            raise ValueError('historical validator binding drift')
    artifact = dict(artifact, current_validation_sha256={
        path: transition['current_sha256'][path] for path in current})
    current = artifact['current_validation_sha256']
    # Before the repair commit, HEAD is exactly fb11e23. Once committed, also
    # require the artifact and validator bytes to match HEAD (no mutable manifest).
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != AUTHORIZED_REPAIR:
        if raw != git_bytes('HEAD', REPAIR_PATH):
            raise ValueError('committed repair artifact drift')
        for path, expected in current.items():
            committed = transition['historical_sha256'][path] if head == acquisition.ACQUISITION else expected
            require_hash(git_bytes('HEAD', path), committed, 'committed V2 drift: ' + path)
    for path, expected in [('docs/' + STEM + '.md', DOC_SHA256),
                           ('results/' + STEM + '.json', JSON_SHA256)]:
        require_hash((ROOT / path).read_bytes(), expected, path)
        for checkpoint in (PREREGISTRATION, AUTHORIZED_REPAIR):
            require_hash(git_bytes(checkpoint, path), expected, checkpoint + ':' + path)
    design = json.loads(JSON_PATH.read_bytes())
    for path, expected in design['provenance_requirements']['bound_files_sha256'].items():
        require_hash(git_bytes(PARENT, path), expected, 'parent ' + path)
        if path != STAGE37_TEST:
            actual = sha((ROOT / path).read_bytes())
            if path in acquisition.TRANSITIONS:
                actual = acquisition.historical_digest(ROOT, path, actual)
            if actual != expected:
                raise ValueError('provenance drift: ' + path)
        elif expected != HISTORICAL_STAGE37_SHA256:
            raise ValueError('historical Stage 37 binding drift')
    changed = subprocess.check_output(['git', 'diff', '--name-only', '-z', PARENT], cwd=ROOT)
    untracked = subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    unexpected = set((changed + untracked).decode().split('\0')) - {''} - INTENDED - {STAGE37_TEST, REPAIR_PATH} - acquisition.AUTHORIZED_PATHS
    if unexpected:
        raise ValueError('unrecognized descendant paths: ' + repr(sorted(unexpected)))
    return artifact


class DiscriminationPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(JSON_PATH.read_bytes())

    def test_frozen_payload_and_document(self):
        validate(self.design)
        self.assertEqual(sha(JSON_PATH.read_bytes()), JSON_SHA256)
        self.assertEqual(sha(DOC_PATH.read_bytes()), DOC_SHA256)
        self.assertIn(self.design['decision'], DOC_PATH.read_text())

    def test_versioned_historical_and_current_hashes(self):
        artifact = verify_repair()
        self.assertEqual(sha(git_bytes(PREREGISTRATION, STAGE37_TEST)), HISTORICAL_STAGE37_SHA256)
        self.assertEqual(sha(git_bytes(AUTHORIZED_REPAIR, STAGE37_TEST)), REPAIRED_STAGE37_SHA256)
        self.assertEqual(sha(git_bytes(PREREGISTRATION, V2_TEST)), HISTORICAL_V2_SHA256)
        for path, expected in artifact['current_validation_sha256'].items():
            self.assertEqual(sha((ROOT / path).read_bytes()), expected)

    def test_reject_validator_science_and_artifact_mutations(self):
        original = Path.read_bytes
        paths = {STAGE37_TEST, V2_TEST, REPAIR_PATH,
                 'docs/' + STEM + '.md', 'results/' + STEM + '.json'}
        paths.update(self.design['provenance_requirements']['bound_files_sha256'])
        for path in sorted(paths):
            # Use valid JSON when mutating the manifest, so rejection is semantic.
            def mutated(file):
                raw = original(file)
                if file == ROOT / path:
                    if path == REPAIR_PATH:
                        artifact = json.loads(raw)
                        artifact['authorized_v2_paths'].append('results/fourth.json')
                        return json.dumps(artifact).encode()
                    return raw + b'\nchanged'
                return raw

            with self.subTest(path=path), patch.object(Path, 'read_bytes', mutated):
                with self.assertRaises(ValueError):
                    verify_repair()

    def test_reject_reverted_or_missing_descendant_authorization(self):
        original = Path.read_bytes
        for checkpoint in (PREREGISTRATION, AUTHORIZED_REPAIR):
            reverted = git_bytes(checkpoint, STAGE37_TEST)
            def changed(file):
                return reverted if file == ROOT / STAGE37_TEST else original(file)
            with self.subTest(checkpoint=checkpoint), patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'provenance drift'):
                    verify_repair()
        def missing(file):
            if file == ROOT / STAGE37_TEST:
                raise FileNotFoundError(STAGE37_TEST)
            return original(file)
        with patch.object(Path, 'read_bytes', missing), self.assertRaises(FileNotFoundError):
            verify_repair()

    def test_reject_historical_hash_drift(self):
        original = subprocess.check_output
        for checkpoint, path in ((PREREGISTRATION, STAGE37_TEST),
                                 (AUTHORIZED_REPAIR, STAGE37_TEST),
                                 (PREREGISTRATION, V2_TEST)):
            def changed(cmd, **kwargs):
                raw = original(cmd, **kwargs)
                return raw + b'changed' if cmd == ['git', 'show', checkpoint + ':' + path] else raw
            with self.subTest(checkpoint=checkpoint, path=path):
                with patch.object(subprocess, 'check_output', side_effect=changed):
                    with self.assertRaisesRegex(ValueError, 'provenance drift'):
                        verify_repair()

    def test_reject_broken_transition_ancestry(self):
        original = subprocess.run
        for earlier, later in ((PREREGISTRATION, AUTHORIZED_REPAIR), (AUTHORIZED_REPAIR, 'HEAD')):
            def rejected(cmd, **kwargs):
                if cmd == ['git', 'merge-base', '--is-ancestor', earlier, later]:
                    raise subprocess.CalledProcessError(1, cmd)
                return original(cmd, **kwargs)
            with self.subTest(earlier=earlier, later=later):
                with patch.object(subprocess, 'run', side_effect=rejected):
                    with self.assertRaises(subprocess.CalledProcessError):
                        verify_repair()

    def test_reject_arbitrary_fourth_descendant(self):
        original = subprocess.check_output
        for command in (['git', 'diff', '--name-only', '-z', PARENT],
                        ['git', 'ls-files', '--others', '--exclude-standard', '-z']):
            def extra(cmd, **kwargs):
                raw = original(cmd, **kwargs)
                return raw + b'results/fourth.json\0' if cmd == command else raw
            with self.subTest(command=command):
                with patch.object(subprocess, 'check_output', side_effect=extra):
                    with self.assertRaisesRegex(ValueError, 'unrecognized descendant'):
                        verify_repair()

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
        verify_repair()

    def test_all_parent_tracked_files_unchanged(self):
        verify_repair()
        changed = set(subprocess.check_output(
            ['git', 'diff', '--name-only', PARENT], cwd=ROOT, text=True).splitlines())
        parent_files = set(subprocess.check_output(
            ['git', 'ls-tree', '-r', '--name-only', PARENT], cwd=ROOT, text=True).splitlines())
        self.assertEqual(changed & parent_files, acquisition.TRANSITIONS & parent_files)

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
        self.assertEqual(self.design['decision'], REPAIR_METADATA['v2_decision'])
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
        self.assertLessEqual(modules, {'ast', 'copy', 'hashlib', 'json', 'pathlib', 'subprocess', 'unittest', 'unittest.mock', 'provenance'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess' and node.func.attr != 'CalledProcessError':
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
