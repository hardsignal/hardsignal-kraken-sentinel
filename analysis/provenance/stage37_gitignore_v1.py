"""Read-only binding of the sole Stage 36 post-execution ignore transition."""
import hashlib
import json
from pathlib import Path
import subprocess

FREEZE = '0df44abb54231d5e8bfe84fe316ebbcf10d3130c'
EXECUTION = 'e559d63e3a88822ff5443d5a83d0ad60fc3e3348'
HISTORICAL_SHA256 = '24459e7feded9172d32c80b041c4ef76fe903f720037559a0f44ff3e82ea0d7a'
FROZEN_SHA256 = '3bea5d21bee9a0982907fab3c62f8a873010c8e5d8e4722722a967ba103439ba'
ADDITION = b'\nresults/episode-component-tracking-v2-draft2-full-matrix-exact-v1/\n'
RUNNER = 'analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py'
REVIEW_VALIDATOR = 'tests/draft2_review_provenance.py'
ORIGINAL_REVIEW_VALIDATOR_SHA256 = '77083f4dbf33f755b3cfb00331d0bebb7e54eac0b88e31ea01bbed4152575920'
HELPER = 'analysis/provenance/stage37_gitignore_v1.py'
BINDING = 'results/episode-component-tracking-v2-stage37-provenance-repair-v1.json'
ORIGINAL_RUNNER_SHA256 = 'e727324d756a4c6635d2ef11844656ffbbcc34ebfb5f60c7dc6777952cbb5392'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def historical_bytes(root, revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=root)


def validate_gitignore(root, expected, actual):
    """Require historical truth AND the exact freeze state, never either/or."""
    old = historical_bytes(root, EXECUTION, '.gitignore')
    frozen = historical_bytes(root, FREEZE, '.gitignore')
    if (expected != HISTORICAL_SHA256 or sha(old) != expected
            or sha(frozen) != FROZEN_SHA256 or frozen != old + ADDITION):
        raise ValueError('Historical .gitignore transition binding drift')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', FREEZE, 'HEAD'],
                      cwd=root, capture_output=True).returncode != 0:
        raise ValueError('HEAD does not contain evidence-freeze checkpoint')
    if actual != frozen:
        raise ValueError('Provenance source hash drift / Baseline bytes changed: .gitignore')


def validate_repair(root, runner_digest):
    """Keep launch binding V2 immutable; bind the verification-only runner edit."""
    from provenance.v2_acquisition_lock_v1 import historical_digest
    historical_runner = historical_digest(root, RUNNER, runner_digest)
    historical_review = historical_digest(root, REVIEW_VALIDATOR, sha((root / REVIEW_VALIDATOR).read_bytes()))
    historical_helper = historical_digest(root, HELPER, sha((root / HELPER).read_bytes()))
    binding = json.loads((root / BINDING).read_bytes())
    expected = dict(format='KRAKEN_STAGE37_PROVENANCE_REPAIR_V1',
                    freeze_checkpoint=FREEZE, execution_checkpoint=EXECUTION,
                    historical_gitignore_sha256=HISTORICAL_SHA256,
                    frozen_gitignore_sha256=FROZEN_SHA256,
                    original_runner_sha256=ORIGINAL_RUNNER_SHA256,
                    runner_sha256=historical_runner,
                    original_review_validator_sha256=ORIGINAL_REVIEW_VALIDATOR_SHA256,
                    review_validator_sha256=historical_review,
                    helper_sha256=historical_helper)
    if (binding != expected or
            sha(historical_bytes(root, FREEZE, RUNNER)) != ORIGINAL_RUNNER_SHA256 or
            sha(historical_bytes(root, FREEZE, REVIEW_VALIDATOR)) != ORIGINAL_REVIEW_VALIDATOR_SHA256):
        raise ValueError('Launch binding / exact runner source hash drift (Stage 37 repair)')
    return ORIGINAL_RUNNER_SHA256


def effective_historical_digest(root, path, actual_digest):
    """Validate explicitly bound repair files before returning their old digest."""
    if path in (RUNNER, REVIEW_VALIDATOR):
        validate_repair(root, actual_digest if path == RUNNER else sha((root / RUNNER).read_bytes()))
        if path == REVIEW_VALIDATOR and actual_digest != sha((root / REVIEW_VALIDATOR).read_bytes()):
            raise ValueError('Provenance source hash drift: ' + path)
        return ORIGINAL_RUNNER_SHA256 if path == RUNNER else ORIGINAL_REVIEW_VALIDATOR_SHA256
    return actual_digest
