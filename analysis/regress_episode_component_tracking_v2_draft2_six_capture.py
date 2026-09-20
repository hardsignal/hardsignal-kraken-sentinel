"""V1 bounded, predeclared saved-input regression; no detection or matrix runner."""
from contextlib import ExitStack, contextmanager
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import regress_episode_component_tracking_v2_draft2_limited as limited
import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_exact_count as previous
import episode_component_tracking_v2_draft2_e02_margin1_count as counter
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'results/episode-component-tracking-v2-draft2-six-capture-plan.json'
PLAN_SHA256='e6917efb66bc9eda0eddb94ec2d39a7c8c7271fcd1251b61d3eff70c17556728'
OLD=ROOT/'results/episode-component-tracking-v2-draft2-limited-regression'
TESTS=limited.TESTS+['test_episode_component_tracking_v2_draft2_e02_margin1_count.py',
                     'test_episode_component_tracking_v2_draft2_six_capture.py']
write=limited.write
memory=limited.memory
event=limited.event


def read_plan():
    if sc.sha(PLAN)!=PLAN_SHA256:raise ValueError('Frozen plan changed')
    p=json.loads(PLAN.read_text())
    for path,digest in [('input_artifact','input_sha256'),('specification','specification_sha256'),('counter','counter_sha256')]:
        if sc.sha(ROOT/p[path])!=p[digest]:raise ValueError('Frozen input/source changed: '+path)
    raw=json.loads((ROOT/p['input_artifact']).read_text())
    inventory={(e['capture'],e['episode']) for e in raw['episodes'] if e['capture'] in p['captures']}
    selected={(e['capture'],e['episode']) for e in p['selected']}
    if inventory!=selected or len(selected)!=p['episode_count'] or p['case_count']!=len(selected)*4:
        raise ValueError('Incomplete/duplicate episode inventory')
    if p['arms']!=['connected','margin-0','margin-0.25','margin-1']:raise ValueError('Arm mismatch')
    return p


def sources():
    return [ROOT/p for p in staged.SOURCE_VERSIONS]+[Path(__file__).resolve(),Path(counter.__file__).resolve(),
        Path(limited.__file__).resolve()]+[ROOT/'tests'/p for p in TESTS]


def control_map():
    p=json.loads(limited.PLAN.read_text())
    return {(e['capture'],e['episode']):e['label'] for e in p['selected']}


def limited_parity(result,selected,arm,family_path=None):
    label=control_map().get((selected['capture'],selected['episode']))
    if label is None:return 'NOT_APPLICABLE'
    old=json.loads((OLD/label/arm/'result.json').read_text())
    for field in ('representation','family_complete_as_predicate','association','metrics','query_operations','query_calls','computational_limits'):
        if result.get(field)!=old.get(field):raise ValueError('Limited scientific parity failure: '+field)
    for phase in ('provenance_validation','family_construction','exact_queries','metric_projection'):
        if result['states'][phase]!=old['states'][phase]:raise ValueError('Limited stage parity failure: '+phase)
    if label=='TPMS004-ordinary' and arm=='margin-1':
        expected=dict(state='EXACT',value_decimal='5788836',reason=None)
    else:expected=old['cardinality']
    if result['cardinality']!=expected:raise ValueError('Limited cardinality parity failure')
    if family_path and sc.sha(family_path)!=old['provenance']['request']['family']['sha256']:
        raise ValueError('Limited family byte mismatch')
    return 'PASS_E02_CARDINALITY_CORRECTION' if label=='TPMS004-ordinary' and arm=='margin-1' else 'PASS'


@contextmanager
def construction_limits(seconds):
    """Bound aggregate model validation/rebuild time inside unchanged integration."""
    used=[0.];validate=sc.validate;initialize=exact.EpisodeFamily.__init__
    def bounded(fn):
        def call(*a,**kw):
            remaining=seconds-used[0]
            if remaining<=0:raise exact.Unresolved('Family validation/reconstruction time exhausted')
            start=time.perf_counter()
            try:
                with staged.deadline(remaining):return fn(*a,**kw)
            finally:used[0]+=time.perf_counter()-start
        return call
    with patch.object(sc,'validate',bounded(validate)),patch.object(exact.EpisodeFamily,'__init__',bounded(initialize)):
        yield used


