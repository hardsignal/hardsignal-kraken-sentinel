"""Exact-count equivalence tests; no RF, IQ, or modifications of old artifacts."""
import itertools
import math
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import episode_component_tracking_v2_draft2_experiment as old
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as counter


def nodes(rows):
    return [dict(candidate_id=f'F{i+1:03d}_C{j+1:03d}',fragment_index=i+1,
                 frequency_hz=float(f),eligible_for_tracking=True,contrast_db=12.,width_hz=10.)
            for i,row in enumerate(rows) for j,f in enumerate(row)]


class ExactCountingTests(unittest.TestCase):
    def compare(self,rows):
        ns=nodes(rows); s=exact.Solver(ns,len(rows))
        for margin in exact.MARGINS:
            expected=old.solve_group(ns,margin)['hypotheses']
            f=s.family(margin)
            self.assertEqual(counter.count(f)['count'],len(expected))
            self.assertEqual(counter.count(f,backend='ieee')['count'],len(expected))

    def test_random_small_complete_families(self):
        for seed in range(40):
            rng=random.Random(seed)
            rows=[[3000+rng.uniform(-65,65) for _ in range(rng.randrange(1,3))] for _ in range(rng.randrange(2,5))]
            with self.subTest(seed=seed): self.compare(rows)

    def test_equal_cost_assignments_count_separately(self):
        self.compare([[3000]*4,[3000]*4])
        self.assertEqual(counter.count(exact.Solver(nodes([[3000]*4]*2),2).family(0))['count'],math.factorial(4))

    def test_millions_counted_without_hypothesis_enumeration(self):
        f=exact.Solver(nodes([[3000]*10]*2),2).family(0)
        result=counter.count(f)
        self.assertEqual(result['count'],math.factorial(10))
        self.assertLess(result['stats']['peak_states'],3000)

    def test_paths_not_labelled_or_permuted(self):
        ns=nodes([[3000,5000],[3005,5005],[3010,5010]])
        f=exact.Solver(ns,3).family(0)
        self.assertEqual(counter.count(f)['count'],1)
        witness=f.find()
        self.assertTrue(f.contains(tuple(reversed(witness))))

    def test_singletons_exactly_once(self):
        self.compare([[3000,4000],[3005],[3010]])
        self.assertEqual(counter.count(exact.EpisodeFamily(nodes([[1000,2000]]),1,1))['count'],1)
        self.assertEqual(counter.count(exact.Solver([],2).family(0))['count'],1)

    def test_global_margin_not_product_of_local_counts(self):
        rows=[[3000,5000],[3000,3025,5000,5025]]
        ns=nodes(rows)
        fragments=[dict(usable_spectrum=True,components=[c for c in ns if c['fragment_index']==i+1]) for i in range(2)]
        for margin,arm in ((0,'paths_margin0'),(.25,'paths_margin0.25'),(1,'paths_margin1')):
            episode=exact.EpisodeFamily(ns,2,margin)
            expected=old.association(fragments,arm)['retained_hypothesis_count']
            self.assertEqual(counter.count(episode)['count'],expected)
        self.assertEqual(counter.count(exact.EpisodeFamily(ns,2,.25))['count'],3)

    def test_disconnected_cost_histories_preserve_multiplicity(self):
        rows=[[3000,3000,5000,5000],[3000,3000,5000,5000]]
        f=exact.EpisodeFamily(nodes(rows),2,0)
        self.assertEqual(counter.count(f)['count'],4)

    def test_range_and_fragment_skip_boundaries(self):
        for rows in ([[3000],[3050],[3100],[3150]],[[3000],[],[3000]],[[3000],[],[],[3000]]): self.compare(rows)

    def test_numeric_margin_boundary_and_fallback(self):
        for change in (0,1e-10,-1e-10): self.compare([[3000],[3000,3025+change]])
        f=exact.Solver(nodes([[3000],[3000,3025]]),2).family(.25)
        with self.assertRaises(counter.CertificateUnavailable): counter.count(f,backend='lattice')
        self.assertEqual(counter.count(f)['count'],2)

    def test_certified_lattice_matches_exhaustive(self):
        for rows in ([[3000,3003,3006],[3001.5,3004.5]],[[3000,3003],[3001.5,3004.5,3007.5]]):
            s=exact.Solver(nodes(rows),2)
            for margin in (.25,1):
                actual=counter.count(s.family(margin),backend='lattice')
                self.assertEqual(actual['count'],len(old.solve_group(nodes(rows),margin)['hypotheses']))
                self.assertIn('certified lattice',actual['method'])

    def test_exact_polynomial_product(self):
        a={0:10**30,1:7,5:10**28}; b={0:9,2:10**29,4:10**31}
        for cap in (0,2,5,9):
            expected={}
            for i,x in a.items():
                for j,y in b.items():
                    if i+j<=cap: expected[i+j]=expected.get(i+j,0)+x*y
            self.assertEqual(counter.convolve(a,b,cap,counter.Budget()),expected)

    def test_frontier_factorization_and_column_identity(self):
        rows=[[(0,0),(1,2)],[(0,1),(1,0),(2,3)],[(3,0),(4,1)]]
        expected={}
        for choices in itertools.product(*rows):
            if len({c for c,w in choices})!=len(rows): continue
            cost=sum(w for c,w in choices)
            if cost<=5: expected[cost]=expected.get(cost,0)+1
        actual=counter.frontier_histogram(rows,5,counter.Budget(),'test')
        self.assertEqual(actual,expected)

    def test_deterministic_and_original_queries_unchanged(self):
        ns=nodes([[3000,3010],[3005,3015],[3010]])
        f=exact.Solver(ns,3).family(.25)
        before=f.artifact(); decision=f.classify(); witness=f.find()
        a=counter.count(f)['count']; b=counter.count(exact.Solver(ns[::-1],3).family(.25))['count']
        self.assertEqual(a,b); self.assertEqual(f.artifact(),before)
        self.assertEqual(f.classify(),decision); self.assertTrue(f.contains(witness))

    def test_resource_failure_is_not_partial_count(self):
        f=exact.Solver(nodes([[3000]*4]*2),2).family(0)
        with self.assertRaises(counter.CountUnresolved): counter.count(f,counter.Budget(max_states=1))
        with self.assertRaises(counter.CountUnresolved): counter.convolve({0:1,100:1},{0:1,100:1},200,counter.Budget(max_polynomial_bytes=1))

    def test_certified_lattice_global_margin(self):
        rows=[[3000,3015,5001,5016],[3001.5,3016.5,5002.5,5017.5]]
        ns=nodes(rows)
        fragments=[dict(usable_spectrum=True,components=[c for c in ns if c['fragment_index']==i+1]) for i in range(2)]
        for margin,arm in ((.25,'paths_margin0.25'),(1,'paths_margin1')):
            result=counter.count(exact.EpisodeFamily(ns,2,margin),backend='lattice')
            self.assertEqual(result['count'],old.association(fragments,arm)['retained_hypothesis_count'])
        self.assertEqual(counter.count(exact.EpisodeFamily(ns,2,.25),backend='lattice')['count'],3)

    def test_assignment_dual_and_unmatched_penalties(self):
        rng=random.Random(41)
        for trial in range(15):
            m,n=3,5
            rows=[[(j,rng.randrange(30)) for j in range(n)] for i in range(m)]
            optimum,reduced,penalties=counter.assignment_dual(rows)
            expected={}
            original=[]
            for cols in itertools.permutations(range(n),m):
                cost=sum(dict(rows[i])[j] for i,j in enumerate(cols))
                residual=sum(dict(reduced[i])[j] for i,j in enumerate(cols))+sum(v for j,v in penalties.items() if j not in cols)
                self.assertEqual(cost-optimum,residual)
                original.append(cost)
                if residual<=20: expected[residual]=expected.get(residual,0)+1
            self.assertEqual(optimum,min(original))
            self.assertEqual(counter.frontier_histogram(reduced,20,counter.Budget(),'dual test',penalties),expected)

    def test_assignment_dual_rejects_infeasible_matching(self):
        with self.assertRaises(counter.CountUnresolved):
            counter.assignment_dual([[(0,1)],[(0,2)],[(1,1),(2,2)]])

if __name__=='__main__': unittest.main()
