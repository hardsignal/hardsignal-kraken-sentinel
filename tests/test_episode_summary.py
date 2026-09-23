import csv
import json
import unittest
from pathlib import Path

from watcher.episode_summary import (
    build_episode_summary,
    episode_summary_json,
)
from watcher.source_episode import SourceEpisodeEngine
from watcher.tracker_engine import TrackerEngine


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "tpms_hysteresis_clean_v1_inputs.csv"
)


def replay_real_rf():
    tracker = TrackerEngine()
    episodes = SourceEpisodeEngine()

    with FIXTURE.open(newline="") as f:
        rows = list(csv.DictReader(f))

    for index, observation in enumerate(rows, start=1):
        result = tracker.process(
            float(observation["bearing"]),
            observation["quality"],
        )
        episodes.process(index, result)

    return episodes


class EpisodeSummaryTests(unittest.TestCase):

    def test_closed_real_rf_episode_summary(self):
        episodes = replay_real_rf()

        summary = build_episode_summary(
            episodes.completed_episodes[0]
        )

        self.assertEqual(
            summary,
            {
                "version": 1,
                "episode_id": 1,
                "status": "CLOSED",
                "start_index": 8,
                "end_index": 16,
                "end_reason": "SHIFT_CONFIRMED",
                "start_mean": 286.0,
                "latest_mean": 286.0,
                "max_support": 5,
                "degraded_seen": True,
            },
        )

    def test_active_real_rf_episode_summary(self):
        episodes = replay_real_rf()

        summary = build_episode_summary(
            episodes.active_episode
        )

        self.assertEqual(
            summary,
            {
                "version": 1,
                "episode_id": 2,
                "status": "ACTIVE",
                "start_index": 17,
                "end_index": None,
                "end_reason": None,
                "start_mean": 144.0,
                "latest_mean": 151.9,
                "max_support": 10,
                "degraded_seen": True,
            },
        )

    def test_json_is_deterministic(self):
        episodes = replay_real_rf()

        encoded_a = episode_summary_json(
            episodes.completed_episodes[0]
        )
        encoded_b = episode_summary_json(
            episodes.completed_episodes[0]
        )

        self.assertEqual(encoded_a, encoded_b)

        decoded = json.loads(encoded_a)

        self.assertEqual(decoded["episode_id"], 1)
        self.assertEqual(decoded["end_reason"], "SHIFT_CONFIRMED")

    def test_missing_field_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "missing episode fields",
        ):
            build_episode_summary(
                {
                    "episode_id": 1,
                    "status": "ACTIVE",
                }
            )


if __name__ == "__main__":
    unittest.main()
