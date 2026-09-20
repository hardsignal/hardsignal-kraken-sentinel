"""Execute the hash-pinned, predeclared 28-case saved-candidate regression only."""
from contextlib import ExitStack
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_column_count as counter
import episode_component_tracking_v2_draft2_exact_count as previous

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'results/episode-component-tracking-v2-draft2-limited-regression-plan.json'
PLAN_SHA256 = '7abc15ebb82631adca9043640dcaeb17c7beb2cc238c53bdfd02b5ddd8e27425'
E08_FAMILIES = ROOT/'results/episode-component-tracking-v2-draft2-exact-solver-benchmark'
E08_CARDS = ROOT/'results/episode-component-tracking-v2-draft2-margin1-investigation'
E08_RESULTS = ROOT/'results/episode-component-tracking-v2-draft2-staged-e08-verified'
TESTS = ['test_episode_component_tracking_v2_draft2_'+name+'.py' for name in
         ('limited_regression','staged','exact_solver','exact_count','column_count',
          'cardinality_sidecar','margin1_investigation')]


def write(path, value):
    with Path(path).open('xb') as f:
        f.write(exact.canonical_bytes(value))


def read_plan():
    if sc.sha(PLAN) != PLAN_SHA256:
        raise ValueError('Predeclared plan changed')
    plan = json.loads(PLAN.read_text())
    if sc.sha(ROOT/plan['input_artifact']) != plan['input_sha256']:
        raise ValueError('Saved input changed')
    if sc.sha(ROOT/plan['specification']) != plan['specification_sha256']:
        raise ValueError('Frozen specification changed')
    return plan


def saved_episode(plan, selected):
    raw = json.loads((ROOT/plan['input_artifact']).read_text())
    episode = next(e for e in raw['episodes'] if (e['capture'],e['episode']) ==
                   (selected['capture'],selected['episode']))
    if staged.digest(episode['components']) != selected['fragments_sha256']:
        raise ValueError('Selected candidate context changed')
    return episode


def memory(pid='self'):
    try:
        return {k:int(v.split()[0]) for line in Path(f'/proc/{pid}/status').read_text().splitlines()
                for k,v in [line.split(':',1)] if k in ('VmHWM','VmRSS')}
    except FileNotFoundError:
        return {}


def event(stage):
    print(json.dumps(dict(stage=stage)),flush=True)


def sources():
    return [ROOT/p for p in staged.SOURCE_VERSIONS] + [Path(__file__).resolve(),
            ROOT/'tests/test_episode_component_tracking_v2_draft2_limited_regression.py']


def blocked(plan, selected, arm, context, phase, reason):
    """A preparation failure cannot manufacture a family, count or association."""
    states = {k:staged.state('NOT_EVALUATED') for k in
              ('family_construction','exact_queries','cardinality_counting','metric_projection')}
    states['provenance_validation'] = staged.state('SAVED_INPUT_AND_PLAN_VERIFIED')
    states[phase] = staged.state('COMPUTATION_UNRESOLVED',reason)
    states['metric_projection'] = staged.state('BLOCKED_BY_PREPARATION_FAILURE')
    return dict(format='KRAKEN_DRAFT2_LIMITED_PREPARATION_FAILURE_V1',
        representation=staged.COMPACT,states=states,family_complete_as_predicate=False,
        association=None,metrics=None,cardinality=None,query_calls=None,
        provenance=dict(plan_sha256=PLAN_SHA256,input_sha256=plan['input_sha256'],
            specification_sha256=plan['specification_sha256'],
            fragments_sha256=selected['fragments_sha256'],capture=selected['capture'],
            episode=selected['episode'],arm=arm,git=context,
            sources={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()}))


