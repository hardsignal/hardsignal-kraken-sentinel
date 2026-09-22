"""Synthetic arrays, fake clocks and temporary files only; never import SDR code."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import jsonschema
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v2_runner', ROOT / 'capture/v2_acquisition_runner.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
CONTRACT = json.loads(v.CONTRACT.read_text())


class Clock:
    mono = 0
    real = 1780000000000000000
    def monotonic_ns(self): return self.mono
    def realtime_ns(self): return self.real


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock()

    def recorder(self, **kwargs):
        r = v.Recorder(self.tmp.name, 'session-1', 'capture-1', 'S1', 1,
                       monotonic_ns=self.clock.monotonic_ns,
                       realtime_ns=self.clock.realtime_ns, **kwargs)
        self.addCleanup(r.file.close)
        return r

    def populate(self, r):
        # 400 kB reusable chunk; no huge allocation and no real clock waits.
        chunk = np.zeros(25000, dtype='<c16')
        for second in range(180):
            self.clock.mono = second * v.NS
            self.clock.real -= 100 * v.NS  # deliberately backwards UTC
            if second % 30 == 5:
                r.activation(second // 30 + 1)
            r.write(chunk)
        self.clock.mono = 180 * v.NS

    def test_exact_contract_without_allocation(self):
        self.assertEqual(v.RATE * v.DURATION, 4500000)
        self.assertEqual(v.SAMPLES * np.dtype('<c16').itemsize, 72000000)
        v.check_count(4500000, 72000000)
        for samples, size in [(4499999,72000000),(4500000,71999999),(4500001,72000016)]:
            with self.assertRaises(v.CaptureError): v.check_count(samples,size)

    def test_complete_atomic_sha_schema_and_clock_independence(self):
        r = self.recorder()
        self.populate(r)
        self.assertFalse(r.final.exists())
        self.assertTrue(r.partial.exists())
        result = r.finish()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertFalse(r.partial.exists())
        self.assertEqual(result['raw']['size_bytes'],72000000)
        self.assertEqual(result['raw']['sha256'],v.sha(r.final))
        self.assertEqual(r.final.stat().st_mode & 0o222,0)
        self.assertEqual(result['counters']['input_overflow'],'UNKNOWN')
        self.assertFalse(result['scientific_eligible'])
        jsonschema.validate(result, CONTRACT['rehearsal_manifest_schema'])
        self.assertEqual(result['ended_monotonic_ns']-result['started_monotonic_ns'],180*v.NS)
        self.assertLess(result['ended_realtime_ns'],result['started_realtime_ns'])

    def test_dtype_little_endian_rejected_types(self):
        r=self.recorder()
        for dtype in ['>c16','<c8','<f8']:
            with self.assertRaises(v.CaptureError): r.write(np.zeros(2,dtype=dtype))
        with self.assertRaises(v.CaptureError): r.write(np.zeros((2,2),dtype='<c16'))
        with self.assertRaises(v.CaptureError): r.write(np.array([1+2j],dtype='<c16'))
        self.assertEqual(r.count,0)

    def test_partial_and_count_mismatch_fail(self):
        r=self.recorder(); self.clock.mono=180*v.NS
        result=r.finish()
        self.assertEqual(result['status'],'FAILED')
        self.assertNotEqual(result['exit_code'],0)
        self.assertIsNone(result['raw']); self.assertTrue(r.partial.exists())
        self.assertFalse(r.final.exists())
        jsonschema.validate(result,CONTRACT['rehearsal_manifest_schema'])
        result['status']='COMPLETE'
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(result,CONTRACT['rehearsal_manifest_schema'])

    def test_error_cannot_be_ignored(self):
        r=self.recorder()
        with self.assertRaises(v.CaptureError): r.write(np.zeros(1,dtype='<c8'))
        self.clock.mono=180*v.NS
        self.assertEqual(r.finish()['status'],'FAILED')

    def test_context_abort_preserves_evidence(self):
        r=self.recorder()
        with self.assertRaises(RuntimeError):
            with r:
                raise RuntimeError('source unavailable')
        self.assertEqual(r.status,'FAILED')
        self.assertTrue(r.partial.exists())
        self.assertFalse(r.final.exists())

    def test_nonfinite(self):
        r=self.recorder()
        with self.assertRaises(v.CaptureError): r.write(np.array([complex(float('nan'),0)],dtype='<c16'))
        self.assertEqual(r.counters['non_finite_samples'],1)
        result=r.finish(v.CaptureError('non-finite samples'))
        self.assertEqual(result['status'],'FAILED')

    def test_signal_abort(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            with self.subTest(sig=sig), tempfile.TemporaryDirectory() as directory:
                r=v.Recorder(directory,'s','c','S1',1)
                before=signal.getsignal(sig)
                r.install_signal_handlers()
                try:
                    signal.getsignal(sig)(sig,None)
                except v.Interrupted as exc:
                    result=r.finish(exc)
                self.assertEqual(result['status'],'ABORTED')
                self.assertEqual(result['exit_code'],130)
                self.assertEqual(signal.getsignal(sig),before)
                self.assertFalse(r.final.exists())

    def test_collision_and_no_overwrite_race(self):
        r=self.recorder()
        with self.assertRaises(FileExistsError): self.recorder()
        r.final.write_bytes(b'original')
        with self.assertRaises(OSError): v.rename_exclusive(r.partial,r.final)
        self.assertEqual(r.final.read_bytes(),b'original')
        self.assertTrue(r.partial.exists())
        with self.assertRaises(v.CaptureError): self.recorder()

    def test_fsync_failure_is_instrumented(self):
        r=self.recorder()
        with patch.object(v.os,'fsync',side_effect=[OSError('disk failure'),None,None]):
            result=r.finish()
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(result['counters']['writer_errors'],1)
        self.assertTrue(r.partial.exists())
        self.assertFalse(r.final.exists())

    def test_atomic_publish_and_failure(self):
        a=Path(self.tmp.name)/'a'; b=Path(self.tmp.name)/'b'
        a.write_bytes(b'payload')
        with patch.object(v,'sync_dir', wraps=v.sync_dir) as sync:
            v.rename_exclusive(a,b)
            sync.assert_called_once_with(b.parent)
        self.assertFalse(a.exists()); self.assertEqual(b.read_bytes(),b'payload')

    def test_fixed_deadlines_activation_spacing(self):
        t=v.Timeline(100*v.NS,40*v.NS)
        self.assertEqual(t.end,280*v.NS)
        self.assertEqual(t.activations,[x*v.NS for x in (105,135,165,195,225,255)])
        t.event(1,105*v.NS,0)
        self.assertEqual(t.end,280*v.NS)
        with self.assertRaises(v.CaptureError): v.Timeline(100*v.NS,40*v.NS+1)
        with self.assertRaises(v.CaptureError): t.event(1,104*v.NS,10**30)
        r=self.recorder(); self.clock.mono=180*v.NS
        with self.assertRaises(v.CaptureError): r.write(np.zeros(1,dtype='<c16'))

    def test_naming_utc_and_validation(self):
        n=v.raw_name('s','c','S2',3,0)
        self.assertEqual(n,'ECT-V2__s__c__S2__r3__19700101T000000.000000000Z.iq')
        with self.assertRaises(v.CaptureError): v.raw_name('../s','c','S2',3,0)

    def test_hash_drift_synthetic_only(self):
        p=Path(self.tmp.name)/'settings'; p.write_bytes(b'{}')
        c={'external_files':{'settings':{'path':str(p),'sha256':hashlib.sha256(b'{}').hexdigest()}},'external_repositories':{}}
        self.assertIn('settings',v.external_snapshot(c)['files'])
        p.write_bytes(b'{ }')
        with self.assertRaises(v.CaptureError): v.external_snapshot(c)

    def test_dirty_repo_drift(self):
        c={'external_files':{},'external_repositories':{'test':{'path':self.tmp.name,'head':'a'*40,'tracked_diff_sha256':hashlib.sha256(b'diff').hexdigest()}}}
        with patch.object(v.subprocess,'check_output',side_effect=[b'a'*40+b'\n',b'drift']):
            with self.assertRaises(v.CaptureError): v.external_snapshot(c)

    def test_external_evidence_pinned(self):
        self.assertEqual(CONTRACT['receiver_serials'],['1000','1001','1002','1003','1004'])
        self.assertEqual(CONTRACT['external_repositories']['kraken']['tracked_diff_sha256'],'7fef45f8adb5194184d267dda0a785c89fde3a3dadd7bfe6574b79dee5cbeb61')
        self.assertEqual(CONTRACT['external_repositories']['heimdall']['tracked_diff_sha256'],'27e96bf7a00d9cb8377fd7cfdab27e93946b93dc1b795cdf859df9906fbfedaa')
        self.assertEqual(CONTRACT['scientific_channel_mapping']['index'],1)
        self.assertEqual(CONTRACT['scientific_channel_mapping']['status'],'BLOCKED')
        for value in CONTRACT['unavailable'].values(): self.assertIsNone(value)

    def test_cli_blocked_no_hardware(self):
        result=subprocess.run([sys.executable,str(ROOT/'capture/v2_acquisition_runner.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,3)
        self.assertEqual(json.loads(result.stdout)['state'],'BLOCKED_PENDING_ACQUISITION_SETTINGS')
        source=(ROOT/'capture/v2_acquisition_runner.py').read_text()
        for forbidden in ['rtlsdr_open','Popen(','estimate_DOA','grid_sigma','classify_episode']:
            self.assertNotIn(forbidden,source)
        self.assertFalse(CONTRACT['acquisition_authorized'])
        lock=json.loads((ROOT/'results/episode-component-tracking-v2-v2-acquisition-lock.json').read_text())
        self.assertEqual(lock['decision'],'V2_ACQUISITION_LOCK_BLOCKED')

    def test_strict_schema_unknown_fields_and_instrumentation(self):
        r=self.recorder(); result=r.finish(v.CaptureError('test'))
        result['extra']=True
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(result,CONTRACT['rehearsal_manifest_schema'])
        del result['extra']; result['counters']['input_overflow']=None
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(result,CONTRACT['rehearsal_manifest_schema'])

    def test_exact_provenance(self):
        sys.path.insert(0,str(ROOT/'analysis'))
        from provenance import v2_execution_contract_v1 as provenance
        provenance.validate(ROOT)
        read=Path.read_bytes
        for path in provenance.PATHS-{provenance.BINDING}:
            with self.subTest(path=path), patch.object(Path,'read_bytes',lambda p:read(p)+b' drift' if p==ROOT/path else read(p)):
                with self.assertRaises(ValueError): provenance.validate(ROOT)


if __name__=='__main__': unittest.main()
