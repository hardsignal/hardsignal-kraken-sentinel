import csv
import unittest
from pathlib import Path

from watcher.source_episode import SourceEpisodeEngine
from watcher.tracker_engine import TrackerEngine


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "tpms_hysteresis_clean_v1_inputs.csv"
)


def load_inputs():
    with FIXTURE.open(newline="") as f:
        return list(csv.DictReader(f))


class SourceEpisodeTests(unittest.TestCase):

    def replay(self):
        tracker = TrackerEngine()
        episodes = SourceEpisodeEngine()

        outputs = []

        for index, observation in enumerate(load_inputs(), start=1):
            track = tracker.process(
                float(observation["bearing"]),
                observation["quality"],
            )

            episode = episodes.process(index, track)

            outputs.append(
                {
                    "index": index,
                    "track": track,
                    "episode": episode,
                }
            )

        return tracker, episodes, outputs

    def test_real_rf_shift_creates_two_source_episodes(self):
        _, episodes, _ = self.replay()

        self.assertEqual(len(episodes.completed_episodes), 1)

        first = episodes.completed_episodes[0]
        second = episodes.active_episode

        self.assertEqual(first["episode_id"], 1)
        self.assertEqual(first["start_index"], 8)
        self.assertEqual(first["end_index"], 16)
        self.assertEqual(first["end_reason"], "SHIFT_CONFIRMED")

        self.assertAlmostEqual(first["start_mean"], 286.0, places=1)

        self.assertIsNotNone(second)
        self.assertEqual(second["episode_id"], 2)
        self.assertEqual(second["start_index"], 17)
        self.assertEqual(second["status"], "ACTIVE")

        self.assertAlmostEqual(second["start_mean"], 144.0, places=1)

    def test_degradation_does_not_split_episode(self):
        _, episodes, outputs = self.replay()

        first = episodes.completed_episodes[0]
        second = episodes.active_episode

        self.assertTrue(first["degraded_seen"])
        self.assertTrue(second["degraded_seen"])

        started = []

        for output in outputs:
            started.extend(
                event
                for event in output["episode"]["events"]
                if event["event"] == "EPISODE_STARTED"
            )

        self.assertEqual(
            [event["episode_id"] for event in started],
            [1, 2],
        )

    def test_shift_boundary_matches_real_rf_confirmation(self):
        _, _, outputs = self.replay()

        shift_output = outputs[16]  # observation 17

        self.assertTrue(
            shift_output["track"]["shift_confirmed"]
        )

        events = shift_output["episode"]["events"]

        self.assertEqual(
            [event["event"] for event in events],
            [
                "EPISODE_CLOSED",
                "EPISODE_STARTED",
            ],
        )

        self.assertEqual(
            events[0]["reason"],
            "SHIFT_CONFIRMED",
        )

        self.assertEqual(events[0]["episode_id"], 1)
        self.assertEqual(events[1]["episode_id"], 2)

    def test_track_loss_closes_episode(self):
        tracker = TrackerEngine()
        episodes = SourceEpisodeEngine()

        # Establish one clean track.
        for index, bearing in enumerate(
            [100.0, 100.5, 99.5, 100.2, 99.8],
            start=1,
        ):
            result = tracker.process(bearing, "STABLE")
            episodes.process(index, result)

        self.assertIsNotNone(episodes.active_episode)

        # Established tracks are lost after five rejected bursts.
        last_episode_result = None

        for index in range(6, 11):
            result = tracker.process(100.0, "MULTIPATH")
            last_episode_result = episodes.process(index, result)

        self.assertEqual(result["track_health"], "LOST")

        self.assertIsNone(episodes.active_episode)
        self.assertEqual(len(episodes.completed_episodes), 1)

        closed = episodes.completed_episodes[0]

        self.assertEqual(closed["end_reason"], "TRACK_LOST")
        self.assertEqual(closed["end_index"], 10)

        self.assertEqual(
            last_episode_result["events"][0]["event"],
            "EPISODE_CLOSED",
        )


if __name__ == "__main__":
    unittest.main()
