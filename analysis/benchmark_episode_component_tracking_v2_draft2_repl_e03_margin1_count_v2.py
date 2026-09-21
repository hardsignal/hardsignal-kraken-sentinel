"""V1 solved bounded-case counting controls, then REPL E02 target and staged validation."""
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_repl_e03_margin1_count_v2 as new
import episode_component_tracking_v2_draft2_repl_e03_exact_queries as queries
import episode_component_tracking_v2_draft2_exact_count as old
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_staged as staged
import diagnose_episode_component_tracking_v2_draft2_repl_e03_margin1_count as diagnostic

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=diagnostic.OUTPUT/'v2'
LIMITS=diagnostic.LIMITS
REGRESSION=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-regression'
TARGET=REGRESSION/'C6-E03/margin-1'
QUERY_RESULT=ROOT/'results/episode-component-tracking-v2-draft2-repl-e03-query-investigation/margin-1-forward.result.json'
from regress_episode_component_tracking_v2_draft2_six_capture import TESTS
PATTERNS=TESTS+['test_episode_component_tracking_v2_draft2_repl_e02_margin1.py','test_episode_component_tracking_v2_draft2_repl_e03_queries.py','test_episode_component_tracking_v2_draft2_repl_e03_margin1_count.py','test_episode_component_tracking_v2_draft2_repl_e03_margin1_count_v2.py']


def write(path,value):
    with path.open('xb') as f:f.write(old.solver.canonical_bytes(value))


def sources():
    return [ROOT/p for p in staged.SOURCE_VERSIONS]+[Path(new.__file__).resolve(),Path(new.dyadic.__file__).resolve(),Path(new.dyadic.previous.__file__).resolve(),Path(queries.__file__).resolve(),Path(__file__).resolve(),
            Path(diagnostic.__file__).resolve()]+[ROOT/'tests'/p for p in PATTERNS]


def child(path,ordering):
    start=time.perf_counter();_,_,family=sc.load_family(ROOT/path)
    load_seconds=time.perf_counter()-start
    current=[None];factor_trace=[]
    class TracedBudget(old.Budget):
        def check(self,states=0,transitions=0,**location):
            if current[0] is not None:current[0]['peak_live_states']=max(current[0]['peak_live_states'],states)
            return super().check(states,transitions,**location)
    budget=TracedBudget(**LIMITS)
    histogram=new.histogram
    def traced_hist(f,b,*a,**kw):
        row=dict(factor=family.factors.index(f),peak_live_states=0)
        factor_trace.append(row);current[0]=row
        try:return histogram(f,b,*a,**kw)
        finally:current[0]=None
    row=dict(count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None,
             family_path=path,family_sha256=sc.sha(ROOT/path),ordering=ordering,
             method=new.VERSION,load_seconds=load_seconds)
    try:
        with staged.deadline(LIMITS['max_seconds']),patch.object(new,'histogram',traced_hist):
            result=new.count(family,budget,ordering)
        result['factor_state_trace']=factor_trace
        row.update(count_state='EXACT',exact_count_decimal=str(result.pop('count')),
                   method=result['method'],certificate=result.get('certificate'),details=result)
    except old.CountUnresolved as exc:
        row['failure']=exc.details
    except old.solver.Unresolved as exc:
        row['failure']=dict(reason=str(exc),stage='counting')
    row['statistics']=dict(budget.stats(),process_peak_rss_kib=diagnostic.memory()['VmHWM'])
    return row


def launch(path,ordering):
    process=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',str(path),ordering],
                           cwd=ROOT,check=True,capture_output=True,text=True,timeout=90)
    return json.loads(process.stdout)


def integration(row,context):
    family_path=ROOT/row['family_path']
    side=sc.create(ROOT,family_path,row,sources(),LIMITS)
    side_path=OUTPUT/'target-margin-1.cardinality.json';write(side_path,side)
    sc.validate(ROOT,side,family_path)
    # Reject forged bindings without touching the family or sidecar on disk.
    for key in ('family_sha256','model_sha256'):
        tampered=dict(side);tampered[key]='0'*64
        try:sc.validate(ROOT,tampered,family_path)
        except ValueError:pass
        else:raise AssertionError('Tampered sidecar binding accepted')
    old_result=json.loads(QUERY_RESULT.read_text())
    old_request=old_result['provenance']['request']
    raw=json.loads((ROOT/old_request['saved_input']['path']).read_text())
    episode=next(e for e in raw['episodes'] if e['capture']=='BETWEEN-DEVICE-REPL-V1-20260919-024341' and e['episode']==3)
    request=staged.request(ROOT,episode['components'],staged.COMPACT,family_path,side_path,old_request['saved_input'])
    start=time.perf_counter()
    result,query_stats=queries.integrate(ROOT,request,episode['components'],context,old_result['query_engine'])
    elapsed=time.perf_counter()-start
    assert result['states']['metric_projection']['state']=='COMPLETE'
    for field in ('family_complete_as_predicate','association','metrics','query_operations','query_calls','computational_limits'):
        assert result[field]==old_result[field],field
    for phase in ('provenance_validation','family_construction','exact_queries','metric_projection'):
        assert result['states'][phase]==old_result['states'][phase],phase
    assert old_result['cardinality']['state']=='COMPUTATION_UNRESOLVED'
    assert result['cardinality']==dict(state='EXACT',value_decimal=row['exact_count_decimal'],reason=None)
    assert sc.sha(family_path)==old_request['family']['sha256']
    write(OUTPUT/'target-staged-result.json',result)
    start=time.perf_counter();reloaded,_=queries.reproduce(ROOT,json.loads((OUTPUT/'target-staged-result.json').read_text()),episode['components'])
    assert old.solver.canonical_bytes(reloaded)==old.solver.canonical_bytes(result)
    return dict(state='PASS',family_unchanged=True,exact_queries_unchanged=True,association_unchanged=True,
        metrics_unchanged=True,query_calls_unchanged=True,only_scientific_change='cardinality state/value/reason',
        expected_provenance_changes=['new sidecar path/hash and bound counter source','current checkpoint/batch context'],
        deterministic_reload=True,integration_seconds=elapsed,reload_seconds=time.perf_counter()-start,
        process_memory_kib=diagnostic.memory(),new_sidecar_sha256=sc.sha(side_path),
        new_result_sha256=sc.sha(OUTPUT/'target-staged-result.json'),
        old_result_sha256=sc.sha(QUERY_RESULT))


