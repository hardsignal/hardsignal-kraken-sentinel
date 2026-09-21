"""Frozen Stage 37 selection regressions; saved evidence only, no scientific runs.

The persistent-membership check reads hash-bound arm.json files from the external
archive. No detector, family builder, query, counter, or matrix worker is called.
"""
import copy
import hashlib
import json
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_full_matrix_exact as launch
from provenance import stage37_gitignore_v1 as repair
import test_episode_component_tracking_v2_stage37_scientific_review as scientific
import test_episode_component_tracking_v2_stage37_computational_review as computational

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-'
CHECKPOINT = 'b109ede179e11021e13b8a84713439aa8a4c1ab8'
SELECTION_CHECKPOINT = '4d61b04867e479187a3ae5c6914df98e382fc18b'
# Exact bytes committed by the V2 preregistration at 9eda24f.
V2_DESCENDANTS = {
    'docs/episode-component-tracking-v2-v2-discrimination-preregistration.md':
        'f28d4d168a2475c6a755b21c521270e8f2de269a12e67227f24116137321b7c7',
    'results/episode-component-tracking-v2-v2-discrimination-preregistration.json':
        'dd9a1694c5d0bc7a47ad2f0bfa917816cc66325f5325e4718b95a7bb9780a7b6',
    'tests/test_episode_component_tracking_v2_v2_discrimination_preregistration.py':
        'e3652e9025070e72101468b4aca738b403cbe762122d6e5de50140c5f9156596',
}
DECISION = 'STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED'
PAYLOAD_SHA256 = '269caf62e65faadd6c04e729681195829559f4519728e55419f95b97202198f3'
REPORT_SHA256 = '20ec4954eac2474d06a607d641b1725c19fca64f08b2727b2b3cfee163d9247c'
FIELDS = ('arm_id', 'representation', 'width_hz', 'association')


def read(name):
    return json.loads((ROOT / 'results' / (STEM + name + '.json')).read_bytes())


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def validate_payload(payload):
    if payload['provenance']['selection_checkpoint'] != CHECKPOINT:
        raise ValueError('selection checkpoint drift')
    if payload['decision'] != DECISION or payload['selected_configuration'] is not None:
        raise ValueError('selection decision drift')
    if digest(canonical(payload)) != PAYLOAD_SHA256:
        raise ValueError('selection payload drift')


def verify_provenance(selection):
    """Keep frozen evidence bound; authorize only the byte-pinned V2 addition."""
    for checkpoint in (CHECKPOINT, SELECTION_CHECKPOINT):
        subprocess.run(['git', 'merge-base', '--is-ancestor', checkpoint, 'HEAD'],
                       cwd=ROOT, check=True)
    for path, expected in selection['provenance']['bound_files_sha256'].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('bound-file drift: ' + path)
        if digest(subprocess.check_output(
                ['git', 'show', CHECKPOINT + ':' + path], cwd=ROOT)) != expected:
            raise ValueError('checkpoint bound-file drift: ' + path)
    for path, expected in V2_DESCENDANTS.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('V2 descendant drift: ' + path)
        if digest(subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT)) != expected:
            raise ValueError('committed V2 drift: ' + path)
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', '-z', CHECKPOINT], cwd=ROOT)
    untracked = subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    intended = {'docs/' + STEM + 'stage37-configuration-selection.md',
                'results/' + STEM + 'stage37-configuration-selection.json',
                'tests/test_episode_component_tracking_v2_stage37_configuration_selection.py'}
    unexpected = set((changed + untracked).decode().split('\0')) - {''} - intended - V2_DESCENDANTS.keys()
    if unexpected:
        raise ValueError('unrecognized descendant paths: ' + repr(sorted(unexpected)))


