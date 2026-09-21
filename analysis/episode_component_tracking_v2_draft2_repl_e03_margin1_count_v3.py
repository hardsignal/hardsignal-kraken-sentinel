"""V3 certified short-path cover -> independent bipartite matching polynomials.

Applicable only when all directed paths have <=3 nodes, every incidence block
has a uniform gap penalty and an exact dummy-column completion, and a rigorous dyadic
rounding envelope separates both adjacent integer excess shells. Otherwise use
the exact IEEE fallback. No target labels or expected cardinalities are used.
"""
from collections import defaultdict
from fractions import Fraction
import math
from types import SimpleNamespace
import episode_component_tracking_v2_draft2_repl_e03_margin1_count_v2 as fallback
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_column_count as column
VERSION='KRAKEN_DRAFT2_CERTIFIED_SHORT_PATH_MATCHING_COUNT_V3'


def certificate(family):
    factors=family.factors if isinstance(family,old.solver.EpisodeFamily) else [family]
    if not factors or family.margin==0:raise old.CertificateUnavailable('Use frozen IEEE/column zero-margin route')
    quantum=old.cost_lattice(factors)
    if quantum<=0:raise old.CertificateUnavailable('Nonpositive lattice')
    blocks=[];coefficient_error=Fraction(0);penalty_total=Fraction(0);total_links=0
    for fi,f in enumerate(factors):
        s=f.solver;depth=[1]*len(s.nodes)
        for a,b in sorted(s.edges):depth[b]=max(depth[b],depth[a]+1)
        if max(depth,default=1)>3:raise old.CertificateUnavailable('Directed path longer than three candidates')
        adjacency=defaultdict(set)
        for a,b in s.edges:
            adjacency[('out',a)].add(('in',b));adjacency[('in',b)].add(('out',a))
        unseen=set(adjacency);factor_links=0;factor_optimum=0;factor_penalty=Fraction(0)
        weights={};penalties={}
        for e,cost in s.edges.items():
            gap=s.nodes[e[1]]['fragment_index']-s.nodes[e[0]]['fragment_index']
            penalty=Fraction(int(gap==2),4);penalties[e]=penalty
            weight=round((Fraction.from_float(cost)-penalty)/quantum);weights[e]=weight
            if weight<0:raise old.CertificateUnavailable('Negative residual weight')
            coefficient_error=max(coefficient_error,abs(Fraction.from_float(cost)-penalty-quantum*weight))
        while unseen:
            component=set();todo=[min(unseen)]
            while todo:
                v=todo.pop()
                if v in component:continue
                component.add(v);todo.extend(adjacency[v]-component)
            unseen-=component
            left=sorted(v[1] for v in component if v[0]=='out');right=sorted(v[1] for v in component if v[0]=='in')
            es=[e for e in s.edges if e[0] in left and e[1] in right]
            constants={penalties[e] for e in es}
            if len(constants)!=1:raise old.CertificateUnavailable('Mixed gap penalties in a matching block')
            # Roles are computation vertices only. Original candidate IDs remain
            # bound by the input model; edge sets determine original path covers.
            roles=[('out',i) for i in left]+[('in',i) for i in right]
            index={v:i for i,v in enumerate(roles)}
            nodes=[dict(fragment_index=1 if role=='out' else 2,frequency_hz=s.nodes[i]['frequency_hz'],candidate_id=s.nodes[i]['candidate_id']+'/'+role) for role,i in roles]
            paths=[SimpleNamespace(nodes=(index['out',a],index['in',b])) for a,b in es]
            by=[[] for _ in nodes]
            w={}
            for k,p in enumerate(paths):
                for i in p.nodes:by[i].append(k)
                w[k]=weights[es[k]]
            small=range(len(left)) if len(left)<=len(right) else range(len(left),len(nodes))
            rows=[[(next(j for j in paths[k].nodes if j!=i),w[k]) for k in by[i]] for i in small]
            # Determine maximum real cardinality without costs. Complete with
            # exactly d labelled dummy columns; each original maximum matching
            # then has d! extensions, removed exactly from every coefficient.
            owner={}
            def augment(i,seen):
                for c,_ in rows[i]:
                    if c in seen:continue
                    seen.add(c)
                    if c not in owner or augment(owner[c],seen):owner[c]=i;return True
                return False
            links=sum(augment(i,set()) for i in range(len(rows)))
            deficiency=len(rows)-links
            row_ids=list(small)
            column_fragment=2 if len(left)<=len(right) else 1
            for dummy in range(deficiency):
                c=len(nodes);nodes.append(dict(fragment_index=column_fragment,frequency_hz=min(x['frequency_hz'] for x in nodes),candidate_id=f'dummy-{dummy}'))
                by.append([])
                for i in row_ids:
                    k=len(paths);paths.append(SimpleNamespace(nodes=(i,c)));w[k]=0;by[i].append(k);by[c].append(k)
            rows=[[(next(j for j in paths[k].nodes if j!=i),w[k]) for k in by[i]] for i in row_ids]
            optimum,_,_=old.assignment_dual(rows)
            constant=next(iter(constants))*links
            factor_links+=links;factor_optimum+=optimum;factor_penalty+=constant
            blocks.append(dict(factor=fi,solver=SimpleNamespace(nodes=nodes,paths=paths,by_candidate=by),weights=w,optimum=optimum,links=links,penalty=constant,left=len(left),right=len(right),edges=len(es),dummy_columns=deficiency,dummy_factor=math.factorial(deficiency)))
        if factor_links!=f.optimum.links:raise old.CertificateUnavailable('Maximum-link decomposition mismatch')
        witness_edges=[e for k in f.optimum.paths for e in zip(s.paths[k].nodes,s.paths[k].nodes[1:])]
        if sum(weights[e] for e in witness_edges)!=factor_optimum or sum((penalties[e] for e in witness_edges),Fraction(0))!=factor_penalty:
            raise old.CertificateUnavailable('Frozen optimum not in certified integer optimum shell')
        total_links+=factor_links;penalty_total+=factor_penalty
    n=sum(len(f.solver.nodes) for f in factors);m=len(factors)
    # <=n selected edges; path coefficients use <=n additions, each group fold,
    # prefix subtraction, residual optimum and episode prefix uses O(n+m) ops.
    # Every intermediate magnitude < U; one ulp(U) strictly bounds any rounding.
    # The factor 64 also covers absolute coefficient errors in both sides of
    # comparisons. Fixed gap penalties cancel for every maximum-link prefix.
    upper=16.*(n+m+1)
    error=4*n*coefficient_error+64*(n+m+1)*Fraction.from_float(math.ulp(upper))
    margin=Fraction.from_float(family.margin);tol=Fraction.from_float(old.solver.TOLERANCE)
    cutoff=margin//quantum
    lower=margin-quantum*cutoff;upper_gap=quantum*(cutoff+1)-margin
    if min(lower,upper_gap)<=error+tol or quantum<=2*error:
        raise old.CertificateUnavailable('Integer shell touches frozen binary64 acceptance envelope')
    proof=dict(version=VERSION,quantum=str(quantum),coefficient_error=str(coefficient_error),rounding_envelope=str(error),
        lower_shell_gap=str(lower),upper_shell_gap=str(upper_gap),cutoff=int(cutoff),fixed_penalty=str(penalty_total),
        maximum_links=total_links,maximum_directed_path_nodes=3,
        policy='Exact edge-incidence bijection; rigorous separation of every frozen prefix comparison; no rounded predicate')
    return blocks,int(cutoff),proof


