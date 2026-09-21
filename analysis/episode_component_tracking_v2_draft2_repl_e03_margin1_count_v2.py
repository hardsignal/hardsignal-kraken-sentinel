"""V2 contract forced zero-cost singleton chains and drain IEEE DAG states; reuse exact dyadic bounds and pivot join.

The earliest-uncovered-candidate DAG only inserts into strictly later buckets.
Removing a consumed source entry cannot change future merging or multiplicity.
FIFO/LIFO changes traversal, never any hypothesis's scientific cost fold.
"""
from collections import Counter,OrderedDict
from fractions import Fraction
from unittest.mock import patch
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_repl_e02_margin1_count as dyadic
VERSION='KRAKEN_DRAFT2_FORCED_SINGLETON_FRONTIER_COUNT_V2'
ORIGINAL_HISTOGRAM=old.ieee_histogram


def histogram(family,budget,reverse=False,trace=None):
    s=family.solver
    gap=s._cheap_unique_certificate(s.full,family.optimum)
    if family.optimum.links==0 or (gap is not None and gap>Fraction.from_float(family.margin+old.solver.TOLERANCE)+4*s.rounding_bound):
        return ORIGINAL_HISTOGRAM(family,budget)
    n=len(s.nodes)
    adjacency=[0]*n
    for a,b in s.edges:
        adjacency[a]|=1<<b;adjacency[b]|=1<<a
    budget=dyadic.previous.HeldBudget(budget,n)
    buckets=[OrderedDict() for _ in range(n+1)]
    buckets[0][(s.full,family.optimum.links,family.optimum.cost+family.margin,0.)]=1
    result=Counter();active=1
    for position in range(n+1):
        states=buckets[position];start=len(states);before=budget.transitions
        while states:
            (mask,target,remaining,cost),multiplicity=states.popitem(last=reverse);active-=1
            if not mask:
                if target==0:result[cost]+=multiplicity
                budget.check(states=active+len(result)+1,phase='drained IEEE terminal',position=position)
                continue
            first=(mask & -mask).bit_length()-1
            for k in s.by_candidate[first]:
                p=s.paths[k]
                if p.nodes[0]!=first or p.mask & mask!=p.mask:continue
                tail=s.optimum(mask ^ p.mask)
                budget.check(states=active+len(result)+1,transitions=1,phase='drained IEEE DAG',position=position)
                if p.links+tail.links!=target or p.cost+tail.cost>remaining+old.solver.TOLERANCE:continue
                new_mask=mask ^ p.mask
                new_remaining=remaining-p.cost
                # An isolated residual candidate has exactly one feasible path:
                # its zero-cost singleton. Removing it preserves optimum links
                # and right-folded optimum cost. One exact guard represents all
                # consecutive such singleton-prefix guards.
                contracted=0
                while new_mask:
                    low=new_mask & -new_mask;first_remaining=low.bit_length()-1
                    if adjacency[first_remaining] & new_mask:break
                    new_mask^=low;contracted+=1
                if contracted:
                    budget.check(states=active+len(result)+1,transitions=1,phase='forced singleton macro',position=position)
                    if tail.cost>new_remaining+old.solver.TOLERANCE:continue
                dest=(new_mask & -new_mask).bit_length()-1 if new_mask else n
                assert dest>position
                key=(new_mask,target-p.links,new_remaining,cost+p.cost)
                if key not in buckets[dest]:active+=1
                buckets[dest][key]=buckets[dest].get(key,0)+multiplicity
                budget.check(states=active+len(result)+1,phase='drained IEEE DAG',position=position)
        if trace is not None:trace.append(dict(position=position,input_states=start,remaining_frontier_states=active,histogram_entries=len(result),transitions=budget.transitions-before))
    return result


def count(family,budget=None,ordering='forward',force_ieee=False):
    if ordering not in ('forward','reverse'):raise ValueError('Unknown order')
    budget=budget or old.Budget();traces=[]
    def local(f,b):
        trace=[];before=budget.transitions
        row=dict(candidate_count=len(f.solver.nodes),positions=trace);traces.append(row)
        value=histogram(f,b,ordering=='reverse',trace)
        row.update(histogram_entries=len(value),assignments_decimal=str(sum(value.values())),transitions=budget.transitions-before)
        return value
    with patch.object(old,'ieee_histogram',local):result=dyadic.count(family,budget,ordering,force_ieee)
    result['method']=VERSION+' / '+result['method']
    result['local_frontiers']=traces
    return result