def check_projection(result, episode, arm):
    """Check all defined outputs; never turn an unresolved field into an empty set."""
    fs = episode['components'];a = result['association']
    if a is None:
        assert result['metrics'] is None
        assert result['states']['exact_queries']['state'] != 'EXACT'
        return dict(state='UNAVAILABLE_EXPLICIT_FAILURE')
    assert a['original_fragment_count'] == len(fs)
    if arm == 'connected':
        reference = {k:v for k,v in episode['association'].items()
                     if k not in ('hypotheses','retained_hypothesis_count')}
        reference['original_fragment_count'] = len(fs)
        assert a == reference, 'Connected historical parity failed'
        return dict(state='PASS',parity='SAVED_CONNECTED_COMPLETE_OUTPUT')
    nodes = {c['candidate_id']:c for f in fs for c in f['components'] if c['eligible_for_tracking']}
    invariant = set(map(tuple,a['invariant_membership']))
    alternative = set(map(tuple,a['alternative_membership']))
    assert not invariant & alternative
    union = invariant | alternative
    assert set(a['candidate_membership_alternatives']) == set(nodes)
    for c,paths in a['candidate_membership_alternatives'].items():
        assert paths == sorted([list(p) for p in union if c in p]) and paths
    for p in union:
        cs = [nodes[c] for c in p]
        assert len({c['fragment_index'] for c in cs}) == len(cs)
        assert max(c['frequency_hz'] for c in cs)-min(c['frequency_hz'] for c in cs) <= 100
        assert all(b['fragment_index']-a['fragment_index'] in (1,2) and
                   abs(b['frequency_hz']-a['frequency_hz']) <= 50 for a,b in zip(cs,cs[1:]))
    assert a['support_coverage'] == [dict(members=list(p),support=len(p),coverage=len(p)/len(fs),coherent=True)
                                      for p in sorted(union)]
    persistent = {p for p in union if len(p)>=3 and len(p)/len(fs)>=.6}
    assert a['persistent_tracks'] == sorted(map(list,persistent))
    if a['primary'] is not None:
        assert persistent == {tuple(a['primary'])} and tuple(a['primary']) in invariant
    if len(fs)<=2:
        assert not persistent and a['primary'] is None
        assert a['status'] in ('INSUFFICIENT_SUPPORT','AMBIGUOUS_ASSOCIATION','UNUSABLE_INPUT','NO_ELIGIBLE_COMPONENT')
    if len(fs)==1:
        assert result['cardinality'] == dict(state='EXACT',value_decimal='1',reason=None)
        assert a['status']=='INSUFFICIENT_SUPPORT' and not alternative
    assert a['structural_constraint_violations']==0
    assert result['metrics']['possible_path_count']==len(union)
    assert result['metrics']['original_fragment_count']==len(fs)
    return dict(state='PASS',parity='EXACT_QUERY_PROJECTION_CONSISTENCY')


def reference_parity(result, selected, arm):
    if result['association'] is None:
        return 'UNAVAILABLE_EXPLICIT_FAILURE'
    if selected['label']=='TPMS008-control':
        control=json.loads((E08_RESULTS/f'{arm}.json').read_text())
        assert result['association']==control['association']
        assert result['metrics']==control['metrics']
        assert result['cardinality']==control['cardinality']
        return 'COMMITTED_STAGED_E08_EXACT_SCIENTIFIC_PAYLOAD'
    if arm=='margin-0':
        path=ROOT/'results/episode-component-tracking-v2-draft2-experiment/native__w200__paths_margin0.partial.json'
        # Compare stored derived outputs only; never enumerate the stored arrays.
        rows=json.loads(path.read_text())['episodes']
        control=next((e for e in rows if (e['capture'],e['episode']) ==
                      (selected['capture'],selected['episode'])),None)
        if control is not None:
            old=control['association']
            expected={k:v for k,v in old.items() if k not in ('hypotheses','retained_hypothesis_count')}
            expected['original_fragment_count']=selected['original_fragment_count']
            assert result['association']==expected, 'Stored margin-zero derived-output mismatch'
            if result['cardinality']['state']=='EXACT':
                assert result['cardinality']['value_decimal']==str(old['retained_hypothesis_count'])
            return 'HISTORICAL_MARGIN_ZERO_DERIVED_FIELDS'
    return 'NO_COMPLETE_HISTORICAL_COMPACT_REFERENCE'


def construct(fs, margin, seconds):
    with staged.deadline(seconds):
        return exact.EpisodeFamily([c for f in fs for c in f['components'] if c['eligible_for_tracking']],len(fs),margin)


