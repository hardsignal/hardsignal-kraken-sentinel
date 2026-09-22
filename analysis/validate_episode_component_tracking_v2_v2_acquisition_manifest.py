#!/usr/bin/env python3
"""Metadata-only, fail-closed acquisition contract gate. Never opens raw IQ paths."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from provenance import v2_acquisition_lock_v1 as provenance

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = 'results/episode-component-tracking-v2-v2-acquisition-lock.json'
SCHEMA_PATH = 'results/episode-component-tracking-v2-v2-acquisition-manifest-schema-v1.json'
LOCK_CANONICAL_SHA256 = '2dfc6029ba45c0cf88d39441b60b9086f852f37c396467b86051a253f28ca0b9'
BLOCKED = 'BLOCKED_PENDING_ACQUISITION_SETTINGS'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON: ' + value)


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=reject_constant)


def schema_check(value, spec, definitions, label='manifest'):
    """Implement only the closed schema vocabulary used by this version."""
    if '$ref' in spec:
        return schema_check(value, definitions[spec['$ref'].split('/')[-1]], definitions, label)
    if 'const' in spec:
        require(canonical(value) == canonical(spec['const']), label + ': fixed value changed')
    if 'enum' in spec:
        require(any(canonical(value) == canonical(x) for x in spec['enum']), label + ': enum')
    if 'type' in spec:
        allowed = spec['type'] if isinstance(spec['type'], list) else [spec['type']]
        types = {'object': type(value) is dict, 'array': type(value) is list,
                 'integer': type(value) is int, 'number': type(value) in (int, float),
                 'string': type(value) is str, 'boolean': type(value) is bool,
                 'null': value is None}
        require(any(types[t] for t in allowed), label + ': type')
    if isinstance(value, dict) and 'properties' in spec:
        require(set(spec['required']) <= set(value), label + ': missing field')
        require(not (set(value) - set(spec['properties'])), label + ': unknown field')
        for key, child in value.items():
            schema_check(child, spec['properties'][key], definitions, label + '.' + key)
    if isinstance(value, list):
        require(len(value) >= spec.get('minItems', 0), label + ': too few entries')
        require(len(value) <= spec.get('maxItems', len(value)), label + ': too many entries')
        for child in value:
            schema_check(child, spec.get('items', {}), definitions, label + '[]')
    if isinstance(value, str):
        require(len(value) >= spec.get('minLength', 0), label + ': empty')
        if 'pattern' in spec:
            require(re.fullmatch(spec['pattern'], value) is not None, label + ': syntax')
    if type(value) in (int, float):
        require(value >= spec.get('minimum', value), label + ': below minimum')
        require(value <= spec.get('maximum', value), label + ': above maximum')


def verify_contract(lock, root=ROOT):
    require(digest(canonical(lock)) == LOCK_CANONICAL_SHA256, 'immutable acquisition lock changed')
    require(lock['state'] == BLOCKED, 'this version cannot assert READY')
    provenance.validate(root)
    for path, expected in lock['evidence_sha256'].items():
        require(re.fullmatch('[0-9a-f]{64}', expected) is not None, 'invalid evidence hash')
        actual = digest((root / path).read_bytes())
        if path in provenance.TRANSITIONS:
            actual = provenance.historical_digest(root, path, actual)
        require(actual == expected, 'evidence drift: ' + path)
    require(digest((root / SCHEMA_PATH).read_bytes()) == lock['schema_sha256'], 'schema drift')
    schema = read_json(root / SCHEMA_PATH)
    schema_check(lock, schema['$defs']['experiment'], schema['$defs'])
    return schema


def utc(value):
    require(type(value) is str and value.endswith('Z'), 'UTC timestamp required')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise ValueError('invalid timestamp') from exc


def optional_utc(value):
    return None if value is None else utc(value)


def capture_order(ordinal):
    sources = ['S1', 'S2'] if ordinal % 2 else ['S2', 'S1']
    return [(source, repeat) for repeat in range(1, 4) for source in sources]


def validate_structure(series, lock, schema):
    """Metadata diagnostics only; success is NEVER collection authorization.

    In-memory test fixtures may exercise this separately from the closed gate.
    Raw files and log paths are deliberately not dereferenced.
    """
    schema_check(series, schema['$defs']['series'], schema['$defs'])
    lock_hash = digest((ROOT / LOCK_PATH).read_bytes())
    require(series['lock_sha256'] == lock_hash, 'lock byte hash mismatch')
    settings_hash = digest(canonical(lock['settings']))
    session_ids, capture_ids, raw_paths = set(), set(), set()
    previous = None
    for ordinal, session in enumerate(series['sessions'], 1):
        sid = f'V2-J{ordinal:02d}'
        require(session['session_id'] not in session_ids, 'duplicate session ID')
        session_ids.add(session['session_id'])
        require(session['ordinal'] == ordinal and session['session_id'] == sid, 'session ordinal/ID')
        start, end = optional_utc(session['started_at']), optional_utc(session['ended_at'])
        require(start is None or end is None or end >= start, 'session time reversal')
        if previous and start is not None and previous['started_at'] is not None:
            delta = (start - utc(previous['started_at'])).total_seconds()
            require(delta >= 86400 and start.date() != utc(previous['started_at']).date(), 'session spacing')
            require(previous['ended_at'] is None or start >= utc(previous['ended_at']), 'overlapping sessions')
            require(session['previous_session_id'] == previous['session_id'] and
                    session['separation_seconds'] == delta, 'separation ledger')
        elif previous:
            require(session['previous_session_id'] == previous['session_id'] and
                    session['separation_seconds'] is None, 'unverifiable separation must be null')
        else:
            require(session['previous_session_id'] is None and session['separation_seconds'] is None,
                    'first-session separation must be null')
        expected = [(f'{sid}-{source}-R{repeat}', source, repeat)
                    for source, repeat in capture_order(ordinal)]
        require(session['capture_order'] == [row[0] for row in expected], 'capture order')
        previous_capture = None
        for capture, (cid, source, repeat) in zip(session['captures'], expected):
            require(capture['capture_id'] not in capture_ids, 'duplicate capture ID')
            capture_ids.add(capture['capture_id'])
            require((capture['capture_id'], capture['source_id'], capture['repetition'], capture['session_id'])
                    == (cid, source, repeat, sid), 'capture identity/order')
            cs, ce = optional_utc(capture['started_at']), optional_utc(capture['ended_at'])
            require(cs is None or (start is not None and start <= cs), 'capture before session')
            require(ce is None or (cs is not None and end is not None and cs <= ce <= end), 'capture outside session')
            ms, me = capture['started_monotonic_ns'], capture['ended_monotonic_ns']
            require((cs is None) == (ms is None) and (ce is None) == (me is None), 'capture clock presence')
            require(me is None or (ms is not None and me >= ms), 'monotonic reversal')
            if previous_capture and cs is not None and previous_capture['ended_at'] is not None:
                require((cs - utc(previous_capture['ended_at'])).total_seconds() >= 60, 'capture spacing')
            if capture['completeness'] == 'COMPLETE':
                require(cs is not None and ce is not None and bool(capture['logs']), 'missing completed capture timing/logs')
                require((ce - cs).total_seconds() == 180, 'capture duration')
                require(capture['ended_monotonic_ns'] - capture['started_monotonic_ns'] == 180000000000,
                        'monotonic duration')
                require(capture['recorder_exit_status'] == 0 and capture['dropped_samples'] == 0
                        and not capture['errors'], 'recorder failure')
            for index, activation in enumerate(capture['activations'], 1):
                require((activation['slot_id'], activation['ordinal'], activation['scheduled_offset_seconds'])
                        == (f'{cid}-T{index:02d}', index, (index - 1) * 30 + 5), 'activation slot')
                actual, mono = activation['actual_utc'], activation['actual_monotonic_ns']
                require((actual is None) == (mono is None), 'activation clocks must both be present or absent')
                if actual is None:
                    require(bool(activation['failure']), 'missing activation failure ledger')
                else:
                    require(cs is not None and ce is not None and cs <= utc(actual) <= ce, 'activation outside capture')
                    require(capture['started_monotonic_ns'] <= mono <= capture['ended_monotonic_ns'],
                            'activation monotonic bounds')
            for raw in capture['raw_files']:
                require(raw['path'] not in raw_paths, 'duplicate raw path')
                raw_paths.add(raw['path'])
                if capture['completeness'] == 'COMPLETE':
                    require(raw['complete'], 'partial raw file')
            previous_capture = capture
        for record in [session] + session['captures']:
            require(record['lock_sha256'] == series['lock_sha256'] and
                    record['authorizing_commit'] == series['authorizing_commit'], 'immutable binding drift')
            require(record['settings_sha256'] == settings_hash, 'configuration hash drift')
            for key in ['settings_at_start', 'settings_at_finish']:
                if record[key] is None:
                    require(record['completeness'] != 'COMPLETE' and bool(record['errors']),
                            'missing actual settings need incomplete state and error')
                else:
                    require(canonical(record[key]) == canonical(lock['settings']), 'hardware/recorder drift')
            if record['completeness'] != 'COMPLETE':
                require(bool(record['errors']), 'incomplete record needs reason')
            if record['completeness'] == 'NOT_STARTED':
                require(record['started_at'] is None and record['ended_at'] is None, 'not-started timing')
        if session['completeness'] == 'COMPLETE':
            require(start is not None and end is not None, 'missing session timing')
            require(not session['errors'] and all(c['completeness'] == 'COMPLETE' for c in session['captures']),
                    'session completeness')
        previous = session
    require(len(capture_ids) == 48 and len(session_ids) == 8, 'series structure')


def acquisition_gate(lock, series=None):
    schema = verify_contract(lock)
    if series is not None:
        validate_structure(series, lock, schema)
    unresolved = [key for key, value in lock['settings'].items()
                  if value['mandatory'] and (value['value'] is None or value['status'] == 'NOT_ESTABLISHED')]
    require(not unresolved and not lock['conflicts'], BLOCKED + ': ' + ', '.join(unresolved))
    # This version is a blocked contract, not a configurable READY implementation.
    raise ValueError(BLOCKED + ': new reviewed version and post-commit authorization required')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, help='Optional assembled metadata series; raw files never read')
    args = parser.parse_args(argv)
    try:
        acquisition_gate(read_json(ROOT / LOCK_PATH), read_json(args.manifest) if args.manifest else None)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc))
        return 2
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
