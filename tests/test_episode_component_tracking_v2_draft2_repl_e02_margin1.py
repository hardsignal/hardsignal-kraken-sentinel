"""Exact dyadic residual matching equivalence and retained-count validation."""
from fractions import Fraction
import itertools
import math
from pathlib import Path
import random
import sys
from types import MethodType
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_repl_e02_margin1_count as new
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_experiment as brute
from test_episode_component_tracking_v2_draft2_e02_margin1_count import brute as product_count


def solver(rows):
    fs=brute.make_fragments(rows)
    return exact.Solver([c for f in fs for c in f['components']],len(fs))


def adapt(s):
    ratios={e:v.as_integer_ratio() for e,v in s.edges.items()}
    s._integer_denominator=max((q for p,q in ratios.values()),default=1)
    s._integer_edges={e:p*(s._integer_denominator//q) for e,(p,q) in ratios.items()}
    s._matching=MethodType(new.integer_matching,s)
    return s


class ReplCounterTests(unittest.TestCase):
    def test_residual_matching_all_small_masks_ties_and_constraints(self):
        for seed in range(12):
            rng=random.Random(seed)
            rows=[[(3000+rng.choice([0,5,25,50]),str(i),12) for i in range(2)] for _ in range(3)]
            a=solver(rows);b=adapt(solver(rows))
            for mask in range(1<<len(a.nodes)):
                for target in (None,0,1,2):
                    forbidden=frozenset(list(a.edges)[:seed%3])
                    mandatory=frozenset([0]) if seed%2 else frozenset()
                    self.assertEqual(a._matching(mask,target,forbidden,mandatory),b._matching(mask,target,forbidden,mandatory))

    def test_dyadic_extremes_and_exact_selected_path_ties(self):
        rows=[[(3000,'A',12),(3000,'B',12)],[(3000,'C',12),(3000,'D',12)]]
        for costs in ([0.]*4,[math.ulp(0.),0.,math.nextafter(.1,0.),.1],[.1,math.nextafter(.1,1.),2.**40,1.]):
            a=solver(rows);b=solver(rows)
            for s in (a,b):s.edges=dict(zip(s.edges,costs));s._matching_cache.clear()
            adapt(b)
            for target in (None,0,1,2):self.assertEqual(a._matching(a.full,target),b._matching(b.full,target))

    def test_small_graph_counts_exhaustive_both_orders(self):
        for seed in range(24):
            rng=random.Random(seed)
            rows=[[(3000+5*rng.randrange(15),str(i),12) for i in range(2)] for _ in range(1+seed%3)]
            fs=brute.make_fragments(rows);nodes=[c for f in fs for c in f['components']]
            for margin in exact.MARGINS:
                want=brute.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count']
                for order in ('forward','reverse'):
                    f=exact.EpisodeFamily(nodes,len(fs),margin);before=f.artifact()
                    self.assertEqual(new.count(f,ordering=order,force_ieee=True)['count'],want)
                    self.assertEqual(before,f.artifact())
                    self.assertTrue(all('_matching' not in x.solver.__dict__ for x in f.factors))

    def test_weighted_histogram_boundaries_multiplicity(self):
        for costs in ([0.,0.,math.ulp(0.)],[.1,.2,.3,math.nextafter(.3,0.),math.nextafter(.3,1.)],[2.**53,1.,2.],[0.,1e-12,math.nextafter(1e-12,0.)]):
            histories=[{v:10**50+i+1 for i,v in enumerate(costs)}, {v:i+2 for i,v in enumerate(reversed(costs))}]
            optima=[min(h) for h in histories]
            for margin in exact.MARGINS:
                for reverse in (False,True):self.assertEqual(new.previous.compose(histories,optima,margin,old.Budget(),reverse)['count'],product_count(histories,optima,margin))

    def test_exhaustion_restores_solver_and_never_returns_partial_count(self):
        fs=brute.make_fragments([[(3000,'A',12),(3010,'B',12)]]*3)
        for limits in [dict(max_states=1),dict(max_transitions=1),dict(max_seconds=1e-12)]:
            f=exact.EpisodeFamily([c for x in fs for c in x['components']],3,1.)
            with self.assertRaises(old.CountUnresolved):new.count(f,old.Budget(**limits),force_ieee=True)
            self.assertTrue(all('_matching' not in x.solver.__dict__ and not hasattr(x.solver,'_integer_edges') for x in f.factors))

if __name__=='__main__':unittest.main()
