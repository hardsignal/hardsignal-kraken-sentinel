"""Exact blocked recovery descendant transition; read-only Git/file validation."""
import hashlib
import json
from pathlib import Path
import subprocess

from provenance import v2_execution_contract_v1 as execution

BASE = '77035ae9aca0fc35d8979cca5662020f396b3c84'
STEM = 'episode-component-tracking-v2-v2-acquisition-settings-recovery-v1'
DOC = 'docs/' + STEM + '.md'
DATA = 'results/' + STEM + '.json'
TEST = 'tests/test_episode_component_tracking_v2_v2_acquisition_settings_recovery.py'
LEGACY = 'analysis/provenance/v2_acquisition_lock_v1.py'
HELPER = 'analysis/provenance/v2_acquisition_settings_recovery_v1.py'
BINDING = 'results/episode-component-tracking-v2-v2-acquisition-settings-recovery-provenance-v1.json'
RECOVERY_PATHS = {DOC, DATA, TEST}
HISTORICAL_PATHS = RECOVERY_PATHS | {LEGACY, HELPER, BINDING}
PATHS = HISTORICAL_PATHS | execution.PATHS
ORIGINAL_RECOVERY_SHA256 = {
    DOC: 'c05980aa743a24168eee03eca42b4dd868f24cf45c14a00e29075eec70ce0f6a',
    DATA: '5563adc955f0a6037e8264c8403c468e80eda3150a15c6f60693d6c3696169fd',
    TEST: '105cbbd81251692bd5894685e9def96a6317f513e4b17be34c6ef1190bc2968e',
}
LEGACY_SHA256 = 'cf3cea07f51a6b859d0da73f14d4ff4cc8c5ef742cd4c0a49966a91009792471'
DECISIONS = {
    'recovery': 'V2_ACQUISITION_SETTINGS_RECOVERY_RECORDED_BLOCKED',
    'acquisition': 'V2_ACQUISITION_LOCK_BLOCKED',
    'preregistration': 'V2_DISCRIMINATION_EXPERIMENT_PREREGISTERED',
    'stage37': 'STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def require(condition, label):
    if not condition:
        raise ValueError('provenance drift / source hash drift: ' + label)


def validate(root):
    """Permit exact preparation at BASE; subsequently require committed bytes."""
    root = Path(root)
    execution_manifest = execution.validate(root)
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'],
                   cwd=root, check=True, capture_output=True)
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    raw = (root / BINDING).read_bytes()
    manifest = json.loads(raw)
    require(set(manifest) == {'format', 'parent_checkpoint', 'recovery_paths',
        'integration_paths', 'original_recovery_sha256', 'historical_sha256',
        'current_sha256', 'decisions', 'test_transition'}, 'recovery manifest fields')
    require(manifest['format'] == 'KRAKEN_V2_ACQUISITION_SETTINGS_RECOVERY_PROVENANCE_V1'
        and manifest['parent_checkpoint'] == BASE
        and manifest['recovery_paths'] == sorted(RECOVERY_PATHS)
        and manifest['integration_paths'] == sorted(HISTORICAL_PATHS - RECOVERY_PATHS)
        and manifest['original_recovery_sha256'] == ORIGINAL_RECOVERY_SHA256
        and manifest['historical_sha256'] == {LEGACY: LEGACY_SHA256}
        and manifest['decisions'] == DECISIONS
        and manifest['test_transition'] == 'Only descendant-scope validation and additional provenance regressions; original test was uncommitted, not present at BASE.',
        'recovery manifest metadata')
    require(set(manifest['current_sha256']) == HISTORICAL_PATHS - {BINDING}, 'exact current path inventory')
    require(sha(git(root, 'show', BASE + ':' + LEGACY)) == LEGACY_SHA256,
            'historical acquisition helper')
    for path in (DOC, DATA):
        require(manifest['current_sha256'][path] == ORIGINAL_RECOVERY_SHA256[path],
                'immutable recovery evidence ' + path)
    for path, expected in manifest['current_sha256'].items():
        current_expected = execution_manifest['sha256'][path] if path == HELPER else expected
        if path == HELPER:
            require(expected == execution_manifest['historical_helper_sha256'], 'historical recovery helper')
        require(sha((root / path).read_bytes()) == current_expected, path)
        if head != BASE:
            committed_expected = expected if head == execution.BASE else current_expected
            require(sha(git(root, 'show', 'HEAD:' + path)) == committed_expected, 'committed ' + path)
    if head != BASE:
        require(raw == git(root, 'show', 'HEAD:' + BINDING), 'committed recovery manifest')
    changes = git(root, 'diff', '--name-status', BASE).decode().splitlines()
    for row in changes:
        status, path = row.split('\t')
        require(path in PATHS, 'unrecognized descendant ' + path)
        require(status == ('M' if path == LEGACY else 'A'), 'recovery change status ' + row)
    untracked = set(git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''}
    require(not (untracked - PATHS), 'unrecognized descendant ' + repr(sorted(untracked - PATHS)))
    # The exact transition covers all files, whether staged, unstaged or committed.
    require({row.split('\t')[1] for row in changes} | untracked == PATHS,
            'exact six-path recovery transition')
    for path, decision in {
        DATA: DECISIONS['recovery'],
        'results/episode-component-tracking-v2-v2-acquisition-lock.json': DECISIONS['acquisition'],
        'results/episode-component-tracking-v2-v2-discrimination-preregistration.json': DECISIONS['preregistration'],
        'results/episode-component-tracking-v2-stage37-configuration-selection.json': DECISIONS['stage37'],
    }.items():
        payload = json.loads((root / path).read_bytes())
        require(payload['decision'] == decision, 'blocked/deferred decision ' + path)
        if path == DATA:
            require(payload['state'] == 'BLOCKED_PENDING_ACQUISITION_SETTINGS'
                and payload['acquisition_authorized'] is False
                and payload['authorizing_commit'] is None, 'recovery never authorizes acquisition')
    return manifest
