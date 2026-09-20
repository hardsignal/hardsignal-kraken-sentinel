"""Exact local feasibility preflight for the staged episode query consumer.

An episode query requires a feasible local partition in every constrained group.
Rejecting an impossible local constraint before composing groups changes only
search order. All positive answers still use the frozen global episode predicate.
No retained hypothesis list is built, no approximate cost bound is introduced.
"""


VERSION = 'KRAKEN_DRAFT2_EXACT_QUERY_PREFLIGHT_V1'


class Queries:
    def __init__(self, family):
        self.family = family
        self.cache = {}

    def find(self, required=(), forbidden=()):
        required = frozenset(map(tuple,required))
        forbidden = frozenset(map(tuple,forbidden))
        key = required,forbidden
        if key in self.cache:
            return self.cache[key]
        if required & forbidden or set(self.family.singletons) & forbidden:
            self.cache[key] = None
            return None
        constraints = {}
        for paths,kind in ((required,0),(forbidden,1)):
            for path in sorted(paths):
                if path in self.family.singletons:
                    continue
                factor_path = self.family._factor_path(path)
                if factor_path is None:
                    if kind == 0:
                        self.cache[key] = None
                        return None
                    continue
                factor,k = factor_path
                constraints.setdefault(factor,[[],[]])[kind].append(k)
        for i,(req,ban) in sorted(constraints.items()):
            if self.family.factors[i].find(required=req,forbidden=ban) is None:
                self.cache[key] = None
                return None
        # Local feasibility is necessary, never sufficient for a positive answer.
        answer = self.family.find(required=required,forbidden=forbidden)
        self.cache[key] = answer
        return answer

    def contains(self, paths):
        return self.family.contains(paths)

    def possible(self, path):
        return self.find(required=(path,)) is not None

    def invariant(self, path):
        return self.possible(path) and self.find(forbidden=(path,)) is None

    def alternative(self, witness=None):
        if witness is None:
            witness = self.find()
        if witness is None:
            return None
        for path in witness:
            alternative = self.find(forbidden=(path,))
            if alternative is not None:
                return alternative
        return None

    def classify(self):
        # Frozen EpisodeFamily classification with queries routed through preflight.
        possible = []
        for factor in self.family.factors:
            s = factor.solver
            for k,p in enumerate(s.paths):
                if len(p.nodes)>=3 and len(p.nodes)/s.fragment_count>=.6:
                    ids = tuple(s.ids((k,))[0])
                    if self.possible(ids):
                        possible.append(ids)
        primary = possible[0] if len(possible)==1 and self.invariant(possible[0]) else None
        multiple = False
        if primary is None:
            for i,a in enumerate(possible):
                for b in possible[i+1:]:
                    if self.find(required=(a,b)) is not None:
                        multiple = True
                        break
                if multiple:
                    break
        if not self.family.by_id and not self.family.singletons:
            status = 'NO_ELIGIBLE_COMPONENT'
        elif primary is not None:
            status = 'UNIQUE_PERSISTENT_TRACK'
        elif multiple:
            status = 'MULTIPLE_PERSISTENT_TRACKS'
        elif self.alternative() is not None:
            status = 'AMBIGUOUS_ASSOCIATION'
        else:
            status = 'INSUFFICIENT_SUPPORT'
        return dict(status=status,primary=list(primary) if primary is not None else None,
                    possible_persistent_paths=sorted(map(list,possible)))
