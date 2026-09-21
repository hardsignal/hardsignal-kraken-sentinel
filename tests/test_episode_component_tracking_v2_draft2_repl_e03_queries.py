"""Every public query against complete small-family enumeration."""
import itertools
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
import episode_component_tracking_v2_draft2_repl_e03_exact_queries as new
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_experiment as historical
from episode_component_tracking_v2_draft2_staged_queries import Queries as Previous


def build(rows,margin):
    fs=historical.make_fragments(rows)
    return exact.EpisodeFamily([c for f in fs for c in f['components']],len(fs),margin)


def enumerate_family(family):
    choices=[f.materialize() for f in family.factors];result=[]
    for covers in itertools.product(*choices):
        paths=list(family.singletons)
        for f,ks in zip(family.factors,covers):paths.extend(map(tuple,f.solver.ids(ks)))
        if family.contains(paths):result.append(frozenset(paths))
    return result


class ReplQueryTests(unittest.TestCase):
    def compare(self,rows,margin):
        family=build(rows,margin);covers=enumerate_family(family)
        paths=list(family.singletons)
        for f in family.factors:paths.extend(tuple(f.solver.ids((k,))[0]) for k in range(len(f.solver.paths)))
        paths += [('absent',)]
        old=Previous(build(rows,margin))
        for order in ('forward','reverse'):
            q=new.Queries(build(rows,margin),order)
            for p in paths:
                possible=any(p in c for c in covers);invariant=all(p in c for c in covers)
                self.assertEqual(q.possible(p),possible)
                self.assertEqual(q.invariant(p),possible and invariant)
                self.assertEqual(old.possible(p),possible)
                for req,ban in [((),(p,)),((p,),()),((p,),(p,))]:
                    want=any(set(req)<=c and not set(ban)&c for c in covers)
                    answer=q.find(req,ban);self.assertEqual(answer is not None,want)
                    if answer is not None:self.assertIn(frozenset(answer),covers)
            for a,b in itertools.combinations(paths,2):
                for req,ban in [((a,b),()),((),(a,b)),((a,),(b,))]:
                    want=any(set(req)<=c and not set(ban)&c for c in covers)
                    answer=q.find(req,ban);self.assertEqual(answer is not None,want)
                    if answer is not None:self.assertTrue(q.contains(answer))
            self.assertEqual(q.classify(),old.classify())
            witness=q.find();alternative=q.alternative(witness)
            self.assertEqual(alternative is not None,len(covers)>1)
            if alternative is not None:self.assertNotEqual(frozenset(alternative),frozenset(witness))

    def test_random_small_complete_queries(self):
        for seed in range(12):
            rng=random.Random(seed)
            rows=[[(3000+10*rng.randrange(8),str(i),12) for i in range(2)] for _ in range(1+seed%3)]
            for margin in exact.MARGINS:self.compare(rows,margin)

    def test_crossing_persistent_disconnected_and_singleton(self):
        cases=[[[ (3000+i*20,'A',12),(3080-i*20,'B',12)] for i in range(3)],
               [[(3000,'A',12),(5000,'B',12)],[(3025,'C',12),(5025,'D',12)]],
               [[(3000,'A',12)]]]
        for rows in cases:
            for m in exact.MARGINS:self.compare(rows,m)

    def test_exhaustion_is_not_cached_as_absence(self):
        f=build([[(3000,'A',12),(3025,'B',12)]]*3,1.)
        q=new.Queries(f);factor=f.factors[0];factor.solver.search_limit=0
        p=tuple(factor.solver.ids((next(k for k,x in enumerate(factor.solver.paths) if len(x.nodes)==1),))[0])
        with self.assertRaises(exact.Unresolved):q.find(forbidden=(p,))
        self.assertNotIn((frozenset(),frozenset([p])),q.cache)

    def test_query_cache_reuses_global_positive_answer(self):
        f=build([[(3000,'A',12)],[(3025,'B',12),(3030,'C',12)]],1.)
        q=new.Queries(f)
        for factor in f.factors:
            for k in range(len(factor.solver.paths)):q.possible(tuple(factor.solver.ids((k,))[0]))
        before=q.stats['base_global_queries']
        for factor in f.factors:
            for k in range(len(factor.solver.paths)):q.invariant(tuple(factor.solver.ids((k,))[0]))
        self.assertEqual(before,q.stats['base_global_queries'])

if __name__=='__main__':unittest.main()

class QueryEngineProvenanceTests(unittest.TestCase):
    def test_engine_hash_and_limits_tamper_fail_before_queries(self):
        from copy import deepcopy
        root=Path(__file__).resolve().parents[1]
        ref=new.engine_reference(root,'forward')
        for field,value in [('sha256','0'*64),('search_limit',200001),('query_limits',dict(max_calls=5001,max_seconds=120))]:
            forged=deepcopy(ref);forged[field]=value
            with self.assertRaises(ValueError):new.integrate(root,{},[],{},forged)
