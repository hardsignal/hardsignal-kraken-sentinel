#!/usr/bin/env python3
"""New exact retained-family counter; committed solvers/artifacts are read only.

Two exact backends: IEEE prefix-state DAG, and certified integer-weighted
bipartite frontier DP. Lattice quantization is accepted ONLY with a proof that
it cannot change any frozen acceptance decision. No approximate counts.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
import math
import time

import episode_component_tracking_v2_draft2_exact_solver as solver


class CountUnresolved(RuntimeError):
    def __init__(self, reason, **details):
        self.details=dict(reason=reason,**details)
        super().__init__(str(self.details))


class CertificateUnavailable(ValueError):
    pass


@dataclass
class Budget:
    # Computational limits only; established before saved-case counting.
    max_states: int = 250000
    max_transitions: int = 5000000
    max_seconds: float = 60.
    max_polynomial_bytes: int = 32*1024*1024
    started: float = field(default_factory=time.perf_counter)
    transitions: int = 0
    peak_states: int = 0
    checkpoints: list = field(default_factory=list)

    def check(self, states=0, transitions=0, **location):
        self.transitions+=transitions
        self.peak_states=max(self.peak_states,states)
        elapsed=time.perf_counter()-self.started
        detail=dict(location=location,states=states,peak_states=self.peak_states,
                    transitions=self.transitions,elapsed_seconds=elapsed)
        if states>self.max_states:
            raise CountUnresolved('frontier/state budget exceeded',limit=self.max_states,**detail)
        if self.transitions>self.max_transitions:
            raise CountUnresolved('transition budget exceeded',limit=self.max_transitions,**detail)
        if elapsed>self.max_seconds:
            raise CountUnresolved('wall-clock budget exceeded',limit_seconds=self.max_seconds,**detail)

    def stats(self):
        return dict(peak_states=self.peak_states,transitions=self.transitions,
                    elapsed_seconds=time.perf_counter()-self.started,checkpoints=self.checkpoints)


def emitted_cost(family, paths):
    value=0.
    for k in family.solver._ordered(paths): value+=family.solver.paths[k].cost
    return value


def ieee_histogram(family,budget):
    """Count a group by merging identical frozen-prefix computation states.

    State includes exact binary64 remaining budget AND emitted cost; merging
    either approximately would change global-margin behavior. No path lists.
    """
    s=family.solver
    # This asks for a proof of uniqueness, not for a selected primary.
    gap=s._cheap_unique_certificate(s.full,family.optimum)
    if family.optimum.links==0 or (gap is not None and gap>Fraction.from_float(family.margin+solver.TOLERANCE)+4*s.rounding_bound):
        witness=family.optimum.paths
        if not family.contains(witness): raise CountUnresolved('Unique witness failed frozen membership')
        return Counter({emitted_cost(family,witness):1})
    n=len(s.nodes)
    buckets=[{} for _ in range(n+1)]
    buckets[0][(s.full,family.optimum.links,family.optimum.cost+family.margin,0.)]=1
    histogram=Counter()
    active_states=1
    for position in range(n+1):
        states=buckets[position]; active_states-=len(states)
        for (mask,target,remaining,cost),multiplicity in states.items():
            if not mask:
                if target==0: histogram[cost]+=multiplicity
                continue
            first=(mask & -mask).bit_length()-1
            for k in s.by_candidate[first]:
                p=s.paths[k]
                if p.nodes[0]!=first or p.mask & mask!=p.mask: continue
                tail=s.optimum(mask ^ p.mask)
                budget.check(transitions=1,phase='IEEE prefix DAG',position=position)
                if p.links+tail.links!=target or p.cost+tail.cost>remaining+solver.TOLERANCE: continue
                new_mask=mask ^ p.mask
                dest=(new_mask & -new_mask).bit_length()-1 if new_mask else n
                key=(new_mask,target-p.links,remaining-p.cost,cost+p.cost)
                if key not in buckets[dest]: active_states+=1
                buckets[dest][key]=buckets[dest].get(key,0)+multiplicity
                budget.check(states=active_states+len(states)+len(histogram),phase='IEEE prefix DAG',position=position)
        buckets[position]={}
    return histogram


def ieee_episode_count(episode,budget):
    # Group histories merge only when their emitted binary64 costs are equal.
    # Episode prefixes reproduce the committed combine() addition order.
    histories=[ieee_histogram(f,budget) for f in episode.factors]
    states={0.:1}
    for i,hist in enumerate(histories):
        next_states=Counter()
        suffix=sum(f.optimum.cost for f in episode.factors[i:])
        for cost,multiplicity in states.items():
            if cost+suffix>episode.optimum_cost+episode.margin+solver.TOLERANCE: continue
            for group_cost,count in hist.items():
                next_states[cost+group_cost]+=multiplicity*count
                budget.check(states=len(states)+len(next_states),transitions=1,phase='IEEE group composition',factor=i)
        states=next_states
    return sum(count for cost,count in states.items() if cost<=episode.optimum_cost+episode.margin+solver.TOLERANCE)


def cost_lattice(families):
    """Propose a rational lattice; the proposal has no scientific authority.

    All actual binary64 coefficient residuals are bounded below. Rational
    reconstruction merely proposes a potentially useful computational unit.
    """
    fs=[Fraction(c['frequency_hz']).limit_denominator(1000000)
        for f in families for c in f.solver.nodes]
    if not fs: return Fraction(1)
    denominator=math.lcm(*(x.denominator for x in fs))
    integers=[x.numerator*(denominator//x.denominator) for x in fs]
    divisor=math.gcd(*(x-integers[0] for x in integers))
    if divisor==0: return Fraction(1)
    return (Fraction(divisor,denominator)/50)**2


def lattice_certificate(families,margin,quantum):
    """Prove equivalence of integer excess <= cutoff and frozen acceptance.

    Restricted to two-fragment maximum matchings saturating the smaller side.
    Rounding envelope includes both optimum folds, all local prefix operations,
    emitted costs, and episode prefix operations. If either adjacent lattice
    shell can touch a decision boundary, certification FAILS (no rounding).
    """
    total_n=sum(len(f.solver.nodes) for f in families)
    total_links=sum(f.optimum.links for f in families)
    coefficient_error=Fraction(0)
    weights=[]; optima=[]
    for f in families:
        s=f.solver
        if any(len(p.nodes)>2 for p in s.paths): raise CertificateUnavailable('A path has more than two candidates')
        layers=Counter(c['fragment_index'] for c in s.nodes)
        if len(layers)!=2 or f.optimum.links!=min(layers.values()):
            raise CertificateUnavailable('Not a smaller-side-saturating two-layer matching')
        w={}
        for k,p in enumerate(s.paths):
            exact=Fraction.from_float(p.cost)
            w[k]=round(exact/quantum)
            coefficient_error=max(coefficient_error,abs(exact-quantum*w[k]))
        optimum=sum(w[k] for k in f.optimum.paths)
        weights.append(w); optima.append(optimum)
    # Every original path has at most one edge here. Each floating operation
    # is < one ulp(U), U strictly bounds all intermediate cost magnitudes.
    operations=8*(total_n+len(families)+1)
    upper=8.*(total_n+len(families)+1)
    error=2*total_links*coefficient_error+operations*Fraction.from_float(math.ulp(upper))
    tolerance=Fraction.from_float(solver.TOLERANCE)
    threshold=Fraction.from_float(float(margin))
    cutoff=threshold//quantum
    lower_gap=threshold-quantum*cutoff
    upper_gap=quantum*(cutoff+1)-threshold
    coefficients=[Fraction.from_float(p.cost) for f in families for p in f.solver.paths]
    denominator=max((v.denominator for v in coefficients),default=1)
    integers=[v.numerator*(denominator//v.denominator) for v in coefficients]
    divisor=math.gcd(*integers) if integers else 0
    addition_exact=divisor==0 or max(integers)*(total_n+1)//divisor < 2**53
    zero_exact=coefficient_error==0 and addition_exact
    # At a zero margin exact integer arithmetic can also certify ties; otherwise
    # use the IEEE backend, rather than treating near-equal costs as equal.
    if margin==0 and zero_exact and quantum<=error+tolerance:
        raise CertificateUnavailable('Tolerance may admit an additional integer shell at zero margin')
    if not (margin==0 and zero_exact):
        if min(lower_gap,upper_gap)<=error+tolerance:
            raise CertificateUnavailable('Floating-point envelope overlaps an integer-shell acceptance boundary')
    if quantum<=2*error and not zero_exact:
        raise CertificateUnavailable('Integer cost order is not certified')
    for f,opt in zip(families,optima):
        if abs(Fraction.from_float(f.optimum.cost)-quantum*opt)>error:
            raise CertificateUnavailable('Optimum witness outside certified envelope')
    return dict(quantum=quantum,weights=weights,optima=optima,cutoff=int(cutoff),
                coefficient_error=coefficient_error,rounding_envelope=error,
                lower_boundary_gap=lower_gap,upper_boundary_gap=upper_gap,
                zero_margin_exact_arithmetic=zero_exact)


def convolve(a,b,cap,budget):
    """Exact truncated nonnegative polynomial product using carry-free digits.

    A digit width exceeding sum(a)*sum(b) prevents every possible carry. Python
    integer multiplication is exact, not FFT floating-point approximation.
    """
    if not a or not b: return {}
    if a=={0:1}: return {k:v for k,v in b.items() if k<=cap}
    if b=={0:1}: return {k:v for k,v in a.items() if k<=cap}
    width=max(1,((sum(a.values())*sum(b.values())).bit_length()+7)//8)
    da,db=max(a),max(b)
    size=(da+db+1)*width
    if size>budget.max_polynomial_bytes:
        raise CountUnresolved('exact polynomial byte budget exceeded',bytes_required=size,limit=budget.max_polynomial_bytes)
    def pack(poly,degree):
        raw=bytearray((degree+1)*width)
        for power,count in poly.items(): raw[power*width:(power+1)*width]=count.to_bytes(width,'little')
        return int.from_bytes(raw,'little')
    product=pack(a,da)*pack(b,db)
    raw=product.to_bytes(size,'little')
    result={}
    for k in range(min(cap,da+db)+1):
        value=int.from_bytes(raw[k*width:(k+1)*width],'little')
        if value: result[k]=value
    budget.check(states=len(a)+len(b)+len(result),phase='exact polynomial product')
    return result


def frontier_histogram(rows,cap,budget,label,penalties=None):
    """Rows: list of [(column identity, nonnegative integer cost)].

    Saturate rows. Remember only used columns that any future row may use.
    State multiplicity counts distinct assignments; completed paths/singletons
    are never enumerated or stored.
    """
    penalties=penalties or {}
    columns=sorted({c for row in rows for c,w in row})
    bits={c:1<<i for i,c in enumerate(columns)}
    suffix=[0]*(len(rows)+1)
    for i in range(len(rows)-1,-1,-1): suffix[i]=suffix[i+1] | sum(bits[c] for c,w in rows[i])
    width=max(1,cap.bit_length()); costmask=(1<<width)-1
    states={0:1}
    penalty_by_bit={bits[c]:v for c,v in penalties.items() if c in bits and v}
    for i,row in enumerate(rows):
        expiring=suffix[i] & ~suffix[i+1]
        new={}; transitions=0
        for key,count in states.items():
            used,cost=key>>width,key&costmask
            for c,w in row:
                transitions+=1
                bit=bits[c]
                if used & bit or cost+w>cap: continue
                missing=expiring & ~(used | bit)
                penalty=0
                while missing:
                    low=missing & -missing
                    penalty+=penalty_by_bit.get(low,0)
                    missing^=low
                next_cost=cost+w+penalty
                if next_cost>cap: continue
                dest=(((used | bit)&suffix[i+1])<<width) | next_cost
                new[dest]=new.get(dest,0)+count
            if transitions>=4096:
                budget.check(states=len(states)+len(new),transitions=transitions,
                             phase='matching frontier',component=label,row=i+1,rows=len(rows),
                             prior_states=len(states),next_states=len(new),integer_budget=cap,
                             future_columns=suffix[i+1].bit_count())
                transitions=0
        budget.check(states=len(states)+len(new),transitions=transitions,
                     phase='matching frontier',component=label,row=i+1,rows=len(rows),
                     prior_states=len(states),next_states=len(new),integer_budget=cap,
                     future_columns=suffix[i+1].bit_count())
        states=new
    result={key&costmask:count for key,count in states.items()}
    budget.checkpoints.append(dict(component=label,rows=len(rows),columns=len(columns),
                                   histogram_entries=len(result),count=sum(result.values())))
    return result


def assignment_dual(rows):
    """Exact integer rectangular Hungarian primal/dual certificate.

    u_i+v_j <= cost_ij, v_j <= 0, optimum=sum(u)+sum(v).
    Missing edges use a finite bound larger than every all-real-edge matching;
    a missing-edge optimum is rejected, never silently accepted.
    """
    columns=sorted({c for row in rows for c,w in row})
    m,n=len(rows),len(columns)
    if m>n: raise CountUnresolved('Insufficient assignment columns')
    largest=max((w for row in rows for c,w in row),default=0)
    infinity=(m+1)*(largest+1)+1
    costs=[dict(row) for row in rows]
    a=[[row.get(c,infinity) for c in columns] for row in costs]
    u=[0]*(m+1); v=[0]*(n+1); owner=[0]*(n+1); way=[0]*(n+1)
    for i in range(1,m+1):
        owner[0]=i; column=0; distance=[infinity*(m+n+1)+1]*(n+1); used=[False]*(n+1)
        while True:
            used[column]=True; row=owner[column]; delta=infinity*(m+n+1)+1; next_column=0
            for j in range(1,n+1):
                if used[j]: continue
                reduced=a[row-1][j-1]-u[row]-v[j]
                if reduced<distance[j]: distance[j]=reduced; way[j]=column
                if distance[j]<delta: delta=distance[j]; next_column=j
            for j in range(n+1):
                if used[j]: u[owner[j]]+=delta; v[j]-=delta
                else: distance[j]-=delta
            column=next_column
            if not owner[column]: break
        while column:
            previous=way[column]; owner[column]=owner[previous]; column=previous
    selected=[(owner[j]-1,columns[j-1]) for j in range(1,n+1) if owner[j]]
    if any(c not in costs[i] for i,c in selected): raise CountUnresolved('No saturating real-edge matching')
    primal=sum(costs[i][c] for i,c in selected)
    dual=sum(u[1:])+sum(v[1:])
    if primal!=dual or any(x>0 for x in v[1:]): raise CountUnresolved('Assignment dual certificate failed')
    reduced=[]
    for i,row in enumerate(rows):
        reduced.append([(c,w-u[i+1]-v[columns.index(c)+1]) for c,w in row])
    if any(w<0 for row in reduced for c,w in row): raise CountUnresolved('Negative reduced cost')
    return primal,reduced,{c:-v[j+1] for j,c in enumerate(columns)}


def matching_histogram(family,weights,optimum,cutoff,budget,label):
    s=family.solver
    layers=defaultdict(list)
    for i,c in enumerate(s.nodes): layers[c['fragment_index']].append(i)
    small,large=sorted(layers.values(),key=lambda v:(len(v),s.nodes[v[0]]['fragment_index']))
    small=sorted(small,key=lambda i:(s.nodes[i]['frequency_hz'],s.nodes[i]['candidate_id']))
    large_set=set(large); rows=[]
    for i in small:
        options=[]
        for k in s.by_candidate[i]:
            p=s.paths[k]
            if len(p.nodes)!=2: continue
            j=next(j for j in p.nodes if j!=i)
            if j in large_set: options.append((j,weights[k]))
        if not options: return {}
        rows.append(options)
    primal,rows,penalties=assignment_dual(rows)
    if primal!=optimum: raise CountUnresolved('Integer assignment optimum disagrees with certified family optimum')
    # Exact identity: cost - optimum = sum(selected reduced costs)
    #                              + sum(unmatched column penalties).
    # All terms are nonnegative; every discarded edge exceeds the full margin.
    rows=[[(c,w) for c,w in row if w<=cutoff] for row in rows]
    remaining_columns={c for row in rows for c,w in row}
    forced=sum(w for c,w in penalties.items() if c not in remaining_columns)
    cap=cutoff-forced
    if cap<0: return {}
    unseen=set(range(len(rows))); components=[]
    while unseen:
        stack=[min(unseen)]; indices=set(); columns=set()
        while stack:
            i=stack.pop()
            if i in indices: continue
            indices.add(i); columns.update(c for c,w in rows[i])
            stack.extend(j for j in sorted(unseen-indices) if columns & {c for c,w in rows[j]})
        unseen-=indices; components.append(sorted(indices))
    histogram={0:1}
    for number,indices in enumerate(components):
        component=[rows[i] for i in indices]
        columns={c for row in component for c,w in row}
        local_penalties={c:penalties[c] for c in columns}
        divisor=math.gcd(*(list(local_penalties.values())+[w for row in component for c,w in row])) or 1
        normalized=[[(c,w//divisor) for c,w in row] for row in component]
        partial=frontier_histogram(normalized,cap//divisor,budget,f'{label}/block{number}',
                                   {c:w//divisor for c,w in local_penalties.items()})
        partial={k*divisor:v for k,v in partial.items()}
        histogram=convolve(histogram,partial,cap,budget)
    return {forced+k:v for k,v in histogram.items()}


def count(family,budget=None,backend='auto'):
    """Return an exact cardinality or raise; never return a partial estimate."""
    if budget is None: budget=Budget()
    episode=isinstance(family,solver.EpisodeFamily)
    factors=family.factors if episode else [family]
    margin=family.margin
    if not factors: return dict(count=1,method='fixed singletons',certificate=None,stats=budget.stats())
    if backend not in ('auto','ieee','lattice'): raise ValueError('Unknown backend')
    certificate=None; unavailable=None
    if backend!='ieee':
        try: certificate=lattice_certificate(factors,margin,cost_lattice(factors))
        except CertificateUnavailable as exc:
            unavailable=str(exc)
            if backend=='lattice': raise
    if certificate is None:
        value=ieee_episode_count(family,budget) if episode else sum(ieee_histogram(family,budget).values())
        return dict(count=value,method='exact IEEE prefix-state DAG',
                    lattice_unavailable=unavailable,certificate=None,stats=budget.stats())
    histogram={0:1}
    for i,(f,w,opt) in enumerate(zip(factors,certificate['weights'],certificate['optima'])):
        partial=matching_histogram(f,w,opt,certificate['cutoff'],budget,f'factor{i}')
        histogram=convolve(histogram,partial,certificate['cutoff'],budget)
    value=sum(histogram.values())
    proof={k:([v.numerator,v.denominator] if isinstance(v,Fraction) else v)
           for k,v in certificate.items() if k!='weights'}
    return dict(count=value,method='certified lattice + factored weighted matching frontier DP',
                certificate=proof,histogram_entries=len(histogram),stats=budget.stats())
