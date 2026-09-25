"""Offline v1 audit probes. Expected failures are OPEN release risks, not passes.

Run this file directly from the repository root; its gate fails on expected
failures too. B1 prior-only isolation probes are normal passing tests.
"""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ai import cli
from ai.artifact import canonical_sha256
from ai.evidence_bundle import load_ml_result
from ai.experiment_guard import SentinelExperimentGuardError, validate_experiment_suggestion
from ai.history import build_history_bundle
from ai.history_artifact import build_history_artifact
from ai.history_experiment import build_history_experiment_prompt, suggest_history_experiment_from_prompt
from ai.history_experiment_guard import validate_history_experiment
from ai.history_report import build_history_report
from ai.llm_client import EXPECTED_MODEL_DIGEST, SentinelLLMError, generate_text, get_model_digest
from scripts import verify_ai_release as v01
def make_record(number, cluster=1):
    return {
        'session_id': f'TPMS-NATURAL-{number:03d}-20260925-000000',
        'assigned_cluster': cluster,
        'novelty': 'WITHIN_OBSERVED_TRAINING_RANGE',
        'feature_row': {
            'bearing_circular_std_deg': float(number),
            'peak_power_mean_db': -20.0 - number,
            'median_confidence_mean': 3.0 + number / 100,
            'doa_width_mean_deg': 50.0 + number / 10,
            'single_peak_ratio_mean': 0.9,
            'burst_count': 10,
        },
    }


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.target = make_record(6)['session_id']
        for n in (5, 6):
            self.write(n)

    def write(self, number, record=None):
        record = make_record(number) if record is None else record
        path = self.root / (make_record(number)['session_id'] + '.json')
        path.write_text(json.dumps(record), encoding='utf-8')
        return path

    def bundle(self):
        return build_history_bundle(self.target, results_dir=self.root)

    def test_future_presence_cannot_change_prompt(self):
        before = build_history_experiment_prompt(self.target, results_dir=self.root)
        self.write(17)
        self.assertEqual(before, build_history_experiment_prompt(self.target, results_dir=self.root))

    def test_future_features_cannot_change_prior_statistics(self):
        self.write(17)
        before = self.bundle()
        record = make_record(17, cluster=2)
        record['feature_row'] = {k: 1e12 for k in record['feature_row']}
        self.write(17, record)
        self.assertEqual(before, self.bundle())

    def test_corrupt_future_cannot_block_earlier_target(self):
        before = self.bundle()
        self.write(17).write_text('{', encoding='utf-8')
        self.assertEqual(before, self.bundle())

    def test_excluded_filename_cannot_supply_formal_record(self):
        # Keep this B2 probe inside the target cutoff so it tests membership,
        # independently of B1 future-file isolation.
        self.write(14, make_record(15))
        with self.assertRaises(ValueError):
            build_history_bundle(make_record(15)['session_id'], results_dir=self.root)

    def test_excluded_target_rejected(self):
        self.write(14)
        with self.assertRaises(ValueError):
            build_history_bundle(make_record(14)['session_id'], results_dir=self.root)

    def test_earliest_history_report_has_no_comparison(self):
        report = build_history_report(make_record(5)['session_id'], results_dir=self.root)
        self.assertEqual(report['history']['nearest_prior_sessions'], [])
        self.assertEqual(report['history']['prior_formal_session_count'], 0)
        self.assertIn('unavailable; no prior same-cluster sessions', report['text'])

    @unittest.expectedFailure
    def test_earliest_suggestion_cannot_invent_prior_mean(self):
        prompt = build_history_experiment_prompt(make_record(5)['session_id'], results_dir=self.root)
        with self.assertRaises(SentinelExperimentGuardError):
            suggest_history_experiment_from_prompt(prompt, generate_fn=lambda _: 'Repeat and compare with the prior C1 mean.')

    @unittest.expectedFailure
    def test_missing_required_prior_record_fails_closed(self):
        self.write(5).unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.bundle()

    def test_missing_and_corrupt_normal_ml(self):
        with self.assertRaises(FileNotFoundError):
            load_ml_result('MISSING', self.root)
        self.write(6).write_text('{', encoding='utf-8')
        with self.assertRaises(ValueError):
            load_ml_result(self.target, self.root)

    def test_normal_session_mismatch(self):
        self.write(6, make_record(5))
        with self.assertRaises(ValueError):
            load_ml_result(self.target, self.root)

    @unittest.expectedFailure
    def test_nonobject_ml_has_evidence_error(self):
        self.write(6, [])
        with self.assertRaises(ValueError):
            load_ml_result(self.target, self.root)

    @unittest.expectedFailure
    def test_history_artifact_rejects_stale_bundle(self):
        history = self.bundle()
        record = make_record(5, cluster=2)
        self.write(5, record)
        with self.assertRaises(ValueError):
            build_history_artifact(target_session_id=self.target, history_bundle=history,
                history_report='stale', experiment_prompt='stale', experiment_suggestion='Repeat and measure.',
                model_digest=EXPECTED_MODEL_DIGEST, results_dir=self.root)

    def test_ollama_unavailable_is_llm_error(self):
        with patch('ai.llm_client.request.urlopen', side_effect=URLError('offline')):
            for operation in (lambda: generate_text('prompt'), get_model_digest):
                with self.assertRaises(SentinelLLMError):
                    operation()

    def test_two_history_rejections_exit_six_without_publication(self):
        generate = Mock(return_value='Measure propagation changes.')
        with patch('ai.cli.verify_model_digest', return_value='locked'), \
             patch('ai.cli.build_history_report', return_value={'text': 'history', 'history': {}}), \
             patch('ai.cli.build_history_experiment_prompt', return_value='prompt'), \
             patch('ai.history_experiment.generate_text', generate), \
             patch('ai.cli.save_history_artifact') as save, \
             contextlib.redirect_stdout(io.StringIO()) as output, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['--session', self.target, '--history', '--save']), 6)
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(output.getvalue(), '')
        save.assert_not_called()

    def assert_claim_rejected(self, text):
        # Both public CLI suggestion paths must reject the claim.
        accepted = []
        for guard in (validate_experiment_suggestion, validate_history_experiment):
            try:
                guard(text)
            except SentinelExperimentGuardError:
                continue
            accepted.append(guard.__name__)
        self.assertEqual(accepted, [], f'Unsafe claim accepted by {accepted}')

    @unittest.expectedFailure
    def test_device_identity_rejected(self):
        self.assert_claim_rejected('Repeat the capture. This is device ABC123.')

    @unittest.expectedFailure
    def test_causal_environment_rejected(self):
        self.assert_claim_rejected('Repeat the capture. Interference caused the observed variability.')

    @unittest.expectedFailure
    def test_calibration_claim_rejected(self):
        self.assert_claim_rejected('Repeat the capture. Bearing is calibrated to within 0.1 degrees.')

    @unittest.expectedFailure
    def test_discrimination_claim_rejected(self):
        self.assert_claim_rejected('Repeat and compare to prove reliable device classification.')


class HistoricalVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Exact reviewed verifier, no network, checkout, or execution of an LLM.
        cls.v02 = types.ModuleType('audited_v02_verifier')
        cls.v02.__file__ = str(ROOT / 'scripts/verify_ai_v02_release.py')
        source = subprocess.check_output(['git', 'show',
            '42ec68e237ee66a7dc199e1b8086969fdd339b79:scripts/verify_ai_v02_release.py'], cwd=ROOT)
        exec(compile(source, cls.v02.__file__, 'exec'), cls.v02.__dict__)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name in (v01.REFERENCE, self.v02.REFERENCE, *self.v02.SOURCE_FILES):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def test_v02_changed_source_rejected(self):
        path = self.root / self.v02.SOURCE_FILES[0]
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source SHA256 mismatch'):
            self.v02.check_artifact(self.root)

    @unittest.expectedFailure
    def test_v01_changed_source_rejected(self):
        path = self.root / self.v02.SOURCE_FILES[-1]
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            v01.check_artifact(self.root)

    def test_v02_future_manifest_rejected_even_with_rehashed_manifest(self):
        artifact = json.loads((self.root / self.v02.REFERENCE).read_text())
        artifact['source_record_sha256'][make_record(17)['session_id']] = '0' * 64
        artifact['source_record_manifest_sha256'] = canonical_sha256(artifact['source_record_sha256'])
        with self.assertRaisesRegex(ValueError, 'source session set mismatch'):
            self.v02.check_source_manifest(self.root, artifact)

    def test_malformed_artifacts_rejected(self):
        for verifier in (v01, self.v02):
            for value in ('{', '[]', 'null', '{}'):
                with self.subTest(verifier=verifier.__name__, value=value):
                    (self.root / verifier.REFERENCE).write_text(value)
                    with self.assertRaises(ValueError):
                        verifier.check_artifact(self.root)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # Expected failures document open blockers; never call this a passing release gate.
    ready = result.wasSuccessful() and not result.expectedFailures
    print(f"{'PASS' if ready else 'NOT READY'}: "
          f"{len(result.expectedFailures)} open contract failures", file=sys.stderr)
    sys.exit(0 if ready else 1)
