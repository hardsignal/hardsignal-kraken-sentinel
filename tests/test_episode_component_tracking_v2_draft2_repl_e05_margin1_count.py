"""Exhaustive semantics and weighted cutoff checks, independent of target count."""
from pathlib import Path
import sys
import math
import random
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_repl_e05_margin1_count as new
import episode_component_tracking_v2_draft2_e02_margin1_count as previous
from test_episode_component_tracking_v2_draft2_e02_margin1_count import PivotCountTests, brute

class CutoffTests(PivotCountTests):
    def setUp(self):
        # Inherit exhaustive graph, singleton, duplicate assignment, IEEE and
        # resource fixtures, applying them to the new implementation.
        import test_episode_component_tracking_v2_draft2_e02_margin1_count as base
        self.base=base;self.saved=base.new;base.new=new
    def tearDown(self):self.base.new=self.saved
    def test_large_deterministic_cutoff_grid(self):
        for seed in range(250):
            rng=random.Random(seed)
            values=[0.,math.ulp(0.),.1,.2,.3,math.nextafter(.3,0.),math.nextafter(.3,1.),1.,2.**53]
            h={rng.choice(values)+rng.randrange(100)/128:10**50+rng.randrange(5) for _ in range(40)}
            histories=[{0.:3,.1:2},h,{0.:7,.2:11},{0.:2,.2:5}]
            optima=[min(x) for x in histories]
            for margin in (0.,.25,1.):
                want=brute(histories,optima,margin)
                for rev in (False,True):
                    got=new.compose(histories,optima,margin,new.old.Budget(),rev)
                    self.assertEqual(got['count'],want)
                    self.assertEqual(got['count'],previous.compose(histories,optima,margin,new.old.Budget(),rev)['count'])
    def test_cutoff_charges_actual_probes(self):
        b=new.old.Budget()
        result=new.compose([{i/1024:10**60 for i in range(1024)}],[0.],.25,b)
        self.assertTrue(result['cutoff_mode'])
        self.assertEqual(result['count'],257*10**60)
        self.assertEqual(b.transitions,1024+1+result['cutoff_probes']+1)

if __name__=='__main__':unittest.main()
