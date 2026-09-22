"""Non-scientific contract tests. All observation fixtures exist only in memory."""
import ast
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import validate_episode_component_tracking_v2_v2_acquisition_manifest as v

ROOT = v.ROOT
PARENT = 'c98ad53a6d278140c98ecbe045f2462c24f5852f'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def fixture(lock):
    """Structural fixture only: not persisted or offered as collection evidence."""
    lock_hash = v.digest((ROOT / v.LOCK_PATH).read_bytes())
    shared = dict(lock_sha256=lock_hash, authorizing_commit='1' * 40,
                  settings_sha256=v.digest(v.canonical(lock['settings'])),
                  settings_at_start=copy.deepcopy(lock['settings']),
                  settings_at_finish=copy.deepcopy(lock['settings']),
                  errors=[], warnings=[], completeness='COMPLETE')
    series = dict(lock_sha256=lock_hash, authorizing_commit='1' * 40, sessions=[])
    epoch = datetime(2030, 1, 1, tzinfo=timezone.utc)
    iso = lambda dt: dt.isoformat().replace('+00:00', 'Z')
    for ordinal in range(1, 9):
        sid = f'V2-J{ordinal:02d}'
        start = epoch + timedelta(days=ordinal - 1)
        session = dict(copy.deepcopy(shared), session_id=sid, ordinal=ordinal,
                       started_at=iso(start), ended_at=iso(start + timedelta(seconds=1380)),
                       previous_session_id=f'V2-J{ordinal-1:02d}' if ordinal > 1 else None,
                       separation_seconds=86400 if ordinal > 1 else None,
                       metadata={key:'unit-test-only' for key in ['operator_id','operator_notes',
                       'ambient_temperature','battery_states','interference','deviations',
                       'location_geometry_reference','source_state']}, capture_order=[], captures=[])
        for index, (source, repeat) in enumerate(v.capture_order(ordinal)):
            cid = f'{sid}-{source}-R{repeat}'
            cs = start + timedelta(seconds=240 * index)
            capture = dict(copy.deepcopy(shared), capture_id=cid, session_id=sid, source_id=source,
                           repetition=repeat, expected_activation_slots=6,
                           started_at=iso(cs), ended_at=iso(cs+timedelta(seconds=180)),
                           started_monotonic_ns=0, ended_monotonic_ns=180000000000,
                           recorder_exit_status=0, dropped_samples=0,
                           raw_files=[dict(path='/not-real/'+cid+'.iq', sha256='a'*64,
                                           size_bytes=16, mtime_ns=1, complete=True)],
                           activations=[dict(slot_id=f'{cid}-T{slot:02d}',ordinal=slot,
                                             scheduled_offset_seconds=(slot-1)*30+5,
                                             actual_utc=None, actual_monotonic_ns=None,
                                             failure='unit-test-only absent marker') for slot in range(1,7)],
                           logs=[dict(path='/not-real/log',sha256='b'*64)],operator_notes='unit-test-only')
            session['capture_order'].append(cid)
            session['captures'].append(capture)
        series['sessions'].append(session)
    return series


