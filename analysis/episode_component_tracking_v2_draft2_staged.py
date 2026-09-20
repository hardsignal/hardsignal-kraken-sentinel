"""Separate staged association consumer. No detector, capture or matrix entrypoint.

Inputs are pinned artifacts and saved candidate fragments. Results contain no
expanded retained-hypothesis array. Timing belongs to the audit, not result bytes.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import signal
import subprocess

import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sidecar
import episode_component_tracking_v2_draft2_experiment as historical
from episode_component_tracking_v2_draft2_staged_queries import Queries, VERSION as QUERY_VERSION

FORMAT = 'KRAKEN_DRAFT2_STAGED_ASSOCIATION_V1'
CONNECTED = 'CONNECTED_GROUPS_HISTORICAL_V1'
COMPACT = 'COMPACT_EXACT_FAMILY_V1'
QUERY_LIMITS = dict(max_calls=5000, max_seconds=120)
SPEC = 'docs/episode-component-tracking-v2-draft2-experiment.md'
SOURCE_VERSIONS = {
    'analysis/episode_component_tracking_v2_draft2_exact_solver.py': 'EXACT_SOLVER_V1',
    'analysis/episode_component_tracking_v2_draft2_exact_count.py': 'EXACT_COUNTER_V1',
    'analysis/episode_component_tracking_v2_draft2_column_count.py': 'COLUMN_COUNTER_V1',
    'analysis/episode_component_tracking_v2_draft2_cardinality_sidecar.py': sidecar.FORMAT,
    'analysis/episode_component_tracking_v2_draft2_staged.py': FORMAT,
    'analysis/episode_component_tracking_v2_draft2_staged_queries.py': QUERY_VERSION,
    'analysis/episode_component_tracking_v2_draft2_experiment.py': 'FROZEN_DRAFT2',
    'analysis/episode_component_tracking_v2_draft1.py': 'FROZEN_DRAFT1',
}


def digest(value):
    return hashlib.sha256(exact.canonical_bytes(value)).hexdigest()


def reference(root, path):
    root = Path(root).resolve()
    path = Path(path).resolve()
    return dict(path=str(path.relative_to(root)), sha256=sidecar.sha(path))


def git_context(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    status = git('status', '--porcelain=v1', '--untracked-files=all').splitlines()
    return dict(commit=git('rev-parse', 'HEAD'), dirty=bool(status), status_at_batch_start=status,
                policy='Frozen batch-start context; output creation does not change result identity')


def request(root, fragments, representation, family_path=None, sidecar_path=None, input_ref=None):
    """Pin selected inputs once; persist this request for deterministic reproduction."""
    root = Path(root).resolve()
    if representation not in (CONNECTED, COMPACT):
        raise ValueError('Explicit supported representation required')
    if representation == COMPACT and (family_path is None or sidecar_path is None):
        raise ValueError('Compact inputs require both artifact paths')
    if representation == CONNECTED and (family_path is not None or sidecar_path is not None):
        raise ValueError('Connected inputs must not carry compact artifacts')
    return dict(representation=representation, fragments_sha256=digest(fragments),
                saved_input=deepcopy(input_ref),
                family=reference(root, family_path) if family_path else None,
                cardinality_sidecar=reference(root, sidecar_path) if sidecar_path else None,
                experiment_specification=reference(root, root/SPEC),
                sources={p: dict(version=v, sha256=sidecar.sha(root/p)) for p,v in SOURCE_VERSIONS.items()})


def state(value, reason=None):
    return dict(state=value, reason=reason)


def verify_reference(root, ref):
    if set(ref) != {'path', 'sha256'}:
        raise ValueError('Invalid artifact reference')
    path = sidecar.local(root, ref['path'])
    if sidecar.sha(path) != ref['sha256']:
        raise ValueError('Pinned artifact SHA-256 mismatch: '+ref['path'])
    return path


def validate_context(fragments, model):
    """Prevent joining a correct family to different candidate metadata/denominator."""
    if len(fragments) != model['original_fragment_count']:
        raise ValueError('Original fragment denominator mismatch')
    expected = {c['candidate_id']: (c['fragment_index'], float(c['frequency_hz']).hex())
                for f in fragments for c in f['components'] if c['eligible_for_tracking']}
    eligible = [c for f in fragments for c in f['components'] if c['eligible_for_tracking']]
    if len(expected) != len(eligible):
        raise ValueError('Duplicate candidate identity in fragments')
    actual = {c['candidate_id']: (c['fragment_index'], float(c['frequency_hz']).hex())
              for f in model['factors'] for c in f['candidates']}
    # Singleton frequencies are omitted from the episode artifact; their IDs are
    # bound to the supplied saved fragments and checked through reconstruction.
    singles = [p[0] for p in model['singletons']]
    if set(expected) != set(actual) | set(singles):
        raise ValueError('Candidate inventory mismatch')
    if any(expected[k] != v for k,v in actual.items()):
        raise ValueError('Candidate attributes mismatch')
    if any(c['fragment_index'] != i for i,f in enumerate(fragments,1) for c in f['components']):
        raise ValueError('Fragment/candidate index mismatch')


class QueryBudget:
    def __init__(self, limits):
        self.limits, self.calls = limits, 0

    def call(self, function, *args, **kwargs):
        self.calls += 1
        if self.calls > self.limits['max_calls']:
            raise exact.Unresolved('Staged exact-query call limit exceeded')
        return function(*args, **kwargs)


@contextmanager
def deadline(seconds):
    """POSIX main-thread deadline; raise, never substitute a query answer."""
    def expired(signum, frame):
        raise exact.Unresolved('Staged exact-query wall-clock limit exceeded')
    old = signal.getsignal(signal.SIGALRM)
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError('Staged deadline cannot nest an active timer')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def fixture_metrics(fragments, association, representation, recoverable):
    """Historical metric math with an explicit representation branch."""
    if representation == CONNECTED:
        paths = [g['candidate_ids'] for g in association['connected_groups'] if g['coherent']]
    elif representation == COMPACT:
        paths = association['invariant_membership'] + association['alternative_membership']
    else:
        raise ValueError('Unknown metric representation')
    nodes = {c['candidate_id']: c for f in fragments for c in f['components']}
    switches = sum(nodes[a]['truth'] != nodes[b]['truth'] for p in paths for a,b in zip(p,p[1:]))
    links = sum(max(0,len(p)-1) for p in paths)
    primary = association['primary']
    correct = bool(primary and recoverable and len({nodes[i]['truth'] for i in primary}) == 1)
    return dict(false_primary=bool(primary and not correct), identity_switches=switches, link_count=links,
                identity_switch_rate=switches/links if links else None, correct_primary=correct,
                ambiguity_retained=not bool(primary) if not recoverable else None,
                abstained=not bool(primary), recoverable=recoverable,
                structural_constraint_violations=association['structural_constraint_violations'])


def project_metrics(fragments, association, representation, recoverable):
    if representation == COMPACT:
        paths = association['invariant_membership'] + association['alternative_membership']
        invariants = len(association['invariant_membership'])
        alternatives = len(association['alternative_membership'])
    elif representation == CONNECTED:
        paths = [g['candidate_ids'] for g in association['connected_groups'] if g['coherent']]
        invariants = alternatives = None
    else:
        raise ValueError('Unknown metric representation')
    truth = None
    if recoverable is not None:
        truth = fixture_metrics(fragments,association,representation,recoverable)
    return dict(original_fragment_count=len(fragments), eligible_candidate_count=sum(
        c['eligible_for_tracking'] for f in fragments for c in f['components']),
        possible_path_count=len(paths), invariant_path_count=invariants,
        alternative_path_count=alternatives, union_link_count=sum(len(p)-1 for p in paths),
        persistent_path_count=len(association['persistent_tracks']),
        abstained=association['primary'] is None,
        structural_constraint_status='VALID_BY_EXACT_CONSTRAINTS' if representation==COMPACT else 'HISTORICAL_CONNECTED_DIAGNOSTICS',
        truth_metrics=truth, truth_metrics_state='EXACT' if truth is not None else 'NOT_APPLICABLE')


def integrate(root, pinned, fragments, batch_context, query_limits=None, recoverable=None):
    """Return deterministic facts and independent stage states; no counting rerun.

    A provenance rejection returns no scientific payload. A query failure leaves
    a complete, validated family reference and independent cardinality intact,
    but never publishes an incomplete path union or guessed status/primary.
    """
    root = Path(root).resolve()
    limits = dict(QUERY_LIMITS if query_limits is None else query_limits)
    if (set(limits) != {'max_calls','max_seconds'}
            or not isinstance(limits['max_calls'],int)
            or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v <= 0
                   for v in limits.values())):
        raise ValueError('Invalid computational query limits')
    stages = {k:state('NOT_EVALUATED') for k in
              ('provenance_validation','family_construction','exact_queries','cardinality_counting','metric_projection')}
    out = dict(format=FORMAT, representation=pinned['representation'], states=stages,
               family_complete_as_predicate=False, association=None, cardinality=None, metrics=None,
               query_operations={k:state('NOT_EVALUATED') for k in ('membership','invariance','ambiguity')},
               computational_limits=limits,
               provenance=dict(request=deepcopy(pinned), request_sha256=digest(pinned),
                               git=deepcopy(batch_context), git_context_sha256=digest(batch_context),
                               embedded_model_sha256=None))
    try:
        rep = pinned['representation']
        if rep not in (COMPACT,CONNECTED):
            raise ValueError('Unknown explicit representation')
        if digest(fragments) != pinned['fragments_sha256']:
            raise ValueError('Fragment input hash mismatch')
        if batch_context['commit'] != subprocess.check_output(
                ['git','-C',str(root),'rev-parse','HEAD'],text=True).strip():
            raise ValueError('Batch Git checkpoint mismatch')
        if batch_context['dirty'] != bool(batch_context['status_at_batch_start']):
            raise ValueError('Inconsistent batch Git dirty state')
        if pinned['experiment_specification']['path'] != SPEC:
            raise ValueError('Unexpected experiment specification')
        verify_reference(root,pinned['experiment_specification'])
        if set(pinned['sources']) != set(SOURCE_VERSIONS):
            raise ValueError('Incomplete source provenance')
        for path,record in pinned['sources'].items():
            if record['version'] != SOURCE_VERSIONS[path] or sidecar.sha(root/path) != record['sha256']:
                raise ValueError('Source version/hash mismatch')
        if pinned['saved_input'] is not None:
            verify_reference(root,pinned['saved_input'])
        if rep == COMPACT:
            family_path = verify_reference(root,pinned['family'])
            card_path = verify_reference(root,pinned['cardinality_sidecar'])
            model = json.loads(family_path.read_text())
            if model['format'] != 'KRAKEN_DRAFT2_EXACT_IMPLICIT_EPISODE_V1':
                raise ValueError('Episode family required')
            model_body = dict(model); embedded = model_body.pop('model_sha256')
            if digest(model_body) != embedded:
                raise ValueError('Embedded model hash mismatch')
            out['provenance']['embedded_model_sha256'] = embedded
            card = json.loads(card_path.read_text())
            for name in ('analysis/episode_component_tracking_v2_draft2_exact_solver.py',
                         'analysis/episode_component_tracking_v2_draft2_exact_count.py',
                         'analysis/episode_component_tracking_v2_draft2_column_count.py'):
                if card['counter_source_hashes'].get(name) != pinned['sources'][name]['sha256']:
                    raise ValueError('Cardinality counter/solver source binding mismatch')
            validate_context(fragments,model)
        elif pinned['family'] is not None or pinned['cardinality_sidecar'] is not None:
            raise ValueError('Connected representation cannot carry compact artifacts')
        stages['provenance_validation'] = state('BYTE_BINDINGS_VERIFIED')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        stages['provenance_validation'] = state('REJECTED',str(exc))
        return out

    if rep == COMPACT:
        try:
            family = sidecar.validate(root,card,family_path)
            # Reconstruct the episode from supplied candidates as well. This
            # proves isolated singleton IDs really are isolated at these inputs.
            nodes = [c for f in fragments for c in f['components'] if c['eligible_for_tracking']]
            rebuilt = exact.EpisodeFamily(nodes,len(fragments),family.margin)
            if rebuilt.artifact() != model:
                raise ValueError('Saved family does not match supplied candidate episode')
        except exact.Unresolved as exc:
            stages['family_construction'] = state('COMPUTATION_UNRESOLVED',str(exc))
            return out
        except (ValueError,KeyError,TypeError,OSError) as exc:
            stages['provenance_validation'] = state('REJECTED',str(exc))
            return out
        stages['family_construction'] = state('COMPLETE')
        stages['provenance_validation'] = state('VERIFIED')
        out['family_complete_as_predicate'] = True
        out['cardinality'] = deepcopy(card['cardinality'])
        stages['cardinality_counting'] = state(card['cardinality']['state'],card['cardinality']['reason'])
        stages['cardinality_counting']['mode'] = 'CONSUMED_VALIDATED_SIDECAR_NO_RECOUNT'
        budget = QueryBudget(limits)
        queries = Queries(family)
        operation = 'membership'
        try:
            with deadline(limits['max_seconds']):
                witness = budget.call(queries.find)
                if witness is None or not budget.call(queries.contains,witness):
                    raise exact.Unresolved('No verified retained witness')
                possible = set(family.singletons)
                for factor in family.factors:
                    for k in range(len(factor.solver.paths)):
                        path = tuple(factor.solver.ids((k,))[0])
                        if budget.call(queries.possible,path):
                            possible.add(path)
                out['query_operations'][operation] = state('EXACT')
                operation = 'invariance'
                # An invariant path must belong to the verified witness.
                invariant = {tuple(p) for p in witness if budget.call(queries.invariant,p)}
                out['query_operations'][operation] = state('EXACT')
                operation = 'ambiguity'
                classification = budget.call(queries.classify)
                out['query_operations'][operation] = state('EXACT')
                candidates = {c['candidate_id'] for c in nodes}
                association = dict(status=classification['status'] if any(f['usable_spectrum'] for f in fragments) else 'UNUSABLE_INPUT',
                    primary=classification['primary'], optimum_links=family.maximum_links,
                    optimum_cost=family.optimum_cost, original_fragment_count=family.fragment_count,
                    persistent_tracks=classification['possible_persistent_paths'],
                    invariant_membership=sorted(map(list,invariant)),
                    alternative_membership=sorted(map(list,possible-invariant)),
                    candidate_membership_alternatives={c:sorted([list(p) for p in possible if c in p]) for c in sorted(candidates)},
                    support_coverage=[dict(members=list(p),support=len(p),coverage=len(p)/family.fragment_count,coherent=True) for p in sorted(possible)],
                    structural_constraint_violations=0)
        except exact.Unresolved as exc:
            out['query_operations'][operation] = state('COMPUTATION_UNRESOLVED',str(exc))
            stages['exact_queries'] = state('COMPUTATION_UNRESOLVED',str(exc))
            stages['metric_projection'] = state('BLOCKED_BY_QUERY_FAILURE')
            out['query_calls'] = budget.calls
            return out
        out['query_calls'] = budget.calls
        stages['exact_queries'] = state('EXACT')
    else:
        stages['provenance_validation'] = state('VERIFIED')
        stages['family_construction'] = state('NOT_APPLICABLE_CONNECTED')
        stages['exact_queries'] = state('NOT_APPLICABLE_CONNECTED')
        stages['cardinality_counting'] = state('NOT_APPLICABLE_CONNECTED')
        out['query_operations'] = {k:state('NOT_APPLICABLE_CONNECTED') for k in out['query_operations']}
        association = historical.association(fragments,'connected')
        association = {k:v for k,v in association.items() if k not in ('hypotheses','retained_hypothesis_count')}
        association['original_fragment_count'] = len(fragments)
    out['association'] = association
    try:
        out['metrics'] = project_metrics(fragments,association,rep,recoverable)
        stages['metric_projection'] = state('COMPLETE')
    except (ValueError,KeyError,TypeError) as exc:
        stages['metric_projection'] = state('COMPUTATION_UNRESOLVED',str(exc))
    return out


def reproduce(root, saved, fragments, recoverable=None):
    """Recheck pinned bytes and recompute against archived batch-start context."""
    p = saved['provenance']
    if digest(p['request']) != p['request_sha256'] or digest(p['git']) != p['git_context_sha256']:
        raise ValueError('Result provenance digest mismatch')
    if git_context(root)['commit'] != p['git']['commit']:
        raise ValueError('Reproduction requires original Git checkpoint')
    result = integrate(root,p['request'],fragments,p['git'],saved['computational_limits'],recoverable)
    if exact.canonical_bytes(result) != exact.canonical_bytes(saved):
        raise ValueError('Reproduced association differs from saved artifact')
    return result
