import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from analysis import episode_component_tracking_v2_draft1 as method


def fragment(index, frequencies=(), usable=True, power=1.0):
    return {"fragment_index": index, "usable_spectrum": usable, "components": [
        {"fragment_index": index, "candidate_id": f"F{index:03d}_C{j:03d}",
         "frequency_hz": float(f), "eligible_for_tracking": True,
         "contrast_db": 15., "width_hz": 10., "peak_power": power}
        for j, f in enumerate(frequencies, 1)
    ]}


def tone(n, frequency, amplitude=1.0):
    return amplitude * np.exp(2j * np.pi * frequency * np.arange(n) / 25000)


def synthetic_bundle(root, count=3):
    """New temporary evidence, never any existing repository artifact."""
    bundle = root / "SYNTHETIC-DRAFT1"
    bundle.mkdir()
    records, members, v1_fragments = [], [], []
    rng = np.random.default_rng(4)
    for index in range(count):
        n = 10923
        freq = -2300 * 25000 / n
        iq = tone(n, freq) + 0.02 * (rng.normal(size=n) + 1j * rng.normal(size=n))
        raw = iq.astype("<c16").tobytes()
        path = root / f"fragment{index}.iq"
        path.write_bytes(raw)
        rec = {"path": str(path), "name": path.name, "size_bytes": len(raw),
               "sha256": hashlib.sha256(raw).hexdigest()}
        records.append(rec)
        members.append({**rec, "mtime_ns": 1000000000 + index * 1000000000})
        v1_fragments.append({"path": str(path), "size_bytes": len(raw), "samples": n,
                             "strongest_component_offset_hz": freq})
    manifest = {"format": "HARDSIGNAL_KRAKEN_CAPTURE_MANIFEST_V1", "capture_id": bundle.name,
                "files": records, "new_iq_file_count": count}
    grouping = {"format": "HARDSIGNAL_KRAKEN_EPISODES_V1", "capture_id": bundle.name,
                "episode_gap_seconds": 4., "comparison": ">", "episode_count": 1,
                "file_count": count,
                "episodes": [{"episode": 1, "file_count": count, "files": members}]}
    old = {"format": "HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V1", "capture_id": bundle.name,
           "sample_rate_hz": 25000., "iq_dtype": "complex128", "episode_count": 1,
           "episodes": [{"episode": 1, "fragment_count": count, "fragments": v1_fragments,
                         "median_strongest_component_offset_hz": freq,
                         "strongest_component_offset_spread_hz": 0.}]}
    for name, obj in (("manifest.json", manifest), ("episodes.json", grouping),
                      ("episode-features-v1.json", old)):
        (bundle / name).write_bytes(method.json_bytes(obj))
    (bundle / "files.sha256").write_text("".join(f"{r['sha256']}  {r['path']}\n" for r in records))
    return bundle


