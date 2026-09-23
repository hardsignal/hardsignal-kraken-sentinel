import json
from pathlib import Path
import tempfile
import unittest

from watcher.episode_report import build_episode_report
from watcher.session_summary import (
    TRACK_EVENTS, build_session_summary, format_session_summary,
)


def episode(event, episode_id, session="A", reason=None, degraded=False):
    return {
        "session_id": session, "event": event, "episode_id": episode_id,
        "reason": reason,
        "summary": {
            "start_index": 1, "end_index": 10, "start_mean": 100.0,
            "latest_mean": 105.0, "max_support": 8,
            "degraded_seen": degraded, "end_reason": reason,
        },
    }


class SessionSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths = {key: Path(self.temp.name) / key for key in
                      ("bursts_log", "track_log", "episode_log")}

    def report(self, session="A"):
        return build_session_summary(session, **self.paths)

    def test_all_counts_filtering_and_episode_reuse(self):
        self.paths["bursts_log"].write_text(
            "\nbearing=196.0,peak_power=-14.5,samples=3\n"
            "SESSION_START | id=A | time=2026-09-23T02:02:43 | source=TPMS\n"
            "session_id=LEGACY,bearing=89.3,samples=3\n"
            "session_id=A,quality=STABLE\nsession_id=A,quality=STABLE\n"
            "session_id=A,quality=MULTIPATH\nsession_id=A,quality=LOW_QUALITY\n"
            "session_id=AA,quality=STABLE\n")
        self.paths["track_log"].write_text("\n".join(
            f"session_id={session},event={event}" for session in ("A", "AA")
            for event in (*TRACK_EVENTS, "TRACK_SHIFT_DETECTED", "TRACK_VARIABLE")))
        events = [episode("EPISODE_STARTED", value) for value in (1, 2, 10, 3)]
        events += [episode("EPISODE_CLOSED", 1, reason="SHIFT_CONFIRMED", degraded=True),
                   episode("EPISODE_CLOSED", 2, reason="TRACK_LOST")]
        other = episode("EPISODE_CLOSED", 3, session="AA", reason="TRACK_LOST")
        self.paths["episode_log"].write_text(
            "\n" + "\n".join(json.dumps(row) for row in events + [other]))
        report = self.report()
        self.assertEqual(report["bursts"], {
            "total": 4, "STABLE": 2, "MULTIPATH": 1, "LOW_QUALITY": 1})
        self.assertEqual(report["track_events"], dict.fromkeys(TRACK_EVENTS, 1))
        self.assertEqual(report["episodes"], build_episode_report(events))
        self.assertEqual(report["episodes"]["active_episode_ids"], [3, 10])
        self.assertEqual(report["episodes"]["shift_boundaries"], 1)
        self.assertEqual(report["episodes"]["track_losses"], 1)
        self.assertEqual(report["episodes"]["degraded_closed_episodes"], 1)
        self.assertEqual(report, self.report())
        self.assertEqual(report["missing_logs"], [])
        text = format_session_summary(report)
        for expected in ("session: A", "total: 4", "stable: 2", "multipath: 1",
                         "low quality: 1", "started: 4", "closed: 2", "active: 3, 10",
                         "shift boundaries: 1", "track losses: 1",
                         "degraded closed episodes: 1"):
            self.assertIn(expected, text)

    def test_missing_empty_and_unmatched_logs(self):
        report = self.report()
        self.assertEqual(report["missing_logs"], [str(p) for p in self.paths.values()])
        self.assertEqual(report["bursts"]["total"], 0)
        self.assertEqual(report["track_events"], dict.fromkeys(TRACK_EVENTS, 0))
        self.assertEqual(report["episodes"], build_episode_report([]))
        self.assertIn("active: none", format_session_summary(report))
        for path in self.paths.values():
            path.write_text("\n")
        self.assertEqual(self.report()["missing_logs"], [])
        self.paths["bursts_log"].write_text("session_id=B,quality=STABLE\n")
        self.assertEqual(self.report()["bursts"]["total"], 0)

    def test_malformed_records_have_path_and_line(self):
        bad_records = {
            "bursts_log": ["garbage", "session_id=A,quality", "=x",
                           "session_id=A,quality=STABLE,quality=MULTIPATH",
                           "session_id=A", "session_id=A,quality=UNKNOWN",
                           "session_id=,quality=STABLE"],
            "track_log": ["session_id=A", "session_id=A,event=", "broken"],
            "episode_log": ["{", "null", "[]", "42", "{}",
                            '{"session_id":"A","session_id":"B"}',
                            json.dumps(episode("EPISODE_STARTED", True)),
                            json.dumps(episode("EPISODE_STARTED", "1")),
                            json.dumps(episode("EPISODE_STARTED", 1, session=None)),
                            '{"event":"EPISODE_CLOSED","episode_id":1,"summary":null}'],
        }
        for key, records in bad_records.items():
            for record in records:
                with self.subTest(key=key, record=record):
                    self.paths[key].write_text("\n" + record + "\n")
                    with self.assertRaises(ValueError) as caught:
                        self.report()
                    self.assertIn(f"{self.paths[key]}: line 2:", str(caught.exception))
            self.paths[key].write_text("")

    def test_closed_summary_types_are_validated(self):
        for key, value in (("degraded_seen", "false"), ("start_index", 1.5),
                           ("end_reason", None), ("start_mean", float("nan")),
                           ("latest_mean", float("inf")), ("max_support", True)):
            with self.subTest(key=key):
                record = episode("EPISODE_CLOSED", 1, reason="TRACK_LOST")
                record["summary"][key] = value
                self.paths["episode_log"].write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, "line 1"):
                    self.report()

    def test_real_burst_fixture(self):
        self.paths["bursts_log"] = Path(__file__).parent / "fixtures/tpms_hysteresis_clean_v1.log"
        report = self.report("TPMS-HYST-CLEAN-V1-20260923-020243")
        self.assertEqual(report["bursts"]["total"], 26)
        self.assertEqual(sum(report["bursts"][key] for key in
                             ("STABLE", "MULTIPATH", "LOW_QUALITY")), 26)

    def test_session_is_required(self):
        for session in (None, "", " "):
            with self.assertRaisesRegex(ValueError, "session_id"):
                self.report(session)


if __name__ == "__main__":
    unittest.main()