def run():
    OUTPUT.mkdir(exist_ok=False)
    if (OUTPUT/'benchmark.json').exists():raise ValueError('Benchmark output must be NEW')
    if not (diagnostic.OUTPUT/'diagnostic-pivot.json').exists():raise ValueError('Reproduce/diagnose baseline first')
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    before={p:sc.sha(ROOT/p) for p in names if p and (ROOT/p).is_file()}
    context=staged.git_context(ROOT)
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    suite=unittest.TestSuite();log=io.StringIO()
    for pattern in PATTERNS:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful():raise RuntimeError(log.getvalue())
    (OUTPUT/'tests.txt').write_text(log.getvalue())
    print('PASS',tests.testsRun,'tests; all solved compact regression counts are next, before the target',flush=True)
    regression=json.loads((REGRESSION/'regression.json').read_text());controls=[]
    for case in regression['cases']:
        if case['arm']=='connected' or case['counting']['state']!='EXACT':continue
        label=case['label']+'/'+case['arm']
        request=json.loads((REGRESSION/label/'request.json').read_text())
        expected=case['counting']['value_decimal']
        for ordering in ('forward','reverse'):
            result=launch(request['family']['path'],ordering)
            result.update(case=label,expected_count_decimal=expected,
                          parity=result['count_state']=='EXACT' and result['exact_count_decimal']==expected)
            controls.append(result)
            print('CONTROL',label,ordering,result['count_state'],result['exact_count_decimal'],flush=True)
    corrected=ROOT/'results/episode-component-tracking-v2-draft2-repl-e02-margin1-investigation/target-forward.json'
    reference=json.loads(corrected.read_text())
    for ordering in ('forward','reverse'):
        result=launch(reference['family_path'],ordering)
        result.update(case='REPL_E02_margin1_corrected',expected_count_decimal=reference['exact_count_decimal'],parity=result['count_state']=='EXACT' and result['exact_count_decimal']==reference['exact_count_decimal'])
        controls.append(result)
        print('CONTROL REPL_E02 corrected',ordering,result['count_state'],result['exact_count_decimal'],flush=True)
    write(OUTPUT/'control-counts.json',controls)
    if not all(r['parity'] for r in controls):
        raise AssertionError('Control validation failed; target is not trusted or evaluated')
    target_path=str((TARGET/'family.json').relative_to(ROOT));target=[]
    for ordering in ('forward','reverse'):
        print('TARGET',ordering,flush=True)
        row=launch(target_path,ordering);target.append(row)
        write(OUTPUT/f'target-{ordering}.json',row)
        print('TARGET RESULT',ordering,row['count_state'],row['exact_count_decimal'],row['statistics'],flush=True)
    solved=all(r['count_state']=='EXACT' for r in target) and target[0]['exact_count_decimal']==target[1]['exact_count_decimal']
    integration_result=integration(target[0],context) if solved else dict(state='NOT_RUN_TARGET_UNRESOLVED')
    assert all(sc.sha(ROOT/p)==digest for p,digest in before.items())
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert diff.returncode==0
    report=dict(format='KRAKEN_DRAFT2_REPL_E03_MARGIN1_COUNT_INVESTIGATION_V1',git_context=context,
        limits=LIMITS,tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        solved_control_families=len(controls)//2,control_evaluations=len(controls),all_controls_exact_and_equal=True,
        target=target,integration=integration_result,
        decision='REPL_E03_MARGIN1_EXACT_SOLVED' if solved else 'REPL_E03_MARGIN1_STILL_UNRESOLVED',
        original_file_hashes=before,all_preexisting_tracked_files_unchanged=True,
        source_hashes={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()},
        git_diff_check=dict(exit_code=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),
        full_164_case_regression_rerun=False,rf_capture=False,spectrum_detection=False,
        diagnostic_sha256=sc.sha(diagnostic.OUTPUT/'diagnostic-pivot.json'))
    write(OUTPUT/'benchmark.json',report)
    (OUTPUT/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.name}\n' for p in sorted(OUTPUT.iterdir()) if p.is_file()))
    print(report['decision'],flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        print(json.dumps(child(sys.argv[2],sys.argv[3]),sort_keys=True))
    else:run()
