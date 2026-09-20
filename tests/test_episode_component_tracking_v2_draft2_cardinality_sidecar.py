"""Binding and noninterference tests, using temporary new files only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_exact_solver as exact

class SidecarTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.f=exact.Solver([dict(candidate_id=str(i),fragment_index=i+1,frequency_hz=3000.) for i in range(3)],3).family(.25)
        self.path=self.root/'family.json'; self.path.write_bytes(exact.canonical_bytes(self.f.artifact()))
        self.source=self.root/'counter.py'; self.source.write_text('# test source\n')
        self.outcome=dict(count_state='EXACT',exact_count_decimal='1',method='test',statistics=dict(elapsed_seconds=0.,peak_states=1,transitions=1,process_peak_rss_kib=1))
        self.limits=dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432)
        self.card=sc.create(self.root,self.path,self.outcome,[self.source],self.limits)

    def test_exact_round_trip_no_expansion(self):
        restored=sc.validate(self.root,json.loads(json.dumps(self.card)),self.path)
        self.assertEqual(restored.artifact(),self.f.artifact())
        self.assertNotIn('hypotheses',self.card)
        huge=copy.deepcopy(self.card); huge['cardinality']['value_decimal']='9'*200
        sc.validate(self.root,huge,self.path) # schema capacity, not proof of that count

    def test_wrong_family_and_tamper_rejected(self):
        other=self.root/'different.json'; other.write_bytes(self.path.read_bytes())
        with self.assertRaises(ValueError): sc.validate(self.root,self.card,other)
        for key,value in (('family_sha256','0'*64),('model_sha256','0'*64),('scope','episode'),('margin_hex',float(1).hex()),('arithmetic_policy','other')):
            card=copy.deepcopy(self.card); card[key]=value
            with self.assertRaises(ValueError): sc.validate(self.root,card,self.path)
        self.path.write_bytes(self.path.read_bytes()+b'\n')
        with self.assertRaises(ValueError): sc.validate(self.root,self.card,self.path)

    def test_embedded_model_reconstruction(self):
        model=json.loads(self.path.read_text()); model['maximum_links']=123
        self.path.write_text(json.dumps(model)); card=copy.deepcopy(self.card); card['family_sha256']=sc.sha(self.path)
        with self.assertRaises(ValueError): sc.validate(self.root,card,self.path)

    def test_unresolved_preserves_queries(self):
        before=self.path.read_bytes(); witness=self.f.find(); path=witness[0]
        self.outcome.update(count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None,failure={'reason':'test limit'})
        card=sc.create(self.root,self.path,self.outcome,[self.source],self.limits)
        restored=sc.validate(self.root,card,self.path)
        self.assertEqual(restored.contains(witness),self.f.contains(witness))
        self.assertEqual(restored.invariant(path),self.f.invariant(path))
        self.assertEqual(restored.classify(),self.f.classify())
        self.assertEqual(self.path.read_bytes(),before)

    def test_invalid_cardinality_and_sources(self):
        for card in ({'state':'EXACT','value_decimal':12,'reason':None},
                     {'state':'EXACT','value_decimal':'01','reason':None},
                     {'state':'COMPUTATION_UNRESOLVED','value_decimal':'1','reason':{'reason':'limit'}},
                     {'state':'COMPUTATION_UNRESOLVED','value_decimal':None,'reason':None}):
            modified=copy.deepcopy(self.card); modified['cardinality']=card
            with self.assertRaises(ValueError): sc.validate(self.root,modified,self.path)
        self.source.write_text('# changed\n')
        with self.assertRaises(ValueError): sc.validate(self.root,self.card,self.path)

if __name__=='__main__': unittest.main()
