import tempfile
import unittest
from pathlib import Path

import numpy as np

from analysis import passband_retune_v1 as analysis


def grid_rows():
    return [
        {"pass": p, "offset_hz": offset, "tone_power_db_adc2": 10.0,
         "endpoint_clipped_values": 0, "frequency_within_tolerance": True}
        for p in (1, 2) for offset in analysis.OFFSETS
    ]


class PassbandTests(unittest.TestCase):
    def test_filename_parsing(self):
        self.assertEqual(analysis.parse_filename("pass1_minus100k.cs8"), (1, -100000))
        self.assertEqual(analysis.parse_filename("pass2_plus100k.cs8"), (2, 100000))
        self.assertEqual(analysis.parse_filename("pass2_minus900k.cs8"), (2, -900000))
        for name in ("pass2_minus900k_repeat.cs8", "centre_repeat1.cs8",
                     "pass3_plus100k.cs8", "pass1_plus0k.cs8", "pass1_plus1000k.cs8",
                     "pass1_plus100k.cs8.bak", "pass1_plus150k.cs8"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                analysis.parse_filename(name)

    def test_exact_36_measurements_and_extras(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for p, offset in analysis.EXPECTED_KEYS:
                sign = "minus" if offset < 0 else "plus"
                (root / f"pass{p}_{sign}{abs(offset) // 1000}k.cs8").touch()
            (root / "pass2_minus900k_repeat.cs8").touch()
            files, excluded = analysis.discover_grid(root)
            self.assertEqual(len(files), 36)
            self.assertEqual(excluded, ["pass2_minus900k_repeat.cs8"])
            (root / "pass2_minus900k.cs8").unlink()
            with self.assertRaisesRegex(ValueError, "36"):
                analysis.discover_grid(root)

    def test_reference_is_four_signed_100000_hz_measurements(self):
        rows = grid_rows()
        levels = {(1, -100000): 10., (2, -100000): 12.,
                  (1, 100000): 20., (2, 100000): 22.}
        for row in rows:
            row["tone_power_db_adc2"] = levels.get((row["pass"], row["offset_hz"]), 100.)
        reference, groups, _ = analysis.summarize_grid(rows)
        self.assertEqual(reference, 16.)
        self.assertEqual(groups[-100000]["relative_response_db"], -5.)
        self.assertEqual(groups[100000]["relative_response_db"], 5.)
        self.assertEqual(groups[-100000]["between_pass_difference_db"], 2.)

    def test_missing_and_duplicate_measurements_rejected(self):
        rows = grid_rows()
        for invalid in (rows[:-1], rows[:-1] + [rows[0]], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                analysis.summarize_grid(invalid)

    def test_thresholds_and_contiguous_edges(self):
        rows = grid_rows()
        for row in rows:
            if row["offset_hz"] == -200000:
                row["tone_power_db_adc2"] = 7.0  # exactly -3 dB passes
            if row["offset_hz"] == -300000:
                row["tone_power_db_adc2"] = 6.99
            if row["offset_hz"] == 200000:
                row["tone_power_db_adc2"] = 9.5 if row["pass"] == 1 else 10.5
            if row["offset_hz"] == 300000:
                row["endpoint_clipped_values"] = 1
        _, groups, edges = analysis.summarize_grid(rows)
        self.assertTrue(groups[-200000]["numerical_rules_pass"])
        self.assertTrue(groups[200000]["numerical_rules_pass"])
        self.assertFalse(groups[-300000]["numerical_rules_pass"])
        self.assertFalse(groups[300000]["numerical_rules_pass"])
        self.assertEqual(edges, [-200000, 200000])

    def test_cs8_tone_frequency_power_and_clipping(self):
        # Bin-centred signed tones test both FFT sides and ADC power normalization.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.cs8"
            for sign in (-1, 1):
                frequency = sign * round(100000 * analysis.NFFT / analysis.SAMPLE_RATE) * analysis.SAMPLE_RATE / analysis.NFFT
                phase = 2 * np.pi * frequency * np.arange(analysis.EXPECTED_SAMPLES) / analysis.SAMPLE_RATE
                codes = np.empty(2 * analysis.EXPECTED_SAMPLES, dtype=np.int8)
                codes[0::2] = np.rint(40 * np.cos(phase)).astype(np.int8)
                codes[1::2] = np.rint(40 * np.sin(phase)).astype(np.int8)
                codes[-2:] = (-128, 127)  # tail excluded from FFT, still checked for clipping
                path.write_bytes(codes.tobytes())
                result = analysis.measure(path, 1, sign * 100000)
                self.assertEqual(result["measured_offset_hz"], frequency)
                self.assertEqual(result["endpoint_clipped_values"], 2)
                self.assertAlmostEqual(result["tone_power_db_adc2"], 10 * np.log10(40 ** 2), places=2)
            path.write_bytes(b"\x00")
            with self.assertRaisesRegex(ValueError, "8000000"):
                analysis.measure(path, 1, 100000)


if __name__ == "__main__":
    unittest.main()
