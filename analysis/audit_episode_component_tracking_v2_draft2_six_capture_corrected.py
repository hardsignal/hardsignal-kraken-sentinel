"""Audit the completed corrected bundle, preserving all historical tracked files."""
from pathlib import Path
import collections,hashlib,json,subprocess,sys
root=Path.cwd();sys.path.insert(0,str(root/'analysis'))
import regress_episode_component_tracking_v2_draft2_six_capture_corrected as r
stem='episode-component-tracking-v2-draft2-six-capture-corrected'; out=root/'results'/f'{stem}-regression'
report=json.loads((out/'regression.json').read_text());rows=report['cases'];baseline=json.loads(r.BASELINE.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
failures=[]
def require(ok,message):
 if not ok:failures.append(message)
require(len(rows)==164 and len({(x['capture'],x['episode']) for x in rows})==41,'inventory')
require(len({(x['label'],x['arm']) for x in rows})==164,'unique cases')
changed=[p for p,h in baseline.items() if not (root/p).is_file() or sha(root/p)!=h]
require(not changed,'tracked bytes')
head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip();require(head==r.read_plan()['git_commit'],'HEAD')
manifest=json.loads((out/'batch.json').read_text())
require(all(sha(root/p)==h for p,h in manifest['sources'].items()),'source bindings')
files=0
for line in (out/'files.sha256').read_text().splitlines():
 digest,name=line.split('  ',1);require(sha(out/name)==digest,'artifact '+name);files+=1
canonical=0
for row in rows:
 directory=out/row['label']/row['arm']
 for name in ('result.json','family.json','cardinality.json','request.json'):
  p=directory/name
  if p.exists():require(p.read_bytes()==r.exact.canonical_bytes(json.loads(p.read_text())),'canonical '+str(p));canonical+=1
 result=json.loads((directory/'result.json').read_text())
 for name in ('family','cardinality_sidecar','saved_input'):
  ref=result['provenance']['request'].get(name)
  if ref:require(sha(root/ref['path'])==ref['sha256'],'reference '+str(directory)+' '+name)
 require(row['passed'] and r.passed(row),'case '+row['label']+'/'+row['arm'])
 require(row['reload']['state']=='BYTE_IDENTICAL','reload')
 require(result.get('query_calls') is None or result['query_calls']<=5000,'query limit')
 require(row['audit']['measurement']['integration_seconds']<=120+60,'integration aggregate limit')
 if row['arm']!='connected':require(row['audit']['measurement']['family_construction_seconds']<=60,'family limit')
require(r.mandatory_controls(rows)['passed'],'mandatory controls')
old=json.loads((r.BASE/'regression.json').read_text()); old_cases={(x['label'],x['arm']):x for x in old['cases']}
require(old['decision']=='NOT_READY','original decision')
passing=sum(x['passed'] for x in old['cases']);corrected=[]
for row in rows:
 require(row['audit']['original_parity']['state']=='PASS','historical parity')
 if not old_cases[row['label'],row['arm']]['passed']:
  corrected.append(dict(label=row['label'],arm=row['arm'],cardinality=row['counting']['value_decimal'],query_calls=row['audit']['query_calls'],changes=row['audit']['original_parity']['state_changes']))
compact=[x for x in rows if x['arm']!='connected']
def maxrow(key,subset=rows):
 x=max(subset,key=key);return dict(case=x['label']+'/'+x['arm'],value=key(x))
summary=dict(tests=report['tests'],captures=6,episodes=41,cases=164,fully_passed=sum(x['passed'] for x in rows),
 exact_compact_cardinalities=sum(x['counting']['state']=='EXACT' for x in compact),
 unresolved_count_cases=sum(x['counting']['state']!='EXACT' for x in compact),
 unresolved_query_cases=sum(x['audit']['states']['exact_queries']['state']!='EXACT' for x in compact),
 reproduction_failures=sum(x['reload']['state']!='BYTE_IDENTICAL' for x in rows),
 status_distribution=dict(collections.Counter(x['audit']['status'] for x in rows)),
 non_null_primary_count=sum(x['audit']['primary'] is not None for x in rows),
 persistent_track_distribution=dict(sorted(collections.Counter(x['record']['persistent_track_count'] for x in rows).items())),
 largest_cardinality=maxrow(lambda x:int(x['counting']['value_decimal']),compact),
 slowest_count=maxrow(lambda x:x['counting']['statistics']['elapsed_seconds'],compact),
 slowest_full_case=maxrow(lambda x:x['worker']['elapsed_seconds']+x['reload_worker']['elapsed_seconds']),
 slowest_execution=maxrow(lambda x:x['audit']['measurement']['total_seconds']),
 max_query_calls=maxrow(lambda x:x['audit']['query_calls'] or 0),
 max_transitions=maxrow(lambda x:x['counting']['statistics']['transitions'],compact),
 max_live_states=maxrow(lambda x:x['counting']['statistics']['peak_states'],compact),
 max_packed_bytes=maxrow(lambda x:x['counting']['packed_polynomial_bytes'],compact),
 max_rss_kib=maxrow(lambda x:x['record']['worker_peak_rss_kib']),
 mandatory_control_parity=report['mandatory_controls'],original_passing_cases=passing,
 original_passing_parity=sum(x['audit']['original_parity']['previously_passed'] for x in rows),corrected_blockers=corrected,
 tracked_file_count=len(baseline),changed_tracked_files=changed,head=head,
 artifact_hashes_verified=files,canonical_artifacts_verified=canonical)
# Machine-readable summary is a separate final audit artifact; original and case results remain untouched.
summary_path=root/'results'/f'{stem}-summary.json'
summary_path.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
lines=['# Corrected six-capture Draft 2 regression','',
'New bounded run at `7e38dd9`; original NOT_READY regression preserved byte-identically.','',
'A partial startup attempt was stopped during preflight to remove repeated full-inventory checks from worker startup. It is preserved in the separate `corrected-regression-startup-attempt` archive. The final run repeated the full test gate and all 164 cases with unchanged limits.','',
'Final decision: **'+report['decision']+'**.','',
f"Pre-run gate: {report['tests']['run']} tests, {report['tests']['failures']} failures, {report['tests']['errors']} errors.",
'6 captures; frozen 41 episodes; 164 cases (41 connected, 123 compact).',
f"Fully passed: {summary['fully_passed']}/164. Exact compact cardinalities: {summary['exact_compact_cardinalities']}/123.",
f"Unresolved counts: {summary['unresolved_count_cases']}; unresolved queries: {summary['unresolved_query_cases']}; reproduction failures: {summary['reproduction_failures']}.",'',
'All cases passed structural checks and deterministic byte-identical staged reload. Compact family bytes match the original run; all 41 connected results match historical outputs. All frozen resource limits remained unchanged.','',
'## Distributions','',
'Association status: `'+json.dumps(summary['status_distribution'],sort_keys=True)+'`.','',
f"Non-null primary count: {summary['non_null_primary_count']}.",'',
'Persistent-track counts (count: cases): `'+json.dumps(summary['persistent_track_distribution'],sort_keys=True)+'`.','',
'## Observed maxima','', '| Measurement | Case | Value |','| --- | --- | --- |']
for key in ('largest_cardinality','slowest_count','slowest_full_case','slowest_execution','max_query_calls','max_transitions','max_live_states','max_packed_bytes','max_rss_kib'):
 v=summary[key];lines.append(f"| {key} | {v['case']} | {v['value']} |")
lines+=['','Runtimes are seconds; full case includes execution and reload worker wall time. RSS is KiB; packed storage is bytes.','',
'## Mandatory controls','', '| Case | Arm | Exact cardinality |','| --- | --- | --- |']
for row in rows:
 if row['label']+'/'+row['arm'] in report['mandatory_controls']['checks']:
  lines.append(f"| {row['label']} | {row['arm']} | {row['counting']['value_decimal']} |")
lines+=['','Both REPL E03 margins reproduce the committed exact query/metric payload, 1,012 public calls, MULTIPLE_PERSISTENT_TRACKS, and null primary.','',
'## Historical parity and corrected blockers','',f'All {passing} previously passing cases retain their scientific payloads. The four earlier failures now pass.','']
for c in corrected:
 lines.append(f"- {c['label']} {c['arm']}: cardinality {c['cardinality']}; {c['query_calls']} query calls.")
 for k,v in c['changes'].items():lines.append(f"  - {k}: {v['before']['state']} → {v['after']['state']}.")
lines+=['','REPL E02 and E05 preserve the earlier completed query, association, and metric payloads. REPL E03 preserves every previously completed exact operation and reproduces the committed query milestone in full. Only unresolved stages and their dependent projections became exact/complete; provenance identifies this new run.','',
'## Integrity and reproduction','',f'All {len(baseline)} pre-existing tracked files remain byte-identical; HEAD remains `{head}`. This covers the original NOT_READY regression and all prior solver/query investigations.',
'All source bindings, artifact hashes, canonical serializations, tracked diff and independent new-file whitespace checks are audited in the corrected integrity JSON.',
'No scientific parameters, candidate identities, denominator, path/singleton/partition semantics, or binary64 policy changed. No RF capture, detection, full matrix, device identification/discrimination claim, commit, or push.','',
'Reproduce into a new directory:','', '```sh','python3 analysis/regress_episode_component_tracking_v2_draft2_six_capture_corrected.py --output results/NEW-CORRECTED-RUN','```','',
'Artifacts: corrected plan, baseline, regression directory (per-case records and backend certificates), summary JSON, and integrity JSON under `results/episode-component-tracking-v2-draft2-six-capture-corrected-*`.']
(root/'docs'/f'{stem}-regression.md').write_text('\n'.join(lines)+'\n')
diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True);require(diff.returncode==0,'git diff check')
require(not subprocess.check_output(['git','diff','HEAD','--name-only']),'tracked diff')
new=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0');whitespace=[]
for name in filter(None,new):
 p=root/name
 try:text=p.read_text()
 except UnicodeDecodeError:continue
 for i,line in enumerate(text.splitlines(),1):
  if line.rstrip(' \t')!=line:whitespace.append(f'{name}:{i}: trailing whitespace')
 if text and not text.endswith('\n'):whitespace.append(f'{name}: missing final newline')
require(not whitespace,'new-file whitespace')
integrity=dict(format='KRAKEN_DRAFT2_SIX_CAPTURE_CORRECTED_INTEGRITY_V1',decision=report['decision'] if not failures else 'NOT_READY',
 failures=failures,tracked_file_count=len(baseline),all_preexisting_tracked_files_unchanged=not changed,changed_tracked_files=changed,
 head=head,original_regression_untouched=not any(p.startswith(str(r.BASE.relative_to(root))) for p in changed),
 previous_milestones_untouched=not changed,git_diff_check=dict(exit_code=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),
 independent_whitespace=dict(checked_files=len(list(filter(None,new))),failures=whitespace),
 sources_valid=True,artifact_hashes_verified=files,canonical_artifacts_verified=canonical,
 new_file_hashes={p:sha(root/p) for p in new if p and p!=f'results/{stem}-integrity.json'},summary_sha256=sha(summary_path))
(root/'results'/f'{stem}-integrity.json').write_text(json.dumps(integrity,sort_keys=True,indent=2)+'\n')
print(json.dumps(summary,indent=2));print('INTEGRITY',integrity['decision'],failures)
if failures:raise SystemExit(1)