class SpectrumTests(unittest.TestCase):
    def test_candidate_region_inclusive_boundaries(self):
        values = np.array([-11500.001, -11500, -100, -99.999, 0, 99.999, 100, 11500, 11500.001])
        self.assertEqual(method.eligible_bins(values).tolist(),
                         [False, True, True, False, False, False, True, True, False])

    def test_background_exact_same_side_neighbourhood(self):
        n = 2500
        freq = np.fft.fftshift(np.fft.fftfreq(n, 1 / 25000))
        power = np.arange(n, dtype=float) + 1
        eligible = method.eligible_bins(freq)
        background, valid, counts = method.local_background(freq, power, eligible)
        for target in (-11500, -100, 100, 500, 11500):
            k = np.flatnonzero(freq == target)[0]
            mask = eligible & (np.sign(freq) == np.sign(target)) & (np.abs(freq - target) >= 50) & (np.abs(freq - target) <= 500)
            self.assertTrue(valid[k])
            self.assertEqual(counts[k], np.count_nonzero(mask))
            self.assertEqual(background[k], np.median(power[mask]))

    def test_background_minimum_bin_count(self):
        freq = np.fft.fftshift(np.fft.fftfreq(100, 1 / 25000))
        _, valid, counts = method.local_background(freq, np.ones(100), method.eligible_bins(freq))
        self.assertFalse(np.any(valid))
        self.assertTrue(np.all(counts < 32))

    def detect(self, levels, start=1400, step=10):
        n = 25000 // step
        freq = np.fft.fftshift(np.fft.fftfreq(n, 1 / 25000))
        power = np.ones(n)
        power[start:start + len(levels)] = 10 ** (np.array(levels) / 10)
        return method.detect_components(freq, power, np.ones(n), np.ones(n, bool), method.eligible_bins(freq))

    def test_contrast_boundaries_and_lower_frequency_power_tie(self):
        components, _, _, labels = self.detect([6, 10, 10, 6])
        self.assertEqual(len(components), 1)
        c = components[0]
        self.assertEqual((c["first_bin"], c["last_bin"], c["peak_bin"]), (1400, 1403, 1401))
        self.assertEqual(c["local_maxima_count"], 1)
        self.assertEqual(np.count_nonzero(labels), 4)
        self.assertEqual(self.detect([6, 9.999, 6])[0], [])
        # The weaker-than-6 dB valley splits two detections; exactly 6 joins them.
        self.assertEqual(len(self.detect([10, 5.999, 10])[0]), 2)
        self.assertEqual(len(self.detect([10, 6, 10])[0]), 1)

    def test_width_boundary_and_multiple_maxima(self):
        c = self.detect([10] * 20)[0][0]
        self.assertAlmostEqual(c["width_hz"], 200.)
        self.assertTrue(c["eligible_for_tracking"])
        c = self.detect([10] * 21)[0][0]
        self.assertIn("BROAD_COMPONENT", c["flags"])
        c = self.detect([10, 6, 10])[0][0]
        self.assertEqual(c["local_maxima_count"], 2)
        self.assertIn("MULTIPLE_LOCAL_MAXIMA", c["flags"])

    def test_region_boundary_and_background_contact(self):
        n = 2500
        freq = np.fft.fftshift(np.fft.fftfreq(n, 1 / 25000))
        power, background, valid = np.ones(n), np.ones(n), np.ones(n, bool)
        k = int(np.flatnonzero(freq == 100)[0])
        power[k] = 10
        c = method.detect_components(freq, power, background, valid, method.eligible_bins(freq))[0][0]
        self.assertIn("REGION_BOUNDARY_COMPONENT", c["flags"])
        power[k] = 1
        k = int(np.flatnonzero(freq == 1000)[0])
        power[k] = 10
        valid[k - 1] = False
        c = method.detect_components(freq, power, background, valid, method.eligible_bins(freq))[0][0]
        self.assertIn("BACKGROUND_UNESTIMABLE", c["flags"])

    def test_known_signed_tones_variable_lengths_and_full_samples(self):
        for n in (10923, 21846, 43692, 54615):
            for sign in (-1, 1):
                frequency = sign * round(5300 * n / 25000) * 25000 / n
                rng = np.random.default_rng(n)
                iq = tone(n, frequency) + .01 * (rng.normal(size=n) + 1j * rng.normal(size=n))
                components, arrays, _, usable, selected = method.analyse_spectrum(iq)
                self.assertTrue(usable)
                self.assertEqual(len(arrays["power"]), n)
                self.assertAlmostEqual(selected, frequency, places=8)
                self.assertTrue(any(abs(c["frequency_hz"] - frequency) < 1e-6 for c in components))
                self.assertAlmostEqual(float(np.sum(arrays["power"])), 1., delta=.003)

    def test_dc_edge_weak_and_degenerate(self):
        for iq, flag in ((np.zeros(100, complex), "ZERO_SPECTRAL_POWER"),
                         (np.ones(100, complex), "ZERO_SPECTRAL_POWER"),
                         (np.ones(2, complex), "TOO_SHORT"),
                         (np.array([1, 2, np.nan, 4], complex), "NONFINITE_IQ")):
            components, _, flags, usable, _ = method.analyse_spectrum(iq)
            self.assertFalse(usable)
            self.assertEqual(components, [])
            self.assertIn(flag, flags)
        for hz, flag in ((25, "GLOBAL_MAX_IN_DC_EXCLUSION"),
                         (-12455, "GLOBAL_MAX_IN_EDGE_EXCLUSION")):
            _, _, flags, _, _ = method.analyse_spectrum(tone(25000, hz))
            self.assertIn(flag, flags)
        self.assertEqual(self.detect([5.999, 5, 4])[0], [])


