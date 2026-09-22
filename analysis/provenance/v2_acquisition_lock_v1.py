"""Exact read-only descendant authorization; historical inventories stay historical.

The separately hashed transition manifest avoids self-embedded validator hashes.
At the acquisition checkpoint it permits preparing the repair; at every later
HEAD the manifest and repaired validators must also match committed bytes.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from provenance import v2_acquisition_settings_recovery_v1 as recovery

PARENT = 'c98ad53a6d278140c98ecbe045f2462c24f5852f'
ACQUISITION = 'fed6a58096804859319b11b125f490201ffbb56d'
BINDING = 'results/episode-component-tracking-v2-v2-acquisition-provenance-v1.json'
ACQUISITION_SHA256 = {
    'analysis/validate_episode_component_tracking_v2_v2_acquisition_manifest.py':
        '5e46861256fd8e61e5b27bf16817a028976e097a6a6ee3a94acae8590a1b2b9e',
    'docs/episode-component-tracking-v2-v2-acquisition-lock.md':
        '97e3fee8e60395e9fcae613a9f837c9e9864190fad526f3430fd8809fa87bdf4',
    'results/episode-component-tracking-v2-v2-acquisition-lock.json':
        '2225cb87cb7f7802a8fb414c4d75133f03639a6d8d8cc742a02baa4977a07ce9',
    'results/episode-component-tracking-v2-v2-acquisition-manifest-schema-v1.json':
        '9139863108894fa5a37db556369940c3f4d922185705d434494584882b237a70',
    'tests/test_episode_component_tracking_v2_v2_acquisition_lock.py':
        '5eb31eec23ebc2a7aaa27f2b29ebe83d59a510f3e0afd66c2e97a412d70f9df1',
}
TRANSITIONS = {
    'analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py',
    'analysis/provenance/stage37_gitignore_v1.py',
    'tests/draft2_review_provenance.py',
    'tests/test_episode_component_tracking_v2_stage37_configuration_selection.py',
    'tests/test_episode_component_tracking_v2_v2_discrimination_preregistration.py',
    'analysis/validate_episode_component_tracking_v2_v2_acquisition_manifest.py',
    'tests/test_episode_component_tracking_v2_v2_acquisition_lock.py',
}
ADDITIONS = {
    'analysis/provenance/v2_acquisition_lock_v1.py',
    'tests/test_episode_component_tracking_v2_draft2_full_matrix_acquisition_provenance.py',
}
REPAIR_PATHS = TRANSITIONS | ADDITIONS | {BINDING}
AUTHORIZED_PATHS = set(ACQUISITION_SHA256) | REPAIR_PATHS | recovery.PATHS
DECISIONS = {
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
    """Verify exact checkpoint additions, all transitions and closed current scope."""
    root = Path(root)
    recovery_manifest = recovery.validate(root)
    for earlier, later in ((PARENT, ACQUISITION), (ACQUISITION, 'HEAD')):
        subprocess.run(['git', 'merge-base', '--is-ancestor', earlier, later],
                       cwd=root, check=True, capture_output=True)
    require(git(root, 'rev-parse', ACQUISITION + '^').decode().strip() == PARENT,
            'acquisition parent checkpoint')
    added = git(root, 'diff', '--name-status', PARENT, ACQUISITION).decode().splitlines()
    require(set(added) == {'A\t' + p for p in ACQUISITION_SHA256}, 'exact five additions')
    raw = (root / BINDING).read_bytes()
    manifest = json.loads(raw)
    require(set(manifest) == {'format', 'parent_checkpoint', 'acquisition_checkpoint',
                             'frozen_sha256', 'decisions', 'historical_sha256',
                             'current_sha256'}, 'manifest fields')
    require(manifest['format'] == 'KRAKEN_V2_ACQUISITION_PROVENANCE_V1'
            and manifest['parent_checkpoint'] == PARENT
            and manifest['acquisition_checkpoint'] == ACQUISITION
            and manifest['frozen_sha256'] == ACQUISITION_SHA256
            and manifest['decisions'] == DECISIONS, 'manifest metadata')
    require(set(manifest['historical_sha256']) == TRANSITIONS, 'historical path set')
    require(set(manifest['current_sha256']) == TRANSITIONS | ADDITIONS, 'repair path set')
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    if head != ACQUISITION:
        require(raw == git(root, 'show', 'HEAD:' + BINDING), 'committed manifest')
    for path, expected in manifest['historical_sha256'].items():
        for revision in ((ACQUISITION,) if path in ACQUISITION_SHA256 else (PARENT, ACQUISITION)):
            require(sha(git(root, 'show', revision + ':' + path)) == expected,
                    revision + ':' + path)
    for path, expected in ACQUISITION_SHA256.items():
        require(sha(git(root, 'show', ACQUISITION + ':' + path)) == expected,
                'acquisition ' + path)
        if path in TRANSITIONS:
            require(manifest['historical_sha256'][path] == expected, 'historical acquisition ' + path)
    for path, expected in (ACQUISITION_SHA256 | manifest['current_sha256']).items():
        current_expected = recovery_manifest['current_sha256'][path] if path == recovery.LEGACY else expected
        if path == recovery.LEGACY:
            require(expected == recovery.LEGACY_SHA256, 'historical acquisition helper binding')
        require(sha((root / path).read_bytes()) == current_expected, path)
        if head != ACQUISITION:
            committed_expected = expected if head == recovery.BASE else current_expected
            require(sha(git(root, 'show', 'HEAD:' + path)) == committed_expected, 'committed ' + path)
    changed = git(root, 'diff', '--name-only', '-z', ACQUISITION)
    untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z')
    unexpected = set((changed + untracked).decode().split('\0')) - {''} - REPAIR_PATHS - recovery.PATHS
    if unexpected:
        raise ValueError('unrecognized descendant paths: ' + repr(sorted(unexpected)))
    for suffix, decision in (
            ('v2-acquisition-lock', DECISIONS['acquisition']),
            ('v2-discrimination-preregistration', DECISIONS['preregistration']),
            ('stage37-configuration-selection', DECISIONS['stage37'])):
        payload = json.loads((root / ('results/episode-component-tracking-v2-' + suffix + '.json')).read_bytes())
        require(payload['decision'] == decision, 'decision ' + suffix)
        if suffix == 'v2-acquisition-lock':
            require(payload['state'] == 'BLOCKED_PENDING_ACQUISITION_SETTINGS'
                    and payload['parent_commit'] == PARENT, 'blocked state / parent')
    return manifest


def historical_digest(root, path, actual):
    """Authorize a current validator, then project only its checkpoint digest."""
    manifest = validate(root)
    require(actual == manifest['current_sha256'][path], path)
    return manifest['historical_sha256'][path]
