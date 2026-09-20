#!/usr/bin/env python3
"""Exact, separate Draft 2 solver prototype. No capture or experiment-run API.

Matching gives cardinality/cost bounds. Exact cover handles range constraints.
An implicit retained-family predicate preserves the frozen floating-point
prefix acceptance rule; it is NOT a claim that its cardinality was computed.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from math import gcd, isfinite, ulp
import hashlib
import json

FORMAT = 'KRAKEN_DRAFT2_EXACT_IMPLICIT_FAMILY_V1'
SEARCH_LIMIT = 200000
PATH_LIMIT = 200000
EXPLICIT_LIMIT = 1000000
MARGINS = (0., .25, 1.)
TOLERANCE = 1e-12


class Unresolved(RuntimeError):
    """No truncated family or asserted primary may be returned on this error."""


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


@dataclass(frozen=True)
class PathRecord:
    nodes: tuple
    mask: int
    links: int
    cost: float


@dataclass(frozen=True)
class Optimum:
    links: int
    cost: float
    paths: tuple


class Solver:
    def __init__(self, candidates, fragment_count, search_limit=SEARCH_LIMIT):
        if not isinstance(fragment_count, int) or fragment_count < 1:
            raise ValueError('Original fragment_count must be a positive integer')
        self.nodes = tuple(sorted((dict(c) for c in candidates),
                                  key=lambda c:(c['fragment_index'],c['candidate_id'])))
        ids = [c['candidate_id'] for c in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate candidate ID')
        for c in self.nodes:
            if not isinstance(c['fragment_index'],int) or not 1 <= c['fragment_index'] <= fragment_count or not isfinite(c['frequency_hz']):
                raise ValueError('Invalid candidate')
        self.fragment_count = fragment_count
        self.search_limit = search_limit
        self.full = (1 << len(self.nodes))-1
        self.stats = dict(search_nodes=0, matching_calls=0, augmentations=0,
                          optimum_cache_hits=0, matching_certificates=0)
        self.edges = {}
        for i,a in enumerate(self.nodes):
            for j in range(i+1,len(self.nodes)):
                b = self.nodes[j]
                gap = b['fragment_index']-a['fragment_index']
                difference = b['frequency_hz']-a['frequency_hz']
                if gap in (1,2) and abs(difference)<=50:
                    self.edges[i,j] = (difference/50)**2 + .25*(gap==2)
        outgoing = {i:[] for i in range(len(self.nodes))}
        for i,j in self.edges:
            outgoing[i].append(j)
        paths = []
        self.range_rejected_extensions = 0
        def extend(p, low, high):
            if len(paths)>=PATH_LIMIT:
                raise Unresolved('Feasible path limit reached; no model returned')
            paths.append(PathRecord(tuple(p),sum(1<<i for i in p),len(p)-1,
                                    sum((self.edges[a,b] for a,b in zip(p,p[1:])),0.0)))
            for j in outgoing[p[-1]]:
                f = self.nodes[j]['frequency_hz']
                if max(high,f)-min(low,f)<=100:
                    extend(p+[j],min(low,f),max(high,f))
                else:
                    self.range_rejected_extensions += 1
        for i,c in enumerate(self.nodes):
            extend([i],c['frequency_hz'],c['frequency_hz'])
        self.paths = tuple(sorted(paths,key=lambda p:p.nodes))
        self.by_nodes = {p.nodes:k for k,p in enumerate(self.paths)}
        self.by_candidate = tuple(tuple(k for k,p in enumerate(self.paths) if p.mask & (1<<i)) for i in range(len(self.nodes)))
        self._optima = {}
        self._matching_cache = {}
        # A conservative absolute IEEE rounding bound, not a scientific tolerance.
        # Edge constants are already frozen binary64 values. <= n additions
        # form paths and <= n additions form the partition cost. All sums are
        # nonnegative and < 4(n+1), so each rounding error is < ulp(4(n+1)).
        n = len(self.nodes)
        self.rounding_bound = Fraction.from_float(ulp(4.*(n+1)))*(2*n+4)
        values = [Fraction.from_float(v) for v in self.edges.values()]
        if values:
            denominator = max(v.denominator for v in values)
            integers = [v.numerator*(denominator//v.denominator) for v in values]
            divisor = reduce(gcd,integers)
            self.exact_addition = divisor==0 or max(integers)*(n+1)//divisor < 2**53
        else:
            self.exact_addition = True
        if self.exact_addition:
            self.rounding_bound = Fraction(0)

    def _visit(self):
        self.stats['search_nodes'] += 1
        if self.stats['search_nodes'] > self.search_limit:
            raise Unresolved('Exact-cover search limit reached; result is unresolved')

    def _ordered(self, paths):
        return tuple(sorted(paths,key=lambda k:self.paths[k].nodes[0]))

    def folded_cost(self, paths):
        result = 0.
        # Exactly the old earliest-candidate recursion's cost addition order.
        for k in reversed(self._ordered(paths)):
            result = self.paths[k].cost + result
        return result

    def ids(self, paths):
        return [[self.nodes[i]['candidate_id'] for i in self.paths[k].nodes]
                for k in self._ordered(paths)]

    def _matching(self, mask, target=None, forbidden_edges=frozenset(), mandatory=frozenset()):
        """Exact successive shortest augmenting paths with rational edge costs.

        Split each candidate into an outgoing and incoming vertex. Forward-only
        fragment indices imply the selected edges form a path cover, not cycles.
        Whole-path range is checked separately; ignoring it gives a relaxation.
        """
        cache_key=(mask,target,forbidden_edges,mandatory)
        if cache_key in self._matching_cache: return self._matching_cache[cache_key]
        self.stats['matching_calls'] += 1
        active = [i for i in range(len(self.nodes)) if mask & (1<<i)]
        n = len(active)
        position = {i:k for k,i in enumerate(active)}
        source,sink = 2*n,2*n+1
        graph = [[] for _ in range(2*n+2)]
        refs = []
        def edge(a,b,cost):
            graph[a].append([b,len(graph[b]),1,cost])
            graph[b].append([a,len(graph[a])-1,0,-cost])
            return len(graph[a])-1
        for i in range(n):
            edge(source,i,Fraction(0)); edge(n+i,sink,Fraction(0))
        for (a,b),cost in self.edges.items():
            if a in position and b in position and (a,b) not in forbidden_edges:
                u,v = position[a],n+position[b]
                # In a two-fragment graph each mandatory node has at most
                # one incident selected edge. 2*n+1 exceeds the entire
                # possible original matching cost, so missing a mandatory
                # node cannot beat any feasible mandatory-cover matching.
                reward=(2*n+1)*(int(a in mandatory)+int(b in mandatory))
                refs.append((a,b,u,edge(u,v,Fraction.from_float(cost)-reward)))
        flow = 0
        while target is None or flow<target:
            distances = [None]*len(graph); predecessor = [None]*len(graph)
            distances[source] = Fraction(0)
            for _ in range(len(graph)-1):
                changed = False
                for u in range(len(graph)):
                    if distances[u] is None: continue
                    for k,(v,rev,capacity,cost) in enumerate(graph[u]):
                        value = distances[u]+cost
                        if capacity and (distances[v] is None or value<distances[v]):
                            distances[v],predecessor[v] = value,(u,k)
                            changed = True
                if not changed: break
            if distances[sink] is None: break
            v = sink
            while v!=source:
                u,k = predecessor[v]
                e = graph[u][k]; e[2]-=1; graph[v][e[1]][2]+=1
                v = u
            flow += 1
            self.stats['augmentations'] += 1
        selected = [(a,b) for a,b,u,k in refs if graph[u][k][2]==0]
        covered={i for e in selected for i in e}
        if not mandatory<=covered:
            result=(-1,Fraction(0),None)
            self._matching_cache[cache_key]=result
            return result
        rational_cost = sum((Fraction.from_float(self.edges[e]) for e in selected),Fraction(0))
        successor = dict(selected); incoming = {b for a,b in selected}
        path_indices = []
        for i in active:
            if i in incoming: continue
            p = [i]
            while p[-1] in successor: p.append(successor[p[-1]])
            key = self.by_nodes.get(tuple(p))
            if key is None:
                result=(flow,rational_cost,None)
                self._matching_cache[cache_key]=result
                return result
            path_indices.append(key)
        result=(flow,rational_cost,self._ordered(path_indices))
        self._matching_cache[cache_key]=result
        return result

    def _options(self, mask, forbidden):
        # Exact-cover pivot: branch on EVERY feasible path containing the
        # chosen uncovered candidate, not merely paths beginning there.
        best = None
        for i in range(len(self.nodes)):
            if not mask & (1<<i): continue
            options = [k for k in self.by_candidate[i] if k not in forbidden and self.paths[k].mask & mask == self.paths[k].mask]
            if best is None or len(options)<len(best): best=options
        return best or []

    def _mandatory_singletons(self, mask, forbidden):
        fragments={c['fragment_index'] for i,c in enumerate(self.nodes) if mask & (1<<i)}
        if len(fragments)>2: return frozenset()
        return frozenset(self.paths[k].nodes[0] for k in forbidden
                         if len(self.paths[k].nodes)==1 and self.paths[k].mask & mask)

    def _forbidden_edges(self, mask, forbidden):
        # Forbidding an entire two-node PATH does not forbid that edge inside
        # a longer path. Remove an edge only when no such extension exists.
        result=set()
        for k in forbidden:
            pair=self.paths[k].nodes
            if len(pair)!=2: continue
            extended=any(len(p.nodes)>2 and p.mask & mask == p.mask
                         and pair in tuple(zip(p.nodes,p.nodes[1:])) for p in self.paths)
            if not extended: result.add(pair)
        return frozenset(result)

    def _covers(self, mask, chosen, target, budget, forbidden=frozenset()):
        """Complete exact-cover search with admissible matching bounds.

        budget is a rational upper bound on accepted *floating* objective cost;
        conservative rounding bounds only weaken pruning, never acceptance.
        """
        self._visit()
        links = sum(self.paths[k].links for k in chosen)
        if not mask:
            if links==target:
                yield self._ordered(chosen)
            return
        needed = target-links
        if needed<0: return
        forbidden_edges = self._forbidden_edges(mask,forbidden)
        count,lower,_ = self._matching(mask,needed,forbidden_edges,self._mandatory_singletons(mask,forbidden))
        if count<needed: return
        selected_cost = sum((Fraction.from_float(self.paths[k].cost) for k in chosen),Fraction(0))
        if budget is not None and selected_cost+lower-self.rounding_bound>budget: return
        options = self._options(mask,forbidden)
        options.sort(key=lambda k:(-self.paths[k].links,self.paths[k].cost,self.paths[k].nodes))
        for k in options:
            p = self.paths[k]
            yield from self._covers(mask ^ p.mask,chosen+(k,),target,budget,forbidden)

    def _cheap_unique_certificate(self, mask, matched):
        """Two-layer distinct row minima certify a unique rational optimum.

        Any different maximum matching costs at least the smallest row's
        second-choice excess more. A conservative rounding bound certifies
        that it is also strictly worse under the original binary64 folding.
        """
        active = [i for i in range(len(self.nodes)) if mask & (1<<i)]
        fragments = sorted({self.nodes[i]['fragment_index'] for i in active})
        if len(fragments)!=2 or fragments[1]-fragments[0] not in (1,2): return None
        left = [i for i in active if self.nodes[i]['fragment_index']==fragments[0]]
        right = [i for i in active if self.nodes[i]['fragment_index']==fragments[1]]
        if len(left)<len(right) or matched.links!=len(right): return None
        minima=[]; gaps=[]
        for b in right:
            choices = sorted((Fraction.from_float(self.edges[a,b]),a) for a in left if (a,b) in self.edges)
            if not choices: return None
            minima.append(choices[0][1])
            if len(choices)>1: gaps.append(choices[1][0]-choices[0][0])
        if len(set(minima))!=len(minima): return None
        gap = min(gaps) if gaps else None
        if gap is not None and gap<=2*self.rounding_bound: return None
        return gap

    def optimum(self, mask=None):
        if mask is None: mask=self.full
        if mask in self._optima:
            self.stats['optimum_cache_hits'] += 1
            return self._optima[mask]
        count,lower,cover = self._matching(mask)
        best = Optimum(count,self.folded_cost(cover),cover) if cover is not None else None
        if best is not None:
            gap = self._cheap_unique_certificate(mask,best)
            if (self.exact_addition and Fraction.from_float(best.cost)==lower) or gap is not None:
                self.stats['matching_certificates'] += 1
                self._optima[mask]=best
                return best
        if best is None:
            # Matching is an upper bound when its cover violates track range.
            for target in range(count,-1,-1):
                candidate = next(self._covers(mask,(),target,None),None)
                if candidate is not None:
                    best=Optimum(target,self.folded_cost(candidate),candidate)
                    break
        # Exact IEEE objective, not a rounded/scaled surrogate. All potentially
        # improving covers survive the conservative rational lower bound.
        for candidate in self._covers(mask,(),best.links,Fraction.from_float(best.cost)):
            cost=self.folded_cost(candidate)
            if cost<best.cost:
                best=Optimum(best.links,cost,candidate)
        self._optima[mask]=best
        return best

    def family(self, margin):
        if margin not in MARGINS: raise ValueError('Only predeclared margins are supported')
        return Family(self,float(margin))


class Family:
    """Lossless implicit family; exact query procedures, no solution cap.

    This is a proposed NEW artifact type. It must not be mistaken for the old
    fully materialized hypotheses array or for an evaluated family count.
    """
    def __init__(self, solver, margin):
        self.solver,self.margin=solver,margin
        self.optimum=solver.optimum()

    def contains(self, paths):
        s=self.solver
        if len(set(paths))!=len(paths) or any(k<0 or k>=len(s.paths) for k in paths): return False
        ordered=s._ordered(paths); mask=s.full
        target=self.optimum.links; remaining=self.optimum.cost+self.margin
        for k in ordered:
            p=s.paths[k]
            if p.mask & mask != p.mask: return False
            tail=s.optimum(mask ^ p.mask)
            # Preserve the frozen DP's PREFIX tests and subtraction order,
            # including behavior at a floating-point margin boundary.
            if p.links+tail.links!=target or p.cost+tail.cost>remaining+TOLERANCE: return False
            mask ^= p.mask; target-=p.links; remaining-=p.cost
        return mask==0 and target==0

    def _prepared(self, required, forbidden):
        s=self.solver; mask=s.full
        required=tuple(sorted(set(required))); forbidden=frozenset(forbidden)
        if any(k<0 or k>=len(s.paths) for k in required+tuple(forbidden)):
            raise ValueError('Unknown path index')
        for k in required:
            p=s.paths[k]
            if k in forbidden or p.mask & mask != p.mask: return None
            mask ^= p.mask
        return mask,required,forbidden

    def find(self, required=(), forbidden=()):
        s=self.solver; prepared=self._prepared(required,forbidden)
        if prepared is None: return None
        mask,chosen,forbidden=prepared
        needed=self.optimum.links-sum(s.paths[k].links for k in chosen)
        if needed<0: return None
        forbidden_edges=s._forbidden_edges(mask,forbidden)
        count,lower,proposal=s._matching(mask,needed,forbidden_edges,s._mandatory_singletons(mask,forbidden))
        if count<needed: return None
        # Prefix subtraction can accumulate roundoff. This envelope is ONLY a
        # pruning bound; contains() is the exact frozen acceptance predicate.
        budget=Fraction.from_float(self.optimum.cost+self.margin+TOLERANCE)+s.rounding_bound
        selected=sum((Fraction.from_float(s.paths[k].cost) for k in chosen),Fraction(0))
        if lower+selected-s.rounding_bound>budget: return None
        if proposal is not None:
            candidate=s._ordered(chosen+proposal)
            if not forbidden.intersection(candidate) and self.contains(candidate): return candidate
        for candidate in s._covers(mask,chosen,self.optimum.links,budget,forbidden):
            if self.contains(candidate): return candidate
        return None

    def possible(self, path):
        return self.find(required=(path,)) is not None

    def invariant(self, path):
        return self.possible(path) and self.find(forbidden=(path,)) is None

    def alternative(self, witness=None):
        s=self.solver
        gap=s._cheap_unique_certificate(s.full,self.optimum)
        if self.optimum.links==0 or (gap is not None and gap>Fraction.from_float(self.margin+TOLERANCE)+4*s.rounding_bound):
            return None
        if witness is None: witness=self.find()
        if witness is None: return None
        # Every cover has n-L* paths. Any distinct cover omits at least one
        # witness path. This disjunction is exact and does not label paths.
        for k in witness:
            other=self.find(forbidden=(k,))
            if other is not None: return other
        return None

    def materialize(self, limit=EXPLICIT_LIMIT):
        """For validation/small graphs only. Reaching limit raises, never truncates."""
        s=self.solver
        budget=Fraction.from_float(self.optimum.cost+self.margin+TOLERANCE)+s.rounding_bound
        result=[]
        for cover in s._covers(s.full,(),self.optimum.links,budget):
            if self.contains(cover):
                if len(result)>=limit: raise Unresolved('Explicit family exceeds limit; no truncated list returned')
                result.append(cover)
        return sorted(result)

    def classify(self):
        s=self.solver
        persistent=[k for k,p in enumerate(s.paths) if len(p.nodes)>=3 and len(p.nodes)/s.fragment_count>=.6 and self.possible(k)]
        primary=persistent[0] if len(persistent)==1 and self.invariant(persistent[0]) else None
        multiple=False
        if primary is None:
            for i,a in enumerate(persistent):
                for b in persistent[i+1:]:
                    if self.find(required=(a,b)) is not None:
                        multiple=True; break
                if multiple: break
        if not s.nodes: status='NO_ELIGIBLE_COMPONENT'
        elif primary is not None: status='UNIQUE_PERSISTENT_TRACK'
        elif multiple: status='MULTIPLE_PERSISTENT_TRACKS'
        elif self.alternative() is not None: status='AMBIGUOUS_ASSOCIATION'
        else: status='INSUFFICIENT_SUPPORT'
        return dict(status=status,primary=s.ids((primary,))[0] if primary is not None else None,
                    possible_persistent_paths=s.ids(persistent),
                    retained_hypothesis_count=None,count_state='NOT_EVALUATED',
                    family_complete_as_predicate=True)

    def artifact(self):
        s=self.solver
        model=dict(format=FORMAT,original_fragment_count=s.fragment_count,
                   candidates=[dict(candidate_id=c['candidate_id'],fragment_index=c['fragment_index'],
                                    frequency_hz=c['frequency_hz']) for c in s.nodes],
                   paths=[dict(candidate_ids=[s.nodes[i]['candidate_id'] for i in p.nodes],
                               links=p.links,cost_hex=p.cost.hex()) for p in s.paths],
                   maximum_links=self.optimum.links,minimum_cost_hex=self.optimum.cost.hex(),
                   optimum_witness=s.ids(self.optimum.paths),margin=self.margin,
                   numerical_policy='FROZEN_DRAFT2_BINARY64_PATH_COST_RIGHT_FOLD_AND_PREFIX_MARGIN_V1',
                   cost_tolerance_hex=TOLERANCE.hex(),
                   constraints=['each candidate in exactly one selected path','sum(path.links) == maximum_links',
                                'frozen earliest-candidate prefix margin predicate'],
                   family_representation='complete implicit constraints plus exact membership predicate',
                   retained_hypothesis_count=None,count_state='NOT_EVALUATED',
                   scientific_parameters_unchanged=True)
        model['model_sha256']=hashlib.sha256(canonical_bytes(model)).hexdigest()
        return model

    @classmethod
    def from_artifact(cls, model, search_limit=SEARCH_LIMIT):
        expected=dict(model); digest=expected.pop('model_sha256')
        if hashlib.sha256(canonical_bytes(expected)).hexdigest()!=digest: raise ValueError('Model hash mismatch')
        if model['format']!=FORMAT: raise ValueError('Unknown family schema')
        s=Solver(model['candidates'],model['original_fragment_count'],search_limit)
        family=s.family(model['margin'])
        if family.artifact()!=model: raise ValueError('Model/certificate does not match reconstructed problem')
        return family


class EpisodeFamily:
    """Independent exact group families with the frozen GLOBAL cost filter.

    This adapter receives eligible candidates only. Caller-owned unusable-input
    flags and spectral detection remain outside the solver and unchanged.
    """
    def __init__(self, candidates, fragment_count, margin, search_limit=SEARCH_LIMIT):
        if margin not in MARGINS: raise ValueError('Only predeclared margins are supported')
        candidates=sorted((dict(c) for c in candidates),key=lambda c:(c['fragment_index'],c['candidate_id']))
        if len({c['candidate_id'] for c in candidates})!=len(candidates): raise ValueError('Duplicate candidate ID')
        adjacency={c['candidate_id']:set() for c in candidates}
        by={c['candidate_id']:c for c in candidates}
        for i,a in enumerate(candidates):
            for b in candidates[i+1:]:
                if b['fragment_index']-a['fragment_index'] in (1,2) and abs(b['frequency_hz']-a['frequency_hz'])<=50:
                    adjacency[a['candidate_id']].add(b['candidate_id'])
                    adjacency[b['candidate_id']].add(a['candidate_id'])
        unseen=set(by); groups=[]
        while unseen:
            stack=[min(unseen)]; group=set()
            while stack:
                v=stack.pop()
                if v in group: continue
                group.add(v); stack.extend(sorted(adjacency[v]-group,reverse=True))
            unseen-=group; groups.append([by[i] for i in sorted(group)])
        def group_key(group):
            fs=sorted(c['frequency_hz'] for c in group); n=len(fs)
            median=fs[n//2] if n%2 else (fs[n//2-1]+fs[n//2])/2
            return median,min(c['fragment_index'] for c in group),min(c['candidate_id'] for c in group)
        groups.sort(key=group_key)
        self.singletons=tuple((g[0]['candidate_id'],) for g in groups if len(g)==1)
        self.factors=[Solver(g,fragment_count,search_limit).family(margin) for g in groups if len(g)>1]
        self.fragment_count,self.margin=fragment_count,float(margin)
        self.by_id={c['candidate_id']:(i,j) for i,f in enumerate(self.factors) for j,c in enumerate(f.solver.nodes)}
        self.optimum_cost=sum(f.optimum.cost for f in self.factors)
        self.maximum_links=sum(f.optimum.links for f in self.factors)

    def _factor_path(self, ids):
        if not ids: return None
        mapped=[self.by_id.get(i) for i in ids]
        if any(v is None for v in mapped) or len({v[0] for v in mapped})!=1: return None
        group=mapped[0][0]
        path=self.factors[group].solver.by_nodes.get(tuple(v[1] for v in mapped))
        return (group,path) if path is not None else None

    @staticmethod
    def _hypothesis_cost(family, cover):
        # Frozen enumerate_partitions accumulates emitted costs LEFT-to-right,
        # while its optimal cost recurrence is right-associated.
        cost=0.
        for k in family.solver._ordered(cover): cost+=family.solver.paths[k].cost
        return cost

    def contains(self, paths):
        paths=[tuple(p) for p in paths]
        if len(set(paths))!=len(paths): return False
        present=set(paths)
        if not set(self.singletons)<=present: return False
        covers=[[] for _ in self.factors]
        for p in paths:
            if p in self.singletons: continue
            value=self._factor_path(p)
            if value is None: return False
            group,path=value; covers[group].append(path)
        cost=0.
        for i,(f,cover) in enumerate(zip(self.factors,covers)):
            if cost+sum(t.optimum.cost for t in self.factors[i:])>self.optimum_cost+self.margin+TOLERANCE: return False
            if not f.contains(cover): return False
            cost+=self._hypothesis_cost(f,cover)
        return cost<=self.optimum_cost+self.margin+TOLERANCE

    def find(self, required=(), forbidden=()):
        required=set(map(tuple,required)); forbidden=set(map(tuple,forbidden))
        if required & forbidden or set(self.singletons)&forbidden: return None
        req=[[] for _ in self.factors]; ban=[[] for _ in self.factors]
        for p in required:
            if p in self.singletons: continue
            value=self._factor_path(p)
            if value is None: return None
            i,k=value; req[i].append(k)
        for p in forbidden:
            value=self._factor_path(p)
            if value is not None:
                i,k=value; ban[i].append(k)
        def choices(i):
            f=self.factors[i]; s=f.solver
            proposal=f.find(required=req[i],forbidden=ban[i])
            if proposal is None: return
            yield proposal
            mask,chosen,excluded=f._prepared(req[i],ban[i])
            budget=Fraction.from_float(f.optimum.cost+f.margin+TOLERANCE)+s.rounding_bound
            for cover in s._covers(mask,chosen,f.optimum.links,budget,excluded):
                if cover!=proposal and f.contains(cover): yield cover
        def combine(i, paths, cost):
            if cost+sum(f.optimum.cost for f in self.factors[i:])>self.optimum_cost+self.margin+TOLERANCE: return None
            if i==len(self.factors): return sorted(paths+list(self.singletons))
            f=self.factors[i]
            for cover in choices(i):
                result=combine(i+1,paths+[tuple(p) for p in f.solver.ids(cover)],cost+self._hypothesis_cost(f,cover))
                if result is not None: return result
            return None
        return combine(0,[],0.)

    def possible(self, path): return self.find(required=(path,)) is not None
    def invariant(self, path): return self.possible(path) and self.find(forbidden=(path,)) is None

    def alternative(self, witness=None):
        if witness is None: witness=self.find()
        if witness is None: return None
        for path in witness:
            alternative=self.find(forbidden=(path,))
            if alternative is not None: return alternative
        return None

    def classify(self):
        possible=[]
        for f in self.factors:
            s=f.solver
            for k,p in enumerate(s.paths):
                if len(p.nodes)>=3 and len(p.nodes)/self.fragment_count>=.6:
                    ids=tuple(s.ids((k,))[0])
                    if self.possible(ids): possible.append(ids)
        primary=possible[0] if len(possible)==1 and self.invariant(possible[0]) else None
        multiple=False
        if primary is None:
            for i,a in enumerate(possible):
                for b in possible[i+1:]:
                    if self.find(required=(a,b)) is not None:
                        multiple=True; break
                if multiple: break
        if not self.by_id and not self.singletons: status='NO_ELIGIBLE_COMPONENT'
        elif primary is not None: status='UNIQUE_PERSISTENT_TRACK'
        elif multiple: status='MULTIPLE_PERSISTENT_TRACKS'
        elif self.alternative() is not None: status='AMBIGUOUS_ASSOCIATION'
        else: status='INSUFFICIENT_SUPPORT'
        return dict(status=status,primary=list(primary) if primary else None,
                    possible_persistent_paths=sorted(map(list,possible)),retained_hypothesis_count=None,
                    count_state='NOT_EVALUATED',family_complete_as_predicate=True)

    def artifact(self):
        model=dict(format='KRAKEN_DRAFT2_EXACT_IMPLICIT_EPISODE_V1',
                    original_fragment_count=self.fragment_count,margin=self.margin,
                    singletons=sorted(map(list,self.singletons)),factors=[f.artifact() for f in self.factors],
                    maximum_links=self.maximum_links,minimum_cost_hex=float(self.optimum_cost).hex(),
                    composition='frozen Draft 2 ordered group prefix filter; one GLOBAL cost margin',
                    retained_hypothesis_count=None,count_state='NOT_EVALUATED')

        model['model_sha256']=hashlib.sha256(canonical_bytes(model)).hexdigest()
        return model

    @classmethod
    def from_artifact(cls, model, search_limit=SEARCH_LIMIT):
        expected=dict(model); digest=expected.pop('model_sha256')
        if hashlib.sha256(canonical_bytes(expected)).hexdigest()!=digest: raise ValueError('Episode model hash mismatch')
        if model['format']!='KRAKEN_DRAFT2_EXACT_IMPLICIT_EPISODE_V1': raise ValueError('Unknown episode schema')
        result=cls.__new__(cls)
        result.fragment_count=model['original_fragment_count']; result.margin=model['margin']
        result.singletons=tuple(map(tuple,model['singletons']))
        result.factors=[Family.from_artifact(f,search_limit) for f in model['factors']]
        if any(f.margin!=result.margin or f.solver.fragment_count!=result.fragment_count for f in result.factors):
            raise ValueError('Inconsistent factor margin/denominator')
        result.by_id={c['candidate_id']:(i,j) for i,f in enumerate(result.factors) for j,c in enumerate(f.solver.nodes)}
        all_ids=[i for p in result.singletons for i in p]+[c['candidate_id'] for f in result.factors for c in f.solver.nodes]
        if len(set(all_ids))!=len(all_ids) or any(len(p)!=1 for p in result.singletons): raise ValueError('Inconsistent candidate inventory')
        result.optimum_cost=sum(f.optimum.cost for f in result.factors)
        result.maximum_links=sum(f.optimum.links for f in result.factors)
        if result.artifact()!=model: raise ValueError('Episode objective certificate mismatch')
        return result
