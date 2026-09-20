"""Separate versioned cardinality sidecar prototype. Does not mutate families."""
import hashlib
import json
from pathlib import Path
import re
import episode_component_tracking_v2_draft2_exact_solver as exact

FORMAT='KRAKEN_DRAFT2_RETAINED_CARDINALITY_V1'
DEFINITION='UNORDERED_COMPLETE_CANDIDATE_PATH_PARTITION_MAX_LINKS_V1'
ARITHMETIC='FROZEN_DRAFT2_BINARY64_PATH_COST_RIGHT_FOLD_AND_PREFIX_MARGIN_GLOBAL_EPISODE_V1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local(root, name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts: raise ValueError('Repository-relative path required')
    target=(root/p).resolve()
    if not target.is_relative_to(root.resolve()): raise ValueError('Path escapes repository')
    return target


def load_family(path):
    model=json.loads(Path(path).read_text())
    if model['format']==exact.FORMAT: scope='group'; cls=exact.Family
    elif model['format']=='KRAKEN_DRAFT2_EXACT_IMPLICIT_EPISODE_V1': scope='episode'; cls=exact.EpisodeFamily
    else: raise ValueError('Unknown family format')
    return scope,model,cls.from_artifact(model)


def create(root, family_path, outcome, sources, limits):
    root=Path(root).resolve(); family_path=Path(family_path).resolve()
    scope,model,family=load_family(family_path)
    value=outcome.get('exact_count_decimal')
    result=dict(format=FORMAT, family_artifact=str(family_path.relative_to(root)),
        family_sha256=sha(family_path),model_sha256=model['model_sha256'],scope=scope,
        margin_hex=family.margin.hex(),counting_definition_version=DEFINITION,arithmetic_policy=ARITHMETIC,
        cardinality=dict(state=outcome['count_state'],value_decimal=value,reason=outcome.get('failure')),
        counter_source_hashes={str(Path(p).resolve().relative_to(root)):sha(p) for p in sources},
        computational_limits=limits,runtime_state_statistics=outcome['statistics'],
        method=outcome['method'],certificate=outcome.get('certificate'))
    validate(root,result,family_path)
    return result


def validate(root, sidecar, expected_family_path):
    """Validate binding/provenance, reconstruct frozen family; never change queries.

    The caller must supply the intended family, not trust the sidecar's path.
    A binding validator is not a proof of a claimed count: reproducible counting
    and its numerical certificate/test evidence provide that separate assurance.
    """
    root=Path(root).resolve()
    required={'format','family_artifact','family_sha256','model_sha256','scope','margin_hex',
        'counting_definition_version','arithmetic_policy','cardinality','counter_source_hashes',
        'computational_limits','runtime_state_statistics','method','certificate'}
    if set(sidecar)!=required: raise ValueError('Unknown or missing sidecar fields')
    for key,value in (('format',FORMAT),('counting_definition_version',DEFINITION),('arithmetic_policy',ARITHMETIC)):
        if sidecar[key]!=value: raise ValueError(f'Unsupported {key}')
    path=local(root,sidecar['family_artifact'])
    if path!=Path(expected_family_path).resolve(): raise ValueError('Different expected family')
    if sha(path)!=sidecar['family_sha256']: raise ValueError('Family SHA-256 mismatch')
    scope,model,family=load_family(path)
    if scope!=sidecar['scope'] or model['model_sha256']!=sidecar['model_sha256']:
        raise ValueError('Scope/model binding mismatch')
    if family.margin.hex()!=sidecar['margin_hex']: raise ValueError('Margin binding mismatch')
    card=sidecar['cardinality']
    if set(card)!={'state','value_decimal','reason'}: raise ValueError('Cardinality fields mismatch')
    if card['state']=='EXACT':
        if not isinstance(card['value_decimal'],str) or not re.fullmatch(r'0|[1-9][0-9]*',card['value_decimal']):
            raise ValueError('Exact count must be an arbitrary-precision decimal string')
        if card['reason'] is not None: raise ValueError('Exact count cannot carry a failure')
    elif card['state']=='COMPUTATION_UNRESOLVED':
        if card['value_decimal'] is not None or not isinstance(card['reason'],dict) or not card['reason'].get('reason'):
            raise ValueError('Unresolved count requires null value and explicit reason')
    else: raise ValueError('Unknown count state')
    sources=sidecar['counter_source_hashes']
    if not isinstance(sources,dict) or not sources: raise ValueError('Missing source hashes')
    for name,digest in sources.items():
        if sha(local(root,name))!=digest: raise ValueError('Counter/source hash mismatch')
    limits=sidecar['computational_limits']
    if set(limits)!={'max_states','max_transitions','max_seconds','max_polynomial_bytes'}:
        raise ValueError('Missing computational limits')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not 0<v<float('inf') for v in limits.values()):
        raise ValueError('Invalid limit')
    stats=sidecar['runtime_state_statistics']
    for key in ('elapsed_seconds','peak_states','transitions','process_peak_rss_kib'):
        v=stats.get(key)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not 0<=v<float('inf'): raise ValueError('Missing/invalid statistics')
    if not isinstance(sidecar['method'],str) or not sidecar['method']: raise ValueError('Missing method')
    return family
