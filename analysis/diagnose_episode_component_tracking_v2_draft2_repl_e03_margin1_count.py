"""V1 instrument the unchanged local IEEE counter at its frozen state failure."""
from collections import Counter
import inspect
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
import episode_component_tracking_v2_draft2_e02_margin1_count as pivot
import episode_component_tracking_v2_draft2_repl_e02_margin1_count as dyadic
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
from diagnose_episode_component_tracking_v2_draft2_e02_margin1 import memory,LIMITS
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression/C6-E03/margin-1'
OUTPUT=ROOT/'results/episode-component-tracking-v2-draft2-repl-e03-margin1-count-investigation'

def run(mode='pivot'):
    OUTPUT.mkdir(exist_ok=True);dest=OUTPUT/f'diagnostic-{mode}.json'
    if dest.exists():raise ValueError('New output required')
    _,model,family=sc.load_family(TARGET/'family.json')
    plan=json.loads((ROOT/'results/episode-component-tracking-v2-draft2-six-capture-plan.json').read_text());selected=next(e for e in plan['selected'] if e['label']=='C6-E03')
    structure=[]
    for i,f in enumerate(family.factors):
        s=f.solver;structure.append(dict(factor=i,candidates=len(s.nodes),per_fragment=dict(Counter(c['fragment_index'] for c in s.nodes)),edges=len(s.edges),paths=len(s.paths),path_lengths=dict(Counter(len(p.nodes) for p in s.paths)),optimum_links=f.optimum.links,optimum_cost_hex=f.optimum.cost.hex()))
    rows=[];current=[None];hist=old.ieee_histogram;failure={}
    class Budget(old.Budget):
        def check(self,states=0,transitions=0,**where):
            if current[0] is not None:current[0]['peak_states']=max(current[0]['peak_states'],states)
            try:return super().check(states,transitions,**where)
            except old.CountUnresolved:
                frame=inspect.currentframe().f_back
                while frame and frame.f_code.co_name!='ieee_histogram':frame=frame.f_back
                if frame:
                    v=frame.f_locals;s=v['s'];p=v.get('p');mask=v.get('new_mask');rem=v.get('remaining',0)-p.cost
                    nxt=(mask & -mask).bit_length()-1 if mask else None
                    survivor=None
                    if mask:
                        survivor=any(s.paths[k].links+s.optimum(mask^s.paths[k].mask).links==v['target']-p.links and
                            s.paths[k].cost+s.optimum(mask^s.paths[k].mask).cost<=rem+old.solver.TOLERANCE
                            for k in s.by_candidate[nxt] if s.paths[k].nodes[0]==nxt and s.paths[k].mask & mask==s.paths[k].mask)
                    failure.update(factor=current[0]['factor'],position=v['position'],current_bucket_size=len(v['states']),
                        active_future_states=v['active_states'],histogram_entries=len(v['histogram']),
                        new_mask_hex=hex(mask),target_links=v['target']-p.links,remaining_hex=rem.hex(),emitted_cost_hex=(v['cost']+p.cost).hex(),
                        selected_path_ids=s.ids((v['k'],))[0],prior_mask_hex=hex(v['mask']),
                        survives_next_exact_prefix=survivor,bucket_sizes=[len(x) for x in v['buckets']])
                raise
    budget=Budget(**LIMITS)
    def trace(f,b):
        row=dict(factor=family.factors.index(f),state='RUNNING',peak_states=0);rows.append(row);current[0]=row
        start=time.perf_counter();before=budget.transitions
        try:
            h=hist(f,b);row.update(state='COMPLETE',histogram_entries=len(h),assignments_decimal=str(sum(h.values())));return h
        finally:row.update(seconds=time.perf_counter()-start,transitions=budget.transitions-before);current[0]=None
    outcome=dict(state='COMPUTATION_UNRESOLVED',value_decimal=None)
    with patch.object(old,'ieee_histogram',trace):
        try:
            with staged.deadline(60):result=(pivot if mode=='pivot' else dyadic).count(family,budget)
            outcome.update(state='EXACT',value_decimal=str(result['count']),details=result)
        except old.CountUnresolved as exc:outcome['reason']=exc.details
        except old.solver.Unresolved as exc:outcome['reason']=dict(reason=str(exc))
    report=dict(format='KRAKEN_REPL_E03_MARGIN1_COUNT_DIAGNOSTIC_V1',mode=mode,selected=selected,limits=LIMITS,
        fixed_singletons=len(family.singletons),nontrivial_factors=len(family.factors),factor_structure=structure,
        factor_order='unchanged stored order',factor_statistics=rows,failure=failure,outcome=outcome,statistics=budget.stats(),memory_kib=memory(),
        packed_polynomial_bytes=0,family_sha256=sc.sha(TARGET/'family.json'),model_sha256=model['model_sha256'],
        source_hashes={str(Path(p).resolve().relative_to(ROOT)):sc.sha(p) for p in (__file__,old.__file__,pivot.__file__,dyadic.__file__,old.solver.__file__)})
    with dest.open('xb') as f:f.write(old.solver.canonical_bytes(report))
    print(json.dumps(report,indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'pivot')
