"""Read-only review artifact checks; no candidate generation or scientific execution."""
import collections
import hashlib
import json
from pathlib import Path
import unittest

from draft2_review_provenance import validate_review

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-draft2-full-matrix'


def read(path):
    return json.loads((ROOT / path).read_text())


class FeasibilityReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = read(f'results/{STEM}-feasibility-review.json')
        cls.manifest = read(f'results/{STEM}-risk-manifest.json')

    def test_exact_matrix_inventory_and_distribution(self):
        original = read('results/episode-component-tracking-v2-draft2-experiment/arms.json')
        keys = ('arm_id', 'representation', 'width_hz', 'association')
        expected = [{k: a[k] for k in keys} for a in original]
        actual = [{k: a[k] for k in keys} for a in self.manifest['arms']]
        self.assertEqual(actual, expected)
        self.assertEqual(len({a['arm_id'] for a in actual}), 160)
        counts = dict(collections.Counter(a['risk_category'] for a in self.manifest['arms']))
        self.assertEqual(counts, self.manifest['distribution'])
        self.assertEqual(counts, self.review['risk_distribution'])
        for a in self.manifest['arms']:
            self.assertTrue(a['risk_reason'])
            self.assertTrue(a['expected_exact_dispatch_route'])
            if a['risk_category'] == 'UNKNOWN_WITHOUT_EXECUTION':
                self.assertTrue(a['unsupported_or_unknown_structural_feature'])

    def test_resource_summary_and_frozen_limits(self):
        summary = read('results/episode-component-tracking-v2-draft2-six-capture-corrected-summary.json')
        for key, value in self.review['resource_maxima_independently_verified'].items():
            self.assertEqual(value, summary[key]['value'])
        for row in self.review['resource_envelope']:
            self.assertAlmostEqual(row['percent_of_limit'], 100 * row['value'] / row['limit'])
            self.assertLess(row['value'], row['limit'])
        limits = self.review['frozen_limits']
        self.assertEqual([limits[k] for k in ('max_states', 'max_transitions', 'max_seconds',
                         'max_polynomial_bytes', 'max_query_calls', 'max_query_seconds',
                         'family_construction_seconds', 'worker_timeout_seconds', 'worker_rss_kib')],
                         [250000, 5000000, 60, 33554432, 5000, 120, 60, 400, 524288])

    def test_saved_family_coverage_is_complete_and_bound(self):
        base = ROOT / 'results/episode-component-tracking-v2-draft2-six-capture-corrected-regression'
        families = {str(p.parent.relative_to(base)): p for p in base.glob('*/*/family.json')}
        rows = self.review['family_coverage']
        self.assertEqual(len(rows), 123)
        self.assertEqual({r['case'] for r in rows}, set(families))
        for row in rows:
            p = families[row['case']]
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), row['family_sha256'])
            count = json.loads((p.parent / 'count-outcome.json').read_text())
            self.assertEqual(row['exact_route'], count['method'])
            self.assertEqual(row['state'], 'EXACT')

    def test_original_tracked_inventory_is_byte_identical(self):
        self.assertEqual(validate_review('feasibility'), 3068)

    def test_no_launch_approval_is_inferred(self):
        self.assertEqual(self.review['decision'], 'COMPUTATIONAL_BLOCKERS_REMAIN')
        self.assertTrue(self.review['blockers'])
        self.assertEqual(self.review['concurrency']['recommended_initial_workers'], 1)
        self.assertEqual(self.review['concurrency']['conditional_max_workers'], 2)


if __name__ == '__main__':
    unittest.main()
