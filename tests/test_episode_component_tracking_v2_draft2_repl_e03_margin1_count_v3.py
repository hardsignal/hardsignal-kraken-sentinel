"""Certified path-cover/matching bijection against exhaustive retained families."""
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_repl_e03_margin1_count_v3 as new
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_experiment as brute

class CertificateTests(unittest.TestCase):
    def test_certified_three_layer_counts_against_complete_enumeration(self):
        certified=0
        for seed in range(30):
            rng=random.Random(seed)
            rows=[[(3000+7*rng.randrange(5),str(j),12) for j in range(2)],[],
                  [(3000+7*rng.randrange(5),str(j),12) for j in range(2)],[],
                  [(3000+7*rng.randrange(5),str(j),12) for j in range(2)]]
            fs=brute.make_fragments(rows);nodes=[c for f in fs for c in f['components']]
            for margin in (.25,1.):
                f=exact.EpisodeFamily(nodes,5,margin)
                want=brute.association(fs,f'paths_margin{margin:g}')['retained_hypothesis_count']
                for order in ('forward','reverse'):
                    result=new.count(f,ordering=order)
                    certified+=result['method']==new.VERSION
                    self.assertEqual(result['count'],want)
        self.assertGreater(certified,80)

    def test_deficient_matching_dummy_factorial_is_exact(self):
        fs=brute.make_fragments([[(3000,'A',12),(3000,'B',12),(3000,'C',12),(3049,'D',12)],
                                 [(3000,'E',12),(3098,'F',12),(3098,'G',12),(3098,'H',12)]])
        f=exact.EpisodeFamily([c for x in fs for c in x['components']],2,1.)
        blocks,_,_=new.certificate(f)
        self.assertTrue(any(b['dummy_factor']==2 for b in blocks))
        for order in ('forward','reverse'):
            self.assertEqual(new.count(f,ordering=order)['count'],brute.association(fs,'paths_margin1')['retained_hypothesis_count'])

    def test_long_directed_paths_reject_certificate(self):
        fs=brute.make_fragments([[(3000+7*i,'A',12)] for i in range(4)])
        f=exact.EpisodeFamily([c for x in fs for c in x['components']],4,1.)
        with self.assertRaises(old.CertificateUnavailable):new.certificate(f)
        self.assertEqual(new.count(f)['count'],brute.association(fs,'paths_margin1')['retained_hypothesis_count'])

    def test_zero_margin_uses_frozen_fallback(self):
        fs=brute.make_fragments([[(3000,'A',12),(3007,'B',12)]]*3)
        f=exact.EpisodeFamily([c for x in fs for c in x['components']],3,0.)
        with self.assertRaises(old.CertificateUnavailable):new.certificate(f)
        self.assertEqual(new.count(f)['count'],old.count(f)['count'])

    def test_frozen_exhaustion_on_certified_route(self):
        fs=brute.make_fragments([[(3000,'A',12),(3007,'B',12)],[],[(3007,'A',12),(3014,'B',12)],[],[(3014,'A',12),(3021,'B',12)]])
        f=exact.EpisodeFamily([c for x in fs for c in x['components']],5,1.)
        new.certificate(f)
        for limits in [dict(max_states=1),dict(max_seconds=1e-12),dict(max_polynomial_bytes=1)]:
            with self.assertRaises(old.CountUnresolved):new.count(f,old.Budget(**limits))

if __name__=='__main__':unittest.main()
