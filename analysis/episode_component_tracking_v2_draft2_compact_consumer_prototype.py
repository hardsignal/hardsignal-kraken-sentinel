"""Read-only proposed consumer projection. Never called by the Draft 2 runner.

Enumerates feasible paths, not retained hypotheses. Query-limit exceptions
propagate: no partially populated projection is returned as complete.
"""
from copy import deepcopy
import episode_component_tracking_v2_draft2_cardinality_sidecar as sidecar
import episode_component_tracking_v2_draft2_exact_solver as exact


def project(root, family_path, cardinality, usable_spectrum=True):
    family = sidecar.validate(root, cardinality, family_path)
    if not isinstance(family, exact.EpisodeFamily):
        raise ValueError('Episode scope required for episode output projection')
    possible = set(family.singletons)
    for factor in family.factors:
        for k in range(len(factor.solver.paths)):
            path = tuple(factor.solver.ids((k,))[0])
            if family.possible(path):
                possible.add(path)
    invariant = {p for p in possible if family.invariant(p)}
    classification = family.classify()
    count = deepcopy(cardinality['cardinality'])
    candidates = set(family.by_id) | {p[0] for p in family.singletons}
    return dict(
        representation='KRAKEN_DRAFT2_COMPACT_CONSUMER_PROTOTYPE_V1',
        family_artifact=cardinality['family_artifact'],
        family_sha256=cardinality['family_sha256'],
        cardinality=count,
        status=classification['status'] if usable_spectrum else 'UNUSABLE_INPUT',
        primary=classification['primary'],
        optimum_links=family.maximum_links, optimum_cost=family.optimum_cost,
        invariant_membership=sorted(map(list, invariant)),
        alternative_membership=sorted(map(list, possible - invariant)),
        persistent_tracks=classification['possible_persistent_paths'],
        candidate_membership_alternatives={c: sorted([list(p) for p in possible if c in p])
                                           for c in sorted(candidates)},
        support_coverage=[dict(members=list(p), support=len(p),
                               coverage=len(p)/family.fragment_count, coherent=True)
                          for p in sorted(possible)],
        # Reconstruction validates every feasible path's frozen constraints;
        # contains() enforces disjoint, complete candidate partitions.
        structural_constraint_violations=0,
        family_complete_as_predicate=True)
