#!/usr/bin/env python3
"""Benchmark ONLY stored TPMS-008 E08 candidates; never rerun the experiment."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

import episode_component_tracking_v2_draft2_experiment as old
import episode_component_tracking_v2_draft2_exact_solver as new

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/episode-component-tracking-v2-draft2-experiment'
INPUT=BASE/'native__w200__connected.json'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def run(output):
    if output.exists(): raise ValueError('Refusing to overwrite any existing output')
    expected={name:digest for digest,name in (line.split('  ',1) for line in (BASE/'files.sha256').read_text().splitlines())}
    for name,digest in expected.items():
        if sha(BASE/name)!=digest: raise ValueError(f'Stored Draft 2 hash mismatch: {name}')
    raw=json.loads(INPUT.read_text())
    episode=next(e for e in raw['episodes'] if e['capture']=='PIPELINE-TPMS-008-20260918-003900' and e['episode']==8)
    nodes=[c for f in episode['components'] for c in f['components'] if c['eligible_for_tracking']]
    by={c['candidate_id']:c for c in nodes}
    group=next(g for g in episode['association']['connected_groups'] if len(g['candidate_ids'])==73)
    failed=[by[i] for i in group['candidate_ids']]
    before={str(p.relative_to(ROOT)):sha(p) for p in BASE.iterdir() if p.is_file()}
    report=dict(format='KRAKEN_DRAFT2_EXACT_SOLVER_BENCHMARK_V1',
                git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                python=platform.python_version(),platform=platform.platform(),
                input_path=str(INPUT.relative_to(ROOT)),input_sha256=sha(INPUT),
                baseline_artifact_hashes=before,
                scope='Saved TPMS-008 E08 only; no spectral analysis or full-matrix rerun',
                capture=episode['capture'],episode=8,failed_group_id=group['track_id'],
                candidates=len(failed),original_fragments=len(episode['components']))
    log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_episode_component_tracking_v2_draft2_exact_solver.py')
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    report['tests']=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),passed=tests.wasSuccessful())
    if not tests.wasSuccessful(): raise RuntimeError(log.getvalue())
    print('Validation tests passed; benchmarking old failing group.',flush=True)
    start=time.perf_counter()
    try:
        result=old.solve_group(failed,0)
        report['old_dp']=dict(state='COMPLETE',states=result['states'],optimum_links=result['optimum_links'],optimum_cost=result['optimum_cost'])
    except old.ComputationUnresolved as exc:
        report['old_dp']=dict(state='COMPUTATION_UNRESOLVED',details=exc.details)
    report['old_dp']['elapsed_seconds']=time.perf_counter()-start
    print('Benchmarking exact replacement on the same group.',flush=True)
    start=time.perf_counter()
    solver=new.Solver(failed,len(episode['components']))
    optimum=solver.optimum()
    report['new_group_optimum']=dict(elapsed_seconds=time.perf_counter()-start,
        maximum_links=optimum.links,minimum_cost=optimum.cost,minimum_cost_hex=optimum.cost.hex(),
        paths=solver.ids(optimum.paths),feasible_paths=len(solver.paths),edges=len(solver.edges),
        fragment_candidate_counts=dict(Counter(c['fragment_index'] for c in solver.nodes)),
        stats=dict(solver.stats),method='rational min-cost matching with distinct-row-minima uniqueness certificate')
    report['group_margins']=[]; artifacts={}
    for margin in new.MARGINS:
        start=time.perf_counter(); family=solver.family(margin)
        classification=family.classify(); witness=family.find()
        assert witness is not None and family.contains(witness)
        alternative=family.alternative(witness)
        if alternative is not None: assert family.contains(alternative) and alternative!=witness
        model=family.artifact(); name=f'group-margin-{margin:g}.json'
        artifacts[name]=model
        report['group_margins'].append(dict(margin=margin,classification=classification,
            alternative_exists=alternative is not None,alternative_witness=solver.ids(alternative) if alternative else None,
            serialized_family_bytes=len(new.canonical_bytes(model)),elapsed_seconds=time.perf_counter()-start))
    report['episode_margins']=[]
    for margin in new.MARGINS:
        print(f'Benchmarking full saved E08 episode, margin {margin}.',flush=True)
        start=time.perf_counter(); family=new.EpisodeFamily(nodes,len(episode['components']),margin)
        print(f'Episode optimum established for margin {margin}; checking ambiguity.',flush=True)
        classification=family.classify(); witness=family.find()
        assert witness is not None and family.contains(witness)
        alternative=family.alternative(witness)
        if alternative is not None: assert family.contains(alternative)
        model=family.artifact(); artifacts[f'episode-margin-{margin:g}.json']=model
        report['episode_margins'].append(dict(margin=margin,maximum_links=family.maximum_links,
            minimum_cost=family.optimum_cost,classification=classification,alternative_exists=alternative is not None,
            serialized_family_bytes=len(new.canonical_bytes(model)),elapsed_seconds=time.perf_counter()-start,
            factor_count=len(family.factors),singleton_count=len(family.singletons)))
    report['schema_status']=dict(existing_expanded_schema_sufficient=False,
        compact_format='lossless implicit retained-family model with exact query procedures',
        exact_positive_margin_counts='NOT_EVALUATED',
        integration_ready=False,
        required_before_full_run=['Explicitly adopt/version implicit-family artifact schema',
            'Decide and implement exact family counting required by the original metrics, or explicitly revise that output requirement',
            'Add runner/verification integration without altering frozen files or scientific parameters',
            'Validate remaining representation/width candidate graphs; benchmark is not a completion guarantee'])
    report['existing_files_unchanged']=all(sha(ROOT/name)==digest for name,digest in before.items())
    assert report['existing_files_unchanged']
    report['source_hashes']={str(p.relative_to(ROOT)):sha(p) for p in (
        Path(new.__file__),Path(__file__),ROOT/'tests/test_episode_component_tracking_v2_draft2_exact_solver.py',
        Path(old.__file__),ROOT/'analysis/episode_component_tracking_v2_draft1.py')}
    output.mkdir(parents=True)
    for name,value in artifacts.items(): (output/name).write_bytes(new.canonical_bytes(value))
    (output/'benchmark.json').write_bytes(new.canonical_bytes(report))
    (output/'tests.txt').write_text(log.getvalue())
    lines=['# Separate Draft 2 exact-solver benchmark','',
        'Only saved TPMS-008 E08 candidates were used. This is not a new experiment run.',
        f"Validation: {tests.testsRun} tests passed.",
        f"Old DP: {report['old_dp']['state']} after {report['old_dp']['elapsed_seconds']:.6f} s.",
        f"New 73-candidate group optimum: {optimum.links} links, cost {optimum.cost:.17g}, {report['new_group_optimum']['elapsed_seconds']:.6f} s.",
        f"New optimum search statistics: {json.dumps(report['new_group_optimum']['stats'],sort_keys=True)}",'',
        '| Scope | Margin | Maximum links | Minimum cost | Status | Primary | Compact bytes | Seconds |',
        '|---|---:|---:|---:|---|---|---:|---:|']
    for x in report['group_margins']:
        lines.append(f"| Failed group | {x['margin']} | {optimum.links} | {optimum.cost:.17g} | {x['classification']['status']} | null | {x['serialized_family_bytes']} | {x['elapsed_seconds']:.6f} |")
    for x in report['episode_margins']:
        lines.append(f"| Entire E08 | {x['margin']} | {x['maximum_links']} | {x['minimum_cost']:.17g} | {x['classification']['status']} | null | {x['serialized_family_bytes']} | {x['elapsed_seconds']:.6f} |")
    lines += ['',
        'Times are one local measurement, not a full-matrix runtime forecast. All membership and ambiguity decisions are exact; no selected assignment is promoted to a primary.',
        'The serialized model defines the complete retained family. It does not enumerate that family or establish its cardinality. Positive-margin counts remain explicitly NOT_EVALUATED.',
        'The original expanded schema and exact-count output requirement must be addressed explicitly before a complete Draft 2 run. No scientific parameter change is proposed.',
        'Original experimental status is unchanged: 1/160 real arms complete, one resource-limit failure, 158 NOT_RUN, spectral matrix NOT_STARTED. No RF or raw IQ was used.']
    (output/'review.md').write_text('\n'.join(lines)+'\n')
    (output/'files.sha256').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()))
    print(json.dumps({k:report[k] for k in ('tests','old_dp','new_group_optimum','episode_margins')},indent=2))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    sys.exit(run(parser.parse_args().output))