def polynomial_bytes(value):
    if isinstance(value,dict):
        values=[v for k,v in value.items() if k in ('peak_packed_bytes','polynomial_bytes','packed_polynomial_bytes','bytes_required') and isinstance(v,int)]
        return max(values+[polynomial_bytes(v) for v in value.values()]+[0])
    if isinstance(value,list):return max([polynomial_bytes(v) for v in value]+[0])
    return 0


def execute(manifest,selected,arm,directory,reload=False):
    plan=read_plan();episode=limited.saved_episode(plan,selected);fs=episode['components']
    started=time.perf_counter();measure={};family_path=card_path=None
    if reload:
        event('reproduction');saved=json.loads((directory/'result.json').read_text())
        with construction_limits(plan['family_construction_seconds']) as rebuild:
            staged.reproduce(ROOT,saved,fs)
        return dict(state='BYTE_IDENTICAL',seconds=time.perf_counter()-started,
                    reconstruction_seconds=rebuild[0],memory_kib=memory())
    if arm!='connected':
        event('family_construction');tick=time.perf_counter()
        family=limited.construct(fs,float(arm.removeprefix('margin-')),plan['family_construction_seconds'])
        measure['family_construction_seconds']=time.perf_counter()-tick
        family_path=directory/'family.json';write(family_path,family.artifact())
        event('cardinality_counting');budget=previous.Budget(**plan['count_limits'])
        outcome=dict(count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None,method=counter.VERSION)
        try:
            with staged.deadline(plan['count_limits']['max_seconds']):counted=counter.count(family,budget)
            outcome.update(count_state='EXACT',exact_count_decimal=str(counted.pop('count')),
                           method=counted['method'],certificate=counted.get('certificate'),details=counted)
        except previous.CountUnresolved as exc:outcome['failure']=exc.details
        except exact.Unresolved as exc:outcome['failure']=dict(reason=str(exc),stage='counting')
        outcome['statistics']=dict(budget.stats(),process_peak_rss_kib=memory()['VmHWM'])
        outcome['packed_polynomial_bytes']=polynomial_bytes(outcome)
        measure['counting_seconds']=outcome['statistics']['elapsed_seconds']
        write(directory/'count-outcome.json',outcome)
        event('sidecar_validation')
        with staged.deadline(plan['family_construction_seconds']):
            side=sc.create(ROOT,family_path,outcome,sources(),plan['count_limits'])
        card_path=directory/'cardinality.json';write(card_path,side)
    req=staged.request(ROOT,fs,staged.CONNECTED if arm=='connected' else staged.COMPACT,
        family_path,card_path,dict(path=plan['input_artifact'],sha256=plan['input_sha256']))
    write(directory/'request.json',req)
    event('staged_integration');tick=time.perf_counter()
    with construction_limits(plan['family_construction_seconds']) as rebuild:
        result=staged.integrate(ROOT,req,fs,manifest['git_context'],plan['query_limits'])
    measure['integration_seconds']=time.perf_counter()-tick
    measure['integration_reconstruction_seconds']=rebuild[0]
    write(directory/'result.json',result)
    event('projection_checks')
    # Do not make count failure block a valid single-fragment projection check.
    projection=limited.check_projection(result,episode,arm)
    parity=limited_parity(result,selected,arm,family_path)
    measure.update(total_seconds=time.perf_counter()-started,memory_kib=memory())
    return dict(states=result['states'],projection=projection,limited_parity=parity,
        cardinality=result['cardinality'],status=result['association']['status'] if result['association'] else None,
        primary=result['association']['primary'] if result['association'] else None,
        query_calls=result.get('query_calls'),metrics=result['metrics'],measurement=measure)


