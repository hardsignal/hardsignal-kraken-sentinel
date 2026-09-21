"""Read-only definition and artifact audits; never import or execute detector/solver runners."""
import ast
import collections
import copy
import csv
import hashlib
import io
import itertools
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-draft2-full-matrix'
BASE = ROOT / 'results/episode-component-tracking-v2-draft2-experiment'
MANIFEST = ROOT / 'results' / (STEM + '-canonical-arms.json')
REVIEW = ROOT / 'results' / (STEM + '-definition-review.json')
REPS = ('native', 'grid_sigma0', 'grid_sigma5', 'grid_sigma10', 'grid_sigma20')
WIDTHS = (200, 225, 250, 275, 300, 325, 350, None)
ASSOCIATIONS = ('connected', 'paths_margin0', 'paths_margin0.25', 'paths_margin1')
FIELDS = ('arm_id', 'representation', 'width_hz', 'association')


def load(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def expected_grid():
    return [dict(arm_id=f'{r}__w{w if w is not None else "unlimited"}__{a}',
                 representation=r, width_hz=w, association=a)
            for r, w, a in itertools.product(REPS, WIDTHS, ASSOCIATIONS)]


def validate_grid(manifest):
    rows = [{k: row[k] for k in FIELDS} for row in manifest['arms']]
    if rows != expected_grid() or len({row['arm_id'] for row in rows}) != 160:
        raise ValueError('Frozen Cartesian grid or ordering changed')
    if digest(canonical(rows)) != manifest['original_matrix_sha256']:
        raise ValueError('Frozen matrix hash mismatch')


class MatrixDefinitionReviewTests(unittest.TestCase):
    def test_independent_cartesian_inventory(self):
        manifest = load(MANIFEST)
        validate_grid(manifest)
        self.assertEqual(manifest['arm_count'], 160)
        self.assertEqual(manifest['dimensions'], dict(representations=5, widths=8, associations=4))
        self.assertEqual(MANIFEST.read_bytes(), canonical(manifest))

    def test_missing_duplicate_added_changed_and_reordered_arms_rejected(self):
        for mutation in ('missing', 'duplicate', 'added', 'width', 'association', 'order'):
            m = copy.deepcopy(load(MANIFEST))
            if mutation == 'missing':
                m['arms'].pop()
            elif mutation == 'duplicate':
                m['arms'][-1] = copy.deepcopy(m['arms'][0])
            elif mutation == 'added':
                m['arms'].append(copy.deepcopy(m['arms'][0]))
            elif mutation == 'width':
                m['arms'][0]['width_hz'] = 201
            elif mutation == 'association':
                m['arms'][0]['association'] = 'compact'
            else:
                m['arms'][0], m['arms'][1] = m['arms'][1], m['arms'][0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_grid(m)

    def test_original_source_constants_without_execution(self):
        path = ROOT / 'analysis/episode_component_tracking_v2_draft2_experiment.py'
        names = {'REPRESENTATIONS': REPS, 'WIDTHS': WIDTHS, 'ASSOCIATIONS': ASSOCIATIONS}
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(path.read_text()).body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                  and n.targets[0].id in names}
        self.assertEqual(values, names)

    def test_original_commits_json_csv_and_current_inventory(self):
        want = expected_grid()
        for revision in ('51861e1', 'f00dc2a', '6bd63ac'):
            prefix = f'{revision}:{BASE.relative_to(ROOT)}'
            rows = json.loads(subprocess.check_output(['git', 'show', prefix + '/arms.json'], cwd=ROOT))
            self.assertEqual([{k: row[k] for k in FIELDS} for row in rows], want)
            raw = subprocess.check_output(['git', 'show', prefix + '/arms.csv'], cwd=ROOT).decode()
            csv_rows = list(csv.DictReader(io.StringIO(raw)))
            self.assertEqual([r['arm_id'] for r in csv_rows], [r['arm_id'] for r in want])
            self.assertEqual([r['state'] for r in csv_rows], [r['state'] for r in rows])

    def test_all_original_provenance_and_bundle_bindings(self):
        p = load(BASE / 'run.json')['provenance']
        sources = {'code_sha256': 'analysis/episode_component_tracking_v2_draft2_experiment.py',
                   'frozen_control_code_sha256': 'analysis/episode_component_tracking_v2_draft1.py',
                   'spec_sha256': 'docs/episode-component-tracking-v2-draft2-experiment.md',
                   'test_sha256': 'tests/test_episode_component_tracking_v2_draft2_experiment.py'}
        for key, name in sources.items():
            self.assertEqual(digest((ROOT / name).read_bytes()), p[key])
            for revision in ('51861e1', 'f00dc2a'):
                self.assertEqual(digest(subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT)), p[key])
        for name, expected in p['inputs'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected)
        for line in (BASE / 'files.sha256').read_text().splitlines():
            expected, name = line.split('  ', 1)
            self.assertEqual(digest((BASE / name).read_bytes()), expected)

    def test_original_failure_is_not_reclassified(self):
        rows = load(MANIFEST)['arms']
        self.assertEqual(collections.Counter(r['historical_execution_state'] for r in rows),
                         {'COMPLETE': 1, 'COMPUTATION_UNRESOLVED': 1, 'NOT_RUN': 158})
        self.assertEqual(rows[1]['arm_id'], 'native__w200__paths_margin0')
        self.assertEqual(rows[1]['historical_failure']['visited_states'], 200001)
        self.assertEqual(rows[1]['historical_completed_episode_count'], 26)
        self.assertTrue(all(r['restart_execution_state'] == 'NOT_EXECUTED' for r in rows))
        self.assertFalse(load(MANIFEST)['execution_authorized'])
        self.assertFalse(load(BASE / 'run.json')['gates_evaluable'])

    def test_false_primaries_and_crossing_evidence_come_from_saved_fixtures(self):
        fixtures = load(BASE / 'association-fixtures.json')
        reported = load(REVIEW)['historical_run']['association_fixture_evidence']
        self.assertEqual(len(fixtures), 452)
        for association in ASSOCIATIONS:
            rows = [r for r in fixtures if r['association'] == association]
            false = [r['name'] for r in rows if r['metrics']['false_primary']]
            self.assertEqual(false, reported[association]['false_primary_fixture_names'])
            self.assertEqual(len(false), 1 if association == 'connected' else 10)
            crossing = next(r for r in rows if r['name'] == 'crossing')
            self.assertEqual(crossing['metrics']['identity_switches'], 0 if association == 'connected' else 8)
            self.assertIsNone(crossing['result']['primary'])

    def test_representation_width_and_association_semantics_are_separate(self):
        s = load(MANIFEST)['scientific_configuration']
        self.assertEqual([r['identifier'] for r in s['representations']], list(REPS))
        self.assertEqual([r['sigma_hz'] for r in s['representations']], [None, 0, 5, 10, 20])
        self.assertEqual([w['value_hz'] for w in s['widths']], list(WIDTHS))
        self.assertEqual([a['identifier'] for a in s['associations']], list(ASSOCIATIONS))
        self.assertEqual([a['margin'] for a in s['associations']], [None, 0, .25, 1])
        self.assertEqual(s['grid']['bin_width_hz'], 2.5)
        self.assertEqual(s['numerical_policy']['tolerance_hex'], float(1e-12).hex())
        self.assertEqual(s['association_shared']['fragment_increment'], [1, 2])
        self.assertEqual(s['association_shared']['maximum_step_hz'], 50)
        self.assertEqual(s['association_shared']['maximum_whole_path_range_hz'], 100)
        self.assertEqual(s['association_shared']['minimum_support'], 3)
        self.assertEqual(s['association_shared']['minimum_coverage'], .6)

    def test_corrected_candidate_contexts_remain_native_200_slice(self):
        p = load(ROOT / 'results/episode-component-tracking-v2-draft2-six-capture-corrected-plan.json')
        original = load(ROOT / p['input_artifact'])
        self.assertEqual(digest((ROOT / p['input_artifact']).read_bytes()), p['input_sha256'])
        self.assertEqual(original['arm']['arm_id'], 'native__w200__connected')
        lookup = {(e['capture'], e['episode']): e for e in original['episodes']}
        for selected in p['selected']:
            episode = lookup[selected['capture'], selected['episode']]
            self.assertEqual(digest(canonical(episode['components'])), selected['fragments_sha256'])
            self.assertEqual(len(episode['components']), selected['original_fragment_count'])
        comparison = load(REVIEW)['corrected_comparison']
        self.assertEqual(len(comparison['compact_bindings']), 123)
        self.assertTrue(all(x['valid'] for x in comparison['compact_bindings']))
        self.assertEqual(comparison['drift'], [])

    def test_checkpoint_and_all_preexisting_tracked_bytes(self):
        b = load(REVIEW)['before']
        self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), b['head'])
        self.assertEqual(subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT).decode().strip(), b['branch'])
        for name, expected in b['files'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)


if __name__ == '__main__':
    unittest.main()
