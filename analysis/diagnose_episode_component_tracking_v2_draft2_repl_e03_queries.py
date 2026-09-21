"""V1 reproduce frozen query exhaustion with constraint and residual-search traces."""
from collections import Counter
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
from episode_component_tracking_v2_draft2_staged_queries import Queries
from diagnose_episode_component_tracking_v2_draft2_e02_margin1 import memory
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression/C6-E03'
OUTPUT=ROOT/'results/episode-component-tracking-v2-draft2-repl-e03-query-investigation'

def inputs(arm):
    old=json.loads((BASE/arm/'result.json').read_text());ref=old['provenance']['request']['saved_input']
    data=json.loads((ROOT/ref['path']).read_text())
    episode=next(e for e in data['episodes'] if e['capture']=='BETWEEN-DEVICE-REPL-V1-20260919-024341' and e['episode']==3)
    req=staged.request(ROOT,episode['components'],staged.COMPACT,BASE/arm/'family.json',BASE/arm/'cardinality.json',ref)
    return episode,req

def run(arm):
    OUTPUT.mkdir(exist_ok=True);dest=OUTPUT/f'diagnostic-{arm}.json'
    if dest.exists():raise ValueError('New output required')
    episode,req=inputs(arm);current={};history=[];residual=Counter();full=Counter();branches=Counter();depth=Counter();local=[]
    counters=dict(covers=0,matching_calls=0,matching_seconds=0.,feasibility_checks=0);engines=[]
    covers=exact.Solver._covers;match=exact.Solver._matching;options=exact.Solver._options;find=exact.Family.find
    class Traced(Queries):
        def __init__(self,family):super().__init__(family);engines.append(self)
        def find(self,required=(),forbidden=()):
            current.clear();current.update(required=[list(p) for p in required],forbidden=[list(p) for p in forbidden],cache_entries=len(self.cache))
            t=time.perf_counter();before=counters['covers']
            try:
                result=super().find(required,forbidden);state='FOUND' if result is not None else 'PROVED_ABSENT';return result
            except exact.Unresolved:state='COMPUTATION_UNRESOLVED';raise
            finally:history.append(dict(current,state=state,seconds=time.perf_counter()-t,covers=counters['covers']-before))
    def traced_cover(s,mask,chosen,target,budget,forbidden=frozenset()):
        counters['covers']+=1;depth[len(chosen)]+=1
        residual[(id(s),mask,target-sum(s.paths[k].links for k in chosen),forbidden)]+=1
        full[(id(s),mask,chosen,target,budget,forbidden)]+=1
        yield from covers(s,mask,chosen,target,budget,forbidden)
    def traced_match(s,*a,**kw):
        counters['matching_calls']+=1;t=time.perf_counter()
        try:return match(s,*a,**kw)
        finally:counters['matching_seconds']+=time.perf_counter()-t
    def traced_options(s,*a):
        result=options(s,*a);branches[len(result)]+=1;return result
    def traced_find(f,required=(),forbidden=()):
        counters['feasibility_checks']+=1;t=time.perf_counter();before=f.solver.stats['search_nodes']
        try:
            result=find(f,required,forbidden);state='FOUND' if result is not None else 'PROVED_ABSENT';return result
        except exact.Unresolved:state='COMPUTATION_UNRESOLVED';raise
        finally:
            local.append(dict(required=list(required),forbidden=list(forbidden),candidate_count=len(f.solver.nodes),state=state,seconds=time.perf_counter()-t,search_nodes=f.solver.stats['search_nodes']-before))
    start=time.perf_counter()
    with patch.object(staged,'Queries',Traced),patch.object(exact.Solver,'_covers',traced_cover),patch.object(exact.Solver,'_matching',traced_match),patch.object(exact.Solver,'_options',traced_options),patch.object(exact.Family,'find',traced_find):
        result=staged.integrate(ROOT,req,episode['components'],staged.git_context(ROOT))
    family=engines[0].family
    data=dict(format='KRAKEN_REPL_E03_QUERY_DIAGNOSTIC_V1',arm=arm,states=result['states'],query_operations=result['query_operations'],query_calls=result.get('query_calls'),
        candidate_count=sum(len(f['components']) for f in episode['components']),eligible_per_fragment=[sum(c['eligible_for_tracking'] for c in f['components']) for f in episode['components']],
        fixed_singletons=len(family.singletons),factors=[dict(nodes=len(f.solver.nodes),paths=len(f.solver.paths),per_fragment=dict(Counter(c['fragment_index'] for c in f.solver.nodes)),edges=len(f.solver.edges),path_lengths=dict(Counter(len(p.nodes) for p in f.solver.paths)),solver_stats=f.solver.stats,optimum_cache=len(f.solver._optima),matching_cache=len(f.solver._matching_cache)) for f in family.factors],
        last_constraint=history[-1],query_history=history,local_feasibility=local,search=counters,
        max_recursion_chosen_depth=max(depth,default=0),depth_histogram=dict(depth),branching_histogram=dict(branches),
        residual_key_distinct=len(residual),residual_key_repeated_visits=sum(n-1 for n in residual.values()),full_key_distinct=len(full),full_key_repeated_visits=sum(n-1 for n in full.values()),
        seconds=time.perf_counter()-start,memory_kib=memory(),family_sha256=sc.sha(BASE/arm/'family.json'),
        source_hashes={str(Path(p).resolve().relative_to(ROOT)):sc.sha(p) for p in [__file__,staged.__file__,exact.__file__]})
    with dest.open('xb') as f:f.write(exact.canonical_bytes(data))
    print(arm,result['states'],history[-1],flush=True)
if __name__=='__main__':run(sys.argv[1])
