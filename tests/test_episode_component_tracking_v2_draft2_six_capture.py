"""Frozen complete inventory, preflight gates and explicit failure contracts."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import regress_episode_component_tracking_v2_draft2_six_capture as r


class SixCaptureTests(unittest.TestCase):
    def test_complete_inventory_and_limits(self):
        p=r.read_plan()
        self.assertEqual((p['episode_count'],p['case_count']),(41,164))
        self.assertEqual(len(p['captures']),6)
        self.assertEqual(p['count_limits'],dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432))
        self.assertEqual(p['query_limits'],dict(max_calls=5000,max_seconds=120))
        self.assertEqual((p['family_construction_seconds'],p['worker_timeout_seconds'],p['worker_peak_rss_limit_kib']),(60,400,524288))
        for selected in p['selected']:
            episode=r.limited.saved_episode(p,selected)
            self.assertEqual(len(episode['components']),selected['original_fragment_count'])
            self.assertEqual([sum(c['eligible_for_tracking'] for c in f['components']) for f in episode['components']],selected['eligible_per_fragment'])

    def test_plan_tamper_rejected(self):
        with patch.object(r.sc,'sha',return_value='0'*64):
            with self.assertRaises(ValueError):r.read_plan()

    def test_preflight_is_exactly_seven_original_episodes(self):
        p=r.read_plan();m=r.control_map()
        self.assertEqual(len(m),7)
        self.assertTrue(set(m)<=set((e['capture'],e['episode']) for e in p['selected']))
        self.assertFalse(r.controls_valid([]))

    def good(self):
        return dict(arm='margin-1',worker=dict(exit_code=0,reason=None),reload_worker=dict(exit_code=0,reason=None),
            reload=dict(state='BYTE_IDENTICAL'),resource_violations=[],audit=dict(projection=dict(state='PASS'),
            states={k:dict(state=v) for k,v in [('provenance_validation','VERIFIED'),('family_construction','COMPLETE'),
                    ('exact_queries','EXACT'),('cardinality_counting','EXACT'),('metric_projection','COMPLETE')]}))

    def test_every_stage_failure_rejects_readiness(self):
        row=self.good();self.assertTrue(r.passed(row))
        for stage in row['audit']['states']:
            bad=copy.deepcopy(row);bad['audit']['states'][stage]['state']='COMPUTATION_UNRESOLVED'
            self.assertFalse(r.passed(bad))
        for worker in ['worker','reload_worker']:
            bad=copy.deepcopy(row);bad[worker]['reason']='resource ceiling'
            self.assertFalse(r.passed(bad))
        bad=copy.deepcopy(row);bad['reload']['state']='REPRODUCTION_FAILED';self.assertFalse(r.passed(bad))
        bad=copy.deepcopy(row);bad['resource_violations']=['peak_states'];self.assertFalse(r.passed(bad))

    def test_corrected_cardinality_only_exception(self):
        p=r.read_plan();selected=next(e for e in p['selected'] if e['label']=='C1-E02')
        old=json.loads((r.OLD/'TPMS004-ordinary/margin-1/result.json').read_text())
        with self.assertRaises(ValueError):r.limited_parity(old,selected,'margin-1')
        fixed=copy.deepcopy(old);fixed['cardinality']=dict(state='EXACT',value_decimal='5788836',reason=None)
        self.assertEqual(r.limited_parity(fixed,selected,'margin-1'),'PASS_E02_CARDINALITY_CORRECTION')
        fixed['association']['original_fragment_count']=999
        with self.assertRaises(ValueError):r.limited_parity(fixed,selected,'margin-1')

    def test_polynomial_peak_is_not_summed_across_released_blocks(self):
        self.assertEqual(r.polynomial_bytes(dict(details=[dict(peak_packed_bytes=20),dict(polynomial_bytes=40)])),40)
        self.assertEqual(r.polynomial_bytes({}),0)

    def test_reconstruction_deadline_propagates(self):
        with r.construction_limits(0):
            with self.assertRaises(r.exact.Unresolved):r.exact.EpisodeFamily([],1,0)


if __name__=='__main__':unittest.main()
