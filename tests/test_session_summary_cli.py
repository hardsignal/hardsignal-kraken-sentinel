import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from watcher.session_summary_cli import build_parser, main


ROOT = Path(__file__).resolve().parents[1]


class SessionSummaryCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.args = ["--session", "A"]
        self.paths = []
        for name in ("bursts", "track", "episode"):
            path = Path(self.temp.name) / name
            self.paths.append(path)
            self.args.extend([f"--{name}-log", str(path)])

    def run_main(self, *extra):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            rc = main(self.args + list(extra))
        return rc, output.getvalue(), errors.getvalue()

    def test_missing_logs_json_and_text(self):
        rc, output, errors = self.run_main("--json")
        self.assertEqual((rc, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["session_id"], "A")
        self.assertEqual(len(report["missing_logs"]), 3)
        self.assertEqual(report["bursts"]["total"], 0)
        self.assertEqual(self.run_main("--json")[1], output)
        rc, text, errors = self.run_main()
        self.assertEqual((rc, errors), (0, ""))
        self.assertIn("KRAKEN RF SENTINEL — SESSION SUMMARY", text)
        self.assertIn("Missing logs (counted as empty):", text)

    def test_explicit_paths_and_exact_filter(self):
        self.paths[0].write_text("session_id=A,quality=STABLE\nsession_id=AB,quality=MULTIPATH\n")
        self.paths[1].write_text("session_id=A,event=TRACK_ACQUIRED\n")
        self.paths[2].write_text('{"session_id":"A","event":"EPISODE_STARTED","episode_id":2}\n')
        rc, output, errors = self.run_main("--json")
        self.assertEqual((rc, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["bursts"]["total"], 1)
        self.assertEqual(report["track_events"]["TRACK_ACQUIRED"], 1)
        self.assertEqual(report["episodes"]["active_episode_ids"], [2])
        self.assertEqual(report["missing_logs"], [])

    def test_malformed_input_has_no_partial_output(self):
        for path in self.paths:
            with self.subTest(path=path):
                path.write_text("\nmalformed\n")
                rc, output, errors = self.run_main("--json")
                self.assertEqual((rc, output), (2, ""))
                self.assertIn(f"{path}: line 2:", errors)
                self.assertNotIn("Traceback", errors)
                path.write_text("")

    def test_unreadable_input_is_a_clean_error(self):
        self.paths[0].mkdir()
        rc, output, errors = self.run_main()
        self.assertEqual((rc, output), (2, ""))
        self.assertIn("session summary:", errors)

    def test_defaults_and_required_session(self):
        args = build_parser().parse_args(["--session", "A"])
        self.assertEqual(args.bursts_log, Path.home() / "kraken_bursts.log")
        self.assertEqual(args.track_log, Path.home() / "kraken_track_events.log")
        self.assertEqual(args.episode_log, Path.home() / "kraken_episode_events.jsonl")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main([])
        self.assertEqual(caught.exception.code, 2)

    def test_script_and_module_entry_points(self):
        for invocation in ([str(ROOT / "watcher/session_summary_cli.py")],
                           ["-m", "watcher.session_summary_cli"]):
            with self.subTest(invocation=invocation):
                result = subprocess.run([sys.executable, *invocation, *self.args, "--json"],
                                        cwd=ROOT, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["session_id"], "A")


if __name__ == "__main__":
    unittest.main()
