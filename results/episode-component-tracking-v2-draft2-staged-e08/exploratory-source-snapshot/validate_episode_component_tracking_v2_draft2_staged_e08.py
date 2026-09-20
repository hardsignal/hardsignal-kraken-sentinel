"""Saved TPMS-008 E08 only: staged integration/reload, never spectral detection.

Every output directory must be new. Committed family and cardinality files are
read directly; their committed manifests are checked. There is no matrix option.
"""
import argparse
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import episode_component_tracking_v2_draft2_staged as staged
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import episode_component_tracking_v2_draft2_column_count as counter

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT/'results/episode-component-tracking-v2-draft2-experiment'
FAMILIES = ROOT/'results/episode-component-tracking-v2-draft2-exact-solver-benchmark'
CARDS = ROOT/'results/episode-component-tracking-v2-draft2-margin1-investigation'
CAPTURE = 'PIPELINE-TPMS-008-20260918-003900'
TESTS = ['test_episode_component_tracking_v2_draft2_'+s+'.py' for s in
         ('staged','exact_solver','exact_count','column_count','cardinality_sidecar','margin1_investigation')]


def manifest_check(directory):
    for line in (directory/'files.sha256').read_text().splitlines():
        sha,name = line.split('  ',1)
        if sc.sha(directory/name) != sha:
            raise ValueError('Committed manifest mismatch: '+str(directory/name))


def inventory():
    paths = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    return {p:sc.sha(ROOT/p) for p in paths if p and (ROOT/p).is_file()}


def memory():
    return {k:int(v.split()[0]) for line in Path('/proc/self/status').read_text().splitlines()
            for k,v in [line.split(':',1)] if k in ('VmHWM','VmRSS')}


def episode():
    raw = json.loads((SAVED/'native__w200__connected.json').read_text())
    return next(e for e in raw['episodes'] if e['capture']==CAPTURE and e['episode']==8)


def child(manifest_path, label, reload):
    manifest = json.loads(manifest_path.read_text())
    fs = episode()['components']
    before = memory(); start = time.perf_counter()
    # Guard against accidental expansion, detection, input-spectrum loading or
    # cardinality recomputation anywhere in this staged real-data path.
    with patch.object(exact.Family,'materialize',side_effect=AssertionError('No expanded hypotheses')), \
         patch.object(staged.historical,'detect',side_effect=AssertionError('No detection')), \
         patch.object(staged.historical,'load_inputs',side_effect=AssertionError('No spectra')), \
         patch.object(counter,'count',side_effect=AssertionError('Consume saved cardinality')):
        if reload:
            saved = json.loads((manifest_path.parent/f'{label}.json').read_text())
            result = staged.reproduce(ROOT,saved,fs)
        else:
            result = staged.integrate(ROOT,manifest['requests'][label],fs,manifest['git_context'])
    return dict(result=result,measurement=dict(elapsed_seconds=time.perf_counter()-start,
                process_before_kib=before,process_after_kib=memory(),
                policy='Linux VmHWM current address-space high-water mark; imports excluded from timing, included in memory'))


