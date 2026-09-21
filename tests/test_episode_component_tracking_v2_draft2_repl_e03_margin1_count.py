"""Exact local histogram equality and complete small-family count parity."""
import random
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_repl_e03_margin1_count as new
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_experiment as brute

class DrainedTests(unittest.TestCase):
    def test_full_histograms_and_counts_against_original_and_exhaustive(self):
        for seed in range(30):
            rng=random.Random(seed)
            rows=[[(3000+rng.randrange(15)*5,str(i),12) for i in range(2)] for _ in range(1+seed%3)]
            fs=brute.make_fragments(rows);nodes=[c for f in fs for c in f['components']]
            for margin in exact.MARGINS:
                family=exact.EpisodeFamily(nodes,len(fs),margin)
                want=brute.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count']
                for f in family.factors:
                    h=old.ieee_histogram(f,old.Budget())
                    for rev in (False,True):self.assertEqual(h,new.histogram(f,old.Budget(),rev))
                for order in ('forward','reverse'):self.assertEqual(new.count(family,ordering=order,force_ieee=True)['count'],want)

    def test_disconnected_and_equal_cost_assignments(self):
        for rows in [[[(3000,'A',12),(3000,'B',12)]]*3,
                     [[(3000,'A',12),(5000,'B',12)],[(3025,'C',12),(5025,'D',12)]]]:
            fs=brute.make_fragments(rows)
            for m in exact.MARGINS:
                f=exact.EpisodeFamily([c for x in fs for c in x['components']],len(fs),m)
                self.assertEqual(new.count(f)['count'],brute.association(fs,f'paths_margin{m:g}')['retained_hypothesis_count'])

    def test_artificial_exhaustion_never_returns_partial(self):
        fs=brute.make_fragments([[(3000,'A',12),(3010,'B',12)]]*3)
        for limit in [dict(max_states=1),dict(max_transitions=1),dict(max_seconds=1e-12)]:
            f=exact.EpisodeFamily([c for x in fs for c in x['components']],3,1.)
            with self.assertRaises(old.CountUnresolved):new.count(f,old.Budget(**limit),force_ieee=True)
            self.assertIs(old.ieee_histogram,new.ORIGINAL_HISTOGRAM)

if __name__=='__main__':unittest.main()