def worker(manifest_path,label,arm,reload):
    manifest=json.loads(manifest_path.read_text());plan=read_plan()
    if manifest['plan_sha256']!=PLAN_SHA256:raise ValueError('Manifest plan mismatch')
    for p,digest in manifest['sources'].items():
        if sc.sha(ROOT/p)!=digest:raise ValueError('Source changed: '+p)
    selected=next(e for e in plan['selected'] if e['label']==label)
    if arm not in plan['arms']:raise ValueError('Undeclared arm')
    directory=manifest_path.parent/label/arm
    with ExitStack() as stack:
        for obj,name in ((staged.historical,'detect'),(staged.historical,'load_inputs'),
                         (staged.historical,'represent'),(staged.historical,'solve_group'),(exact.Family,'materialize')):
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('Forbidden operation: '+name)))
        if reload:stack.enter_context(patch.object(counter,'count',side_effect=AssertionError('Reload must not recount')))
        try:data=execute(manifest,selected,arm,directory,reload)
        except Exception as exc:
            data=dict(state='REPRODUCTION_FAILED' if reload else 'COMPUTATION_UNRESOLVED',
                      reason=f'{type(exc).__name__}: {exc}',memory_kib=memory())
        write(directory/('reload.json' if reload else 'audit.json'),data)
        event('complete')


def launch(manifest_path,label,arm,plan,reload=False):
    directory=manifest_path.parent/label/arm
    command=[sys.executable,str(Path(__file__).resolve()),'--worker',str(manifest_path),label,arm]
    if reload:command.append('--reload')
    started=time.perf_counter();peak=0;reason=None
    with (directory/('reload.log' if reload else 'worker.log')).open('x') as log:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        while proc.poll() is None:
            observed=memory(proc.pid);peak=max(peak,observed.get('VmRSS',0),observed.get('VmHWM',0))
            if peak>plan['worker_peak_rss_limit_kib']:reason='Observed worker RSS ceiling exceeded'
            elif time.perf_counter()-started>plan['worker_timeout_seconds']:reason='Worker wall-clock limit exceeded'
            if reason:proc.kill();proc.wait();break
            time.sleep(.2)
    return dict(exit_code=proc.returncode,elapsed_seconds=time.perf_counter()-started,observed_peak_rss_kib=peak,reason=reason)


def passed(row):
    if row['worker']['exit_code']!=0 or row['worker']['reason']:return False
    if row.get('reload_worker',{}).get('exit_code')!=0 or row.get('reload_worker',{}).get('reason'):return False
    if row.get('reload',{}).get('state')!='BYTE_IDENTICAL':return False
    a=row.get('audit',{})
    if a.get('projection',{}).get('state')!='PASS':return False
    s=a.get('states',{})
    if s.get('provenance_validation',{}).get('state')!='VERIFIED' or s.get('metric_projection',{}).get('state')!='COMPLETE':return False
    if row['arm']!='connected':
        for k,v in [('family_construction','COMPLETE'),('exact_queries','EXACT'),('cardinality_counting','EXACT')]:
            if s.get(k,{}).get('state')!=v:return False
    return not row.get('resource_violations')


