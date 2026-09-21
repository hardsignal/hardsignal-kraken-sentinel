"""V1 query-only controls and target validation using committed cardinality sidecars."""
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import episode_component_tracking_v2_draft2_repl_e03_exact_queries as new
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import diagnose_episode_component_tracking_v2_draft2_repl_e03_queries as diagnostic
from regress_episode_component_tracking_v2_draft2_six_capture import TESTS
ROOT=diagnostic.ROOT;OUTPUT=diagnostic.OUTPUT
BASE=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression'
PATTERNS=TESTS+['test_episode_component_tracking_v2_draft2_repl_e02_margin1.py','test_episode_component_tracking_v2_draft2_repl_e03_queries.py']
FIELDS=['representation','family_complete_as_predicate','association','metrics','query_operations','query_calls','computational_limits','cardinality','states']

def write(path,value):
    with path.open('xb') as f:f.write(exact.canonical_bytes(value))

def sources():
    return [ROOT/p for p in staged.SOURCE_VERSIONS]+[Path(new.__file__).resolve(),Path(__file__).resolve(),Path(diagnostic.__file__).resolve()]+[ROOT/'tests'/p for p in PATTERNS]

def child(label,arm,order,target=False):
    old=json.loads((BASE/label/arm/'result.json').read_text());request=old['provenance']['request'];ref=request['saved_input']
    regression=json.loads((BASE/'regression.json').read_text());row=next(r for r in regression['cases'] if r['label']==label and r['arm']==arm)
    raw=json.loads((ROOT/ref['path']).read_text());episode=next(e for e in raw['episodes'] if e['capture']==row['capture'] and e['episode']==row['episode'])
    context=staged.git_context(ROOT);engine=new.engine_reference(ROOT,order)
    before={k:sc.sha(ROOT/request[k]['path']) for k in ('family','cardinality_sidecar')}
    start=time.perf_counter();result,stats=new.integrate(ROOT,request,episode['components'],context,engine);elapsed=time.perf_counter()-start
    assert all(sc.sha(ROOT/request[k]['path'])==h for k,h in before.items())
    for k in ['representation','family_complete_as_predicate','computational_limits','cardinality']:assert result[k]==old[k],k
    for k in ['provenance_validation','family_construction','cardinality_counting']:assert result['states'][k]==old['states'][k],k
    parity=True
    if not target:
        for k in FIELDS:assert result.get(k)==old.get(k),k
    else:
        # Previously completed membership/invariance sub-operations stay exact.
        for k,v in old['query_operations'].items():
            if v['state']=='EXACT':assert result['query_operations'][k]==v
    audit=dict(label=label,arm=arm,order=order,states=result['states'],query_operations=result['query_operations'],query_calls=result.get('query_calls'),
        association=result['association'],metrics=result['metrics'],cardinality=result['cardinality'],stats=stats,seconds=elapsed,
        memory_kib=diagnostic.memory(),family_sha256=before['family'],sidecar_sha256=before['cardinality_sidecar'],
        available_payload_parity=parity,payload_sha256=staged.digest({k:result.get(k) for k in FIELDS}),query_engine=engine)
    if target:
        write(OUTPUT/f'{arm}-{order}.result.json',result)
        tick=time.perf_counter();reproduced,repro_stats=new.reproduce(ROOT,result,episode['components'])
        audit.update(reproduction='BYTE_IDENTICAL',reproduction_seconds=time.perf_counter()-tick,reproduction_stats=repro_stats)
        if result['association'] is not None:
            from regress_episode_component_tracking_v2_draft2_limited import check_projection
            audit['projection_checks']=check_projection(result,episode,arm)
    return audit

def launch(label,arm,order,target=False):
    args=[sys.executable,str(Path(__file__).resolve()),'--child',label,arm,order]
    if target:args.append('--target')
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=400)
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)

def run():
    if (OUTPUT/'benchmark.json').exists():raise ValueError('New output required')
    for arm in ['margin-0.25','margin-1']:
        d=json.loads((OUTPUT/f'diagnostic-{arm}.json').read_text())
        assert d['states']['exact_queries']['state']=='COMPUTATION_UNRESOLVED'
    initial={p:sc.sha(ROOT/p) for p in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if p}
    context=staged.git_context(ROOT);log=io.StringIO();suite=unittest.TestSuite()
    for p in PATTERNS:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=p))
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUTPUT/'tests.txt').write_text(log.getvalue())
    if not tests.wasSuccessful():raise RuntimeError(log.getvalue())
    print('TESTS PASS',tests.testsRun,flush=True)
    prior=json.loads((BASE/'regression.json').read_text());controls=[]
    for row in prior['cases']:
        if row['arm']=='connected' or row['audit']['states']['exact_queries']['state']!='EXACT':continue
        for order in ('forward','reverse'):
            audit=launch(row['label'],row['arm'],order);controls.append(audit)
            print('CONTROL',row['label'],row['arm'],order,'PASS',audit['query_calls'],flush=True)
    write(OUTPUT/'controls.json',controls)
    targets=[]
    for arm in ('margin-0.25','margin-1'):
        for order in ('forward','reverse'):
            print('TARGET',arm,order,flush=True)
            audit=launch('C6-E03',arm,order,True);targets.append(audit);write(OUTPUT/f'{arm}-{order}.audit.json',audit)
            print('TARGET RESULT',arm,order,audit['states'],audit['query_calls'],audit['seconds'],flush=True)
        assert targets[-1]['payload_sha256']==targets[-2]['payload_sha256'],'Independent traversal answers differ'
    solved=all(x['states']['exact_queries']['state']=='EXACT' and x['states']['metric_projection']['state']=='COMPLETE' and x['reproduction']=='BYTE_IDENTICAL' for x in targets)
    assert all(sc.sha(ROOT/p)==h for p,h in initial.items())
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'])
    subprocess.run(['git','diff','--check'],check=True)
    report=dict(format='KRAKEN_DRAFT2_REPL_E03_QUERY_BENCHMARK_V1',decision='REPL_E03_QUERIES_EXACT_SOLVED' if solved else 'REPL_E03_QUERIES_STILL_UNRESOLVED',
        tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),control_evaluations=len(controls),control_families=len(controls)//2,
        targets=targets,source_hashes={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()},initial_tracked_hashes=initial,git_context=context,
        all_preexisting_tracked_files_unchanged=True,cardinalities_reused_without_recount=True,full_regression_rerun=False)
    write(OUTPUT/'benchmark.json',report)
    (OUTPUT/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.name}\n' for p in sorted(OUTPUT.iterdir()) if p.is_file()))
    print(report['decision'],flush=True)

if __name__=='__main__':
    # Counting entrypoints cannot be invoked by this benchmark or target reload.
    import episode_component_tracking_v2_draft2_exact_count as counter
    import episode_component_tracking_v2_draft2_e02_margin1_count as pivot
    import episode_component_tracking_v2_draft2_repl_e02_margin1_count as dyadic
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        with patch.object(counter,'count',side_effect=AssertionError('Query-only')),patch.object(pivot,'count',side_effect=AssertionError('Query-only')),patch.object(dyadic,'count',side_effect=AssertionError('Query-only')):
            print(json.dumps(child(sys.argv[2],sys.argv[3],sys.argv[4],'--target' in sys.argv),sort_keys=True))
    else:run()