class TrackingTests(unittest.TestCase):
    def test_detector_and_tracker_together_preserve_weaker_recurring_tone(self):
        n = 10923
        persistent = -2300 * 25000 / n
        fragments = []
        for index in range(1, 6):
            rng = np.random.default_rng(index)
            unrelated = (1000 + 200 * index) * 25000 / n
            iq = tone(n, persistent) + tone(n, unrelated, 4.) + .02 * (rng.normal(size=n) + 1j * rng.normal(size=n))
            components, _, _, usable, global_frequency = method.analyse_spectrum(iq)
            self.assertAlmostEqual(global_frequency, unrelated, places=8)
            for c in components:
                c.update(fragment_index=index, candidate_id=f"F{index}_C{c['component_index']}")
            fragments.append({"fragment_index": index, "components": components, "usable_spectrum": usable})
        result = method.track_episode(fragments)
        matching = [g for g in result["groups"] if g["coherent"]
                    and abs(g["summary"]["median_hz"] - persistent) < 1e-6]
        self.assertEqual(len(matching), 1)
        self.assertTrue(matching[0]["persistent"])
        self.assertEqual(matching[0]["support_count"], 5)
        # The specified local-contrast test can also detect recurring noise.
        # It must retain the target without forcing it to be the unique primary.
        self.assertEqual(result["status"], "MULTIPLE_PERSISTENT_TRACKS")
        self.assertIsNone(result["primary_summary"])

    def test_persistent_weaker_component_survives_unrelated_maxima(self):
        fragments = [fragment(i, [-5300, 1000 + 500 * i]) for i in range(1, 6)]
        for f in fragments:
            f["components"][1]["peak_power"] = 10000.
        result = method.track_episode(fragments)
        self.assertEqual(result["status"], "UNIQUE_PERSISTENT_TRACK")
        self.assertEqual(result["primary_summary"]["median_hz"], -5300)
        self.assertEqual(result["primary_support_count"], 5)

    def test_two_persistent_components_and_signed_spacing(self):
        result = method.track_episode([fragment(i, [-5300 + i, 1000 + 2 * i]) for i in range(1, 6)])
        self.assertEqual(result["status"], "MULTIPLE_PERSISTENT_TRACKS")
        self.assertIsNone(result["primary_summary"])
        self.assertEqual(result["pairwise_spacings"][0]["signed_spacings_hz"], [6301., 6302., 6303., 6304., 6305.])

    def test_crossing_branch_is_not_split_or_resolved_by_power(self):
        result = method.track_episode([fragment(1, [-1000, -900]), fragment(2, [-950]),
                                       fragment(3, [-1000, -900])])
        self.assertEqual(result["status"], "AMBIGUOUS_ASSOCIATION")
        self.assertEqual(len(result["groups"]), 1)
        self.assertIn("MULTIPLE_CANDIDATES_SAME_FRAGMENT", result["groups"][0]["flags"])

    def test_one_missing_fragment_vs_longer_gap(self):
        result = method.track_episode([fragment(1, [-5300]), fragment(2, [], usable=False),
                                       fragment(3, [-5300]), fragment(4, []), fragment(5, [-5300])])
        self.assertEqual(result["status"], "UNIQUE_PERSISTENT_TRACK")
        self.assertEqual(result["primary_coverage"], .6)
        self.assertIn("ONE_FRAGMENT_GAP", result["groups"][0]["flags"])
        result = method.track_episode([fragment(1, [-5300]), fragment(2), fragment(3),
                                       fragment(4, [-5300]), fragment(5, [-5300])])
        self.assertEqual(result["status"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(len(result["groups"]), 2)

    def test_exact_association_and_track_range_boundaries(self):
        result = method.track_episode([fragment(1, [-1000]), fragment(2, [-950]), fragment(3, [-900])])
        self.assertEqual(result["status"], "UNIQUE_PERSISTENT_TRACK")
        self.assertEqual(result["primary_summary"]["range_hz"], 100.)
        result = method.track_episode([fragment(1, [-1000]), fragment(2, [-949.999]), fragment(3, [-900])])
        self.assertNotEqual(result["status"], "UNIQUE_PERSISTENT_TRACK")
        result = method.track_episode([fragment(1, [-1000]), fragment(2, [-950]),
                                       fragment(3, [-900]), fragment(4, [-899.999])])
        self.assertEqual(result["status"], "AMBIGUOUS_ASSOCIATION")
        self.assertIn("TRACK_RANGE_EXCEEDED", result["groups"][0]["flags"])

    def test_coverage_and_recurring_competitor(self):
        result = method.track_episode([fragment(i, [-5300] if i <= 3 else []) for i in range(1, 7)])
        self.assertEqual(result["status"], "INSUFFICIENT_SUPPORT")
        self.assertEqual(result["groups"][0]["coverage"], .5)
        result = method.track_episode([fragment(i, [-5300, 1000] if i <= 2 else [-5300]) for i in range(1, 6)])
        self.assertEqual(result["status"], "AMBIGUOUS_ASSOCIATION")
        self.assertIsNone(result["primary_track_id"])

    def test_single_two_empty_and_unusable(self):
        for count in (1, 2):
            result = method.track_episode([fragment(i, [-5300]) for i in range(1, count + 1)])
            self.assertEqual(result["status"], "INSUFFICIENT_SUPPORT")
            self.assertIsNone(result["primary_summary"])
            if count == 1:
                self.assertIsNone(result["groups"][0]["summary"]["range_hz"])
                self.assertIsNone(result["groups"][0]["summary"]["mad_hz"])
        self.assertEqual(method.track_episode([fragment(1)])["status"], "NO_ELIGIBLE_COMPONENT")
        self.assertEqual(method.track_episode([fragment(1, usable=False)])["status"], "UNUSABLE_INPUT")


class ProvenanceArtifactTests(unittest.TestCase):
    def test_full_extraction_determinism_nulls_and_input_immutability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = synthetic_bundle(root)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            provenance = {"test": "fixed provenance declaration"}
            a = method.extract_capture(bundle, root / "a", provenance)
            b = method.extract_capture(bundle, root / "b", provenance)
            self.assertEqual(a, b)
            expected = {"run.json", "components.json", "tracks.json", "spectra.npz",
                        "episodes.csv", "summary.md", "files.sha256"}
            self.assertEqual({p.name for p in (root / "a").iterdir()}, expected)
            for name in expected:
                self.assertEqual((root / "a" / name).read_bytes(), (root / "b" / name).read_bytes())
            for p, data in before.items():
                self.assertEqual(p.read_bytes(), data)
            for line in (root / "a/files.sha256").read_text().splitlines():
                sha, name = line.split("  ")
                self.assertEqual(method.digest((root / "a" / name).read_bytes()), sha)
            with np.load(root / "a/spectra.npz", allow_pickle=False) as arrays:
                self.assertTrue(all(np.all(np.isfinite(arrays[k])) for k in arrays.files))
            for p in (root / "a").glob("*.json"):
                json.loads(p.read_text(), parse_constant=lambda text: self.fail(text))
            with self.assertRaises(FileExistsError):
                method.extract_capture(bundle, root / "a", provenance)
            with self.assertRaises(ValueError):
                method.extract_capture(bundle, bundle / "output", provenance)

    def test_bad_hash_emits_failure_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = synthetic_bundle(root)
            path = root / "fragment0.iq"
            raw = bytearray(path.read_bytes())
            raw[0] ^= 1
            path.write_bytes(raw)
            with patch.object(method, "analyse_spectrum", side_effect=AssertionError("must not run")):
                result = method.extract_capture(bundle, root / "failure", {})
            self.assertEqual(result["processing_status"], "FAILED")
            self.assertEqual(result["flags"], ["PROVENANCE_MISMATCH"])
            self.assertFalse((root / "failure/components.json").exists())

    def test_omitted_duplicate_members_and_wrong_capture_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = synthetic_bundle(root)
            path = bundle / "episodes.json"
            original = json.loads(path.read_text())
            for change in ("missing", "duplicate", "identity", "metadata"):
                data = copy.deepcopy(original)
                if change == "missing":
                    data["episodes"][0]["files"].pop()
                elif change == "duplicate":
                    data["episodes"][0]["files"][1] = data["episodes"][0]["files"][0]
                elif change == "identity":
                    data["capture_id"] = "wrong"
                else:
                    data["episodes"][0]["files"][0]["sha256"] = "0" * 64
                path.write_bytes(method.json_bytes(data))
                with self.subTest(change=change), self.assertRaises(method.ProvenanceError):
                    method.verify_inputs(bundle)

    def test_single_fragment_null_artifact_and_original_v1_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = synthetic_bundle(root, count=1)
            method.extract_capture(bundle, root / "output", {})
            result = json.loads((root / "output/tracks.json").read_text())["episodes"][0]
            self.assertIsNone(result["primary_summary"])
            self.assertIn('"primary_summary": null', (root / "output/tracks.json").read_text())
            original = json.loads((bundle / "episode-features-v1.json").read_text())
            components = json.loads((root / "output/components.json").read_text())
            self.assertEqual(components["episodes"][0]["fragments"][0]["v1_strongest_component_offset_hz"],
                             original["episodes"][0]["fragments"][0]["strongest_component_offset_hz"])


if __name__ == "__main__":
    unittest.main()