def execute_case(manifest, selected, arm, directory, reload=False):
    plan=read_plan();episode=saved_episode(plan,selected);fs=episode['components']
    context=manifest['git_context'];start=time.perf_counter();measure={}
    if reload:
        saved=json.loads((directory/'result.json').read_text())
        event('reproduction')
        if saved['format']==staged.FORMAT:
            result=staged.reproduce(ROOT,saved,fs)
        else:
            try:
                construct(fs,float(arm.removeprefix('margin-')),plan['family_construction_seconds'])
            except exact.Unresolved as exc:
                result=blocked(plan,selected,arm,context,'family_construction',str(exc))
            else:
                raise ValueError('Previously unresolved preparation now completed')
            if exact.canonical_bytes(result)!=exact.canonical_bytes(saved):
                raise ValueError('Preparation-failure reproduction differs')
        return dict(state='BYTE_IDENTICAL',measurement=dict(elapsed_seconds=time.perf_counter()-start,memory_kib=memory()))
    family_path=card_path=None
    if arm!='connected':
        margin=float(arm.removeprefix('margin-'))
        if selected['label']=='TPMS008-control':
            event('reuse_committed_E08_artifacts')
            family_path=E08_FAMILIES/f'episode-margin-{margin:g}.json'
            card_path=E08_CARDS/f'episode-{margin:g}-column-frequency-bound1.cardinality.json'
        else:
            event('family_construction');tick=time.perf_counter()
            try:
                family=construct(fs,margin,plan['family_construction_seconds'])
            except exact.Unresolved as exc:
                result=blocked(plan,selected,arm,context,'family_construction',str(exc))
                write(directory/'result.json',result)
                return dict(states=result['states'],projection=check_projection(result,episode,arm),
                            measurement=dict(total_seconds=time.perf_counter()-start,memory_kib=memory()))
            measure['family_construction_seconds']=time.perf_counter()-tick
            family_path=directory/'family.json';write(family_path,family.artifact())
            event('cardinality_counting');budget=previous.Budget(**plan['count_limits'])
            outcome=dict(count_state='COMPUTATION_UNRESOLVED',exact_count_decimal=None,method='unchanged column counter with committed IEEE fallback')
            try:
                with staged.deadline(plan['count_limits']['max_seconds']):
                    counted=counter.count(family,budget)
                outcome.update(count_state='EXACT',exact_count_decimal=str(counted['count']),
                               method=counted['method'],certificate=counted.get('certificate'))
            except previous.CountUnresolved as exc:
                outcome['failure']=exc.details
            except exact.Unresolved as exc:
                outcome['failure']=dict(reason=str(exc),stage='counting')
            outcome['statistics']=dict(budget.stats(),process_peak_rss_kib=memory()['VmHWM'])
            measure['counting_seconds']=outcome['statistics']['elapsed_seconds']
            write(directory/'count-outcome.json',outcome)
            event('sidecar_validation')
            card=sc.create(ROOT,family_path,outcome,sources(),plan['count_limits'])
            card_path=directory/'cardinality.json';write(card_path,card)
    request=staged.request(ROOT,fs,staged.CONNECTED if arm=='connected' else staged.COMPACT,
                           family_path,card_path,dict(path=plan['input_artifact'],sha256=plan['input_sha256']))
    write(directory/'request.json',request)
    event('staged_integration');tick=time.perf_counter()
    result=staged.integrate(ROOT,request,fs,context,plan['query_limits'])
    measure['integration_seconds']=time.perf_counter()-tick
    write(directory/'result.json',result)
    event('projection_checks')
    projection=check_projection(result,episode,arm)
    parity=reference_parity(result,selected,arm)
    if result['cardinality'] is not None and result['cardinality']['state']=='COMPUTATION_UNRESOLVED':
        assert result['cardinality']['value_decimal'] is None
        assert result['family_complete_as_predicate']
    measure.update(total_seconds=time.perf_counter()-start,memory_kib=memory())
    return dict(states=result['states'],projection=projection,reference_parity=parity,
                cardinality=result['cardinality'],status=result['association']['status'] if result['association'] else None,
                primary=result['association']['primary'] if result['association'] else None,
                query_calls=result.get('query_calls'),metrics=result['metrics'],measurement=measure)


def worker(manifest_path,label,arm,reload):
    manifest=json.loads(manifest_path.read_text());plan=read_plan()
    assert manifest['plan_sha256']==PLAN_SHA256
    for p,digest in manifest['sources'].items():
        if sc.sha(ROOT/p)!=digest:raise ValueError('Regression source changed')
    selected=next(e for e in plan['selected'] if e['label']==label)
    if arm not in plan['arms']:raise ValueError('Undeclared arm')
    directory=manifest_path.parent/label/arm
    with ExitStack() as stack:
        for obj,name in ((staged.historical,'detect'),(staged.historical,'load_inputs'),
                         (staged.historical,'represent'),(staged.historical,'solve_group'),(exact.Family,'materialize')):
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('Forbidden regression operation: '+name)))
        if label=='TPMS008-control' or reload:
            stack.enter_context(patch.object(counter,'count',side_effect=AssertionError('No recount of bound sidecar')))
        try:
            data=execute_case(manifest,selected,arm,directory,reload)
        except Exception as exc:
            if not reload:raise
            data=dict(state='REPRODUCTION_FAILED',reason=f'{type(exc).__name__}: {exc}')
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
            peak=max(peak,memory(proc.pid).get('VmRSS',0))
            if peak>plan['worker_peak_rss_limit_kib']:
                reason='Predeclared worker resident-memory limit exceeded'
            elif time.perf_counter()-started>plan['worker_timeout_seconds']:
                reason='Predeclared worker wall-clock limit exceeded'
            if reason:
                proc.kill();proc.wait();break
            time.sleep(.2)
    return dict(exit_code=proc.returncode,elapsed_seconds=time.perf_counter()-started,
                observed_peak_rss_kib=peak,reason=reason)


