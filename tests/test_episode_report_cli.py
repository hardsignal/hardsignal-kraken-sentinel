import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from watcher.episode_report_cli import main


class EpisodeReportCliTests(unittest.TestCase):

    def test_missing_log_reports_no_events(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            rc = main([
                "--log",
                "/tmp/definitely-no-kraken-episode-log.jsonl",
            ])

        self.assertEqual(rc, 0)
        self.assertIn(
            "No episode events found.",
            output.getvalue(),
        )

    def test_session_filter_text_report(self):
        records = [
            {
                "version": 1,
                "timestamp": "2026-09-23T04:00:00",
                "project": "KRAKEN RF SENTINEL",
                "session_id": "A",
                "event": "EPISODE_STARTED",
                "episode_id": 1,
                "observation_index": 5,
                "reason": None,
                "summary": {
                    "version": 1,
                    "episode_id": 1,
                    "status": "ACTIVE",
                    "start_index": 5,
                    "end_index": None,
                    "end_reason": None,
                    "start_mean": 100.0,
                    "latest_mean": 100.0,
                    "max_support": 5,
                    "degraded_seen": False,
                },
            },
            {
                "version": 1,
                "timestamp": "2026-09-23T04:00:01",
                "project": "KRAKEN RF SENTINEL",
                "session_id": "B",
                "event": "EPISODE_STARTED",
                "episode_id": 1,
                "observation_index": 5,
                "reason": None,
                "summary": {
                    "version": 1,
                    "episode_id": 1,
                    "status": "ACTIVE",
                    "start_index": 5,
                    "end_index": None,
                    "end_reason": None,
                    "start_mean": 200.0,
                    "latest_mean": 200.0,
                    "max_support": 5,
                    "degraded_seen": False,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"

            with path.open("w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                rc = main([
                    "--log",
                    str(path),
                    "--session",
                    "A",
                ])

        self.assertEqual(rc, 0)

        text = output.getvalue()

        self.assertIn("episodes started:         1", text)
        self.assertIn("active episode ids:       1", text)

    def test_json_output(self):
        record = {
            "version": 1,
            "timestamp": "2026-09-23T04:00:00",
            "project": "KRAKEN RF SENTINEL",
            "session_id": "A",
            "event": "EPISODE_STARTED",
            "episode_id": 1,
            "observation_index": 5,
            "reason": None,
            "summary": {
                "version": 1,
                "episode_id": 1,
                "status": "ACTIVE",
                "start_index": 5,
                "end_index": None,
                "end_reason": None,
                "start_mean": 100.0,
                "latest_mean": 100.0,
                "max_support": 5,
                "degraded_seen": False,
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(json.dumps(record) + "\n")

            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                rc = main([
                    "--log",
                    str(path),
                    "--json",
                ])

        self.assertEqual(rc, 0)

        report = json.loads(output.getvalue())

        self.assertEqual(report["episodes_started"], 1)
        self.assertEqual(report["active_episode_ids"], [1])


if __name__ == "__main__":
    unittest.main()
