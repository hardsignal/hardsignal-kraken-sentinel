import csv
import json
import tempfile
import unittest
from pathlib import Path

from watcher.episode_report import (
    build_episode_report,
    format_episode_report,
    load_episode_events,
)
from watcher.episode_summary import build_episode_event_record
from watcher.source_episode import SourceEpisodeEngine
from watcher.tracker_engine import TrackerEngine


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "tpms_hysteresis_clean_v1_inputs.csv"
)


def make_real_rf_event_records():
    tracker = TrackerEngine()
    episodes = SourceEpisodeEngine()

    with FIXTURE.open(newline="") as f:
        inputs = list(csv.DictReader(f))

    records = []

    for index, observation in enumerate(inputs, start=1):
        track = tracker.process(
            float(observation["bearing"]),
            observation["quality"],
        )

        result = episodes.process(index, track)

        for event in result["events"]:
            if event["event"] == "EPISODE_CLOSED":
                episode = next(
                    item
                    for item in episodes.completed_episodes
                    if item["episode_id"] == event["episode_id"]
                )
            else:
                episode = episodes.active_episode

            records.append(
                build_episode_event_record(
                    event,
                    episode,
                    session_id="REAL-RF-REPLAY",
                    timestamp=f"2026-09-23T04:00:{index:02d}",
                    project_name="KRAKEN RF SENTINEL",
                )
            )

    return records


class EpisodeReportTests(unittest.TestCase):

    def test_real_rf_report_counts(self):
        records = make_real_rf_event_records()

        report = build_episode_report(records)

        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["episodes_started"], 2)
        self.assertEqual(report["episodes_closed"], 1)
        self.assertEqual(report["shift_boundaries"], 1)
        self.assertEqual(report["track_losses"], 0)
        self.assertEqual(report["active_episode_ids"], [2])

    def test_closed_episode_evidence(self):
        records = make_real_rf_event_records()

        report = build_episode_report(records)

        self.assertEqual(len(report["closed_episodes"]), 1)

        episode = report["closed_episodes"][0]

        self.assertEqual(episode["episode_id"], 1)
        self.assertEqual(episode["start_index"], 8)
        self.assertEqual(episode["end_index"], 16)
        self.assertAlmostEqual(
            episode["start_mean"],
            286.0,
            places=1,
        )
        self.assertEqual(
            episode["end_reason"],
            "SHIFT_CONFIRMED",
        )
        self.assertTrue(episode["degraded_seen"])

    def test_jsonl_loader_filters_session(self):
        records = make_real_rf_event_records()

        extra = dict(records[0])
        extra["session_id"] = "OTHER"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"

            with path.open("w") as f:
                for record in records + [extra]:
                    f.write(
                        json.dumps(
                            record,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )

            loaded = load_episode_events(
                path,
                session_id="REAL-RF-REPLAY",
            )

        self.assertEqual(len(loaded), 3)

    def test_missing_log_is_empty(self):
        events = load_episode_events(
            "/tmp/kraken-definitely-missing.jsonl"
        )

        self.assertEqual(events, [])

    def test_text_report_is_stable(self):
        records = make_real_rf_event_records()

        report = build_episode_report(records)
        text = format_episode_report(report)

        self.assertIn("episodes started:         2", text)
        self.assertIn("episodes closed:          1", text)
        self.assertIn("shift boundaries:         1", text)
        self.assertIn("active episode ids:       2", text)
        self.assertIn("Episode 1", text)
        self.assertIn("end reason:   SHIFT_CONFIRMED", text)


if __name__ == "__main__":
    unittest.main()
