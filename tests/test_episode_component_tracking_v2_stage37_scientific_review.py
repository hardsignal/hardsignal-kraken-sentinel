"""Saved-evidence review tests. Never launch arms, detect spectra, or write raw files.

Default tests use committed evidence. Set STAGE37_VERIFY_RAW=1 to additionally
stream every Stage36 inventory hash and compare all complete saved projections.
The external raw tree is opened read-only; absence is an error when opted in.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from provenance.stage37_gitignore_v1 import effective_historical_digest
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = '0df44abb54231d5e8bfe84fe316ebbcf10d3130c'
REVIEW = ROOT / 'results/episode-component-tracking-v2-stage37-scientific-review.json'
REPORT = ROOT / 'docs/episode-component-tracking-v2-stage37-scientific-review.md'
AUDIT = ROOT / 'results/episode-component-tracking-v2-draft2-stage36-final-audit.json'
DECISION = 'STAGE37_SCIENTIFIC_EVIDENCE_REVIEW_COMPLETE'
PAYLOAD_SHA256 = '8c590a6f4186e6044cf8d3cf13611b6bb08339d15786622a39fe9cc7169b2b84'
REPORT_SHA256 = '0d1c3275bc96e71f26638b50cf8f4651138a7c6d9282bccfe216ef15703ae28e'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path):
    return json.loads(path.read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_payload(review):
    require(review['decision'] == DECISION, 'decision drift')
    require(review['configuration_selected'] is False, 'selection is out of scope')
    require(review['provenance']['frozen_checkpoint'] == CHECKPOINT, 'checkpoint drift')
    require(digest(canonical(review)) == PAYLOAD_SHA256, 'review payload drift')


def compare_rows(left, right):
    """Compare saved episode projections, keeping unavailable arms unavailable."""
    if left['state'] != 'COMPLETE' or right['state'] != 'COMPLETE':
        return None
    pairs = list(zip(left['episodes'], right['episodes']))
    return {
        'status_changes': [i for i, (a, b) in enumerate(pairs, 1) if a['status'] != b['status']],
        'primary_presence_changes': [i for i, (a, b) in enumerate(pairs, 1)
                                     if (a['primary'] is None) != (b['primary'] is None)],
        'primary_membership_changes': [i for i, (a, b) in enumerate(pairs, 1)
                                       if a['primary'] != b['primary']],
        'membership_changes': [i for i, (a, b) in enumerate(pairs, 1)
                               if a['membership_sha256'] != b['membership_sha256']],
        'cardinality_changes': [i for i, (a, b) in enumerate(pairs, 1)
                                if a['cardinality'] != b['cardinality']],
        'transitions': dict(Counter(a['status'] + ' -> ' + b['status'] for a, b in pairs)),
    }


class ScientificReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = read(REVIEW)
        cls.audit = read(AUDIT)

    def test_payload_and_report_are_frozen(self):
        validate_payload(self.review)
        self.assertEqual(digest(REPORT.read_bytes()), REPORT_SHA256)
        self.assertIn(DECISION, REPORT.read_text())

    def test_checkpoint_and_committed_bindings(self):
        subprocess.run(['git', 'merge-base', '--is-ancestor', CHECKPOINT, 'HEAD'],
                       cwd=ROOT, check=True)
        for path, expected in self.review['provenance']['committed_files_sha256'].items():
            with self.subTest(path=path):
                frozen = subprocess.check_output(['git', 'show', CHECKPOINT + ':' + path], cwd=ROOT)
                self.assertEqual(digest(frozen), expected)
                self.assertEqual(effective_historical_digest(
                    ROOT, path, digest((ROOT / path).read_bytes())), digest(frozen))
        for path, expected in self.review['provenance']['input_files_sha256'].items():
            self.assertEqual(digest((ROOT / path).read_bytes()), expected, path)

    def test_inherited_gitignore_mismatch_is_explicit_and_only_effective_drift(self):
        plan = read(ROOT / 'results/episode-component-tracking-v2-draft2-full-matrix-launch-plan.json')
        binding = read(ROOT / 'results/episode-component-tracking-v2-draft2-full-matrix-launch-binding-v2.json')
        mismatches = []
        for path, expected in plan['sources'].items():
            if path == binding['runner_path']:
                expected = binding['runner_sha256']
            if effective_historical_digest(ROOT, path, digest((ROOT / path).read_bytes())) != expected:
                mismatches.append(path)
        self.assertEqual(mismatches, ['.gitignore'])
        issue = self.review['provenance']['integrity']['issues'][0]
        self.assertEqual(issue['expected_plan_sha256'], plan['sources']['.gitignore'])
        self.assertEqual(issue['checkpoint_sha256'], digest((ROOT / '.gitignore').read_bytes()))
        execution_ignore = subprocess.check_output(['git', 'show',
            self.review['provenance']['stage36_execution_commit'] + ':.gitignore'], cwd=ROOT)
        self.assertEqual(digest(execution_ignore), issue['expected_plan_sha256'])
        self.assertEqual(self.review['validation']['existing_tests']['errors'], 9)

    def test_exact_inventory_and_unresolved_preservation(self):
        review = self.review
        arms = review['arms']
        self.assertEqual(len(arms), 160)
        self.assertEqual(len({a['arm_id'] for a in arms}), 160)
        self.assertEqual(Counter(a['state'] for a in arms),
                         {'COMPLETE': 152, 'COMPUTATION_UNRESOLVED': 8})
        plan = read(ROOT / 'results/episode-component-tracking-v2-draft2-full-matrix-launch-plan.json')
        self.assertEqual([{k: a[k] for k in ('arm_id', 'representation', 'width_hz', 'association')}
                          for a in arms], plan['arms'])
        audited = {a['arm']: a for a in self.audit['arms']}
        for a in arms:
            self.assertEqual(a['state'], audited[a['arm_id']]['state'])
            self.assertEqual(a['receipt_sha256'], audited[a['arm_id']]['receipt_sha256'])
            if a['state'] != 'COMPLETE':
                self.assertIsNone(a['scientific_summary'])
                self.assertNotIn('episodes', a)
                self.assertNotIn('metrics', a)
                self.assertEqual(a['representation'], 'native')
                self.assertIn(a['width_hz'], (300, 325, 350, None))
                self.assertIn(a['association'], ('paths_margin0.25', 'paths_margin1'))
        for key, value in review['accounting'].items():
            self.assertEqual(value, self.audit[key])

    def test_episode_denominators_statuses_persistence_and_e07(self):
        catalog = self.review['episode_catalog']
        self.assertEqual(len(catalog), 41)
        self.assertEqual(sum(e['fragment_count'] for e in catalog), 210)
        self.assertEqual(len({e['capture'] for e in catalog}), 6)
        self.assertEqual(catalog[40]['episode'], 7)
        self.assertEqual(catalog[40]['fragment_count'], 1)
        totals = Counter()
        for arm in self.review['arms']:
            if arm['state'] != 'COMPLETE':
                continue
            eps = arm['episodes']
            self.assertEqual([e['episode_index'] for e in eps], list(range(1, 42)))
            statuses = Counter(e['status'] for e in eps)
            totals.update(statuses)
            self.assertEqual(statuses, arm['metrics']['statuses'])
            self.assertEqual(sum(e['persistent_paths'] for e in eps), arm['metrics']['persistent_tracks'])
            self.assertEqual(sum(e['primary'] is not None for e in eps), arm['metrics']['primary_tracks'])
            self.assertEqual(eps[40]['status'], 'INSUFFICIENT_SUPPORT')
            for ep in eps:
                self.assertEqual(ep['structural_violations'], 0)
                if ep['primary'] is not None:
                    self.assertEqual(ep['status'], 'UNIQUE_PERSISTENT_TRACK')
                    self.assertGreaterEqual(ep['primary_support'], 3)
                    self.assertGreaterEqual(ep['primary_coverage'], .6)
                    self.assertEqual(ep['primary_coverage'], ep['primary_support'] /
                                     catalog[ep['episode_index'] - 1]['fragment_count'])
                if arm['association'] != 'connected':
                    self.assertEqual(ep['cardinality']['state'], 'EXACT')
                    self.assertGreaterEqual(int(ep['cardinality']['value_decimal']), 1)
        self.assertEqual(totals, {'UNIQUE_PERSISTENT_TRACK': 2334, 'AMBIGUOUS_ASSOCIATION': 904,
                                  'INSUFFICIENT_SUPPORT': 2427, 'MULTIPLE_PERSISTENT_TRACKS': 291,
                                  'NO_ELIGIBLE_COMPONENT': 276})

    def test_aggregates_and_matched_comparisons(self):
        arms = self.review['arms']
        for grouping, groups in self.review['aggregates'].items():
            factors = grouping.removeprefix('by_').split('_and_')
            for key, group in groups.items():
                selected = [a for a in arms if '|'.join(str(a[f]) for f in factors) == key]
                eps = [e for a in selected if a['state'] == 'COMPLETE' for e in a['episodes']]
                self.assertEqual(group['arms'], len(selected))
                self.assertEqual(group['states'], Counter(a['state'] for a in selected))
                self.assertEqual(group['episode_arm_observations'], len(eps))
                self.assertEqual(group['statuses'], Counter(e['status'] for e in eps))
                self.assertEqual(group['primary_count'], sum(e['primary'] is not None for e in eps))
        lookup = {a['arm_id']: a for a in arms}
        for name in ('neighboring_width_comparisons', 'connected_path_comparisons',
                     'path_margin_comparisons', 'native_grid_status_comparisons'):
            for comparison in self.review[name]:
                expected = compare_rows(lookup[comparison['left']], lookup[comparison['right']])
                self.assertEqual(comparison['comparable'], expected is not None)
                if expected is not None:
                    self.assertEqual(comparison['episode_pairs'], 41)
                    for field, value in expected.items():
                        if field in comparison:
                            self.assertEqual(comparison[field], value)

    def test_historical_negative_evidence_is_not_overwritten(self):
        history = self.review['historical_fixture_evidence']['summary']
        source = read(ROOT / 'results/episode-component-tracking-v2-draft2-experiment/association-fixture-summary.json')
        self.assertEqual(history, source)
        for method, metrics in history.items():
            self.assertEqual(metrics['noise_trials'], 100)
            self.assertEqual(metrics['noise_false_primary_count'], 1 if method == 'connected' else 10)
            self.assertEqual(metrics['crossing_competing_switches'], 0 if method == 'connected' else 8)
            self.assertEqual(metrics['correct_primary_count'], 4)

    def test_obvious_review_drift_is_rejected(self):
        mutations = [
            lambda x: x.update(decision='CONFIGURATION_SELECTED'),
            lambda x: x.update(configuration_selected=True),
            lambda x: x['provenance'].update(frozen_checkpoint='wrong'),
            lambda x: x['arms'].pop(),
            lambda x: x['arms'].__setitem__(0, x['arms'][1]),
            lambda x: x['arms'][0]['metrics']['statuses'].update(UNIQUE_PERSISTENT_TRACK=1),
            lambda x: x['arms'][0]['episodes'].pop(),
            lambda x: x['arms'][18].update(state='COMPLETE', scientific_summary={}),
            lambda x: x['historical_fixture_evidence']['summary']['paths_margin0'].update(noise_false_primary_count=0),
            lambda x: x.update(winner='grid_sigma20'),
            lambda x: x['limitations'].clear(),
        ]
        for i, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.review)
            mutate(changed)
            with self.subTest(mutation=i), self.assertRaises(ValueError):
                validate_payload(changed)

    @unittest.skipUnless(os.environ.get('STAGE37_VERIFY_RAW') == '1', 'opt-in read-only raw audit')
    def test_full_raw_hash_inventory_and_saved_episode_projections(self):
        raw = Path(self.review['provenance']['raw_root'])
        inventory = ROOT / 'results/episode-component-tracking-v2-draft2-stage36-files.sha256'
        hashes = {}
        byte_count = 0
        for line in inventory.read_text().splitlines():
            expected, relative = line.split('  ', 1)
            relative = relative.removeprefix('./')
            self.assertNotIn(relative, hashes)
            self.assertNotIn('..', Path(relative).parts)
            path = raw / relative
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
                    byte_count += len(block)
            self.assertEqual(h.hexdigest(), expected, relative)
            hashes[relative] = expected
        self.assertEqual(len(hashes), 46524)
        self.assertEqual(byte_count, 8286982589)
        for arm in self.review['arms']:
            receipt_path = arm['receipt_path']
            self.assertEqual(hashes[receipt_path], arm['receipt_sha256'])
            receipt = read(raw / receipt_path)
            base = Path(receipt_path).parent
            self.assertEqual(receipt['state'], arm['state'])
            self.assertEqual(receipt['plan_sha256'], self.audit['plan_sha256'])
            self.assertEqual(receipt['manifest_sha256'], self.audit['manifest_sha256'])
            for relative, expected in receipt['files'].items():
                self.assertEqual(hashes[str(base / relative)], expected)
            if arm['state'] != 'COMPLETE':
                self.assertFalse((raw / base / 'arm.json').exists())
                continue
            saved = read(raw / base / 'arm.json')
            self.assertEqual(saved['metrics'], arm['metrics'])
            self.assertEqual(len(saved['episodes']), 41)
            for projected, episode in zip(arm['episodes'], saved['episodes']):
                association = episode['association']
                self.assertEqual(projected['status'], association['status'])
                primary = association['primary']
                self.assertEqual(projected['primary'], None if primary is None else sorted(primary))
                self.assertEqual(projected['eligible_candidates'], episode['metrics']['eligible_candidate_count'])
                self.assertEqual(projected['persistent_paths'], len(association['persistent_tracks']))
                self.assertEqual(projected['membership_sha256'], digest(canonical(sorted(
                    sorted(p['members']) for p in association['support_coverage']))))
                result = read(raw / base / f"episode-{projected['episode_index']:03d}/result.json")
                self.assertEqual(result['association'], association)
                self.assertEqual(projected['cardinality'], result.get('cardinality'))
                self.assertIsNone(result['metrics']['truth_metrics'])


if __name__ == '__main__':
    unittest.main()
