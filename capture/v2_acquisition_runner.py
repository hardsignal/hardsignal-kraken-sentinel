"""V2 recorder primitives and synthetic rehearsal only. No hardware adapter.

The command line always refuses acquisition. Enabling a future adapter requires
separate authorization and review; no flag in this package can unlock it.
"""
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'results/episode-component-tracking-v2-v2-execution-contract-v1.json'
RATE, DURATION, SAMPLES, BYTES = 25000, 180, 4500000, 72000000
NS = 1000000000
COUNTERS = ('input_underrun', 'input_overflow', 'dropped_buffers', 'dropped_frames',
            'source_reader_errors', 'writer_errors', 'sample_count_mismatch',
            'non_finite_samples', 'timing_overrun', 'unexpected_process_exit')


class CaptureError(ValueError):
    pass


class Interrupted(CaptureError):
    pass


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def utc(ns):
    seconds, nano = divmod(ns, NS)
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + f'.{nano:09d}Z'


def raw_name(session, capture, source, repeat, realtime_ns):
    if any(not re.fullmatch(r'[A-Za-z0-9-]{1,64}', s) for s in (session, capture)):
        raise CaptureError('invalid identifier')
    if source not in ('S1', 'S2') or type(repeat) is not int or repeat not in (1, 2, 3):
        raise CaptureError('invalid source/repeat')
    return f'ECT-V2__{session}__{capture}__{source}__r{repeat}__{utc(realtime_ns)}.iq'


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def rename_exclusive(source, target):
    """Linux renameat2(RENAME_NOREPLACE): atomic publish without clobber races."""
    libc = ctypes.CDLL(None, use_errno=True)
    fn = libc.renameat2  # Unsupported platforms fail closed, no unsafe fallback.
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(source), -100, os.fsencode(target), 1):
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err), str(target))
    sync_dir(Path(target).parent)


def check_count(samples, size):
    if type(samples) is not int or samples != RATE * DURATION or size != samples * 16:
        raise CaptureError('sample/byte count mismatch')


def verify_raw(path):
    path = Path(path)
    size = path.stat().st_size
    check_count(size // 16, size)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(16 * 65536), b''):
            if not np.isfinite(np.frombuffer(block, dtype='<c16')).all():
                raise CaptureError('non-finite samples')
    return {'path': path.name, 'size_bytes': size, 'sha256': sha(path)}


def external_snapshot(contract):
    """Read-only; explicit invocation only. Does not open any SDR device."""
    files = {}
    for key, spec in contract['external_files'].items():
        raw = Path(spec['path']).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != spec['sha256']:
            raise CaptureError('external hash drift: ' + key)
        files[key] = {'sha256': digest, 'bytes_hex': raw.hex()}
    repos = {}
    for key, spec in contract['external_repositories'].items():
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=spec['path'])
        head = git('rev-parse', 'HEAD').decode().strip()
        diff = git('diff', 'HEAD', '--binary', '--no-ext-diff')
        digest = hashlib.sha256(diff).hexdigest()
        if head != spec['head'] or digest != spec['tracked_diff_sha256']:
            raise CaptureError('external repository drift: ' + key)
        # Untracked source is not covered by tracked diff: preserve inventory.
        repos[key] = {'head': head, 'tracked_diff_sha256': digest,
                      'diff_hex': diff.hex(), 'untracked': git('ls-files', '--others', '--exclude-standard').decode()}
    return {'files': files, 'repositories': repos}


class Timeline:
    """Absolute deadlines; UTC never enters scheduling calculations."""
    def __init__(self, start_ns, previous_end_ns=None):
        if previous_end_ns is not None and start_ns - previous_end_ns < 60 * NS:
            raise CaptureError('inter-capture spacing below 60 seconds')
        self.start = start_ns
        self.end = start_ns + DURATION * NS
        self.slots = [start_ns + i * 30 * NS for i in range(6)]
        self.activations = [s + 5 * NS for s in self.slots]

    def event(self, ordinal, actual_ns, realtime_ns):
        if type(ordinal) is not int or not 1 <= ordinal <= 6:
            raise CaptureError('invalid activation ordinal')
        scheduled = self.activations[ordinal - 1]
        if actual_ns < scheduled or actual_ns >= self.slots[ordinal - 1] + 30 * NS:
            raise CaptureError('activation outside scheduled slot')
        return {'ordinal': ordinal, 'scheduled_monotonic_ns': scheduled,
                'actual_monotonic_ns': actual_ns, 'actual_realtime_ns': realtime_ns,
                'lateness_ns': actual_ns - scheduled}


