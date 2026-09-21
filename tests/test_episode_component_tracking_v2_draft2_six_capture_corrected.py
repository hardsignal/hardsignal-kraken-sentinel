"""Corrected-run inventory, composed dispatch, and scientific parity rejection gates."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import regress_episode_component_tracking_v2_draft2_six_capture_corrected as r
import episode_component_tracking_v2_draft2_experiment as brute
from test_episode_component_tracking_v2_draft2_six_capture import SixCaptureTests


class CorrectedTests(unittest.TestCase):
    def test_frozen_inventory_and_candidate_hashes(self):
        p=r.read_plan();old=r.historical.read_plan()
        self.assertEqual(p['selected'],old['selected'])
        self.assertEqual((len(p['captures']),p['episode_count'],p['case_count']),(6,41,164))
        self.assertNotEqual(r.PLAN,r.historical.PLAN)
        self.assertEqual(p['git_commit'],'7e38dd9caeb19282ecaa7b5d8464074e77fa5986')

    def test_parity_is_required_for_readiness(self):
        row=SixCaptureTests().good()
        self.assertFalse(r.passed(row))
        row['audit']['original_parity']={'state':'PASS'}
        self.assertTrue(r.passed(row))
        row['audit']['original_parity']['state']='FAIL'
        self.assertFalse(r.passed(row))

    def test_original_passing_payload_mutations_rejected(self):
        selected=r.read_plan()['selected'][0]
        original=json.loads((r.BASE/selected['label']/'connected/result.json').read_text())
        self.assertEqual(r.original_parity(original,selected,'connected',None)['state'],'PASS')
        for field in r.SCIENTIFIC_FIELDS+('states','cardinality'):
            changed=copy.deepcopy(original);changed[field]={'tampered':True}
            with self.assertRaises(ValueError):r.original_parity(changed,selected,'connected',None)

    def test_composed_routes_match_exhaustive_partitions(self):
        for rows in ([[(3000+7*i,'A',12)] for i in range(4)],
                     [[(3000,'A',12),(3007,'B',12)]]*3,
                     [[(3000,'A',12),(3007,'B',12)],[],[(3007,'A',12),(3014,'B',12)]]):
            fs=brute.make_fragments(rows)
            for margin in (0,.25,1):
                f=r.exact.EpisodeFamily([c for x in fs for c in x['components']],len(fs),margin)
                got=r.count_exact(f,r.previous.Budget())
                self.assertEqual(got['count'],brute.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count'])

    def test_composition_preserves_budget_and_restores_backend(self):
        fs=brute.make_fragments([[(3000,'A',12),(3007,'B',12)]]*3)
        f=r.exact.EpisodeFamily([c for x in fs for c in x['components']],3,1)
        original=r.cutoff.previous.compose
        with self.assertRaises(r.previous.CountUnresolved):r.count_exact(f,r.previous.Budget(max_transitions=1))
        self.assertIs(r.cutoff.previous.compose,original)

    def test_missing_mandatory_controls_fail(self):
        self.assertFalse(r.mandatory_controls([])['passed'])


if __name__=='__main__':unittest.main()