def verify_saved_memberships(payload):
    """Read archived results only; verify bytes before trusting their projection."""
    raw = Path(payload['provenance']['raw_root'])
    count = 0
    for arm in payload['candidate_evidence']:
        if arm['state'] != 'COMPLETE':
            continue
        saved_bytes = (raw / Path(arm['receipt_path']).parent / 'arm.json').read_bytes()
        evidence = arm['scientific_evidence']
        if digest(saved_bytes) != evidence['arm_json_sha256']:
            raise ValueError('raw arm hash drift')
        original = json.loads(saved_bytes)
        if len(original['episodes']) != 41 or len(evidence['episodes']) != 41:
            raise ValueError('episode count drift')
        for projected, episode in zip(evidence['episodes'], original['episodes']):
            memberships = sorted(sorted(m) for m in episode['association']['persistent_tracks'])
            if (memberships != projected['persistent_memberships'] or
                    digest(canonical(memberships)) != projected['persistent_membership_sha256']):
                raise ValueError('persistent membership drift')
            count += 1
    return count


class ConfigurationSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = read('stage37-configuration-selection')
        cls.scientific = read('stage37-scientific-review')
        cls.computational = read('stage37-computational-review')
        cls.audit = read('draft2-stage36-final-audit')
        cls.arms = cls.selection['candidate_evidence']

    def test_payload_report_and_deferred_output_contract(self):
        validate_payload(self.selection)
        report = ROOT / 'docs' / (STEM + 'stage37-configuration-selection.md')
        self.assertEqual(digest(report.read_bytes()), REPORT_SHA256)
        self.assertIn(DECISION, report.read_text())
        self.assertIsNone(self.selection['reproduction_specification'])
        self.assertFalse((ROOT / 'results' / (STEM + 'v1-frozen-configuration.json')).exists())

    def test_checkpoint_ancestry_and_byte_bindings(self):
        verify_provenance(self.selection)

    def test_selection_checkpoint_ancestry_required(self):
        original = subprocess.run

        def reject_selection(cmd, **kwargs):
            if cmd == ['git', 'merge-base', '--is-ancestor', SELECTION_CHECKPOINT, 'HEAD']:
                raise subprocess.CalledProcessError(1, cmd)
            return original(cmd, **kwargs)

        with patch.object(subprocess, 'run', side_effect=reject_selection):
            with self.assertRaises(subprocess.CalledProcessError):
                verify_provenance(self.selection)

    def test_each_v2_mutation_and_deletion_rejected(self):
        original = Path.read_bytes
        for path in V2_DESCENDANTS:
            for deleted in (False, True):
                def changed_bytes(file):
                    if file == ROOT / path:
                        if deleted:
                            raise FileNotFoundError(path)
                        return original(file) + b'\nchanged'
                    return original(file)

                with self.subTest(path=path, deleted=deleted):
                    with patch.object(Path, 'read_bytes', changed_bytes):
                        with self.assertRaises(FileNotFoundError if deleted else ValueError):
                            verify_provenance(self.selection)

    def test_committed_v2_drift_rejected(self):
        original = subprocess.check_output
        for path in V2_DESCENDANTS:
            def changed_commit(cmd, **kwargs):
                if cmd == ['git', 'show', 'HEAD:' + path]:
                    return b'changed committed bytes'
                return original(cmd, **kwargs)

            with self.subTest(path=path):
                with patch.object(subprocess, 'check_output', side_effect=changed_commit):
                    with self.assertRaisesRegex(ValueError, 'committed V2 drift'):
                        verify_provenance(self.selection)

    def test_arbitrary_descendant_path_rejected(self):
        original = subprocess.check_output
        for command in (['git', 'diff', '--name-only', '-z', CHECKPOINT],
                        ['git', 'ls-files', '--others', '--exclude-standard', '-z']):
            def extra_file(cmd, **kwargs):
                value = original(cmd, **kwargs)
                if cmd == command:
                    return value + b'docs/episode-component-tracking-v2-v2-unrecognized.md\0'
                return value

            with self.subTest(command=command):
                with patch.object(subprocess, 'check_output', side_effect=extra_file):
                    with self.assertRaisesRegex(ValueError, 'unrecognized descendant'):
                        verify_provenance(self.selection)

    def test_bound_evidence_mutation_rejected(self):
        original = Path.read_bytes
        for path in self.selection['provenance']['bound_files_sha256']:
            def changed_bytes(file):
                return original(file) + (b'changed' if file == ROOT / path else b'')

            with self.subTest(path=path):
                with patch.object(Path, 'read_bytes', changed_bytes):
                    with self.assertRaisesRegex(ValueError, 'bound-file drift'):
                        verify_provenance(self.selection)

    def test_selection_bytes_and_v2_decision_unchanged(self):
        for path in ('docs/' + STEM + 'stage37-configuration-selection.md',
                     'results/' + STEM + 'stage37-configuration-selection.json'):
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(
                ['git', 'show', SELECTION_CHECKPOINT + ':' + path], cwd=ROOT))
        design = read('v2-discrimination-preregistration')
        self.assertEqual(design['decision'], 'V2_DISCRIMINATION_EXPERIMENT_PREREGISTERED')
        self.assertFalse(design['execution_performed'])

    def test_reviews_remain_unchanged(self):
        scientific.validate_payload(self.scientific)
        computational.validate_review(self.computational)
        self.assertEqual(digest(scientific.REPORT.read_bytes()), scientific.REPORT_SHA256)
        for kind in ('scientific', 'computational'):
            for directory, extension in [('results', 'json'), ('docs', 'md')]:
                path = f'{directory}/{STEM}stage37-{kind}-review.{extension}'
                self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(
                    ['git', 'show', CHECKPOINT + ':' + path], cwd=ROOT))

    def test_original_manifest_accounting_and_unresolved(self):
        manifest = read('draft2-full-matrix-canonical-arms')
        self.assertEqual([{k: a[k] for k in FIELDS} for a in self.arms],
                         [{k: a[k] for k in FIELDS} for a in manifest['arms']])
        self.assertEqual(len({a['arm_id'] for a in self.arms}), 160)
        self.assertEqual(Counter(a['state'] for a in self.arms),
                         {'COMPLETE': 152, 'COMPUTATION_UNRESOLVED': 8})
        for k, v in self.selection['stage36_accounting'].items():
            self.assertEqual(v, self.audit[k])
        unresolved = [a for a in self.arms if a['state'] != 'COMPLETE']
        self.assertEqual({a['arm_id'] for a in unresolved},
                         {f'native__w{w}__paths_margin{m}'
                          for w in (300, 325, 350, 'unlimited') for m in ('0.25', '1')})
        for a in unresolved:
            self.assertIsNone(a['scientific_evidence'])
            self.assertEqual(a['computational_evidence']['classification'], 'B')
        treatment = self.selection['unresolved_arm_treatment']
        self.assertFalse(treatment['inferred_missing_episodes'])
        self.assertFalse(treatment['selected_exception'])
        self.assertEqual(treatment['arms'], self.audit['unresolved'])
        for a in treatment['arms']:
            self.assertEqual(a['reason'], 'Unresolved: Exact-cover search limit reached; result is unresolved')

    def test_selected_configuration_must_exist_and_be_complete(self):
        # This decision is deferred. Keep the manifest/completeness contract explicit.
        selected = self.selection['selected_configuration']
        if selected is not None:
            identity = {k: selected[k] for k in FIELDS}
            originals = [{k: a[k] for k in FIELDS} for a in read('draft2-full-matrix-canonical-arms')['arms']]
            self.assertIn(identity, originals)
            arm = next(a for a in self.arms if a['arm_id'] == selected['arm_id'])
            self.assertEqual(arm['state'], 'COMPLETE')
        else:
            self.assertEqual(self.selection['decision'], DECISION)

    def test_frozen_limits_and_provenance_repair(self):
        self.assertEqual(self.selection['frozen_resource_limits'], computational.LIMITS)
        self.assertEqual(self.selection['frozen_resource_limits'], launch.LIMITS)
        self.assertEqual(self.selection['exact_cover_search_limit_visits'], 200000)
        self.assertEqual(launch.verify_plan()['limits'], computational.LIMITS)
        self.assertEqual(repair.validate_repair(ROOT, launch.sc.sha(ROOT / repair.RUNNER)),
                         repair.ORIGINAL_RUNNER_SHA256)
        repair.validate_gitignore(ROOT, repair.HISTORICAL_SHA256, (ROOT / '.gitignore').read_bytes())
        self.assertEqual(self.selection['inherited_scientific_configuration'],
                         read('draft2-full-matrix-canonical-arms')['scientific_configuration'])

    def test_candidate_projections_and_feasibility(self):
        resources = {a['arm']: a for a in self.computational['arms']}
        for projected, source in zip(self.arms, self.scientific['arms']):
            with self.subTest(arm=source['arm_id']):
                self.assertEqual(projected['state'], source['state'])
                self.assertEqual(projected['receipt_sha256'], source['receipt_sha256'])
                self.assertEqual(projected['receipt_path'], source['receipt_path'])
                self.assertEqual(projected['computational_evidence'], resources[source['arm_id']])
                if source['state'] != 'COMPLETE':
                    continue
                evidence = projected['scientific_evidence']
                self.assertEqual(evidence['metrics'], source['metrics'])
                self.assertEqual(len(evidence['episodes']), 41)
                for ep, original in zip(evidence['episodes'], source['episodes']):
                    self.assertEqual({k: ep[k] for k in original}, original)
                    self.assertEqual(len(ep['persistent_memberships']), ep['persistent_paths'])
                    self.assertEqual(digest(canonical(ep['persistent_memberships'])), ep['persistent_membership_sha256'])
                for capture, summary in evidence['by_capture'].items():
                    catalog = self.selection['evidence_scope']['episode_catalog']
                    indices = [i for i, e in enumerate(catalog, 1) if e['capture'] == capture]
                    self.assertEqual(summary['episode_indices'], indices)
                    eps = [evidence['episodes'][i-1] for i in indices]
                    self.assertEqual(summary['statuses'], Counter(e['status'] for e in eps))
                    self.assertEqual(summary['primary_count'], sum(e['primary'] is not None for e in eps))
                    self.assertEqual(summary['persistent_membership_count'], sum(e['persistent_paths'] for e in eps))
                resource = projected['computational_evidence']
                self.assertLess(resource['elapsed_seconds'], 400)
                self.assertLessEqual(resource['observed_peak_rss_kib'], 524288)
        ids = [i for f in self.selection['candidate_families'] for i in f['arm_ids']]
        self.assertEqual(Counter(ids), Counter(a['arm_id'] for a in self.arms))

    def test_saved_raw_memberships_without_scientific_execution(self):
        with ExitStack() as stack:
            for name in ('run_batch', 'execute_arm', 'worker', 'launch_arm'):
                stack.enter_context(patch.object(launch, name, side_effect=AssertionError('scientific execution forbidden')))
            for name in ('detect', 'represent', 'association'):
                stack.enter_context(patch.object(launch.historical, name, side_effect=AssertionError('scientific execution forbidden')))
            stack.enter_context(patch.object(Path, 'write_bytes', side_effect=AssertionError('write forbidden')))
            stack.enter_context(patch.object(Path, 'write_text', side_effect=AssertionError('write forbidden')))
            validate_payload(self.selection)
            verify_provenance(self.selection)
            self.assertEqual(len(launch.verify_plan()['arms']), 160)
            self.assertEqual(verify_saved_memberships(self.selection), 6232)

    def test_status_primary_and_persistent_neighbor_comparisons(self):
        lookup = {a['arm_id']: a for a in self.arms}
        for p, original in zip(self.selection['neighboring_width_comparisons'],
                               self.scientific['neighboring_width_comparisons']):
            self.assertEqual({k: p[k] for k in original}, original)
            if not p['comparable']:
                self.assertIsNone(p['persistent_membership_changes'])
                continue
            left, right = [lookup[p[k]]['scientific_evidence']['episodes'] for k in ('left', 'right')]
            for key, field in [('status_changes', 'status'), ('primary_membership_changes', 'primary'),
                               ('persistent_membership_changes', 'persistent_memberships')]:
                self.assertEqual(p[key], [i for i, (a, b) in enumerate(zip(left, right), 1) if a[field] != b[field]])
        for key in ('path_margin_comparisons', 'connected_path_comparisons', 'spectral_observations', 'anomaly_fragment_observations'):
            self.assertEqual(self.selection[key], self.scientific[key])

    def test_negative_evidence_and_e07_retained(self):
        self.assertEqual(self.selection['historical_fixture_evidence'], self.scientific['historical_fixture_evidence'])
        for method, summary in self.selection['historical_fixture_evidence']['summary'].items():
            self.assertEqual(summary['noise_false_primary_count'], 1 if method == 'connected' else 10)
            self.assertEqual(summary['crossing_competing_switches'], 0 if method == 'connected' else 8)
            self.assertEqual(summary['correct_primary_count'], 4)
        for arm in self.arms:
            if arm['state'] == 'COMPLETE':
                ep = arm['scientific_evidence']['episodes'][40]
                self.assertEqual(ep['status'], 'INSUFFICIENT_SUPPORT')
                self.assertIsNone(ep['primary'])
        self.assertEqual(self.selection['evidence_scope']['episode_catalog'][40]['fragment_count'], 1)

    def test_hierarchy_and_conservative_claims(self):
        self.assertEqual([c['criterion'] for c in self.selection['decision_criteria_hierarchy']],
                         ['SCIENTIFIC_VALIDITY', 'STABILITY', 'NEGATIVE_EVIDENCE', 'COMPLETENESS',
                          'COMPUTATIONAL_FEASIBILITY', 'ROBUSTNESS_OVER_LOCAL_OPTIMUM', 'SIMPLICITY'])
        self.assertIsNone(self.selection['weighted_score'])
        claims = {c['claim']: c['category'] for c in self.selection['claims_boundary']}
        for k in ('dominant_non_dc_spectral_fragment_behavior', 'persistence_observations'):
            self.assertEqual(claims[k], 'SUPPORTED')
        self.assertEqual(claims['between_device_comparison'], 'DESCRIPTIVE ONLY')
        for k in ('carrier_identity', 'device_identity_fingerprinting', 'universal_threshold_claims', 'source_association_correctness'):
            self.assertEqual(claims[k], 'NOT SUPPORTED')

    def test_candidate_selection_limits_claims_and_negative_drift_rejected(self):
        mutations = [
            lambda p: p['provenance'].update(selection_checkpoint='wrong'),
            lambda p: p.update(selected_configuration={'arm_id': 'native__w300__paths_margin1'}),
            lambda p: p.update(decision='STAGE37_V1_CONFIGURATION_SELECTED'),
            lambda p: p['candidate_evidence'][18].update(state='COMPLETE', scientific_evidence={}),
            lambda p: p['candidate_evidence'][0]['scientific_evidence']['episodes'][0].update(primary=['fabricated']),
            lambda p: p['candidate_evidence'][0]['scientific_evidence']['episodes'][3]['persistent_memberships'].clear(),
            lambda p: p['candidate_evidence'][0]['computational_evidence'].update(elapsed_seconds=0),
            lambda p: p['candidate_families'][0].update(reason='winner'),
            lambda p: p['frozen_resource_limits'].update(worker_timeout_seconds=401),
            lambda p: p['historical_fixture_evidence']['summary']['paths_margin0'].update(noise_false_primary_count=0),
            lambda p: p['claims_boundary'][3].update(category='SUPPORTED'),
            lambda p: p['limitations'].clear(),
            lambda p: p['neighboring_width_comparisons'][0].update(persistent_membership_changes=[1]),
            lambda p: p['unresolved_arm_treatment'].update(inferred_missing_episodes=True),
        ]
        for index, mutate in enumerate(mutations):
            value = copy.deepcopy(self.selection)
            mutate(value)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                validate_payload(value)


if __name__ == '__main__':
    unittest.main()
