"""New exact column counter validation against exhaustive/committed controls."""
import itertools
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_column_count as new
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_experiment as exhaustive


def nodes(rows):
    return [dict(candidate_id=f'{i}:{j}',fragment_index=i+1,frequency_hz=float(f))
            for i,row in enumerate(rows) for j,f in enumerate(row)]


class ColumnTests(unittest.TestCase):
    def test_integer_histograms_exhaustive(self):
        for seed in range(80):
            rng=random.Random(seed)
            rows=[[(j,rng.randrange(10)) for j in range(6) if rng.random()<.8] for i in range(3)]
            if any(not row for row in rows): continue
            cols=sorted({c for row in rows for c,w in row})
            penalties={c:rng.randrange(4) for c in cols}
            expected={}
            for choices in itertools.product(*rows):
                used={c for c,w in choices}
                if len(used)!=len(rows): continue
                cost=sum(w for c,w in choices)+sum(penalties[c] for c in cols if c not in used)
                if cost<=20: expected[cost]=expected.get(cost,0)+1
            for order in (cols,cols[::-1]):
                for bound in (False,True):
                    self.assertEqual(new.column_histogram(rows,20,old.Budget(),'test',penalties,order,bound),expected)
            self.assertEqual(old.frontier_histogram(rows,20,old.Budget(),'control',penalties),expected)

    def test_frozen_families(self):
        for seed in range(30):
            rng=random.Random(seed)
            ns=nodes([[3000+1.5*rng.randrange(35) for j in range(3)] for i in range(2)])
            for margin in exact.MARGINS:
                f=exact.Solver(ns,2).family(margin)
                want=len(exhaustive.solve_group(ns,margin)['hypotheses'])
                self.assertEqual(new.count(f)['count'],want)
                self.assertEqual(new.count(f,ordering='reverse_frequency')['count'],want)
                self.assertEqual(old.count(f)['count'],want)

    def test_global_margin_and_singletons(self):
        for rows in ([[3000,3015,5001,5016],[3001.5,3016.5,5002.5,5017.5]], [[1000,2000]], [[],[]]):
            for margin in exact.MARGINS:
                f=exact.EpisodeFamily(nodes(rows),len(rows),margin)
                self.assertEqual(new.count(f)['count'],old.count(f)['count'])

    def test_equal_cost_identity(self):
        rows=[[(j,0) for j in range(10)] for i in range(10)]
        self.assertEqual(new.column_histogram(rows,0,old.Budget(),'ties'),{0:3628800})

    def test_fallback_and_multifragment(self):
        for rows in ([[3000],[3000,3025]],[[3000,3010],[3005,3015],[3010]]):
            for margin in exact.MARGINS:
                f=exact.Solver(nodes(rows),len(rows)).family(margin)
                self.assertEqual(new.count(f)['count'],old.count(f)['count'])

    def test_resource_failure_not_partial(self):
        with self.assertRaises(old.CountUnresolved):
            new.column_histogram([[(0,0),(1,1)]]*3,2,old.Budget(max_states=1),'limit')
        with self.assertRaises(old.CountUnresolved):
            new.column_histogram([[(0,0)]],100,old.Budget(max_polynomial_bytes=1),'limit')

if __name__=='__main__': unittest.main()
