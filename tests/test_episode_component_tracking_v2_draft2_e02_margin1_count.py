"""Independent exhaustive checks for exact frozen-IEEE threshold composition."""
from collections import Counter
import itertools
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_e02_margin1_count as new
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_experiment as exhaustive


def brute(histories,optima,margin):
    boundary=sum(optima)+margin+exact.TOLERANCE
    total=0
    for choices in itertools.product(*(list(h.items()) for h in histories)):
        cost=0.;multiplicity=1
        for i,(g,n) in enumerate(choices):
            if cost+sum(optima[i:])>boundary:break
            cost+=g;multiplicity*=n
        else:
            if cost<=boundary:total+=multiplicity
    return total


class PivotCountTests(unittest.TestCase):
    def test_preimage_neighbours_rounding_ties_and_subnormals(self):
        values=[0.,math.ulp(0.),math.nextafter(0.,1.)*2,0.1,0.3,1.,math.nextafter(1.,math.inf),
                2.**53,1e100,sys.float_info.max]
        for threshold in values:
            for g in values:
                bound=new.addition_preimage(threshold,g,old.Budget())
                if bound is None:
                    self.assertGreater(g,threshold)
                else:
                    self.assertGreaterEqual(bound,0.)
                    self.assertLessEqual(bound+g,threshold)
                    self.assertGreater(math.nextafter(bound,math.inf)+g,threshold)

    def test_small_weighted_histories_against_full_products(self):
        for seed in range(100):
            rng=random.Random(seed)
            histories=[]
            for i in range(rng.randrange(1,6)):
                h=Counter()
                for _ in range(rng.randrange(1,5)):
                    h[rng.choice([0.,.1,.2,.3,.5,math.nextafter(.3,0.),math.nextafter(.3,1.)])]+=rng.randrange(1,5)
                histories.append(h)
            optima=[min(h) for h in histories]
            for margin in exact.MARGINS:
                want=brute(histories,optima,margin)
                for reverse in (False,True):
                    self.assertEqual(new.compose(histories,optima,margin,old.Budget(),reverse)['count'],want)

    def test_random_graphs_against_exhaustive_and_committed(self):
        for seed in range(35):
            rng=random.Random(seed)
            rows=[[(3000+5*rng.randrange(15),str(j),12) for j in range(2)] for _ in range(1+seed%3)]
            fs=exhaustive.make_fragments(rows)
            nodes=[c for f in fs for c in f['components']]
            for margin in exact.MARGINS:
                f=exact.EpisodeFamily(nodes,len(fs),margin)
                want=exhaustive.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count']
                self.assertEqual(new.count(f,force_ieee=True)['count'],want)
                self.assertEqual(new.count(f,ordering='reverse',force_ieee=True)['count'],want)
                self.assertEqual(old.count(f)['count'],want)

    def test_global_margin_and_singleton_identity(self):
        fs=exhaustive.make_fragments([[(3000,'A',12),(5000,'B',12),(9000,'C',12)],
            [(3000,'A',12),(3025,'D',12),(5000,'B',12),(5025,'E',12)]])
        for margin in exact.MARGINS:
            f=exact.EpisodeFamily([c for x in fs for c in x['components']],2,margin)
            self.assertEqual(new.count(f,force_ieee=True)['count'],
                             exhaustive.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count'])

    def test_equal_cost_assignments_and_unordered_paths(self):
        for fragments in (1,2,3):
            fs=exhaustive.make_fragments([[(3000,'A',12),(3000,'B',12)]]*fragments)
            f=exact.EpisodeFamily([c for x in fs for c in x['components']],fragments,1.)
            self.assertEqual(new.count(f,force_ieee=True)['count'],2**(fragments-1))
        self.assertEqual(new.compose([{0.:10**50},{0.:7}],[0.,0.],1.,old.Budget())['count'],7*10**50)

    def test_boundary_nonassociativity_is_not_reordered(self):
        histories=[{0.1:1},{0.2:1,math.nextafter(.2,1.):2},{.3:1}]
        for margin in (0.,.25,1.):
            self.assertEqual(new.compose(histories,[.1,.2,.3],margin,old.Budget())['count'],
                             brute(histories,[.1,.2,.3],margin))

    def test_resource_exhaustion_returns_no_partial_count(self):
        for budget in (old.Budget(max_states=1),old.Budget(max_transitions=1),old.Budget(max_seconds=1e-12)):
            with self.assertRaises(old.CountUnresolved):
                new.compose([{.1:1,.2:1}]*3,[.1]*3,.25,budget)

    def test_empty_factors_and_invalid_domains(self):
        self.assertEqual(new.compose([],[],0.,old.Budget())['count'],1)
        self.assertEqual(new.compose([{}],[0.],1.,old.Budget())['count'],0)
        with self.assertRaises(ValueError):new.compose([{-1.:1}],[0.],1.,old.Budget())
        with self.assertRaises(ValueError):new.addition_preimage(1.,float('nan'),old.Budget())


if __name__=='__main__':unittest.main()
