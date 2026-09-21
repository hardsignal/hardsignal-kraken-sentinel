"""Adversarial provenance checks using saved bytes only; no scientific imports."""
import hashlib
import json
import unittest

from draft2_review_provenance import (
    ROOT, STEM, REVIEW_CHECKPOINT, REVIEW_COMMITS, git, validate_artifact,
    validate_checkpoint, validate_files,
)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


class ReviewIntegrationTests(unittest.TestCase):
    def test_checkpoint_and_descendant_head_are_accepted(self):
        validate_checkpoint(REVIEW_CHECKPOINT, REVIEW_CHECKPOINT)
        validate_checkpoint(REVIEW_CHECKPOINT)

    def test_wrong_checkpoint_and_non_descendant_history_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Wrong immutable'):
            validate_checkpoint(REVIEW_COMMITS['feasibility'])
        parent = git('rev-parse', REVIEW_CHECKPOINT + '^').decode().strip()
        with self.assertRaisesRegex(ValueError, 'does not contain'):
            validate_checkpoint(REVIEW_CHECKPOINT, parent)

    def test_additional_tracked_review_files_are_allowed(self):
        data = b'original source/result bytes\n'
        validate_files({'original': hashlib.sha256(data).hexdigest()},
                       lambda name: data, {'original', 'later-review.json'})

    def test_every_baseline_path_rejects_mutation_missing_or_untracked_file(self):
        review = json.loads((ROOT / f'results/{STEM}-definition-review.json').read_bytes())
        # Exercise every recorded path independently without modifying the worktree.
        def missing(name):
            raise FileNotFoundError(name)
        for name, expected in review['before']['files'].items():
            inventory = {name: expected}
            with self.subTest(path=name):
                with self.assertRaisesRegex(ValueError, 'bytes changed'):
                    validate_files(inventory, lambda name: b'mutated bytes', {name})
                with self.assertRaisesRegex(ValueError, 'Missing baseline'):
                    validate_files(inventory, missing, {name})
                with self.assertRaisesRegex(ValueError, 'no longer tracked'):
                    validate_files(inventory, lambda name: b'', set())

    def test_review_payload_and_decision_mutations_are_rejected(self):
        for kind, revision in REVIEW_COMMITS.items():
            path = f'results/{STEM}-{kind}-review.json'
            original = json.loads((ROOT / path).read_bytes())
            validate_artifact(path, encode(original), revision)
            for key in ('decision', 'tests', 'before' if kind == 'definition' else 'resource_envelope'):
                changed = dict(original)
                changed[key] = 'tampered'
                with self.subTest(kind=kind, key=key), self.assertRaises(ValueError):
                    validate_artifact(path, encode(changed), revision)

    def test_arm_inventory_and_risk_mutations_are_rejected(self):
        for kind, suffix in (('definition', 'canonical-arms'), ('feasibility', 'risk-manifest')):
            path = f'results/{STEM}-{suffix}.json'
            validate_artifact(path, encode(json.loads((ROOT / path).read_bytes())),
                              REVIEW_COMMITS[kind])
            for mutation in ('inventory', 'payload'):
                changed = json.loads((ROOT / path).read_bytes())
                if mutation == 'inventory':
                    changed['arms'].pop()
                elif kind == 'definition':
                    changed['scientific_configuration']['grid']['bin_width_hz'] = 3
                else:
                    changed['distribution']['LOW_COMPUTATIONAL_RISK'] = 2
                with self.subTest(kind=kind, mutation=mutation), self.assertRaises(ValueError):
                    validate_artifact(path, encode(changed), REVIEW_COMMITS[kind])


if __name__ == '__main__':
    unittest.main()