def run_case(manifest_path,selected,arm,plan):
    label=selected['label'];directory=manifest_path.parent/label/arm;directory.mkdir(parents=True)
    print('START',label,arm,flush=True);execution=launch(manifest_path,label,arm,plan)
    row=dict(selected,arm=arm,worker=execution,input_sha256=plan['input_sha256'],plan_sha256=PLAN_SHA256)
    row['audit']=json.loads((directory/'audit.json').read_text()) if (directory/'audit.json').exists() else dict(state='COMPUTATION_UNRESOLVED',reason=execution['reason'] or 'Worker failed; see log')
    if (directory/'result.json').exists():
        row['reload_worker']=launch(manifest_path,label,arm,plan,True)
        row['reload']=json.loads((directory/'reload.json').read_text()) if (directory/'reload.json').exists() else dict(state='COMPUTATION_UNRESOLVED',reason=row['reload_worker']['reason'] or 'Reload worker failed')
    else:row['reload']=dict(state='NOT_EVALUATED_NO_RESULT')
    count=json.loads((directory/'count-outcome.json').read_text()) if (directory/'count-outcome.json').exists() else None
    row['counting']=None if count is None else dict(state=count['count_state'],value_decimal=count['exact_count_decimal'],reason=count.get('failure'),statistics=count['statistics'],packed_polynomial_bytes=count['packed_polynomial_bytes'],method=count['method'])
    model=json.loads((directory/'family.json').read_text()) if (directory/'family.json').exists() else None
    row['family_sha256']=sc.sha(directory/'family.json') if model else None
    row['model_sha256']=model['model_sha256'] if model else None
    row['sidecar_sha256']=sc.sha(directory/'cardinality.json') if (directory/'cardinality.json').exists() else None
    row['resource_violations']=[]
    if count:
        limits=plan['count_limits'];stats=count['statistics']
        for key,limit in [('peak_states','max_states'),('transitions','max_transitions'),('elapsed_seconds','max_seconds')]:
            if stats[key]>limits[limit]:row['resource_violations'].append(key)
        if count['packed_polynomial_bytes']>limits['max_polynomial_bytes']:row['resource_violations'].append('packed_polynomial_bytes')
    for kind in ['worker','reload_worker']:
        if row.get(kind,{}).get('observed_peak_rss_kib',0)>plan['worker_peak_rss_limit_kib']:row['resource_violations'].append(kind+'_rss')
    result=json.loads((directory/'result.json').read_text()) if (directory/'result.json').exists() else None
    metrics=result.get('metrics') if result else None
    association=result.get('association') if result else None
    row['record']=dict(capture=selected['capture'],episode=selected['episode'],arm=arm,
        fragment_count=selected['original_fragment_count'],eligible_candidates_per_fragment=selected['eligible_per_fragment'],
        input_sha256=plan['input_sha256'],candidate_context_sha256=selected['fragments_sha256'],
        family_sha256=row['family_sha256'],model_sha256=row['model_sha256'],sidecar_sha256=row['sidecar_sha256'],
        stages=result['states'] if result else dict(state='UNAVAILABLE_EXPLICIT_FAILURE',reason=row['audit'].get('reason')),
        cardinality=result['cardinality'] if result else row['counting'],
        association_status=association['status'] if association else None,primary=association['primary'] if association else None,
        association_availability='COMPLETE' if association else 'UNAVAILABLE_EXPLICIT_FAILURE',
        persistent_track_count=metrics['persistent_path_count'] if metrics else None,
        possible_path_count=metrics['possible_path_count'] if metrics else None,
        invariant_membership_count=metrics['invariant_path_count'] if metrics else None,
        alternative_membership_count=metrics['alternative_path_count'] if metrics else None,
        query_calls=result.get('query_calls') if result else None,
        runtimes=row['audit'].get('measurement',{}),reproduction_seconds=row['reload'].get('seconds'),
        counting_transitions=count['statistics']['transitions'] if count else None,
        peak_live_states=count['statistics']['peak_states'] if count else None,
        packed_polynomial_bytes=count['packed_polynomial_bytes'] if count else None,
        worker_peak_rss_kib=max(execution['observed_peak_rss_kib'],row.get('reload_worker',{}).get('observed_peak_rss_kib',0),
            row['audit'].get('measurement',{}).get('memory_kib',{}).get('VmHWM',0),row['reload'].get('memory_kib',{}).get('VmHWM',0)))
    if row['record']['worker_peak_rss_kib']>plan['worker_peak_rss_limit_kib']:row['resource_violations'].append('worker_hwm')
    row['passed']=passed(row)
    row['failure']=None
    if not row['passed']:
        stages=row['audit'].get('states',{})
        bad={k:v for k,v in stages.items() if v['state'] not in ('COMPLETE','EXACT','VERIFIED','NOT_APPLICABLE_CONNECTED')}
        log=(directory/'worker.log').read_text().splitlines()
        row['failure']=dict(stages=bad,reason=row['audit'].get('reason') or execution['reason'],last_progress=log[-3:],resource_violations=row['resource_violations'],reproduction=row['reload'])
    write(directory/'case.json',row)
    print('DONE',label,arm,'PASS' if row['passed'] else 'FAIL',row['audit'].get('status'),row['counting']['value_decimal'] if count else None,flush=True)
    return row


