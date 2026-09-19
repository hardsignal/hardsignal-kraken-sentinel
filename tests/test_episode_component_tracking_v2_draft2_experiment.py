"""Independent invariants for Draft 2; no raw IQ or historical writes."""
import itertools
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis'))
import episode_component_tracking_v2_draft2_experiment as m


class Draft2Tests(unittest.TestCase):
    def test_matrix(self):
        self.assertEqual(len(m.arms()), 160)
        self.assertEqual(len({a['arm_id'] for a in m.arms()}), 160)

    def test_power_conservation_all_resolutions(self):
        for n in (10923, 21846, 43692, 54615):
            f = np.fft.fftshift(np.fft.fftfreq(n, 1/m.FS))
            p = np.random.default_rng(n).exponential(size=n)
            q = m.rebin(f, p)
            self.assertTrue(np.all(q >= 0))
            self.assertAlmostEqual(q.sum()/p.sum(), 1., places=11)
            uniform = m.rebin(f, np.full(n, m.FS/n))
            np.testing.assert_allclose(uniform, 2.5, rtol=1e-10, atol=1e-10)

    def test_periodic_bin_split(self):
        n = 10000
        f = np.fft.fftshift(np.fft.fftfreq(n, 1/m.FS))
        p = np.zeros(n)
        p[0] = 1
        q = m.rebin(f, p)
        self.assertEqual(q[0], .5)
        self.assertEqual(q[-1], .5)
        self.assertEqual(q.sum(), 1.)

    def test_zero_extension(self):
        n = 10000
        f = np.fft.fftshift(np.fft.fftfreq(n, 1/m.FS))
        _, psd, _ = m.represent(f, np.full(n, 2.5), 'grid_sigma20')
        self.assertLess(psd[0], 1.)
        self.assertAlmostEqual(psd[1000], 1.)

    def test_fixture_inventory_and_truth(self):
        specs = list(m.synthetic_specs())
        self.assertEqual(len(specs), 100800)
        self.assertEqual(sum(s['kind']=='single' for s in specs), 14400)
        self.assertEqual({s['seed'] for s in specs}, set(range(100)))
        spec = dict(samples=10000, fwhm_hz=40, centre_hz=3000,
                    background='constant', seed=0, kind='single', contrast_db=20)
        f, p, centres = m.synthetic_spectrum(spec)
        density = p/2.5
        self.assertEqual(centres, [3000])
        self.assertAlmostEqual(density[np.argmin(abs(f-3000))], 100)
        self.assertAlmostEqual(density[np.argmin(abs(f-3020))], 50.5)
        f2, p2, _ = m.synthetic_spectrum(dict(spec, background='exponential', seed=3))
        np.testing.assert_array_equal(p2, m.synthetic_spectrum(dict(spec, background='exponential', seed=3))[1])
        self.assertTrue(np.all(p2 >= 0))

    def test_exact_path_partitions_and_margin(self):
        fragments = m.make_fragments([[(3000, 'A', 12)], [(3000, 'A', 12), (3025, 'B', 12)]])
        nodes = [c for f in fragments for c in f['components']]
        self.assertEqual(len(m.solve_group(nodes, 0)['hypotheses']), 1)
        self.assertEqual(len(m.solve_group(nodes, .25)['hypotheses']), 2)
        self.assertEqual(m.solve_group(nodes, 1)['optimum_links'], 1)

    def test_one_to_one_and_ambiguity(self):
        fragments = m.make_fragments([[(3000, 'A', 12), (3000, 'B', 26)]]*3)
        result = m.association(fragments, 'paths_margin0')
        self.assertEqual(result['retained_hypothesis_count'], 4)
        self.assertIsNone(result['primary'])
        self.assertEqual(result['structural_constraint_violations'], 0)
        for h in result['hypotheses']:
            ids = [i for p in h['paths'] for i in p]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(ids), 6)

    def test_global_margin_not_per_group(self):
        fs = m.make_fragments([[(3000, 'A', 12), (5000, 'B', 12)],
                              [(3000, 'A', 12), (3025, 'C', 12), (5000, 'B', 12), (5025, 'D', 12)]])
        result = m.association(fs, 'paths_margin0.25')
        self.assertEqual(result['retained_hypothesis_count'], 3)

    def test_original_denominator(self):
        fs = m.make_fragments([[(3000, 'A', 12)]]*3 + [[], []])
        self.assertIsNotNone(m.association(fs, 'paths_margin0')['primary'])
        fs.append(dict(usable_spectrum=False, components=[]))
        self.assertIsNone(m.association(fs, 'paths_margin0')['primary'])

    def test_boundaries(self):
        for offsets, links in [([0,50,100],2), ([0,50.000001,100],1), ([0,40,80,120],2)]:
            fs = m.make_fragments([[(3000+x, 'A', 12)] for x in offsets])
            result = m.association(fs, 'paths_margin0')
            self.assertEqual(result['optimum_links'], links)
            self.assertEqual(result['structural_constraint_violations'], 0)

    def test_deterministic_and_amplitude_blind(self):
        fs = m.make_fragments([[(3000, 'A', 12), (3050, 'B', 26)]]*3)
        a = m.association(fs, 'paths_margin1')
        b = m.association(fs, 'paths_margin1')
        self.assertEqual(m.d1.json_bytes(a), m.d1.json_bytes(b))
        for f in fs:
            for c in f['components']:
                c['contrast_db'] = 1000-c['contrast_db']
        self.assertEqual(m.d1.json_bytes(a), m.d1.json_bytes(m.association(fs, 'paths_margin1')))

    def test_limit_never_truncates_success(self):
        fs = m.make_fragments([[(3000, 'A', 12)]]*3)
        nodes = [c for f in fs for c in f['components']]
        with self.assertRaises(m.ComputationUnresolved):
            m.solve_group(nodes, 0, state_limit=1)
        fs = m.make_fragments([[(3000, 'A', 12), (3000, 'B', 12)]]*3)
        with self.assertRaises(m.ComputationUnresolved):
            m.solve_group([c for f in fs for c in f['components']], 0, hypothesis_limit=1)

    def test_missing_fragments(self):
        one = m.make_fragments([[(3000, 'A', 12)], [], [(3000, 'A', 12)], [(3000, 'A', 12)]])
        two = m.make_fragments([[(3000, 'A', 12)], [], [], [(3000, 'A', 12)]])
        self.assertIsNotNone(m.association(one, 'paths_margin0')['primary'])
        self.assertIsNone(m.association(two, 'paths_margin0')['primary'])

    def test_native_control_from_committed_spectrum(self):
        import json
        directory = ROOT/'results/episode-component-tracking-v2-draft1'/m.d1.CAPTURES[0]
        old = json.loads((directory/'components.json').read_text())['episodes'][0]['fragments'][0]
        with np.load(directory/'spectra.npz', allow_pickle=False) as a:
            cs = m.apply_width(m.detect(a['E001_F001_frequency_hz'], a['E001_F001_power'], 'native'), 200, 1, 1)
        for a, b in zip(cs, old['components']):
            for k in ('candidate_id', 'frequency_hz', 'width_hz', 'eligible_for_tracking', 'ineligibility_reasons'):
                self.assertEqual(a[k], b[k])
        self.assertEqual(len(cs), len(old['components']))

    def test_synthetic_merge_and_split_metrics(self):
        c = lambda lo, hi, peak: dict(interval_hz=[lo, hi], frequency_hz=peak, eligible_for_tracking=True)
        self.assertTrue(m.synthetic_metrics([c(0,30,10)], [10,20], 10)['merge'])
        self.assertFalse(m.synthetic_metrics([c(0,30,10)], [10,20], 10)['recovery'])
        self.assertTrue(m.synthetic_metrics([c(0,12,10),c(15,25,20)], [10,20], 10)['recovery'])
        self.assertTrue(m.synthetic_metrics([c(0,9,8),c(10,15,11)], [10], 10)['split'])

    def test_exact_solver_against_independent_edge_enumeration(self):
        fs = m.make_fragments([[(3000, 'A', 12), (3025, 'B', 12)],
                               [(3010, 'A', 12), (3040, 'B', 12)],
                               [(3020, 'A', 12), (3060, 'B', 12)]])
        nodes = [c for f in fs for c in f['components']]
        edges = [(i,j) for i,a in enumerate(nodes) for j,b in enumerate(nodes)
                 if b['fragment_index']-a['fragment_index'] in (1,2)
                 and abs(a['frequency_hz']-b['frequency_hz']) <= 50]
        valid = []
        for mask in range(1 << len(edges)):
            chosen = [e for k,e in enumerate(edges) if mask & (1<<k)]
            if len({a for a,b in chosen}) != len(chosen) or len({b for a,b in chosen}) != len(chosen):
                continue
            successor, incoming = dict(chosen), {b for a,b in chosen}
            paths = []
            for i in range(len(nodes)):
                if i in incoming:
                    continue
                p = [i]
                while p[-1] in successor:
                    p.append(successor[p[-1]])
                paths.append(p)
            if any(max(nodes[i]['frequency_hz'] for i in p)-min(nodes[i]['frequency_hz'] for i in p)>100 for p in paths):
                continue
            cost = sum(m.path_cost(p,nodes) for p in paths)
            ids = tuple(sorted(tuple(nodes[i]['candidate_id'] for i in p) for p in paths))
            valid.append((len(chosen),cost,ids))
        links = max(a for a,b,c in valid)
        minimum = min(b for a,b,c in valid if a==links)
        for margin in (0,.25,1):
            expected = {c for a,b,c in valid if a==links and b<=minimum+margin+1e-12}
            actual = m.solve_group(nodes,margin)
            self.assertEqual({tuple(sorted(map(tuple,h['paths']))) for h in actual['hypotheses']}, expected)

    def test_pair_fixture_power_ratio(self):
        spec = dict(samples=10000, fwhm_hz=10, centre_hz=3000, background='constant', seed=0,
                    kind='pair', contrast_db=26, separation_hz=400, power_ratio_db=12)
        f,p,truth = m.synthetic_spectrum(spec)
        self.assertEqual(truth,[3000,3400])
        signal = p/2.5-1
        peaks = [signal[np.argmin(abs(f-c))] for c in truth]
        self.assertAlmostEqual(10*np.log10(peaks[0]/peaks[1]),12)

    def test_output_overwrite_prohibited(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                m.run(Path(directory))

if __name__ == '__main__':
    unittest.main()