class AcquisitionLockTests(unittest.TestCase):
    def setUp(self):
        self.lock = v.read_json(ROOT / v.LOCK_PATH)
        self.schema = v.read_json(ROOT / v.SCHEMA_PATH)

    def test_parent_and_unchanged_preregistration_bytes(self):
        self.assertEqual(self.lock['parent_checkpoint'], 'c98ad53')
        self.assertEqual(self.lock['parent_commit'], PARENT)
        for path, expected in {
            'results/episode-component-tracking-v2-v2-discrimination-preregistration.json':
            'dd9a1694c5d0bc7a47ad2f0bfa917816cc66325f5325e4718b95a7bb9780a7b6',
            'docs/episode-component-tracking-v2-v2-discrimination-preregistration.md':
            'f28d4d168a2475c6a755b21c521270e8f2de269a12e67227f24116137321b7c7',
        }.items():
            self.assertEqual(v.digest((ROOT/path).read_bytes()), expected)
            self.assertEqual((ROOT/path).read_bytes(), git('show', PARENT+':'+path))

    def test_candidates_and_counts(self):
        self.assertEqual(self.lock['candidates'], {
            'A':dict(representation='grid_sigma5',width_hz=350,association='connected'),
            'B':dict(representation='grid_sigma10',width_hz=350,association='connected')})
        self.assertEqual(self.lock['design'], dict(sessions=8,
            minimum_session_start_separation_seconds=86400,sources=['S1','S2'],
            repeats_per_source_per_session=3,captures=48,slots_per_capture=6,
            activation_slots=288,paired_raw_inputs=True))

    def test_parent_policies_unchanged(self):
        parent = v.read_json(ROOT/'results/episode-component-tracking-v2-v2-discrimination-preregistration.json')
        for key in ['acquisition_plan','anomaly_policy','missing_data_policy']:
            self.assertEqual(self.lock[key],parent[key])
        self.assertEqual(self.lock['episode_segmentation'],parent['fixed_parameters']['episode_segmentation'])
        self.assertEqual(self.lock['stage37_decision'],'STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED')

    def test_all_evidence_bound_to_parent(self):
        v.verify_contract(self.lock)
        for path, expected in self.lock['evidence_sha256'].items():
            self.assertEqual(v.digest(git('show',PARENT+':'+path)),expected,path)

    def test_no_historical_tracked_file_changed(self):
        # No V1/Stage37/scientific evidence change anywhere, not just selected files.
        names = git('diff','--name-only',PARENT).decode().splitlines()
        self.assertTrue(set(names) <= set(self.lock['artifact_paths']),names)

    def test_post_commit_binding(self):
        revision = os.environ.get('V2_LOCK_COMMIT')
        if not revision:
            self.skipTest('post-commit binding requires V2_LOCK_COMMIT; not an acquisition permission')
        self.assertRegex(revision,r'^[0-9a-f]{40}$')
        subprocess.run(['git','merge-base','--is-ancestor',PARENT,revision],cwd=ROOT,check=True)
        self.assertEqual(set(git('diff','--name-only',PARENT,revision).decode().splitlines()),
                         set(self.lock['artifact_paths']))
        for path in self.lock['artifact_paths']:
            self.assertEqual(git('show',revision+':'+path),(ROOT/path).read_bytes(),path)
        v.verify_contract(self.lock)

    def test_every_setting_has_origin_and_bound_evidence(self):
        for key, setting in self.lock['settings'].items():
            self.assertTrue(setting['mandatory'])
            self.assertTrue(setting['detail'])
            for ref in setting['evidence']:
                self.assertIn(ref.split('#')[0],self.lock['evidence_sha256'])
            if setting['status']=='NOT_ESTABLISHED':
                self.assertIsNone(setting['value'],key)

    def test_fixed_settings_cannot_drift(self):
        for key, setting in self.lock['settings'].items():
            altered=copy.deepcopy(self.lock)
            altered['settings'][key]['value']='unapproved'
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.verify_contract(altered)

    def test_ready_cannot_be_asserted(self):
        for edit in ['state','fill','delete','conflict']:
            altered=copy.deepcopy(self.lock)
            if edit=='state': altered['state']='READY_FOR_V2_ACQUISITION'
            if edit=='fill':
                for s in altered['settings'].values():
                    if s['value'] is None:s.update(value='invented',status='ESTABLISHED')
            if edit=='delete':altered['settings'].pop('receiver_gain')
            if edit=='conflict':altered['conflicts']=[]
            with self.subTest(edit=edit), self.assertRaises(ValueError):v.acquisition_gate(altered)

    def test_blocked_contract_is_never_authorization(self):
        with self.assertRaisesRegex(ValueError,v.BLOCKED):v.acquisition_gate(self.lock)
        with self.assertRaisesRegex(ValueError,v.BLOCKED):v.acquisition_gate(self.lock,fixture(self.lock))

    def test_arbitrary_top_level_mutation_fails(self):
        for key in self.lock:
            altered=copy.deepcopy(self.lock); altered[key]=None
            with self.subTest(key=key), self.assertRaises(ValueError):v.verify_contract(altered)

    def test_unknown_and_tuning_parameters_fail(self):
        for key in ['tuning','sigma','gain_override','retry','force','extra']:
            altered=copy.deepcopy(self.lock);altered[key]=True
            with self.assertRaises(ValueError):v.verify_contract(altered)
            data=fixture(self.lock); data['sessions'][0]['captures'][0][key]=True
            with self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)

    def test_structure_fixture_and_no_raw_reads(self):
        data=fixture(self.lock)
        original=Path.read_bytes
        def guarded(path):
            self.assertNotIn('/not-real/',str(path))
            return original(path)
        with patch.object(Path,'read_bytes',guarded):v.validate_structure(data,self.lock,self.schema)

    def test_missing_extra_duplicate_sessions_and_captures(self):
        for level in ['sessions','captures']:
            for mutation in ['missing','extra','duplicate']:
                data=fixture(self.lock)
                rows=data['sessions'] if level=='sessions' else data['sessions'][0]['captures']
                if mutation=='missing':rows.pop()
                elif mutation=='extra':rows.append(copy.deepcopy(rows[0]))
                else:rows[1]=copy.deepcopy(rows[0])
                with self.subTest(level=level,mutation=mutation), self.assertRaises(ValueError):
                    v.validate_structure(data,self.lock,self.schema)

    def test_spacing_and_order_failures(self):
        for edit in ['session_spacing','capture_spacing','repeat','order','ordinal','slot','duration','timezone']:
            data=fixture(self.lock); s=data['sessions'][0]; c=s['captures'][0]
            if edit=='session_spacing':data['sessions'][1]['started_at']='2030-01-01T23:59:59Z'
            if edit=='capture_spacing':s['captures'][1]['started_at']='2030-01-01T00:03:59Z'
            if edit=='repeat':c['repetition']=2
            if edit=='order':s['capture_order'].reverse()
            if edit=='ordinal':s['ordinal']=2
            if edit=='slot':c['activations'][0]['scheduled_offset_seconds']=4
            if edit=='duration':c['ended_at']='2030-01-01T00:03:01Z'
            if edit=='timezone':s['started_at']='2030-01-01T00:00:00'
            with self.subTest(edit=edit), self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)

    def test_hash_and_binding_failures(self):
        for edit in ['invalid','lock','commit','configuration','raw_duplicate']:
            data=fixture(self.lock);c=data['sessions'][0]['captures'][0]
            if edit=='invalid':c['raw_files'][0]['sha256']='bad'
            if edit=='lock':c['lock_sha256']='0'*64
            if edit=='commit':c['authorizing_commit']='0'*40
            if edit=='configuration':c['settings_sha256']='0'*64
            if edit=='raw_duplicate':c['raw_files'].append(copy.deepcopy(c['raw_files'][0]))
            with self.subTest(edit=edit), self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)

    def test_hardware_recorder_drift_rejected(self):
        for name in ['vfo_freq_0','receiver_gain','recorder_implementation']:
            for where in ['settings_at_start','settings_at_finish']:
                data=fixture(self.lock);data['sessions'][0]['captures'][0][where][name]['value']='changed'
                with self.subTest(name=name,where=where), self.assertRaises(ValueError):
                    v.validate_structure(data,self.lock,self.schema)

    def test_incomplete_failure_cannot_be_complete(self):
        for field,value in [('recorder_exit_status',1),('dropped_samples',1),('errors',['overflow'])]:
            data=fixture(self.lock);data['sessions'][0]['captures'][0][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)
        data=fixture(self.lock);data['sessions'][0]['captures'][0]['raw_files'][0]['complete']=False
        with self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)

    def test_aborted_unstarted_records_preserve_missing_facts(self):
        data=fixture(self.lock)
        session=data['sessions'][0]
        session.update(completeness='INCOMPLETE',errors=['planned capture never began'])
        capture=session['captures'][0]
        capture.update(completeness='NOT_STARTED', errors=['acquisition blocked'],
                       started_at=None,ended_at=None,started_monotonic_ns=None,
                       ended_monotonic_ns=None,settings_at_start=None,settings_at_finish=None,
                       recorder_exit_status=None,dropped_samples=None,raw_files=[],logs=[])
        v.validate_structure(data,self.lock,self.schema)
        with self.assertRaisesRegex(ValueError,v.BLOCKED):v.acquisition_gate(self.lock,data)
        capture['completeness']='COMPLETE'
        with self.assertRaises(ValueError):v.validate_structure(data,self.lock,self.schema)

    def test_evidence_and_schema_mutations_rejected(self):
        original=Path.read_bytes
        for target in [v.SCHEMA_PATH, *self.lock['evidence_sha256']]:
            def changed(path):
                return original(path)+b'\n' if path==ROOT/target else original(path)
            with self.subTest(target=target), patch.object(Path,'read_bytes',changed):
                with self.assertRaises(ValueError):v.verify_contract(self.lock)

    def test_strict_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'metadata.json'
            for raw in ['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}']:
                path.write_text(raw)
                with self.assertRaises(ValueError):v.read_json(path)

    def test_no_scientific_or_hardware_execution_interface(self):
        tree=ast.parse(Path(v.__file__).read_text())
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):modules.append(node.module)
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,{'eval','exec','compile','__import__','open'})
        self.assertEqual(set(modules),{'argparse','datetime','hashlib','json','pathlib','re'})
        source=Path(v.__file__).read_text()
        for forbidden in ['subprocess','Popen','socket','numpy','kraken_capture','group_episodes']:
            self.assertNotIn(forbidden,source)
        with patch('builtins.print'):
            self.assertEqual(v.main([]),2)
        for option in ['--gain','--sigma','--ready','--force','--collect']:
            with patch('sys.stderr'), self.assertRaises(SystemExit):v.main([option,'1'])


if __name__ == '__main__':
    unittest.main()