def ready(rows):
    plan=read_plan()
    if {(r['label'],r['arm']) for r in rows} != {(e['label'],a) for e in plan['selected'] for a in plan['arms']} or len(rows)!=plan['case_count']:
        return False
    for row in rows:
        audit=row.get('audit',{})
        if row['worker']['exit_code']!=0 or row.get('reload',{}).get('state')!='BYTE_IDENTICAL':return False
        if audit.get('projection',{}).get('state')!='PASS':return False
        if audit['states']['provenance_validation']['state']!='VERIFIED':return False
        if row['arm']!='connected':
            for phase,value in (('family_construction','COMPLETE'),('exact_queries','EXACT'),
                                ('cardinality_counting','EXACT'),('metric_projection','COMPLETE')):
                if audit['states'][phase]['state']!=value:return False
    return True


def run(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Output must be NEW and repository-relative for sidecar binding')
    plan=read_plan()
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    before={p:sc.sha(ROOT/p) for p in paths if p and (ROOT/p).is_file()}
    context=staged.git_context(ROOT)
    if context['commit']!=plan['git_commit'] or subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT):
        raise ValueError('Checkpoint or historical files changed')
    log=io.StringIO();suite=unittest.TestSuite()
    for pattern in TESTS:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tests.wasSuccessful():raise RuntimeError(log.getvalue())
    print(f'PASS {tests.testsRun} tests; executing fixed plan {PLAN_SHA256}',flush=True)
    output.mkdir();(output/'tests.txt').write_text(log.getvalue())
    manifest=dict(format='KRAKEN_DRAFT2_LIMITED_REGRESSION_BATCH_V1',plan_sha256=PLAN_SHA256,
        git_context=context,sources={str(p.relative_to(ROOT)):sc.sha(p) for p in sources()},
        tests={p:sc.sha(ROOT/'tests'/p) for p in TESTS},historical_file_hashes=before)
    manifest_path=output/'batch.json';write(manifest_path,manifest);rows=[]
    for selected in plan['selected']:
        for arm in plan['arms']:
            label=selected['label'];directory=output/label/arm;directory.mkdir(parents=True)
            print('START',label,arm,flush=True)
            execution=launch(manifest_path,label,arm,plan)
            row=dict(label=label,arm=arm,worker=execution)
            if (directory/'audit.json').exists():row['audit']=json.loads((directory/'audit.json').read_text())
            else:
                row['audit']=dict(state='COMPUTATION_UNRESOLVED' if execution['reason'] else 'IMPLEMENTATION_ERROR',
                    reason=execution['reason'] or 'Worker failed; see worker.log',
                    last_progress=(directory/'worker.log').read_text()[-4000:])
            if (directory/'result.json').exists():
                row['reload_worker']=launch(manifest_path,label,arm,plan,True)
                row['reload']=json.loads((directory/'reload.json').read_text()) if (directory/'reload.json').exists() else dict(state='COMPUTATION_UNRESOLVED',reason=row['reload_worker']['reason'] or 'Reload worker failed')
            else:row['reload']=dict(state='NOT_EVALUATED_NO_RESULT')
            rows.append(row);write(directory/'case.json',row)
            audit=row['audit']
            print(label,arm,json.dumps(dict(states=audit.get('states'),cardinality=audit.get('cardinality'),
                 status=audit.get('status'),queries=audit.get('query_calls'),reload=row['reload']['state'],
                 seconds=execution['elapsed_seconds']),sort_keys=True),flush=True)
    assert all(sc.sha(ROOT/p)==v for p,v in before.items()),'Historical bytes changed'
    assert sc.sha(PLAN)==PLAN_SHA256
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0 and not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    report=dict(format='KRAKEN_DRAFT2_LIMITED_REGRESSION_V1',plan_sha256=PLAN_SHA256,
        selected=plan['selected'],cases=rows,tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        readiness='READY_FOR_BOUNDED_SIX_CAPTURE_REGRESSION' if ready(rows) else 'NOT_READY',
        all_preexisting_tracked_files_unchanged=True,original_file_count=len(before),
        git_head=context['commit'],git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
        git_diff_check=dict(exit_code=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),
        full_matrix=False,spectrum_detection=False,rf_capture=False,scientific_parameters_unchanged=True)
    write(output/'regression.json',report)
    (output/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.relative_to(output)}\n' for p in sorted(output.rglob('*')) if p.is_file()))
    print(report['readiness'],flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output',type=Path)
    mode.add_argument('--worker',nargs=3,metavar=('MANIFEST','LABEL','ARM'))
    parser.add_argument('--reload',action='store_true')
    args=parser.parse_args()
    if args.worker:worker(Path(args.worker[0]),args.worker[1],args.worker[2],args.reload)
    else:run(args.output)
