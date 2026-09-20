"""V1 timed factor/matching trace of the unchanged committed counter."""
from collections import Counter
import json
from pathlib import Path
import time
import traceback
from unittest.mock import patch
import episode_component_tracking_v2_draft2_e02_margin1_count as committed
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
from diagnose_episode_component_tracking_v2_draft2_e02_margin1 import memory,LIMITS
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression/C6-E02/margin-1'
OUTPUT=ROOT/'results/episode-component-tracking-v2-draft2-repl-e02-margin1-investigation'

def run():
    OUTPUT.mkdir(exist_ok=True);dest=OUTPUT/'diagnostic.json'
    if dest.exists():raise ValueError('New output required')
    _,model,family=sc.load_family(TARGET/'family.json')
    plan=json.loads((ROOT/'results/episode-component-tracking-v2-draft2-six-capture-plan.json').read_text())
    selected=next(e for e in plan['selected'] if e['label']=='C6-E02')
    structure=[]
    for i,f in enumerate(family.factors):
        s=f.solver;structure.append(dict(factor=i,candidates=len(s.nodes),per_fragment=dict(Counter(c['fragment_index'] for c in s.nodes)),edges=len(s.edges),path_lengths=dict(Counter(len(p.nodes) for p in s.paths)),optimum_links=f.optimum.links,optimum_cost_hex=f.optimum.cost.hex()))
    try:old.lattice_certificate(family.factors,family.margin,old.cost_lattice(family.factors));backend='certified column';why='certificate passed'
    except old.CertificateUnavailable as exc:backend='IEEE local histogram and monotone pivot';why=str(exc)
    hist=old.ieee_histogram;matching=old.solver.Solver._matching;factors=[];current=[None];timing=dict(calls=0,seconds=0.)
    def traced_matching(*args,**kwargs):
        t=time.perf_counter();timing['calls']+=1
        try:return matching(*args,**kwargs)
        finally:timing['seconds']+=time.perf_counter()-t
    class Budget(old.Budget):
        def check(self,states=0,transitions=0,**location):
            self.last_location=location
            if current[0] is not None:current[0]['peak_reported_states']=max(current[0]['peak_reported_states'],states)
            return super().check(states,transitions,**location)
    budget=Budget(**LIMITS);budget.last_location={}
    def traced_hist(f,b):
        row=dict(factor=family.factors.index(f),peak_reported_states=0,state='RUNNING');current[0]=row;factors.append(row)
        t=time.perf_counter();before=budget.transitions;mt=timing['seconds'];mc=timing['calls']
        try:
            h=hist(f,b);row.update(state='COMPLETE',histogram_entries=len(h),assignments_decimal=str(sum(h.values())));return h
        finally:
            row.update(seconds=time.perf_counter()-t,transitions=budget.transitions-before,matching_seconds=timing['seconds']-mt,matching_calls=timing['calls']-mc,solver_stats=dict(f.solver.stats));current[0]=None
    outcome=dict(state='COMPUTATION_UNRESOLVED',value_decimal=None)
    with patch.object(old,'ieee_histogram',traced_hist),patch.object(old.solver.Solver,'_matching',traced_matching):
        try:
            with staged.deadline(60):result=committed.count(family,budget)
            outcome.update(state='EXACT',value_decimal=str(result['count']),details=result)
        except (old.CountUnresolved,old.solver.Unresolved) as exc:
            outcome.update(reason=str(exc),traceback=traceback.format_exc(),last_budget_location=budget.last_location)
    result=dict(format='KRAKEN_REPL_E02_MARGIN1_DIAGNOSTIC_V1',selected=selected,limits=LIMITS,
        family_sha256=sc.sha(TARGET/'family.json'),model_sha256=model['model_sha256'],fragment_count=family.fragment_count,
        fixed_singletons=len(family.singletons),connected_groups=len(family.singletons)+len(family.factors),factor_structure=structure,
        factor_order='unchanged stored order; independent histogram construction forward',backend=backend,backend_reason=why,
        factors=factors,matching=timing,outcome=outcome,statistics=budget.stats(),memory_kib=memory(),
        source_hashes={str(Path(p).resolve().relative_to(ROOT)):sc.sha(p) for p in (__file__,committed.__file__,old.__file__,old.solver.__file__)})
    with dest.open('xb') as f:f.write(old.solver.canonical_bytes(result))
    print(json.dumps(result,indent=2))
if __name__=='__main__':run()