def count(family,budget=None,ordering='forward',force_ieee=False):
    if ordering not in ('forward','reverse'):raise ValueError('Unknown order')
    budget=budget or old.Budget()
    if force_ieee:return fallback.count(family,budget,ordering,True)
    try:blocks,cutoff,proof=certificate(family)
    except (old.CertificateUnavailable,old.CountUnresolved) as exc:
        result=fallback.count(family,budget,ordering)
        result['short_path_certificate_unavailable']=str(exc)
        return result
    budget.check(states=sum(len(b['solver'].nodes)+len(b['weights']) for b in blocks),phase='short-path certificate')
    held=sum(len(b['solver'].nodes)+len(b['weights']) for b in blocks)
    histogram={0:1};statistics=[];peak_polynomial_bytes=0
    order=list(enumerate(blocks))
    if ordering=='reverse':order.reverse()
    for i,b in order:
        before=budget.transitions
        local=column.matching_histogram(SimpleNamespace(solver=b['solver']),b['weights'],b['optimum'],cutoff,
            fallback.dyadic.previous.HeldBudget(budget,held+len(histogram)),f'factor{b["factor"]}/block{i}',
            'frequency' if ordering=='forward' else 'reverse_frequency')
        if any(value % b['dummy_factor'] for value in local.values()):raise old.CountUnresolved('Dummy matching multiplicity certificate failed')
        excess={cost:value//b['dummy_factor'] for cost,value in local.items()}  # Backend emits excess costs.
        budget.check(states=held+len(histogram)+len(local)+len(excess),phase='block excess conversion')
        del local
        if histogram and excess and histogram!={0:1} and excess!={0:1}:
            width=max(1,((sum(histogram.values())*sum(excess.values())).bit_length()+7)//8)
            peak_polynomial_bytes=max(peak_polynomial_bytes,(max(histogram)+max(excess)+1)*width)
        histogram=old.convolve(histogram,excess,cutoff,fallback.dyadic.previous.HeldBudget(budget,held))
        statistics.append(dict(block=i,factor=b['factor'],left=b['left'],right=b['right'],edges=b['edges'],
            optimum_links=b['links'],integer_optimum=b['optimum'],fixed_penalty=str(b['penalty']),dummy_columns=b['dummy_columns'],dummy_factor=b['dummy_factor'],
            local_histogram_entries=len(excess),local_assignments_decimal=str(sum(excess.values())),
            product_histogram_entries=len(histogram),transitions=budget.transitions-before))
    peak_polynomial_bytes=max([peak_polynomial_bytes]+[x.get('peak_packed_bytes',0) for x in budget.checkpoints])
    return dict(count=sum(histogram.values()),packed_polynomial_bytes=peak_polynomial_bytes,method=VERSION,certificate=proof,blocks=statistics,stats=budget.stats(),ordering=ordering)
