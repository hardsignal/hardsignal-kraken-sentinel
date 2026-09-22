"""Exact execution-preparation descendant, without changing historical gates."""
import hashlib
import json
from pathlib import Path
import subprocess

BASE = '591640798be56d2ee3a862d963e11d35d38890da'
HELPER = 'analysis/provenance/v2_acquisition_settings_recovery_v1.py'
BINDING = 'results/episode-component-tracking-v2-v2-execution-provenance-v1.json'
PATHS = {HELPER, BINDING,
    'analysis/provenance/v2_execution_contract_v1.py',
    'capture/v2_acquisition_runner.py',
    'results/episode-component-tracking-v2-v2-execution-contract-v1.json',
    'docs/episode-component-tracking-v2-v2-execution-contract-v1.md',
    'tests/test_episode_component_tracking_v2_v2_execution_contract.py'}


def validate(root):
    root = Path(root)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root)
    def require(ok, label):
        if not ok:
            raise ValueError('unrecognized descendant / source hash drift: ' + label)
    def sha(raw):
        return hashlib.sha256(raw).hexdigest()
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], cwd=root,
                   check=True, capture_output=True)
    raw = (root / BINDING).read_bytes()
    m = json.loads(raw)
    require(set(m) == {'base', 'decision', 'historical_helper_sha256', 'sha256'}, 'fields')
    require(m['base'] == BASE and m['decision'] ==
            'V2_ACQUISITION_EXECUTION_CONTRACT_REVIEWED_BLOCKED', 'metadata')
    require(m['historical_helper_sha256'] == sha(git('show', BASE + ':' + HELPER)), 'history')
    require(set(m['sha256']) == PATHS - {BINDING}, 'inventory')
    head = git('rev-parse', 'HEAD').decode().strip()
    for p, h in m['sha256'].items():
        require(sha((root / p).read_bytes()) == h, p)
        if head != BASE:
            require(sha(git('show', 'HEAD:' + p)) == h, 'committed ' + p)
    if head != BASE:
        require(raw == git('show', 'HEAD:' + BINDING), 'committed binding')
    rows = git('diff', '--name-status', BASE).decode().splitlines()
    untracked = set(git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''}
    for row in rows:
        status, path = row.split('\t')
        require(path in PATHS and status == ('M' if path == HELPER else 'A'), row)
    require({row.split('\t')[1] for row in rows} | untracked == PATHS, 'exact execution paths')
    c = json.loads((root / 'results/episode-component-tracking-v2-v2-execution-contract-v1.json').read_bytes())
    require(c['decision'] == m['decision'] and c['acquisition_authorized'] is False
            and c['state'] == 'BLOCKED_PENDING_ACQUISITION_SETTINGS', 'blocked decision')
    return m
