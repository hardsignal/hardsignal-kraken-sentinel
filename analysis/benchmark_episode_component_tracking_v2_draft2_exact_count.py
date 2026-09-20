#!/usr/bin/env python3
"""Count six saved E08 family models, not the 160-arm experiment."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import unittest

import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as counter

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/episode-component-tracking-v2-draft2-exact-solver-benchmark'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output):
    if output.exists(): raise ValueError('Output must be a new directory')
    for line in (BASE/'files.sha256').read_text().splitlines():
        digest,name=line.split('  ',1)
        if sha(BASE/name)!=digest: raise ValueError(f'Committed benchmark artifact mismatch: {name}')
    log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_episode_component_tracking_v2_draft2_exact_count.py')
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful(): raise RuntimeError(log.getvalue())
    result=dict(format='KRAKEN_DRAFT2_EXACT_COUNT_BENCHMARK_V1',
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        python=platform.python_version(),platform=platform.platform(),
        tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        limits=dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432),
        cases=[],input_hashes={str(BASE/'files.sha256'):sha(BASE/'files.sha256')},
        full_experiment_rerun=False,old_artifacts_modified=False)
    for scope in ('group','episode'):
        for margin in exact.MARGINS:
            name=f'{scope}-margin-{margin:g}.json'; path=BASE/name
            model=json.loads(path.read_text()); result['input_hashes'][str(path.relative_to(ROOT))]=sha(path)
            print(f'COUNT {scope} margin {margin}',flush=True)
            start=time.perf_counter()
            family=(exact.Family if scope=='group' else exact.EpisodeFamily).from_artifact(model)
            load_seconds=time.perf_counter()-start
            budget=counter.Budget(); row=dict(scope=scope,margin=margin,input_model_sha256=model['model_sha256'],
                family_load_seconds=load_seconds,count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None)
            factors=family.factors if scope=='episode' else [family]
            try:
                preview=counter.lattice_certificate(factors,margin,counter.cost_lattice(factors))
                row['lattice_certificate']={k:([v.numerator,v.denominator] if isinstance(v,counter.Fraction) else v)
                    for k,v in preview.items() if k!='weights'}
            except counter.CertificateUnavailable as exc:
                row['lattice_unavailable']=str(exc)
            try:
                counted=counter.count(family,budget)
                value=counted.pop('count')
                row.update(count_state='EXACT',exact_count_decimal=str(value),result=counted)
                if scope=='group':
                    bound={0.:1,.25:1935360,1.:74680704}[margin]
                    assert value>=bound
                    if margin==0: assert value==1
                    row['analytical_lower_bound_comparison']='PASS'
            except counter.CountUnresolved as exc:
                row['failure']=exc.details
                row['stats']=budget.stats()
                if scope=='group':
                    row['analytical_lower_bound_decimal']=str({0.:1,.25:1935360,1.:74680704}[margin])
                    row['analytical_lower_bound_comparison']='EXACT_COUNT_UNAVAILABLE; lower bound is not an estimate'
            except exact.Unresolved as exc:
                row['failure']=dict(reason='committed exact solver query limit',details=str(exc))
                row['stats']=budget.stats()
            row['count_elapsed_seconds']=time.perf_counter()-budget.started
            row['process_peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            result['cases'].append(row)
            print(json.dumps(row,sort_keys=True),flush=True)
    result['source_hashes']={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(counter.__file__),
        Path(exact.__file__),ROOT/'tests/test_episode_component_tracking_v2_draft2_exact_count.py')}
    result['all_six_counts_exact']=all(c['count_state']=='EXACT' for c in result['cases'])
    result['ready_for_160_arm_run']=False
    result['schema_conclusion']='Explicit versioned adoption of compact-family artifacts is still required; unresolved counts cannot satisfy an exact-count requirement.'
    output.mkdir(parents=True)
    (output/'counts.json').write_bytes(exact.canonical_bytes(result))
    (output/'tests.txt').write_text(log.getvalue())
    lines=['# Exact retained-family counting review','',
        'Only the committed compact TPMS-008 E08 family models were tested. No full experiment or RF capture was run.',
        f'Validation: {tests.testsRun} tests passed. All counts use arbitrary-precision integers; JSON counts are decimal strings.',
        '', '| Scope | Margin | Exact count | State | Count seconds | Process peak RSS KiB |',
        '|---|---:|---:|---|---:|---:|']
    for r in result['cases']:
        lines.append(f"| {r['scope']} | {r['margin']} | {r['exact_count_decimal'] if r['exact_count_decimal'] is not None else 'null'} | {r['count_state']} | {r['count_elapsed_seconds']:.6f} | {r['process_peak_rss_kib']} |")
    lines+=['','RSS is the process high-water mark, cumulative across cases, not isolated per-case memory. Timing includes exact counting and coefficient certification; family loading is recorded separately.',
        'Limits were fixed before counting: 250,000 simultaneously tracked states, 5,000,000 transitions, 60 seconds per count, 32 MiB packed polynomial storage. Hitting a limit yields no partial count.',
        '', '## Blockers']
    for r in result['cases']:
        if 'failure' in r: lines.append(f"- {r['scope']} margin {r['margin']}: {json.dumps(r['failure'],sort_keys=True)}")
    lines += ['', 'Exact membership, invariance and ambiguity functionality remains in the unchanged committed solver. A counting failure does not replace those functions or change a primary decision.',
        'The minimal proposed schema change is a versioned sidecar referencing the immutable family and model hashes, with decimal exact cardinality or explicit COMPUTATION_UNRESOLVED state and resource diagnostics. Exact counts may never be replaced by lower bounds or estimates.',
        'Compact models plus a completed exact count can replace expanded lists only after explicit schema adoption, provided required membership/quality/track outputs remain present and validators verify the predicate. Unresolved counts leave the original exact-count requirement unsatisfied.',
        'We are not declaring readiness to rerun all 160 arms. No parameters, historical results or committed files were changed.']
    (output/'review.md').write_text('\n'.join(lines)+'\n')
    (output/'files.sha256').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    sys.exit(run(parser.parse_args().output))
