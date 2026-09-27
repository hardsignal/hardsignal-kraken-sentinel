import tempfile
import unittest
from pathlib import Path

from ml.dataset_builder import build_dataset


class DatasetBuilderTests(unittest.TestCase):

    def test_build_single_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            burst_log = tmp / "bursts.log"
            track_log = tmp / "tracks.log"
            episode_log = tmp / "episodes.jsonl"

            burst_log.write_text(
                "\n".join([
                    "time=2026-09-25T00:00:00,session_id=TEST-1,"
                    "bearing=359.0,peak_power=-30,max_confidence=4.0,"
                    "doa_width=50,median_doa_peaks=1,bearing_spread=2,"
                    "median_confidence=4.0,single_peak_ratio=1.0,"
                    "quality=STABLE,samples=3",

                    "time=2026-09-25T00:00:10,session_id=TEST-1,"
                    "bearing=1.0,peak_power=-28,max_confidence=4.2,"
                    "doa_width=52,median_doa_peaks=1,bearing_spread=3,"
                    "median_confidence=3.8,single_peak_ratio=1.0,"
                    "quality=STABLE,samples=3",

                    "time=2026-09-25T00:00:20,session_id=TEST-1,"
                    "bearing=2.0,peak_power=-29,max_confidence=3.0,"
                    "doa_width=80,median_doa_peaks=2,bearing_spread=5,"
                    "median_confidence=2.5,single_peak_ratio=0.33,"
                    "quality=MULTIPATH,samples=3",
                ]),
                encoding="utf-8",
            )

            track_log.write_text(
                "\n".join([
                    "time=2026-09-25T00:00:10,session_id=TEST-1,"
                    "event=TRACK_ACQUIRED",

                    "time=2026-09-25T00:00:20,session_id=TEST-1,"
                    "event=TRACK_DEGRADED",
                ]),
                encoding="utf-8",
            )

            rows = build_dataset(
                burst_log,
                track_log,
                episode_log,
                min_bursts=1,
            )

            self.assertEqual(len(rows), 1)

            row = rows[0]

            self.assertEqual(row["session_id"], "TEST-1")
            self.assertEqual(row["burst_count"], 3)
            self.assertEqual(row["stable_count"], 2)
            self.assertEqual(row["multipath_count"], 1)

            self.assertAlmostEqual(row["stable_ratio"], 2 / 3)
            self.assertAlmostEqual(row["multipath_ratio"], 1 / 3)

            # Circular mean should remain near 0°, not incorrectly near 120°.
            bearing = row["bearing_circular_mean_deg"]
            self.assertTrue(bearing < 5 or bearing > 355)

            self.assertEqual(row["track_event_count"], 2)
            self.assertEqual(row["track_acquired_count"], 1)
            self.assertEqual(row["track_degraded_count"], 1)

            self.assertEqual(row["episode_event_count"], 0)


if __name__ == "__main__":
    unittest.main()
