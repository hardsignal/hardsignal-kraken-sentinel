"""Validate the separate solver against frozen exhaustive Draft 2, without RF."""
import copy
import json
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import episode_component_tracking_v2_draft2_experiment as old
import episode_component_tracking_v2_draft2_exact_solver as new


def nodes(rows):
    return [dict(candidate_id=f'F{i+1:03d}_C{j+1:03d}',fragment_index=i+1,
                 frequency_hz=float(f),eligible_for_tracking=True,contrast_db=12.,width_hz=10.)
            for i,row in enumerate(rows) for j,f in enumerate(row)]


def sets(hypotheses):
    return {tuple(sorted(map(tuple,h['paths']))) for h in hypotheses}


class ExactSolverTests(unittest.TestCase):
    def compare(self, rows, margins=(0.,.25,1.)):
        ns=nodes(rows); solver=new.Solver(ns,len(rows))
        for margin in margins:
            reference=old.solve_group(ns,margin)
            family=solver.family(margin)
            self.assertEqual(family.optimum.links,reference['optimum_links'])
            self.assertEqual(family.optimum.cost,reference['optimum_cost'])
            covers=family.materialize()
            actual={tuple(sorted(map(tuple,solver.ids(c)))) for c in covers}
            self.assertEqual(actual,sets(reference['hypotheses']))
        return solver

    def test_random_small_graphs_exact_float_objective_and_entire_family(self):
        for seed in range(50):
            rng=random.Random(seed)
            rows=[[3000+rng.uniform(-70,70) for _ in range(rng.randrange(1,3))] for _ in range(rng.randrange(2,5))]
            with self.subTest(seed=seed): self.compare(rows)

    def test_equal_cost_distinct_assignments_survive(self):
        s=self.compare([[3000,3000]]*3)
        family=s.family(0)
        self.assertEqual(len(family.materialize()),4)
        self.assertIsNone(family.classify()['primary'])
        self.assertEqual(family.classify()['status'],'MULTIPLE_PERSISTENT_TRACKS')

    def test_crossing(self):
        self.compare([[3000,3100],[3025,3075],[3050,3050],[3075,3025],[3100,3000]])

    def test_range_constraint_rejects_matching_relaxation(self):
        s=self.compare([[3000],[3050],[3100],[3150]])
        self.assertGreater(s.range_rejected_extensions,0)
        self.assertEqual(s.optimum().links,2)
        self.assertEqual(s.optimum().cost,2.)

    def test_boundaries(self):
        for rows in ([[3000],[3050],[3100]],[[3000],[3050.000001],[3100]],
                     [[3000],[],[3050]],[[3000],[],[],[3050]],
                     [[3000],[3034],[3068],[3100.000001]]):
            self.compare(rows)

    def test_margin_numeric_boundary(self):
        for delta in (-1e-10,0,1e-10,1e-11,-1e-11):
            self.compare([[3000],[3000,3025+delta]])

    def test_prefix_predicate_and_nonassociative_sums(self):
        self.compare([[3000.1,5000.3],[3003.3,5002.9],[3012.8,5004.5],[3021.7,5008.1]])

    def test_possible_invariant_queries_against_full_family(self):
        s=self.compare([[3000,3010],[3005,3020],[3015]])
        for margin in new.MARGINS:
            f=s.family(margin); covers=f.materialize()
            for k in range(len(s.paths)):
                self.assertEqual(f.possible(k),any(k in c for c in covers))
                self.assertEqual(f.invariant(k),all(k in c for c in covers))
            self.assertEqual(f.alternative() is not None,len(covers)>1)

    def test_forbidden_pair_does_not_forbid_longer_path_edge(self):
        s=new.Solver(nodes([[3000],[3005],[3010]]),3)
        pair=s.by_nodes[(0,1)]
        found=s.family(0).find(forbidden=(pair,))
        self.assertIsNotNone(found)
        self.assertIn(s.by_nodes[(0,1,2)],found)

    def test_required_paths_are_disjoint(self):
        s=new.Solver(nodes([[3000],[3005],[3010]]),3)
        self.assertIsNone(s.family(0).find(required=(s.by_nodes[(0,1)],s.by_nodes[(1,2)])))

    def test_original_fragment_denominator(self):
        ns=nodes([[3000],[3005],[3010]])
        self.assertIsNotNone(new.Solver(ns,5).family(0).classify()['primary'])
        self.assertIsNone(new.Solver(ns,6).family(0).classify()['primary'])

    def test_one_two_fragment_null_primary(self):
        for rows in ([[3000]],[[3000],[3005]]):
            s=self.compare(rows)
            self.assertIsNone(s.family(1).classify()['primary'])

    def test_empty_candidates(self):
        s=self.compare([[],[]])
        self.assertEqual(s.family(0).classify()['status'],'NO_ELIGIBLE_COMPONENT')

    def test_determinism_and_input_permutation(self):
        ns=nodes([[3000,3025],[3010,3035],[3020,3040]])
        a=new.Solver(ns,3).family(.25)
        b=new.Solver(list(reversed(ns)),3).family(.25)
        self.assertEqual(new.canonical_bytes(a.artifact()),new.canonical_bytes(b.artifact()))
        self.assertEqual(a.materialize(),b.materialize())

    def test_roundtrip_lossless_artifact(self):
        s=new.Solver(nodes([[3000,3025],[3010,3035]]),2)
        f=s.family(1); artifact=json.loads(new.canonical_bytes(f.artifact()))
        restored=new.Family.from_artifact(artifact)
        self.assertEqual(f.materialize(),restored.materialize())
        bad=copy.deepcopy(artifact); bad['margin']=0
        with self.assertRaises(ValueError): new.Family.from_artifact(bad)
        self.assertIsNone(artifact['retained_hypothesis_count'])

    def test_no_silent_truncation(self):
        s=new.Solver(nodes([[3000,3000]]*3),3)
        with self.assertRaises(new.Unresolved): s.family(0).materialize(limit=1)
        s=new.Solver(nodes([[3000],[3050],[3100],[3150]]),4,search_limit=0)
        with self.assertRaises(new.Unresolved): s.optimum()

    def test_amplitude_and_labels_do_not_select(self):
        ns=nodes([[3000,3025],[3010,3035],[3020,3040]])
        original=new.Solver(ns,3).family(1).artifact()
        for c in ns: c.update(contrast_db=999,device_label='anything',amplitude=0)
        self.assertEqual(original,new.Solver(ns,3).family(1).artifact())

    def test_reject_duplicate_ids_and_unknown_margin(self):
        ns=nodes([[3000],[3000]])
        with self.assertRaises(ValueError): new.Solver(ns+[ns[0]],2)
        with self.assertRaises(ValueError): new.Solver(ns,2).family(.5)


    def test_episode_global_margin_and_queries(self):
        rows=[[3000,5000],[3000,3025,5000,5025]]
        ns=nodes(rows)
        fragments=[dict(usable_spectrum=True,components=[c for c in ns if c['fragment_index']==i+1]) for i in range(len(rows))]
        for margin,arm in ((0,'paths_margin0'),(.25,'paths_margin0.25'),(1,'paths_margin1')):
            reference=old.association(fragments,arm)
            family=new.EpisodeFamily(ns,len(rows),margin)
            expected=sets(reference['hypotheses'])
            for hypothesis in reference['hypotheses']: self.assertTrue(family.contains(hypothesis['paths']))
            witness=family.find()
            self.assertIn(tuple(sorted(witness)),expected)
            self.assertEqual(family.classify()['status'],reference['status'])
            self.assertEqual(family.classify()['primary'],reference['primary'])
            for p in {p for h in expected for p in h}:
                self.assertEqual(family.possible(p),any(p in h for h in expected))
                self.assertEqual(family.invariant(p),all(p in h for h in expected))
        f=new.EpisodeFamily(ns,2,.25)
        # Taking both +0.25 alternatives would spend the margin twice.
        self.assertFalse(f.contains([['F001_C001','F002_C002'],['F002_C001'],
                                     ['F001_C002','F002_C004'],['F002_C003']]))

    def test_episode_classification_fixture_equivalence(self):
        for name,fragments,recoverable in old.association_fixtures():
            if name.startswith('noise_'): continue
            ns=[c for f in fragments for c in f['components']]
            for margin,arm in ((0,'paths_margin0'),(.25,'paths_margin0.25'),(1,'paths_margin1')):
                with self.subTest(fixture=name,margin=margin):
                    expected=old.association(fragments,arm)
                    actual=new.EpisodeFamily(ns,len(fragments),margin).classify()
                    self.assertEqual(actual['status'],expected['status'])
                    self.assertEqual(actual['primary'],expected['primary'])

    def test_episode_artifact_roundtrip_and_global_filter(self):
        ns=nodes([[3000,5000,9000],[3000,3025,5000,5025]])
        original=new.EpisodeFamily(ns,2,.25)
        restored=new.EpisodeFamily.from_artifact(json.loads(new.canonical_bytes(original.artifact())))
        self.assertEqual(original.find(),restored.find())
        self.assertEqual(original.classify(),restored.classify())
        self.assertTrue(restored.contains(original.find()))

    def test_mandatory_singleton_matching_is_exact(self):
        s=self.compare([[3000,3010,3020],[3001,3011]])
        for margin in new.MARGINS:
            f=s.family(margin); covers=f.materialize()
            for i in range(len(s.nodes)):
                singleton=s.by_nodes[(i,)]
                found=f.find(forbidden=(singleton,))
                self.assertEqual(found is not None,any(singleton not in c for c in covers))
                if found is not None: self.assertTrue(f.contains(found))

if __name__=='__main__': unittest.main()