def run(output):
    if output.exists():
        raise ValueError('Refusing to overwrite output')
    before = inventory()
    context = staged.git_context(ROOT)
    if subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT):
        raise ValueError('Historical tracked files must be unchanged')
    for directory in (SAVED,FAMILIES,CARDS):
        manifest_check(directory)
    log = io.StringIO();suite = unittest.TestSuite()
    for pattern in TESTS:
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    tested = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():
        raise RuntimeError(log.getvalue())
    print(f'{tested.testsRun} tests passed; saved E08 integration begins',flush=True)
    e = episode(); fs = e['components']
    input_ref = staged.reference(ROOT,SAVED/'native__w200__connected.json')
    requests = {'connected':staged.request(ROOT,fs,staged.CONNECTED,input_ref=input_ref)}
    for margin in exact.MARGINS:
        requests[f'margin-{margin:g}'] = staged.request(ROOT,fs,staged.COMPACT,
            FAMILIES/f'episode-margin-{margin:g}.json',
            CARDS/f'episode-{margin:g}-column-frequency-bound1.cardinality.json',input_ref)
    manifest = dict(format='KRAKEN_DRAFT2_STAGED_E08_INPUTS_V1',capture=CAPTURE,episode=8,
                    requests=requests,git_context=context,
                    runner_sha256=sc.sha(Path(__file__)),tests={p:sc.sha(ROOT/'tests'/p) for p in TESTS},
                    subprocess_timeout_seconds=150,query_limits=staged.QUERY_LIMITS,
                    original_fragment_count=len(fs),fragments_sha256=staged.digest(fs),
                    scientific_parameters_unchanged=True)
    output.mkdir(parents=True)
    manifest_path = output/'inputs.json'
    manifest_path.write_bytes(exact.canonical_bytes(manifest))
    (output/'tests.txt').write_text(log.getvalue())
    benchmark = json.loads((FAMILIES/'benchmark.json').read_text())
    expected = {f'margin-{m["margin"]:g}':m for m in benchmark['episode_margins']}
    counts = {'margin-0':'2','margin-0.25':'17067800502243','margin-1':'378038954451765697490'}
    results = {}
    for label in requests:
        print('START',label,flush=True)
        call = [sys.executable,str(Path(__file__).resolve()),'--child',label,'--manifest',str(manifest_path.resolve())]
        proc = subprocess.run(call,cwd=ROOT,check=True,capture_output=True,text=True,timeout=150)
        payload = json.loads(proc.stdout); result = payload['result']
        (output/f'{label}.json').write_bytes(exact.canonical_bytes(result))
        success = result['states']['metric_projection']['state']=='COMPLETE'
        findings = dict(measurement=payload['measurement'],states=result['states'],parity=False,
                        deterministic_reload=False,metric_summary=result['metrics'])
        if success:
            if label=='connected':
                expected_association = {k:v for k,v in e['association'].items()
                                        if k not in ('hypotheses','retained_hypothesis_count')}
                expected_association['original_fragment_count'] = len(fs)
                if result['association'] != expected_association:
                    raise AssertionError('Connected saved-result parity failed')
            else:
                a = result['association']; control = expected[label]
                assert a['status']==control['classification']['status']
                assert a['primary']==control['classification']['primary']
                assert a['persistent_tracks']==control['classification']['possible_persistent_paths']
                assert a['optimum_links']==control['maximum_links']
                assert a['optimum_cost']==control['minimum_cost']
                assert result['cardinality']['state']=='EXACT'
                assert result['cardinality']['value_decimal']==counts[label]
            findings['parity'] = True
            reload = subprocess.run(call+['--reload'],cwd=ROOT,check=True,capture_output=True,text=True,timeout=150)
            reproduced = json.loads(reload.stdout)
            assert exact.canonical_bytes(reproduced['result'])==exact.canonical_bytes(result)
            findings['deterministic_reload'] = True
            findings['reload_measurement'] = reproduced['measurement']
        results[label] = findings
        print(label,json.dumps(findings,sort_keys=True),flush=True)
    assert before == inventory(), 'Tracked historical files changed'
    diff = subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0 and not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT)
    ready = all(x['parity'] and x['deterministic_reload'] for x in results.values())
    report = dict(format='KRAKEN_DRAFT2_STAGED_E08_VALIDATION_V1',
        readiness='READY_FOR_LIMITED_MULTI_EPISODE_REGRESSION' if ready else 'NOT_READY',
        cases=results,tests=dict(run=tested.testsRun,failures=len(tested.failures),errors=len(tested.errors)),
        historical_file_hashes=before,historical_bytes_unchanged=True,
        git_context=context,git_status_after=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
        git_diff_check=dict(exit_code=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),
        python=sys.version,platform=platform.platform(),
        input_manifest_sha256=sc.sha(manifest_path),runner_sha256=sc.sha(Path(__file__)),
        rf_capture=False,spectral_detection=False,full_matrix=False,cardinality_recomputed=False,
        full_matrix_readiness=False,scope='Saved TPMS-008 E08 only, plus exhaustive small fixture validation')
    (output/'validation.json').write_bytes(exact.canonical_bytes(report))
    (output/'files.sha256').write_text(''.join(f'{sc.sha(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()))
    print(report['readiness'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--child',choices=['connected','margin-0','margin-0.25','margin-1'])
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--reload',action='store_true')
    args=parser.parse_args()
    if args.child:
        print(json.dumps(child(args.manifest,args.child,args.reload),sort_keys=True))
    else:
        run(args.output)
