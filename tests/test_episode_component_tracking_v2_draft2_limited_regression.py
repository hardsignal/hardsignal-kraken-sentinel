"""Fixed structural selection, regression failure contract and exhaustive fixtures."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import regress_episode_component_tracking_v2_draft2_limited as regression
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact


class LimitedRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=regression.read_plan()
        cls.raw=json.loads((ROOT/cls.plan['input_artifact']).read_text())

    def selected(self,label):
        selected=next(e for e in self.plan['selected'] if e['label']==label)
        episode=regression.saved_episode(self.plan,selected)
        self.assertEqual(len(episode['components']),selected['original_fragment_count'])
        self.assertEqual([sum(c['eligible_for_tracking'] for c in f['components']) for f in episode['components']],selected['eligible_per_fragment'])
        return episode

    def test_predeclared_coverage_and_immutable_plan(self):
        self.assertEqual(regression.sc.sha(regression.PLAN),regression.PLAN_SHA256)
        self.assertEqual(len(self.plan['selected']),7)
        self.assertEqual(len({e['capture'] for e in self.plan['selected']}),6)
        self.assertEqual(self.plan['case_count'],28)
        self.assertEqual(self.plan['arms'],['connected','margin-0','margin-0.25','margin-1'])
        self.assertTrue(self.plan['selection_before_execution'])

    def test_tpms004_ordinary_multifragment(self):
        e=self.selected('TPMS004-ordinary')
        self.assertEqual(e['episode'],2)
        self.assertEqual(len(e['components']),5)
        self.assertFalse(any(a['capture']==e['capture'] and a['episode']==2 for a in self.raw['anomalous_fragments']))

    def test_tpms004_known_large_spread_anomaly(self):
        e=self.selected('TPMS004-anomaly')
        self.assertEqual(e['episode'],1)
        self.assertEqual(len(e['components']),5)
        self.assertAlmostEqual(e['fragments'][2]['native_reference_hz'],5550.215142360157)
        self.assertGreater(max(f['native_reference_hz'] for f in e['fragments'])-
                           min(f['native_reference_hz'] for f in e['fragments']),10000)

    def test_tpms005_sixth_capture_multifragment(self):
        e=self.selected('TPMS005-ordinary')
        self.assertEqual(e['episode'],1)
        self.assertEqual(len(e['components']),5)
        self.assertIn('TPMS-005',e['capture'])

    def test_tpms007_ordinary_multifragment(self):
        e=self.selected('TPMS007-ordinary')
        self.assertEqual(e['episode'],1)
        self.assertEqual(len(e['components']),5)
        self.assertIn('TPMS-007',e['capture'])

    def test_between_positive_261_anomaly(self):
        e=self.selected('BETWEEN-anomaly')
        self.assertEqual(e['episode'],6)
        self.assertAlmostEqual(e['fragments'][3]['native_reference_hz'],260.9173304037352)
        self.assertEqual(len(e['components']),5)

    def test_repl_single_fragment_input(self):
        e=self.selected('REPL-single')
        self.assertEqual(e['episode'],7)
        self.assertEqual(len(e['components']),1)
        self.assertEqual(sum(c['eligible_for_tracking'] for c in e['components'][0]['components']),38)

    def test_established_e08_two_fragment_control(self):
        e=self.selected('TPMS008-control')
        self.assertEqual(len(e['components']),2)
        for arm in ('margin-0','margin-0.25','margin-1'):
            result=json.loads((regression.E08_RESULTS/f'{arm}.json').read_text())
            regression.check_projection(result,e,arm)
            self.assertEqual(result['association']['persistent_tracks'],[])
            self.assertIsNone(result['association']['primary'])
            self.assertEqual(result['association']['status'],'AMBIGUOUS_ASSOCIATION')

    def test_exhaustive_parity_for_selected_structural_classes(self):
        # Small exact controls preserve denominator and introduce the specified
        # outlier structures without labeling real captures or rerunning detection.
        from test_episode_component_tracking_v2_draft2_staged import StagedTests
        helper=StagedTests();helper.context=staged.git_context(ROOT);helper.setUp()
        self.addCleanup(helper.doCleanups)
        ordinary=[[(-5300+i,'A',12)] for i in range(5)]
        spread=copy.deepcopy(ordinary);spread[2].append((5550,'outlier',26))
        positive=copy.deepcopy(ordinary);positive[3].append((261,'outlier',26))
        crossing=[[(3000+i*25,'A',12),(3100-i*25,'B',20)] for i in range(5)]
        for rows in (ordinary,spread,positive,crossing,[[(-5300,'A',12)]],[[(-5300,'A',12)]]*2):
            fs=staged.historical.make_fragments(rows)
            for margin in exact.MARGINS:helper.assert_parity(fs,margin)

    def test_preparation_failure_cannot_be_empty_success(self):
        selected=self.plan['selected'][0]
        result=regression.blocked(self.plan,selected,'margin-0',staged.git_context(ROOT),
                                  'family_construction','declared construction limit')
        self.assertEqual(result['states']['family_construction']['state'],'COMPUTATION_UNRESOLVED')
        self.assertFalse(result['family_complete_as_predicate'])
        for field in ('association','metrics','cardinality'):self.assertIsNone(result[field])
        self.assertEqual(result['states']['cardinality_counting']['state'],'NOT_EVALUATED')
        self.assertEqual(regression.check_projection(result,self.selected('TPMS004-ordinary'),'margin-0')['state'],
                         'UNAVAILABLE_EXPLICIT_FAILURE')

    def test_readiness_rejects_partial_or_failed_batch(self):
        self.assertFalse(regression.ready([]))
        rows=[dict(label=e['label'],arm=arm,worker=dict(exit_code=1)) for e in self.plan['selected'] for arm in self.plan['arms']]
        self.assertFalse(regression.ready(rows))

    def test_construction_deadline_propagates_unresolved(self):
        with patch.object(exact,'EpisodeFamily',side_effect=exact.Unresolved('test solver limit')):
            with self.assertRaises(exact.Unresolved):regression.construct([],0.,1)


if __name__=='__main__':unittest.main()
