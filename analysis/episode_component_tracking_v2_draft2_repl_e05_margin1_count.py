"""Exact weighted binary-search pivot joins; frozen chronological binary64 fold.

Existing Budget charges local DAG branches and composition pairs, not individual
machine instructions or sorting comparisons. Retain that policy. New work charges
one transition per cumulative-weight entry, reversed buffer entry, prefix guard,
actual binary-search predicate probe, and weighted cutoff accumulation. No probe
or replacement loop iteration is free. All retained weight entries are states.
"""
from bisect import bisect_left
from collections import Counter
import math
from unittest.mock import patch
import episode_component_tracking_v2_draft2_e02_margin1_count as previous
import episode_component_tracking_v2_draft2_repl_e02_margin1_count as dyadic
old=previous.old
addition_preimage=previous.addition_preimage
VERSION='KRAKEN_DRAFT2_WEIGHTED_CUTOFF_PIVOT_COUNT_V1'

def compose(histories,optima,margin,budget,reverse=False):
    """Exact scalar-boundary decomposition; no reordered binary64 arithmetic."""
    if len(histories)!=len(optima):raise ValueError('Histogram/optimum mismatch')
    if not math.isfinite(margin) or margin<0:raise ValueError('Invalid margin')
    if any(not math.isfinite(x) or x<0 for x in optima):raise ValueError('Invalid optimum')
    if any(not math.isfinite(c) or c<0 or not isinstance(n,int) or n<=0
           for h in histories for c,n in h.items()):raise ValueError('Invalid exact histogram')
    if not histories:return dict(count=1,pivot=None,prefix_states=1,suffix_thresholds=1)
    if any(not h for h in histories):return dict(count=0,pivot=None,prefix_states=0,suffix_thresholds=0)
    # Same sum order and expression as the committed episode counter.
    boundary=sum(optima)+margin+old.solver.TOLERANCE
    suffix=[sum(optima[i:]) for i in range(len(optima)+1)]
    pivot=max(range(len(histories)),key=lambda i:(len(histories[i]),-i))
    held=sum(map(len,histories))
    budget.check(states=held,phase='histograms retained')
    prefix={0.:1};prefix_steps=[]
    for i in range(pivot):
        next_states=Counter();attempts=0
        # Iteration order may reverse, the operand order and fold do not.
        prefix_items=sorted(prefix.items(),reverse=reverse)
        factor_items=sorted(histories[i].items(),reverse=reverse)
        buffers=len(prefix_items)+len(factor_items)
        for cost,multiplicity in prefix_items:
            if cost+suffix[i]>boundary:continue
            for g,n in factor_items:
                attempts+=1
                dest=cost+g
                # Exact next frozen prefix check, performed before insertion.
                if dest+suffix[i+1]<=boundary:
                    next_states[dest]+=multiplicity*n
                budget.check(states=held+len(prefix)+len(next_states)+buffers,transitions=1,
                             phase='IEEE pivot left prefix',factor=i)
        prefix_steps.append(dict(factor=i,input_states=len(prefix),output_states=len(next_states),transitions=attempts))
        prefix=next_states
        del prefix_items,factor_items
    # F_n(x) = 1[x <= boundary]. Each stored threshold has an integer weight.
    thresholds={boundary:1};suffix_steps=[]
    for i in range(len(histories)-1,pivot,-1):
        new=Counter();attempts=0
        guard=addition_preimage(boundary,suffix[i],budget,held+len(prefix)+len(thresholds))
        threshold_items=sorted(thresholds.items(),reverse=reverse)
        factor_items=sorted(histories[i].items(),reverse=reverse)
        buffers=len(threshold_items)+len(factor_items)
        for threshold,n in threshold_items:
            for g,m in factor_items:
                attempts+=1
                live=held+len(prefix)+len(thresholds)+len(new)+buffers
                pre=addition_preimage(threshold,g,budget,live)
                if pre is not None and guard is not None:
                    new[min(pre,guard)]+=n*m
                budget.check(states=held+len(prefix)+len(thresholds)+len(new)+buffers,transitions=1,
                             phase='IEEE suffix threshold composition',factor=i)
        suffix_steps.append(dict(factor=i,input_thresholds=len(thresholds),
                                 output_thresholds=len(new),cost_threshold_pairs=attempts))
        thresholds=new
        del threshold_items,factor_items
    caps=sorted(thresholds)
    cumulative=[0]
    for cap in caps:cumulative.append(cumulative[-1]+thresholds[cap])
    # Histograms, prefix map, threshold map, sorted cap references, cumulative
    # coefficients and two iteration buffers all count toward the state limit.
    left=sorted(prefix.items(),reverse=reverse)
    pivot_costs=sorted(histories[pivot].items(),reverse=reverse)
    live=held+len(prefix)+3*len(caps)+1+len(left)+len(pivot_costs)
    budget.check(states=live,phase='IEEE streaming pivot join',pivot=pivot)
    total=0;attempts=0
    cutoff_mode=len(caps)*max(1,len(pivot_costs).bit_length()) < len(pivot_costs)
    cutoff_probes=0
    if cutoff_mode:
        # Existing sorted buffer can be reversed without sorting again.
        if reverse:
            pivot_costs.reverse()
            budget.check(states=live,transitions=len(pivot_costs),phase='IEEE cutoff buffer reversal')
        weights=[0]
        for g,n in pivot_costs:
            weights.append(weights[-1]+n)
            budget.check(states=live+len(weights),transitions=1,phase='IEEE pivot cumulative weights')
        live+=len(weights)
        for cost,multiplicity in left:
            budget.check(states=live,transitions=1,phase='IEEE cutoff prefix guard',pivot=pivot)
            if cost+suffix[pivot]>boundary:continue
            for cap in caps:
                low,high=0,len(pivot_costs)
                while low<high:
                    mid=(low+high)//2
                    accepted=cost+pivot_costs[mid][0]<=cap
                    cutoff_probes+=1
                    budget.check(states=live,transitions=1,phase='IEEE pivot cutoff probe',pivot=pivot)
                    if accepted:low=mid+1
                    else:high=mid
                total+=multiplicity*thresholds[cap]*weights[low]
                attempts+=1
                budget.check(states=live,transitions=1,phase='IEEE pivot weighted cutoff',pivot=pivot)
    else:
        for cost,multiplicity in left:
            if cost+suffix[pivot]>boundary:continue
            for g,n in pivot_costs:
                dest=cost+g
                accepted=cumulative[-1]-cumulative[bisect_left(caps,dest)]
                total+=multiplicity*n*accepted
                attempts+=1
                budget.check(states=live,transitions=1,phase='IEEE streaming pivot join',pivot=pivot)
    return dict(count=total,pivot=pivot,prefix_states=len(prefix),suffix_thresholds=len(caps),
                prefix_steps=prefix_steps,suffix_steps=suffix_steps,join_pairs=0 if cutoff_mode else attempts,
                cutoff_queries=attempts if cutoff_mode else 0,cutoff_probes=cutoff_probes,
                cutoff_mode=cutoff_mode,
                group_histogram_entries=[len(h) for h in histories],packed_polynomial_bytes=0,
                boundary_hex=boundary.hex(),join_live_containers=live)


def count(family,budget=None,ordering='forward',force_ieee=False):
    with patch.object(previous,'compose',compose):
        result=dyadic.count(family,budget,ordering,force_ieee)
    result['counter_version']=VERSION
    if 'composition' in result:
        result['method']=VERSION
        result['certificate']['version']=VERSION
        result['certificate']['join_policy']='Exact binary64 cutoff predicates and integer cumulative multiplicities'
    return result
