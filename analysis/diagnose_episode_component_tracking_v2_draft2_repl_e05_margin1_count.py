"""Read-only reproduction of the committed E05 count with bounded trace storage."""
from collections import Counter
import inspect
import json
from pathlib import Path
import time
import sys
from unittest.mock import patch
import episode_component_tracking_v2_draft2_e02_margin1_count as previous
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
from diagnose_episode_component_tracking_v2_draft2_e02_margin1 import memory
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression/C6-E05/margin-1'
OUTPUT=ROOT/'results/episode-component-tracking-v2-draft2-repl-e05-margin1-count-investigation'
LIMITS=dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432)

def run(filename='diagnostic.json'):
    OUTPUT.mkdir(exist_ok=True)
    _,model,family=sc.load_family(BASE/'family.json')
    structure=[dict(factor=i,candidates=len(f.solver.nodes),per_fragment=dict(Counter(c['fragment_index'] for c in f.solver.nodes)),edges=len(f.solver.edges),paths=len(f.solver.paths),path_lengths=dict(Counter(len(p.nodes) for p in f.solver.paths)),optimum_links=f.optimum.links,optimum_cost=f.optimum.cost,optimum_cost_hex=f.optimum.cost.hex()) for i,f in enumerate(family.factors)]
    active=[None];factor_peaks=Counter()
    phases=Counter();local=[];matching=dict(calls=0,seconds=0.);failure_trace={}
    class Trace(old.Budget):
        def check(self,states=0,transitions=0,**location):
            phases[location.get('phase')]+=transitions
            if active[0] is not None:factor_peaks[active[0]]=max(factor_peaks[active[0]],states)
            try:super().check(states,transitions,**location)
            except old.CountUnresolved:
                frame=inspect.currentframe().f_back
                while frame:
                    if frame.f_code.co_name in ('compose','addition_preimage'):
                        loc=frame.f_locals
                        failure_trace[frame.f_code.co_name]={k:v for k,v in loc.items() if k in ('i','pivot','attempts','cost','g','threshold','addend','low','high','mid','live','boundary','suffix_steps','prefix_steps')}
                        failure_trace[frame.f_code.co_name].update({k+'_size':len(loc[k]) for k in ('prefix','thresholds','new','caps','left','pivot_costs') if k in loc})
                        if 'pivot_costs' in loc and 'cost' in loc:
                            failure_trace['pair_indices_zero_based']=[list(x[0] for x in loc['left']).index(loc['cost']),list(x[0] for x in loc['pivot_costs']).index(loc['g'])]
                            failure_trace['pair_passes_final_boundary']=loc['cost']+loc['g']<=loc['boundary']
                        if 'threshold' in loc and 'g' in loc:failure_trace['pair_rejected_by_monotonicity']=loc['g']>loc['threshold']
                    frame=frame.f_back
                raise
    budget=Trace(**LIMITS)
    hist=old.ieee_histogram;match=old.solver.Solver._matching
    def traced_hist(f,b):
        active[0]=family.factors.index(f)
        start=time.perf_counter();before=budget.transitions;before_match=dict(matching);misses=f.solver.stats['matching_calls']
        h=hist(f,b)
        local.append(dict(factor=family.factors.index(f),entries=len(h),assignments_decimal=str(sum(h.values())),seconds=time.perf_counter()-start,transitions=budget.transitions-before,peak_states=factor_peaks[active[0]],matching_cache_misses=f.solver.stats['matching_calls']-misses,matching_calls=matching['calls']-before_match['calls'],matching_seconds=matching['seconds']-before_match['seconds']))
        active[0]=None
        return h
    def traced_match(s,*a,**kw):
        t=time.perf_counter();matching['calls']+=1
        try:return match(s,*a,**kw)
        finally:matching['seconds']+=time.perf_counter()-t
    try:
        with patch.object(old,'ieee_histogram',traced_hist),patch.object(old.solver.Solver,'_matching',traced_match):
            result=previous.count(family,budget)
        outcome=dict(state='EXACT',value=str(result['count']))
    except old.CountUnresolved as exc:outcome=dict(state='COMPUTATION_UNRESOLVED',value=None,failure=exc.details)
    try:old.lattice_certificate(family.factors,1.,old.cost_lattice(family.factors));certificate='available'
    except old.CertificateUnavailable as exc:certificate=str(exc)
    request=json.loads((BASE/'request.json').read_text());raw=json.loads((ROOT/request['saved_input']['path']).read_text())
    episode=next(e for e in raw['episodes'] if e['capture']=='BETWEEN-DEVICE-REPL-V1-20260919-024341' and e['episode']==5)
    eligible=[sum(c['eligible_for_tracking'] for c in f['components']) for f in episode['components']]
    report=dict(fragment_count=family.fragment_count,eligible_per_fragment=eligible,total_eligible=sum(eligible),fixed_singletons=len(family.singletons),factor_count=len(family.factors),factors=structure,local_histograms=local,phase_transitions=dict(phases),matching=matching,failure_trace=failure_trace,outcome=outcome,statistics=budget.stats(),memory_kib=memory(),packed_polynomial_bytes=0,backend=previous.VERSION,certificate_unavailable=certificate,family_sha256=sc.sha(BASE/'family.json'),limits=LIMITS)
    with (OUTPUT/filename).open('x') as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'diagnostic.json')
