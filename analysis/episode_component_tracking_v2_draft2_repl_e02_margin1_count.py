"""V1 lossless integer implementation of the solver's rational matching bounds.

All finite binary64 edge costs are dyadic rationals. Multiplying every residual
edge cost by one common positive power-of-two denominator preserves every exact
comparison, augmenting path, tie, reward and returned rational bound. Floating
path costs and the frozen retained-family predicate are never scaled or changed.
"""
from fractions import Fraction
from types import MethodType
import time
import episode_component_tracking_v2_draft2_e02_margin1_count as previous

VERSION='KRAKEN_DRAFT2_DYADIC_MATCHING_BOUND_COUNT_V1'

def integer_matching(self, mask, target=None, forbidden_edges=frozenset(), mandatory=frozenset()):
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
            edge(source,i,0); edge(n+i,sink,0)
        for (a,b),cost in self.edges.items():
            if a in position and b in position and (a,b) not in forbidden_edges:
                u,v = position[a],n+position[b]
                # In a two-fragment graph each mandatory node has at most
                # one incident selected edge. 2*n+1 exceeds the entire
                # possible original matching cost, so missing a mandatory
                # node cannot beat any feasible mandatory-cover matching.
                reward=(2*n+1)*(int(a in mandatory)+int(b in mandatory))
                refs.append((a,b,u,edge(u,v,self._integer_edges[a,b]-reward*self._integer_denominator)))
        flow = 0
        while target is None or flow<target:
            distances = [None]*len(graph); predecessor = [None]*len(graph)
            distances[source] = 0
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
        rational_cost = Fraction(sum(self._integer_edges[e] for e in selected),self._integer_denominator)
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


def count(family,budget=None,ordering='forward',force_ieee=False):
    budget=budget or previous.old.Budget()
    factors=family.factors if isinstance(family,previous.old.solver.EpisodeFamily) else [family]
    saved=[];held=0;started=time.perf_counter()
    try:
        for factor in factors:
            solver=factor.solver
            if hasattr(solver,'_integer_edges'):raise ValueError('Counter matching adapter already installed')
            ratios={edge:value.as_integer_ratio() for edge,value in solver.edges.items()}
            denominator=max((q for p,q in ratios.values()),default=1)
            weights={edge:p*(denominator//q) for edge,(p,q) in ratios.items()}
            # Charge the temporary ratios and retained exact weights too.
            budget.check(states=held+len(ratios)+len(weights),phase='dyadic matching preprocessing')
            saved.append((solver,solver.__dict__.get('_matching')))
            solver._integer_denominator=denominator;solver._integer_edges=weights
            solver._matching=MethodType(integer_matching,solver)
            held+=len(weights)
            del ratios
        prepared=time.perf_counter()-started
        result=previous.count(family,previous.HeldBudget(budget,held),ordering,force_ieee)
        result['matching_bound_adapter']=dict(version=VERSION,edge_integer_entries=held,
            preprocessing_seconds=prepared,policy='Exact common dyadic denominator; unchanged residual traversal/ties; Fraction result')
        result['counter_version']=VERSION
        return result
    finally:
        for solver,method in saved:
            if method is None:del solver._matching
            else:solver._matching=method
            del solver._integer_denominator,solver._integer_edges
