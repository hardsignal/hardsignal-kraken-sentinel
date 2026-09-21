"""Read-only provenance checks for reviews integrated after their review checkpoint.

Original JSON/report bytes (including historical branches, test logs and hashes)
remain evidence of the original review, not assertions about the validation HEAD.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from provenance.stage37_gitignore_v1 import validate_gitignore

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-draft2-full-matrix'
REVIEW_CHECKPOINT = '6bd63ac90b9045ecb2eac3544ee63b035103428b'
REVIEW_COMMITS = {
    'definition': '43d2ebe395c12e40454836b02a03b503b6d8f865',
    'feasibility': '7392556eb45a969abdd8ad83185ecb3c0cf887c5',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def validate_checkpoint(review_checkpoint, integration_head='HEAD'):
    if review_checkpoint != REVIEW_CHECKPOINT:
        raise ValueError('Wrong immutable review checkpoint')
    result = subprocess.run(
        ['git', 'merge-base', '--is-ancestor', review_checkpoint, integration_head],
        cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise ValueError('Validation HEAD does not contain the review checkpoint')


def validate_files(inventory, read_bytes, tracked_paths):
    """Check exactly baseline paths; additional tracked review files are allowed."""
    for name, expected in inventory.items():
        if name not in tracked_paths:
            raise ValueError(f'Baseline path no longer tracked: {name}')
        try:
            actual = read_bytes(name)
        except FileNotFoundError as exc:
            raise ValueError(f'Missing baseline file: {name}') from exc
        if name == '.gitignore':
            validate_gitignore(ROOT, expected, actual)
            continue
        if hashlib.sha256(actual).hexdigest() != expected:
            raise ValueError(f'Baseline bytes changed: {name}')


def validate_artifact(path, actual, revision):
    """Bind complete review payloads independently to their integration commit.

    These commits store the original review artifacts; they are NOT the original
    review checkpoint. Pinning full bytes also protects recorded baseline hashes.
    """
    expected = git('show', f'{revision}:{path}')
    if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
        raise ValueError(f'Original review artifact changed: {path}')


def validate_review(kind):
    revision = REVIEW_COMMITS[kind]
    manifest = 'canonical-arms' if kind == 'definition' else 'risk-manifest'
    review_path = f'results/{STEM}-{kind}-review.json'
    paths = (review_path, f'results/{STEM}-{manifest}.json',
             f'docs/{STEM}-{kind}-review.md')
    for path in paths:
        validate_artifact(path, (ROOT / path).read_bytes(), revision)
    review = json.loads((ROOT / review_path).read_bytes())
    baseline = review['before'] if kind == 'definition' else review['integrity']['before']
    validate_checkpoint(baseline['head'])
    inventory = baseline['files' if kind == 'definition' else 'sha256']
    checkpoint_paths = set(git('ls-tree', '-r', '--name-only', '-z', REVIEW_CHECKPOINT)
                           .decode().rstrip('\0').split('\0'))
    if set(inventory) != checkpoint_paths:
        raise ValueError('Recorded baseline does not cover the checkpoint tree')
    tracked = set(git('ls-files', '-z').decode().rstrip('\0').split('\0'))
    validate_files(inventory, lambda name: (ROOT / name).read_bytes(), tracked)
    return len(inventory)