def controls_valid(rows):
    known={('C1-E02','margin-0'):'1',('C1-E02','margin-0.25'):'32743',('C1-E02','margin-1'):'5788836',
           ('C4-E08','margin-0'):'2',('C4-E08','margin-0.25'):'17067800502243',('C4-E08','margin-1'):'378038954451765697490'}
    found={(r['label'],r['arm']):r for r in rows}
    return len(rows)==28 and all(r['passed'] and r['audit']['limited_parity'].startswith('PASS') for r in rows) and all(found.get(k,{}).get('counting',{}).get('value_decimal')==v for k,v in known.items())


def run(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT):raise ValueError('Output must be NEW and repository relative')
    plan=read_plan();before={p:sc.sha(ROOT/p) for p in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if p}
    context=staged.git_context(ROOT)
    if context['commit']!=plan['git_commit'] or subprocess.check_output(['git','diff','HEAD','--name-only']):raise ValueError('Checkpoint changed')
    suite=unittest.TestSuite();log=io.StringIO()
    for pattern in TESTS:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful():raise RuntimeError(log.getvalue())
    output.mkdir();(output/'tests.txt').write_text(log.getvalue())
    print('TESTS PASS',tests.testsRun,flush=True)
    manifest=dict(format='KRAKEN_DRAFT2_SIX_CAPTURE_BATCH_V1',plan_sha256=PLAN_SHA256,git_context=context,
                  sources={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()},historical_file_hashes=before)
    manifest_path=output/'batch.json';write(manifest_path,manifest)
    controls=control_map();first=[e for e in plan['selected'] if (e['capture'],e['episode']) in controls]
    remaining=[e for e in plan['selected'] if (e['capture'],e['episode']) not in controls]
    rows=[]
    for e in first:
        for arm in plan['arms']:rows.append(run_case(manifest_path,e,arm,plan))
    gate=controls_valid(rows);write(output/'preflight.json',dict(limited_cases=28,passed=gate,known_controls_passed=gate,case_refs=[r['label']+'/'+r['arm'] for r in rows]))
    print('PREFLIGHT',gate,flush=True)
    if gate:
        for e in remaining:
            for arm in plan['arms']:rows.append(run_case(manifest_path,e,arm,plan))
    else:
        for e in remaining:
            for arm in plan['arms']:rows.append(dict(e,arm=arm,passed=False,failure=dict(stage='PRE_RUN_VALIDATION',reason='Control gate failed; broader case not evaluated')))
    assert all(sc.sha(ROOT/p)==h for p,h in before.items())
    assert sc.sha(PLAN)==PLAN_SHA256
    subprocess.run(['git','diff','--check'],check=True)
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'])
    decision='READY_FOR_DRAFT2_FULL_MATRIX_REVIEW' if len(rows)==plan['case_count'] and all(r['passed'] for r in rows) else 'NOT_READY'
    report=dict(format='KRAKEN_DRAFT2_SIX_CAPTURE_REGRESSION_V1',decision=decision,plan_sha256=PLAN_SHA256,
        episode_count=plan['episode_count'],case_count=plan['case_count'],cases=rows,preflight_passed=gate,
        tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        all_preexisting_tracked_files_unchanged=True,original_file_count=len(before),full_matrix=False,
        git_commit=context['commit'],scientific_parameters_unchanged=True)
    write(output/'regression.json',report)
    (output/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.relative_to(output)}\n' for p in sorted(output.rglob('*')) if p.is_file()))
    print(decision,flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);m=parser.add_mutually_exclusive_group(required=True)
    m.add_argument('--output',type=Path);m.add_argument('--worker',nargs=3);parser.add_argument('--reload',action='store_true')
    args=parser.parse_args()
    if args.worker:worker(Path(args.worker[0]),args.worker[1],args.worker[2],args.reload)
    else:run(args.output)
