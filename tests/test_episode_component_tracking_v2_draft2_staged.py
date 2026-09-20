"""Staged-only validation. Exhaustive controls are used on small fixtures only."""
import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_column_count as counter
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_experiment as old


class StagedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = staged.git_context(ROOT)
        names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
        cls.historical = {p:sc.sha(ROOT/p) for p in names if p and (ROOT/p).is_file()}

    @classmethod
    def tearDownClass(cls):
        assert cls.historical == {p:sc.sha(ROOT/p) for p in cls.historical}, 'Historical bytes changed'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='staged-test-',dir=ROOT/'results')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.serial = 0

    def prepare(self, fragments, margin=.25, unresolved=False):
        self.serial += 1
        family = exact.EpisodeFamily([c for f in fragments for c in f['components'] if c['eligible_for_tracking']],len(fragments),margin)
        path = self.directory/f'family-{self.serial}.json'
        path.write_bytes(exact.canonical_bytes(family.artifact()))
        result = counter.count(family)
        outcome = dict(count_state='EXACT',exact_count_decimal=str(result['count']),method=result['method'],
                       statistics=dict(result['stats'],process_peak_rss_kib=0))
        if unresolved:
            outcome.update(count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None,failure=dict(reason='test counting limit'))
        card = sc.create(ROOT,path,outcome,[Path(counter.__file__),Path(exact.__file__),
                         ROOT/'analysis/episode_component_tracking_v2_draft2_exact_count.py'],
                         dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432))
        card_path = self.directory/f'card-{self.serial}.json'
        card_path.write_bytes(exact.canonical_bytes(card))
        return staged.request(ROOT,fragments,staged.COMPACT,path,card_path)

    def run_compact(self, fs, margin=.25, unresolved=False, **kwargs):
        req = self.prepare(fs,margin,unresolved)
        with patch.object(exact.Family,'materialize',side_effect=AssertionError('Expansion forbidden')):
            return staged.integrate(ROOT,req,fs,self.context,**kwargs)

    def assert_parity(self, fs, margin, recoverable=False):
        reference = old.association(fs,f'paths_margin{margin:g}')
        result = self.run_compact(fs,margin,recoverable=recoverable)
        self.assertEqual(result['states']['exact_queries']['state'],'EXACT',result)
        self.assertEqual(result['states']['metric_projection']['state'],'COMPLETE')
        self.assertEqual(result['association'],dict(
            {k:v for k,v in reference.items() if k not in ('hypotheses','retained_hypothesis_count')},
            original_fragment_count=len(fs)))
        self.assertEqual(result['cardinality']['value_decimal'],str(reference['retained_hypothesis_count']))
        self.assertEqual(result['metrics']['truth_metrics'],old.fixture_metrics(fs,reference,recoverable))
        self.assertNotIn('hypotheses',result['association'])
        self.assertNotIn('hypotheses',result)
        return result

    def test_exhaustive_declared_small_fixtures(self):
        # All 13 deterministic association fixtures; no noise/spectral matrix.
        for name,fs,recoverable in itertools.islice(old.association_fixtures(),13):
            for margin in exact.MARGINS:
                with self.subTest(name=name,margin=margin):
                    self.assert_parity(fs,margin,recoverable)

    def test_seeded_competing_two_and_three_fragment_parity(self):
        for seed in range(10):
            rng=random.Random(seed)
            fs=old.make_fragments([[(3000+10*rng.randrange(8),str(j),12) for j in range(2)]
                                   for _ in range(2+seed%2)])
            for margin in exact.MARGINS:
                self.assert_parity(fs,margin)

    def test_connected_arm_parity_and_explicit_metric_branch(self):
        for name,fs,recoverable in itertools.islice(old.association_fixtures(),13):
            req=staged.request(ROOT,fs,staged.CONNECTED)
            result=staged.integrate(ROOT,req,fs,self.context,recoverable=recoverable)
            expected=old.association(fs,'connected')
            self.assertEqual(result['association'],dict({k:v for k,v in expected.items()
                if k not in ('hypotheses','retained_hypothesis_count')},original_fragment_count=len(fs)))
            self.assertEqual(result['metrics']['truth_metrics'],old.fixture_metrics(fs,expected,recoverable))
            self.assertEqual(result['states']['cardinality_counting']['state'],'NOT_APPLICABLE_CONNECTED')
            with self.assertRaises(ValueError):
                staged.fixture_metrics(fs,result['association'],'unknown',recoverable)

    def test_unresolved_cardinality_does_not_change_primary_or_queries(self):
        for rows in ([[ (3000,'A',12)]]*3, [[(3000,'A',12),(3000,'B',12)]]*3):
            fs=old.make_fragments(rows)
            a=self.run_compact(fs); b=self.run_compact(fs,unresolved=True)
            self.assertEqual(a['association'],b['association'])
            self.assertEqual(a['metrics'],b['metrics'])
            self.assertEqual(a['query_operations'],b['query_operations'])
            self.assertTrue(b['family_complete_as_predicate'])
            self.assertEqual(b['cardinality']['state'],'COMPUTATION_UNRESOLVED')
            self.assertIsNone(b['cardinality']['value_decimal'])

    def test_query_failures_never_become_empty_alternatives(self):
        fs=old.make_fragments([[(3000,'A',12)]]*3)
        req=self.prepare(fs)
        for method,operation in [('possible','membership'),('invariant','invariance'),('classify','ambiguity')]:
            with patch.object(staged.Queries,method,side_effect=exact.Unresolved('injected '+method)):
                result=staged.integrate(ROOT,req,fs,self.context)
            self.assertEqual(result['query_operations'][operation]['state'],'COMPUTATION_UNRESOLVED')
            self.assertEqual(result['states']['exact_queries']['state'],'COMPUTATION_UNRESOLVED')
            self.assertTrue(result['family_complete_as_predicate'])
            self.assertIsNone(result['association'])
            self.assertIsNone(result['metrics'])
            self.assertEqual(result['cardinality']['state'],'EXACT')

    def test_query_call_and_wall_limits(self):
        fs=old.make_fragments([[(3000,'A',12)]]*2);req=self.prepare(fs)
        result=staged.integrate(ROOT,req,fs,self.context,dict(max_calls=1,max_seconds=5))
        self.assertEqual(result['states']['exact_queries']['state'],'COMPUTATION_UNRESOLVED')
        with patch.object(staged.Queries,'possible',side_effect=lambda *args:time.sleep(.05)):
            result=staged.integrate(ROOT,req,fs,self.context,dict(max_calls=500,max_seconds=.01))
        self.assertEqual(result['states']['exact_queries']['state'],'COMPUTATION_UNRESOLVED')
        self.assertIn('wall-clock',result['states']['exact_queries']['reason'])

    def test_family_failure_is_separate(self):
        fs=old.make_fragments([[(3000,'A',12)]]*2);req=self.prepare(fs)
        with patch.object(sc,'validate',side_effect=exact.Unresolved('reconstruction limit')):
            result=staged.integrate(ROOT,req,fs,self.context)
        self.assertEqual(result['states']['family_construction']['state'],'COMPUTATION_UNRESOLVED')
        self.assertEqual(result['states']['exact_queries']['state'],'NOT_EVALUATED')
        self.assertEqual(result['states']['cardinality_counting']['state'],'NOT_EVALUATED')
        self.assertFalse(result['family_complete_as_predicate'])

    def test_metric_failure_does_not_remove_exact_association(self):
        fs=old.make_fragments([[(3000,'A',12)]]*3);req=self.prepare(fs)
        with patch.object(staged,'project_metrics',side_effect=ValueError('metric failure')):
            result=staged.integrate(ROOT,req,fs,self.context)
        self.assertEqual(result['states']['metric_projection']['state'],'COMPUTATION_UNRESOLVED')
        self.assertIsNotNone(result['association']['primary'])
        self.assertEqual(result['states']['exact_queries']['state'],'EXACT')
        self.assertIsNone(result['metrics'])

    def test_unusable_and_no_candidate_precedence(self):
        for fs in ([dict(usable_spectrum=False,components=[])],
                   [dict(usable_spectrum=True,components=[])],
                   [dict(usable_spectrum=False,components=[]) for _ in range(3)]):
            for margin in exact.MARGINS:
                self.assert_parity(fs,margin)
        fs=old.make_fragments([[(3000,'A',12)]]*3)
        for f in fs:f['usable_spectrum']=False
        result=self.assert_parity(fs,.25)
        self.assertEqual(result['association']['status'],'UNUSABLE_INPUT')
        # Historical semantics compute primary separately from input-status precedence.
        self.assertIsNotNone(result['association']['primary'])

    def test_tampered_artifacts_and_hashes_rejected(self):
        fs=old.make_fragments([[(3000,'A',12)]]*2)
        for field in ('family','cardinality_sidecar','experiment_specification'):
            req=self.prepare(fs);req[field]['sha256']='0'*64
            result=staged.integrate(ROOT,req,fs,self.context)
            self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')
            self.assertIsNone(result['association'])
        for field in ('family','cardinality_sidecar'):
            req=self.prepare(fs);path=ROOT/req[field]['path']
            path.write_bytes(path.read_bytes()+b'\n')
            result=staged.integrate(ROOT,req,fs,self.context)
            self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')
        req=self.prepare(fs);path=ROOT/req['cardinality_sidecar']['path']
        card=json.loads(path.read_text());card['model_sha256']='0'*64
        path.write_bytes(exact.canonical_bytes(card));req['cardinality_sidecar']=staged.reference(ROOT,path)
        result=staged.integrate(ROOT,req,fs,self.context)
        self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')

    def test_wrong_family_candidate_context_and_source_rejected(self):
        fs=old.make_fragments([[(3000,'A',12)]]*2);req=self.prepare(fs)
        for mutate in ('denominator','candidate','source','discriminator'):
            altered=copy.deepcopy(req);other=copy.deepcopy(fs)
            if mutate=='denominator':other.append(dict(usable_spectrum=False,components=[]))
            if mutate=='candidate':other[0]['components'][0]['frequency_hz']+=1
            if mutate=='source':altered['sources'][next(iter(altered['sources']))]['sha256']='0'*64
            if mutate=='discriminator':altered['representation']='implicit_from_null'
            altered['fragments_sha256']=staged.digest(other)
            result=staged.integrate(ROOT,altered,other,self.context)
            self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')

    def test_cross_paired_sidecar_and_git_context_rejected(self):
        fs=old.make_fragments([[(3000,'A',12)]]*2)
        a=self.prepare(fs,0.);b=self.prepare(fs,1.)
        a['cardinality_sidecar']=b['cardinality_sidecar']
        result=staged.integrate(ROOT,a,fs,self.context)
        self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')
        for key,value in [('commit','0'*40),('dirty',not self.context['dirty'])]:
            context=dict(self.context);context[key]=value
            result=staged.integrate(ROOT,b,fs,context)
            self.assertEqual(result['states']['provenance_validation']['state'],'REJECTED')

    def test_no_spectrum_or_expanded_solver_dependency(self):
        fs=old.make_fragments([[(3000,'A',12)]]*3);req=self.prepare(fs)
        with patch.object(old,'solve_group',side_effect=AssertionError('Expanded solver')), \
             patch.object(old,'detect',side_effect=AssertionError('Spectrum detector')), \
             patch.object(counter,'count',side_effect=AssertionError('No recount')):
            result=staged.integrate(ROOT,req,fs,self.context)
        self.assertEqual(result['states']['metric_projection']['state'],'COMPLETE')

    def test_preflight_against_exhaustive_global_constraints(self):
        # Two disconnected ambiguous groups: local feasibility must NOT bypass
        # the single global margin when both groups request expensive choices.
        fs=old.make_fragments([[(3000,'A',12),(5000,'B',12)],
                              [(3000,'A',12),(3025,'C',12),(5000,'B',12),(5025,'D',12)]])
        nodes=[c for f in fs for c in f['components']]
        for margin in exact.MARGINS:
            family=exact.EpisodeFamily(nodes,len(fs),margin);q=staged.Queries(family)
            expanded=old.association(fs,f'paths_margin{margin:g}')
            covers=[set(map(tuple,h['paths'])) for h in expanded['hypotheses']]
            paths=sorted({tuple(p) for factor in family.factors for p in factor.solver.ids(range(len(factor.solver.paths)))})
            for p in paths:
                self.assertEqual(q.possible(p),any(p in h for h in covers))
                self.assertEqual(q.invariant(p),all(p in h for h in covers))
                for other in paths:
                    for required,forbidden in (((p,other),()),((p,),(other,))):
                        expected=any(set(required)<=h and not set(forbidden)&h for h in covers)
                        answer=q.find(required=required,forbidden=forbidden)
                        self.assertEqual(answer is not None,expected)
                        if answer is not None:self.assertTrue(family.contains(answer))
            self.assertEqual(q.classify()['status'],expanded['status'])

    def test_preflight_rejects_late_impossibility_without_global_search(self):
        fs=old.make_fragments([[(3000,'A',12),(3000,'B',12),(5000,'C',12)]]*2)
        family=exact.EpisodeFamily([c for f in fs for c in f['components']],2,1.)
        q=staged.Queries(family)
        # Candidate in an isolated two-node matched group cannot be singleton.
        impossible=(fs[0]['components'][2]['candidate_id'],)
        with patch.object(family,'find',side_effect=AssertionError('Global search must not start')):
            self.assertIsNone(q.find(required=(impossible,)))

    def test_deterministic_serialization_and_reproduction(self):
        fs=old.make_fragments([[(3000,'A',12),(3025,'B',12)]]*3);req=self.prepare(fs)
        a=staged.integrate(ROOT,req,fs,self.context)
        b=staged.integrate(ROOT,req,fs,self.context)
        self.assertEqual(exact.canonical_bytes(a),exact.canonical_bytes(b))
        restored=json.loads(exact.canonical_bytes(a))
        self.assertEqual(staged.reproduce(ROOT,restored,fs),a)
        restored['association']['status']='tampered'
        with self.assertRaises(ValueError):staged.reproduce(ROOT,restored,fs)


if __name__=='__main__':
    unittest.main()
