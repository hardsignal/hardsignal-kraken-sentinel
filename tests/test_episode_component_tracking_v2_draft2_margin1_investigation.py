"""Independent validation additions; all reference implementations are read-only."""
import copy
import itertools
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_column_count as column
import episode_component_tracking_v2_draft2_exact_count as previous
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_experiment as frozen
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_compact_consumer_prototype as consumer


class InvestigationTests(unittest.TestCase):
    def test_arbitrary_order_and_cost_histograms(self):
        # Exhaustive assignments independently establish every coefficient,
        # including rectangular holes, negative feasibility and unused penalties.
        for seed in range(120):
            rng = random.Random(1000+seed)
            rows = [[(j, rng.randrange(13)) for j in range(7) if rng.random()<.6]
                    for _ in range(rng.randrange(1, 5))]
            columns = sorted({c for row in rows for c, _ in row})
            penalties = {c: rng.randrange(7) for c in columns}
            cap = rng.randrange(30)
            expected = {}
            for assignment in itertools.product(*rows):
                used = {c for c, _ in assignment}
                if len(used) != len(rows):
                    continue
                cost = sum(w for _, w in assignment)+sum(penalties[c] for c in columns if c not in used)
                if cost <= cap:
                    expected[cost] = expected.get(cost, 0)+1
            rng.shuffle(columns)
            for bound in (False, True):
                self.assertEqual(column.column_histogram(rows, cap, previous.Budget(),
                    'independent', penalties, columns, bound), expected)
            self.assertEqual(previous.frontier_histogram(rows, cap, previous.Budget(),
                             'committed', penalties), expected)

    def test_rectangular_permanent_and_candidate_identity(self):
        # Closed form P(n,m), no hypothesis enumeration and all costs identical.
        for m, n in ((4, 8), (10, 12), (12, 12)):
            rows = [[(c, 0) for c in range(n)] for _ in range(m)]
            self.assertEqual(column.column_histogram(rows, 0, previous.Budget(), 'permanent'),
                             {0: math.factorial(n)//math.factorial(n-m)})

    def test_projection_against_original_consumer_contract(self):
        cases = [[], [[]], [[(3000, 'A', 12)]],
                 [[(3000, 'A', 12)]]*3,
                 [[(3000, 'A', 12), (3000, 'B', 12)]]*3,
                 [[(3000, 'A', 12)], [], [(3000, 'A', 12)], [(3000, 'A', 12)]],
                 [[(3000, 'A', 12), (5000, 'B', 12)],
                  [(3015, 'A', 12), (5015, 'B', 12)]]]
        for rows in cases:
            fragments = frozen.make_fragments(rows)
            nodes = [c for f in fragments for c in f['components'] if c['eligible_for_tracking']]
            for margin in exact.MARGINS:
                original = frozen.association(fragments, f'paths_margin{margin:g}')
                family = exact.EpisodeFamily(nodes, len(fragments), margin)
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    path = root/'family.json'
                    path.write_bytes(exact.canonical_bytes(family.artifact()))
                    source = root/'source.py'; source.write_text('# test provenance\n')
                    limits = dict(max_states=250000, max_transitions=5000000,
                                  max_seconds=60, max_polynomial_bytes=33554432)
                    with patch.object(exact.Family, 'materialize', side_effect=AssertionError('No expansion')):
                        result = column.count(family)
                        self.assertEqual(result['count'], original['retained_hypothesis_count'])
                        outcome = dict(count_state='EXACT', exact_count_decimal=str(result['count']),
                            method=result['method'], statistics=dict(result['stats'], process_peak_rss_kib=0))
                        side = sc.create(root, path, outcome, [source], limits)
                        projected = consumer.project(root, path, side,
                            any(f['usable_spectrum'] for f in fragments))
                        for key in ('status','primary','optimum_links','optimum_cost',
                                    'invariant_membership','alternative_membership','persistent_tracks',
                                    'candidate_membership_alternatives','support_coverage',
                                    'structural_constraint_violations'):
                            self.assertEqual(projected[key], original[key], (rows, margin, key))
                        unresolved = copy.deepcopy(side)
                        unresolved['cardinality'] = dict(state='COMPUTATION_UNRESOLVED',
                            value_decimal=None, reason={'reason':'declared audit limit'})
                        other = consumer.project(root, path, unresolved,
                            any(f['usable_spectrum'] for f in fragments))
                        self.assertEqual({k:v for k,v in projected.items() if k!='cardinality'},
                                         {k:v for k,v in other.items() if k!='cardinality'})
                        # Metrics need an explicit representation branch in the
                        # future runner. Their math can already consume this union.
                        compatibility = dict(projected, hypotheses=[])
                        for recoverable in (False, True):
                            self.assertEqual(frozen.fixture_metrics(fragments, compatibility, recoverable),
                                             frozen.fixture_metrics(fragments, original, recoverable))

    def test_sidecar_rejects_changed_definition_limits_and_paths(self):
        # Reuse a test fixture, not an artifact under investigation.
        from test_episode_component_tracking_v2_draft2_cardinality_sidecar import SidecarTests
        fixture = SidecarTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for field, value in [('counting_definition_version', 'changed'),
                             ('margin_hex', '1.0'),
                             ('family_artifact', '../family.json'),
                             ('computational_limits', {}),
                             ('runtime_state_statistics', {})]:
            side = copy.deepcopy(fixture.card); side[field] = value
            with self.assertRaises(ValueError):
                sc.validate(fixture.root, side, fixture.path)


if __name__ == '__main__':
    unittest.main()