class Recorder:
    """Synthetic-only push interface for testing the reviewed storage lifecycle.

    A future reader must timestamp contiguous post-channelizer samples, discard
    pre-start data, enforce read deadlines, and prove continuity before adoption.
    This class deliberately cannot produce scientifically eligible evidence.
    """
    def __init__(self, directory, session, capture, source, repeat, *,
                 monotonic_ns=time.monotonic_ns, realtime_ns=time.time_ns,
                 previous_end_ns=None):
        self.mono, self.real = monotonic_ns, realtime_ns
        self.start = self.mono()
        self.started_real = self.real()
        self.timeline = Timeline(self.start, previous_end_ns)
        self.final = Path(directory) / raw_name(session, capture, source, repeat, self.started_real)
        self.partial = self.final.with_suffix('.iq.partial')
        self.manifest = self.final.with_suffix('.manifest.json')
        if self.final.exists() or self.manifest.exists():
            raise CaptureError('naming collision')
        self.file = self.partial.open('xb')
        self.count = 0
        self.status = 'INCOMPLETE'
        self.events = []
        self.counters = {k: 'UNKNOWN' for k in COUNTERS}
        for key in ('writer_errors', 'sample_count_mismatch', 'non_finite_samples', 'timing_overrun'):
            self.counters[key] = 0
        self.old_handlers = {}
        self.latched_error = None

    def install_signal_handlers(self):
        def stop(signum, frame):
            raise Interrupted('signal ' + str(signum))
        for sig in (signal.SIGINT, signal.SIGTERM):
            self.old_handlers[sig] = signal.signal(sig, stop)

    def __enter__(self):
        self.install_signal_handlers()
        return self

    def __exit__(self, kind, error, traceback):
        if self.status == 'INCOMPLETE':
            result = self.finish(error)
            if result['exit_code'] and error is None:
                raise CaptureError(result['failure']['reason'])
        return False

    def activation(self, ordinal):
        if self.status != 'INCOMPLETE' or ordinal != len(self.events) + 1:
            raise CaptureError('duplicate/out-of-order activation')
        self.events.append(self.timeline.event(ordinal, self.mono(), self.real()))

    def write(self, samples):
        try:
            self._write(samples)
        except (Exception, KeyboardInterrupt) as exc:
            self.latched_error = exc
            raise

    def _write(self, samples):
        if self.latched_error is not None:
            raise CaptureError('previous writer failure')
        if self.status != 'INCOMPLETE' or self.file.closed:
            raise CaptureError('writer not active')
        if self.mono() >= self.timeline.end:
            self.counters['timing_overrun'] += 1
            raise CaptureError('capture deadline reached; no extension')
        if not isinstance(samples, np.ndarray) or samples.ndim != 1 or samples.dtype.str != '<c16':
            raise CaptureError('requires one-dimensional little-endian <c16')
        bad = int(samples.size - np.count_nonzero(np.isfinite(samples)))
        self.counters['non_finite_samples'] += bad
        if bad:
            raise CaptureError('non-finite samples')
        if self.count + samples.size > SAMPLES:
            self.counters['sample_count_mismatch'] += 1
            raise CaptureError('too many samples; no rollover')
        try:
            raw = samples.tobytes(order='C')
            if self.file.write(raw) != len(raw):
                raise OSError('short write')
            self.count += samples.size
        except OSError:
            self.counters['writer_errors'] += 1
            raise

    def finish(self, error=None):
        if self.status != 'INCOMPLETE':
            raise CaptureError('already finalized')
        ended, ended_real = self.mono(), self.real()
        raw = None
        code = 0
        try:
            self.file.flush()
            os.fsync(self.file.fileno())
            self.file.close()
            if error or self.latched_error:
                raise error or self.latched_error
            if ended != self.timeline.end:
                self.counters['timing_overrun'] += 1
                raise CaptureError('deadline mismatch; scheduling tolerance not yet frozen')
            if self.count != SAMPLES or self.partial.stat().st_size != BYTES:
                self.counters['sample_count_mismatch'] += 1
            check_count(self.count, self.partial.stat().st_size)
            if len(self.events) != 6:
                raise CaptureError('missing activation events')
            raw = verify_raw(self.partial)
            os.chmod(self.partial, 0o444)
            rename_exclusive(self.partial, self.final)
            raw['path'] = self.final.name
            self.status = 'COMPLETE'
        except (Exception, KeyboardInterrupt) as exc:
            if isinstance(exc, OSError):
                self.counters['writer_errors'] += 1
            self.status = 'ABORTED' if isinstance(exc, (Interrupted, KeyboardInterrupt)) else 'FAILED'
            code = 130 if self.status == 'ABORTED' else 2
            error = exc
            raw = None
        finally:
            self.file.close()
            for sig, handler in self.old_handlers.items():
                signal.signal(sig, handler)
        result = {'format': 'V2_RECORDER_REHEARSAL_V1', 'status': self.status,
                  'synthetic': True, 'scientific_eligible': False, 'exit_code': code,
                  'failure': None if code == 0 else {'type': type(error).__name__, 'reason': str(error)},
                  'raw': raw, 'partial_path': self.partial.name,
                  'samples': self.count, 'dtype': '<c16', 'sample_rate_hz': RATE,
                  'started_monotonic_ns': self.start, 'ended_monotonic_ns': ended,
                  'started_realtime_ns': self.started_real, 'ended_realtime_ns': ended_real,
                  'events': self.events, 'counters': self.counters,
                  'contract_sha256': sha(CONTRACT), 'runner_sha256': sha(__file__)}
        # A failed metadata publish never yields success to the caller. Preserve files.
        temp = self.manifest.with_suffix('.json.partial')
        with temp.open('x') as f:
            json.dump(result, f, sort_keys=True, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        rename_exclusive(temp, self.manifest)
        return result


def main():
    print(json.dumps({'decision': 'V2_ACQUISITION_EXECUTION_CONTRACT_REVIEWED_BLOCKED',
                      'state': 'BLOCKED_PENDING_ACQUISITION_SETTINGS',
                      'failure': 'Future explicit authorization and reviewed hardware adapter required',
                      'exit_code': 3}))
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
