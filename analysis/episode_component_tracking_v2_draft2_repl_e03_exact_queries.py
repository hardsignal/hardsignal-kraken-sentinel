"""V1 exact forbidden-path elimination by candidate-cover disjunction.

Every complete partition covers each candidate exactly once. For a forbidden
path p and any candidate c in p, omitting p is equivalent to choosing one of the
other feasible paths containing c. Each branch remains a GLOBAL episode query.
No local feasibility result alone can establish a positive answer.
"""
from episode_component_tracking_v2_draft2_staged_queries import Queries as Previous
VERSION='KRAKEN_DRAFT2_CANDIDATE_COVER_DISJUNCTION_QUERIES_V1'


class Queries(Previous):
    def __init__(self,family,ordering='forward'):
        super().__init__(family)
        if ordering not in ('forward','reverse'):raise ValueError('Unknown traversal order')
        self.ordering=ordering
        self.incidence={}
        for factor in family.factors:
            s=factor.solver
            for k,p in enumerate(s.paths):
                ids=tuple(s.ids((k,))[0])
                for c in ids:self.incidence.setdefault(c,[]).append(ids)
        for p in family.singletons:self.incidence[p[0]]=[p]
        self.stats=dict(find_calls=0,cache_hits=0,disjunctions=0,branches=0,base_global_queries=0,max_disjunction_depth=0)
        self.depth=0

    def find(self,required=(),forbidden=()):
        self.stats['find_calls']+=1
        required=frozenset(map(tuple,required));forbidden=frozenset(map(tuple,forbidden));key=required,forbidden
        if key in self.cache:
            self.stats['cache_hits']+=1
            return self.cache[key]
        if required & forbidden or set(self.family.singletons)&forbidden:
            self.cache[key]=None;return None
        # Invalid forbidden paths are vacuous, as in the frozen implementation.
        bans=[p for p in sorted(forbidden) if self.family._factor_path(p) is not None]
        if not bans:
            self.stats['base_global_queries']+=1
            answer=super().find(required,())
            self.cache[key]=answer;return answer
        # Required paths cover their candidates already. Overlap makes p absent.
        occupied=set(c for p in required for c in p)
        p=min(bans,key=lambda p:(min(len(self.incidence[c]) for c in p),p))
        remaining=forbidden-{p}
        if occupied.intersection(p):
            answer=self.find(required,remaining)
            self.cache[key]=answer;return answer
        c=min(p,key=lambda c:(len(self.incidence[c]),c))
        choices=[q for q in self.incidence[c] if q!=p and q not in forbidden and not occupied.intersection(q)]
        choices.sort(reverse=self.ordering=='reverse')
        factor_index,_=self.family._factor_path(p)
        solver=self.family.factors[factor_index].solver
        solver._visit()  # Same cumulative SEARCH_LIMIT; no reset or extra allowance.
        self.stats['disjunctions']+=1;self.depth+=1
        self.stats['max_disjunction_depth']=max(self.stats['max_disjunction_depth'],self.depth)
        try:
            for q in choices:
                solver._visit()
                self.stats['branches']+=1
                answer=self.find(required|{q},remaining)
                if answer is not None:
                    self.cache[key]=answer;return answer
            self.cache[key]=None;return None
        finally:self.depth-=1


def engine_reference(root,ordering):
    from pathlib import Path
    import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
    if ordering not in ('forward','reverse'):raise ValueError('Unknown traversal order')
    path=Path(__file__).resolve()
    return dict(version=VERSION,path=str(path.relative_to(root)),sha256=sc.sha(path),ordering=ordering,
                search_limit=200000,query_limits=dict(max_calls=5000,max_seconds=120))


def integrate(root,request,fragments,context,engine):
    """Explicitly bound query adapter around the unchanged staged consumer."""
    from unittest.mock import patch
    import episode_component_tracking_v2_draft2_staged as staged
    if engine!=engine_reference(root,engine['ordering']):raise ValueError('Query engine provenance/limits mismatch')
    instances=[]
    def create(family):
        q=Queries(family,engine['ordering']);instances.append(q);return q
    with patch.object(staged,'Queries',create):
        result=staged.integrate(root,request,fragments,context,engine['query_limits'])
    result['query_engine']=dict(engine)
    stats=dict(engine=instances[0].stats,factors=[dict(f.solver.stats,
        optimum_cache_entries=len(f.solver._optima),matching_cache_entries=len(f.solver._matching_cache))
        for f in instances[0].family.factors],query_cache_entries=len(instances[0].cache)) if instances else None
    return result,stats


def reproduce(root,saved,fragments):
    import episode_component_tracking_v2_draft2_staged as staged
    if staged.digest(saved['provenance']['request'])!=saved['provenance']['request_sha256']:
        raise ValueError('Request hash mismatch')
    if staged.digest(saved['provenance']['git'])!=saved['provenance']['git_context_sha256']:
        raise ValueError('Git context hash mismatch')
    result,stats=integrate(root,saved['provenance']['request'],fragments,saved['provenance']['git'],saved['query_engine'])
    if staged.exact.canonical_bytes(result)!=staged.exact.canonical_bytes(saved):raise ValueError('Query staged reproduction mismatch')
    return result,stats
