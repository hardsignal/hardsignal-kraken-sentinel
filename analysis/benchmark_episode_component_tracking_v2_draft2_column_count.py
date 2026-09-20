"""Saved E08-only benchmark and sidecar integration prototype; never full runner."""
import argparse
import io
import json
from pathlib import Path
import resource
import subprocess
import time
import unittest
import episode_component_tracking_v2_draft2_column_count as new
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/episode-component-tracking-v2-draft2-exact-solver-benchmark'
LIMITS=dict(max_states=250000,max_transitions=5000000,max_seconds=60,max_polynomial_bytes=33554432)


def run(output):
    if output.exists(): raise ValueError('Output must be NEW')
    if subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT): raise ValueError('Tracked files already changed')
    # Actual byte hashes, not normalized Git contents, bind all tracked evidence.
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    before={p:sc.sha(ROOT/p) for p in tracked if p and (ROOT/p).is_file()}
    log=io.StringIO(); suite=unittest.TestSuite()
    for pattern in ('test_episode_component_tracking_v2_draft2_column_count.py',
                    'test_episode_component_tracking_v2_draft2_cardinality_sidecar.py',
                    'test_episode_component_tracking_v2_draft2_exact_count.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful(): raise RuntimeError(log.getvalue())
    sources=[Path(__file__),Path(new.__file__),Path(old.__file__),Path(sc.__file__),Path(old.solver.__file__)]
    sources += [ROOT/'tests'/name for name in ('test_episode_component_tracking_v2_draft2_column_count.py',
        'test_episode_component_tracking_v2_draft2_cardinality_sidecar.py','test_episode_component_tracking_v2_draft2_exact_count.py')]
    results=[]; sidecars={}
    cases=[('group',.25,'column','frequency',True),('episode',.25,'column','frequency',True),
           ('group',1.,'previous','frequency',True),('group',1.,'column','frequency',True),
           ('group',1.,'column','reverse_frequency',True),('group',1.,'column','frequency',False),
           ('episode',1.,'column','frequency',True)]
    for scope,margin,method,ordering,bound in cases:
        path=BASE/f'{scope}-margin-{margin:g}.json'
        _,model,family=sc.load_family(path)
        label=f'{scope}-{margin:g}-{method}-{ordering}-bound{int(bound)}'
        print('START',label,flush=True)
        budget=old.Budget(**LIMITS)
        row=dict(case=label,scope=scope,margin_hex=margin.hex(),method=method,
            count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None)
        try:
            result=old.count(family,budget) if method=='previous' else new.count(family,budget,ordering,bound)
            row.update(count_state='EXACT',exact_count_decimal=str(result.pop('count')),result=result,
                       method=result['method'],certificate=result.get('certificate'))
            if margin==.25:
                assert row['exact_count_decimal']=={'group':'191532581516','episode':'17067800502243'}[scope]
        except old.CountUnresolved as exc: row['failure']=exc.details
        except old.solver.Unresolved as exc: row['failure']={'reason':'committed query limit','detail':str(exc)}
        row['statistics']=dict(budget.stats(),process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        side=sc.create(ROOT,path,row,sources,LIMITS)
        restored=sc.validate(ROOT,side,path)
        # Compare compact queries without demanding an expanded hypothesis list.
        witness=family.find()
        assert restored.contains(witness)==family.contains(witness)
        assert restored.classify()==family.classify()
        if witness: assert restored.invariant(witness[0])==family.invariant(witness[0])
        row['query_noninterference']='PASS'
        sidecars[label+'.cardinality.json']=side
        results.append(row)
        print(json.dumps({k:row[k] for k in ('case','count_state','exact_count_decimal','statistics')},sort_keys=True),flush=True)
    assert before=={p:sc.sha(ROOT/p) for p in before},'Historical bytes changed'
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    report=dict(format='KRAKEN_DRAFT2_COLUMN_COUNT_BENCHMARK_V1',
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        limits=LIMITS,cases=results,tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        historical_byte_hashes=before,historical_bytes_unchanged=True,
        source_hashes={str(p.relative_to(ROOT)):sc.sha(p) for p in sources},
        full_experiment_rerun=False,production_integration=False)
    output.mkdir(parents=True)
    (output/'benchmark.json').write_bytes(old.solver.canonical_bytes(report))
    (output/'tests.txt').write_text(log.getvalue())
    for name,data in sidecars.items(): (output/name).write_bytes(old.solver.canonical_bytes(data))
    (output/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
