"""V1: general exact IEEE pivot join, retaining the certified column backend.

No target IDs or expected count are consulted. An independent suffix assignment
accepts a downward-closed set of nonnegative binary64 prefix costs. Store its
exact maximum accepted prefix, weighted by assignment multiplicity. A largest
histogram pivot is joined by streaming, rather than materializing its Cartesian
cost product. Frozen group addition order and prefix comparisons never change.
"""
from bisect import bisect_left
from collections import Counter
import math
import struct
import time

import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_column_count as column

VERSION='KRAKEN_DRAFT2_IEEE_MONOTONE_PIVOT_COUNT_V1'


class HeldBudget:
    """Charge pre-existing histogram/frontier containers alongside local states."""
    def __init__(self,parent,held):
        self.parent,self.held=parent,held

    def __getattr__(self,name):
        return getattr(self.parent,name)

    def check(self,states=0,**kwargs):
        return self.parent.check(states=states+self.held,**kwargs)


def bits(value):
    return struct.unpack('>Q',struct.pack('>d',value))[0]


def floating(value):
    return struct.unpack('>d',struct.pack('>Q',value))[0]


def addition_preimage(threshold,addend,budget,live_states=0):
    """Largest finite x>=0 with fl(x+addend)<=threshold, or None.

    Nonnegative finite binary64 numbers have increasing unsigned bit patterns.
    Binary search uses the actual frozen operation/comparison, including ties,
    subnormals, overflow and cancellation in the conceptual inverse. It does NOT
    replace the predicate by subtraction. x cannot exceed threshold because a
    nonnegative floating addition cannot decrease x.
    """
    if not math.isfinite(threshold) or not math.isfinite(addend) or addend<0:
        raise ValueError('Finite threshold and nonnegative finite addend required')
    budget.check(states=live_states,transitions=1,phase='IEEE addition preimage')
    if threshold<0 or addend>threshold:
        return None
    if addend==0:
        return max(0.,threshold)
    low,high=0,bits(threshold)+1
    while low+1<high:
        mid=(low+high)//2
        if floating(mid)+addend<=threshold:
            low=mid
        else:
            high=mid
        budget.check(states=live_states,transitions=1,phase='IEEE addition preimage')
    return floating(low)


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
    for cost,multiplicity in left:
        if cost+suffix[pivot]>boundary:continue
        for g,n in pivot_costs:
            dest=cost+g
            accepted=cumulative[-1]-cumulative[bisect_left(caps,dest)]
            total+=multiplicity*n*accepted
            attempts+=1
            budget.check(states=live,transitions=1,phase='IEEE streaming pivot join',pivot=pivot)
    return dict(count=total,pivot=pivot,prefix_states=len(prefix),suffix_thresholds=len(caps),
                prefix_steps=prefix_steps,suffix_steps=suffix_steps,join_pairs=attempts,
                group_histogram_entries=[len(h) for h in histories],packed_polynomial_bytes=0,
                boundary_hex=boundary.hex(),join_live_containers=live)


def count(family,budget=None,ordering='forward',force_ieee=False):
    if ordering not in ('forward','reverse'):raise ValueError('Unknown computation order')
    budget=budget or old.Budget()
    factors=family.factors if isinstance(family,old.solver.EpisodeFamily) else [family]
    if not factors:return dict(count=1,method=VERSION,stats=budget.stats(),certificate=None,packed_polynomial_bytes=0)
    # Keep already certified matching/polynomial acceleration for suitable cases.
    if not force_ieee:
        try:
            old.lattice_certificate(factors,family.margin,old.cost_lattice(factors))
        except old.CertificateUnavailable:
            pass
        else:
            result=column.count(family,budget,'frequency' if ordering=='forward' else 'reverse_frequency')
            result['dispatcher_version']=VERSION
            return result
    if not isinstance(family,old.solver.EpisodeFamily):
        hist=old.ieee_histogram(family,budget)
        return dict(count=sum(hist.values()),method=VERSION+' / committed local IEEE histogram',
                    stats=budget.stats(),certificate=None,packed_polynomial_bytes=0)
    histories={};factor_stats=[]
    order=list(range(len(factors)))
    if ordering=='reverse':order.reverse()
    for i in order:
        held=sum(map(len,histories.values()))
        start=time.perf_counter();before=budget.transitions
        hist=old.ieee_histogram(factors[i],HeldBudget(budget,held))
        histories[i]=hist
        budget.check(states=held+len(hist),phase='group histogram complete',factor=i)
        factor_stats.append(dict(factor=i,histogram_entries=len(hist),assignments_decimal=str(sum(hist.values())),
            elapsed_seconds=time.perf_counter()-start,transitions=budget.transitions-before,
            held_previous_histogram_states=held))
    ordered=[histories[i] for i in range(len(factors))]
    result=compose(ordered,[f.optimum.cost for f in factors],family.margin,budget,ordering=='reverse')
    value=result.pop('count')
    return dict(count=value,method=VERSION,ordering=ordering,stats=budget.stats(),
                factor_statistics=factor_stats,composition=result,packed_polynomial_bytes=0,
                certificate=dict(policy='Exact monotone binary64 addition preimages; frozen chronological fold and all prefix predicates',
                                 version=VERSION,rounding_or_quantization=False))
