"""Fresh-process saved-E08 audit. New output only; no experiment/capture entrypoint."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import unittest

import episode_component_tracking_v2_draft2_column_count as column
import episode_component_tracking_v2_draft2_exact_count as previous
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/episode-component-tracking-v2-draft2-exact-solver-benchmark'
LIMITS = dict(max_states=250000, max_transitions=5000000,
              max_seconds=60, max_polynomial_bytes=33554432)
PATTERNS = ['test_episode_component_tracking_v2_draft2_'+suffix+'.py' for suffix in
            ('margin1_investigation', 'column_count', 'cardinality_sidecar',
             'exact_count', 'exact_solver', 'experiment')]


def inventory():
    names = subprocess.check_output(['git','ls-files','--cached','--others',
                                     '--exclude-standard','-z'], cwd=ROOT).decode().split('\0')
    return {p: sc.sha(ROOT/p) for p in names if p and (ROOT/p).is_file()}


def sources():
    modules = [Path(__file__), Path(column.__file__), Path(previous.__file__),
               Path(previous.solver.__file__), Path(sc.__file__),
               ROOT/'analysis/episode_component_tracking_v2_draft2_compact_consumer_prototype.py']
    # Freeze test and exhaustive-control provenance as well as counter provenance.
    modules += [ROOT/'tests'/p for p in PATTERNS]
    modules += [ROOT/'analysis'/p for p in
                ('episode_component_tracking_v2_draft2_experiment.py',)]
    return modules


def child(case):
    scope, margin, method, ordering, bound = case
    path = BASE/f'{scope}-margin-{margin:g}.json'
    loaded = time.perf_counter()
    _, _, family = sc.load_family(path)
    load_seconds = time.perf_counter()-loaded
    budget = previous.Budget(**LIMITS)
    row = dict(scope=scope, margin_hex=margin.hex(), backend=method, ordering=ordering,
               suffix_bound=bound, method=method, count_state='COMPUTATION_UNRESOLVED',
               exact_count_decimal=None, load_seconds=load_seconds)
    try:
        result = (previous.count(family,budget) if method=='previous'
                  else column.count(family,budget,ordering,bound))
        row.update(count_state='EXACT', exact_count_decimal=str(result['count']),
                   method=result['method'], certificate=result.get('certificate'),
                   histogram_entries=result.get('histogram_entries'))
    except previous.CountUnresolved as exc:
        row['failure'] = exc.details
    except previous.solver.Unresolved as exc:
        row['failure'] = dict(reason='committed solver query limit', detail=str(exc))
    row['statistics'] = dict(budget.stats(),
        process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    side = sc.create(ROOT,path,row,sources(),LIMITS)
    restored = sc.validate(ROOT,side,path)
    witness = family.find()
    assert restored.contains(witness)==family.contains(witness)
    assert restored.classify()==family.classify()
    if witness:
        assert restored.invariant(witness[0])==family.invariant(witness[0])
    row['query_noninterference'] = 'PASS'
    return dict(result=row,sidecar=side)


def run(output):
    if output.exists():
        raise ValueError('Output must be a NEW directory')
    if subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT):
        raise ValueError('Tracked files must be unchanged')
    before = inventory()
    log = io.StringIO()
    suite = unittest.TestSuite()
    for pattern in PATTERNS:
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tests = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful():
        raise RuntimeError(log.getvalue())
    print(f'Validation: {tests.testsRun} tests passed before E08 counting',flush=True)
    cases = [(scope,margin,'column','frequency',True)
             for margin in (0.,.25,1.) for scope in ('group','episode')]
    cases += [(scope,1.,'previous','frequency',True) for scope in ('group','episode')]
    cases += [(scope,1.,'column','reverse_frequency',True) for scope in ('group','episode')]
    cases += [('group',1.,'column','frequency',False)]
    data = {}
    for case in cases:
        scope, margin, backend, order, bound = case
        label = f'{scope}-{margin:g}-{backend}-{order}-bound{int(bound)}'
        # Separate OS processes make RSS measurements attributable per case.
        proc = subprocess.run([sys.executable,str(Path(__file__).resolve()),
            '--child',json.dumps(case)],cwd=ROOT,check=True,capture_output=True,text=True,timeout=90)
        item = json.loads(proc.stdout)
        data[label] = item
        r = item['result']
        print(label, r['count_state'], r['exact_count_decimal'],
              round(r['statistics']['elapsed_seconds'],4),flush=True)
    for scope, expected in [('group',{0.:'1',.25:'191532581516',1.:'9651994153789972'}),
                            ('episode',{0.:'2',.25:'17067800502243',1.:'378038954451765697490'})]:
        for margin, value in expected.items():
            row = data[f'{scope}-{margin:g}-column-frequency-bound1']['result']
            assert row['count_state']=='EXACT' and row['exact_count_decimal']==value
        assert (data[f'{scope}-1-column-reverse_frequency-bound1']['result']['exact_count_decimal']
                == expected[1.])
    assert before=={p:sc.sha(ROOT/p) for p in before},'Pre-existing bytes changed'
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    report = dict(format='KRAKEN_DRAFT2_MARGIN1_INDEPENDENT_INVESTIGATION_V1',
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        computational_limits=LIMITS, limits_increased=False,
        python=sys.version, platform=platform.platform(), per_case_fresh_process=True,
        rss_policy='Linux ru_maxrss KiB; includes imports/model load/count, sampled before sidecar queries',
        state_policy='Previous: mask/cost keys; column: packed mask polynomials; convolution: coefficients. These are not equal-sized states.',
        tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        cases={label:item['result'] for label,item in data.items()},
        initial_file_hashes=before, all_preexisting_bytes_unchanged=True,
        source_hashes={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()},
        production_integration=False, full_experiment_rerun=False, rf_capture=False)
    output.mkdir(parents=True)
    (output/'benchmark.json').write_bytes(previous.solver.canonical_bytes(report))
    (output/'tests.txt').write_text(log.getvalue())
    for label,item in data.items():
        (output/(label+'.cardinality.json')).write_bytes(previous.solver.canonical_bytes(item['sidecar']))
    (output/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.name}\n'
        for p in sorted(output.iterdir()) if p.is_file()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--child')
    args=parser.parse_args()
    if args.child:
        print(json.dumps(child(json.loads(args.child)),sort_keys=True))
    else:
        run(args.output)
