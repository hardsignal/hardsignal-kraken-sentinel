"""Read-only structural trace of the committed E02 counter at its frozen limit."""
from collections import Counter
import inspect
import json
from pathlib import Path
import subprocess
import time

import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_column_count as column
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc

ROOT=Path(__file__).resolve().parents[1]
FAMILY=ROOT/'results/episode-component-tracking-v2-draft2-limited-regression/TPMS004-ordinary/margin-1/family.json'
OUTPUT=ROOT/'results/episode-component-tracking-v2-draft2-e02-margin1-investigation'
LIMITS=dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432)


def memory():
    return {k:int(v.split()[0]) for line in Path('/proc/self/status').read_text().splitlines()
            for k,v in [line.split(':',1)] if k in ('VmHWM','VmRSS')}


class TraceBudget(old.Budget):
    def __post_init__(self):
        pass

    def check(self,states=0,transitions=0,**location):
        if location.get('phase')=='IEEE group composition':
            i=location['factor']
            if i not in self.steps:
                local=inspect.currentframe().f_back.f_locals
                if not self.histories:
                    self.histories=[dict(factor=k,cost_states=len(h),local_assignments_decimal=str(sum(h.values())),
                        minimum_emitted_cost_hex=min(h).hex(),maximum_emitted_cost_hex=max(h).hex())
                        for k,h in enumerate(local['histories'])]
                    self.histogram_generation=dict(transitions=self.transitions,peak_states=self.peak_states,
                        elapsed_seconds=time.perf_counter()-self.started)
                self.steps[i]=dict(factor=i,prior_states=len(local['states']),
                    right_histogram_states=len(local['hist']),start_transitions=self.transitions,
                    start_seconds=time.perf_counter()-self.started,peak_live_states=0,transitions=0)
            step=self.steps[i]
            step['transitions']+=transitions
            step['peak_live_states']=max(step['peak_live_states'],states)
            step['last_live_states']=states
            step['next_states']=states-step['prior_states']
        try:
            super().check(states,transitions,**location)
        except old.CountUnresolved:
            local=inspect.currentframe().f_back.f_locals
            if location.get('phase')=='IEEE group composition':
                e=local['episode'];i=local['i'];cost=local['cost'];g=local['group_cost']
                new=cost+g
                self.first_failure=dict(factor=i,prior_cost_hex=cost.hex(),right_cost_hex=g.hex(),
                    new_cost_hex=new.hex(),prior_cost_index=list(local['states']).index(cost),
                    right_cost_index=list(local['hist']).index(g),prior_multiplicity=str(local['multiplicity']),
                    right_multiplicity=str(local['count']),prior_states=len(local['states']),
                    next_states=len(local['next_states']),live_states=states,
                    next_frozen_prefix_passes=(new+sum(f.optimum.cost for f in e.factors[i+1:])
                        <= e.optimum_cost+e.margin+old.solver.TOLERANCE),
                    remaining_group_histogram_sizes=[len(h) for h in local['histories'][i+1:]])
            raise


def run():
    OUTPUT.mkdir(exist_ok=True)
    dest=OUTPUT/'diagnostic.json'
    if dest.exists():raise ValueError('Diagnostic output must be NEW')
    _,model,family=sc.load_family(FAMILY)
    structure=[]
    for i,f in enumerate(family.factors):
        s=f.solver
        structure.append(dict(factor=i,candidates=len(s.nodes),candidate_ids=[c['candidate_id'] for c in s.nodes],
            per_fragment=dict(Counter(c['fragment_index'] for c in s.nodes)),edges=len(s.edges),
            paths=len(s.paths),path_lengths=dict(Counter(len(p.nodes) for p in s.paths)),
            maximum_links=f.optimum.links,optimum_cost_hex=f.optimum.cost.hex(),
            factor_model_sha256=model['factors'][i]['model_sha256'],
            cross_factor_candidate_frontier=0))
    budget=TraceBudget(**LIMITS);budget.steps={};budget.histories=[];budget.first_failure=None
    try:
        result=column.count(family,budget)
        outcome=dict(state='EXACT',value_decimal=str(result['count']))
    except old.CountUnresolved as exc:
        outcome=dict(state='COMPUTATION_UNRESOLVED',value_decimal=None,reason=exc.details)
    result=dict(format='KRAKEN_DRAFT2_E02_MARGIN1_DIAGNOSTIC_V1',
        family_artifact=str(FAMILY.relative_to(ROOT)),family_sha256=sc.sha(FAMILY),model_sha256=model['model_sha256'],
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        limits=LIMITS,original_fragments=family.fragment_count,eligible_per_fragment=[189,1,19,4,71],
        connected_group_count=len(family.factors)+len(family.singletons),fixed_singletons=len(family.singletons),
        factor_order='Unchanged stored episode order, increasing group median frequency and original tie breaks',
        factor_structure=structure,group_histograms=budget.histories,
        histogram_generation=budget.histogram_generation,composition_steps=list(budget.steps.values()),
        first_failure=budget.first_failure,outcome=outcome,statistics=budget.stats(),memory_kib=memory(),
        source_hashes={str(Path(p).resolve().relative_to(ROOT)):sc.sha(p)
                       for p in (__file__,old.__file__,column.__file__,sc.__file__,old.solver.__file__)})
    with dest.open('xb') as f:f.write(old.solver.canonical_bytes(result))
    print(json.dumps({k:result[k] for k in ('group_histograms','histogram_generation','composition_steps','first_failure','outcome','memory_kib')},indent=2))


if __name__=='__main__':run()
