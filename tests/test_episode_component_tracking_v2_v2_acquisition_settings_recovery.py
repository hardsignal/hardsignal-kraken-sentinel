"""Read-only recovery checkpoint tests; no hardware or acquisition interface."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-v2-acquisition-settings-recovery-v1'
JSON_PATH = ROOT / 'results' / (STEM + '.json')
DOC_PATH = ROOT / 'docs' / (STEM + '.md')
BASE = '77035ae9aca0fc35d8979cca5662020f396b3c84'
JSON_SHA256 = '5563adc955f0a6037e8264c8403c468e80eda3150a15c6f60693d6c3696169fd'
DOC_SHA256 = 'c05980aa743a24168eee03eca42b4dd868f24cf45c14a00e29075eec70ce0f6a'
CANONICAL_SHA256 = '3c59aa6ce0f485559814ede26a26ff5acda36ba128960790e692670183decdd8'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON constant: ' + value)


def read_checkpoint(raw):
    return json.loads(raw, object_pairs_hook=reject_duplicates,
                      parse_constant=reject_constant)


def verify_checkpoint(payload):
    """Test-local integrity check only; never an operational acquisition gate."""
    actual = digest(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                               allow_nan=False).encode())
    if actual != CANONICAL_SHA256:
        raise ValueError('recovery checkpoint drift')


class SettingsRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.data = read_checkpoint(JSON_PATH.read_bytes())
        self.lock = json.loads((ROOT / 'results' /
            'episode-component-tracking-v2-v2-acquisition-lock.json').read_bytes())

    def assert_rejected(self, path, value):
        changed = copy.deepcopy(self.data)
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with self.assertRaises(ValueError):
            verify_checkpoint(changed)

    def test_exact_artifact_bytes_and_base(self):
        self.assertEqual(digest(JSON_PATH.read_bytes()), JSON_SHA256)
        self.assertEqual(digest(DOC_PATH.read_bytes()), DOC_SHA256)
        self.assertEqual(self.data['base_commit'], BASE)
        verify_checkpoint(self.data)

    def test_external_hashes_and_commits(self):
        expected = {
            'kraken_settings': 'fccb9eaddb10467ee04128686d50e5a8586276ae09cb631a83925c9343269b4a',
            'kraken_processor': 'eb0187295ca0f7567a89cacf5146f0f6ee250ee0dbd122f32d054a0a802c8afb',
            'heimdall_config': '2eed4d16bbe497647437f56b726edb236c0439f0db4de9b9b0d7628aaa550e66',
            'historical_iq': '20561d440a122cd5f6faec2756d7979eed0d140de74760cb47fa2f691e362626',
        }
        for key, value in expected.items():
            self.assertEqual(self.data['external_evidence'][key]['sha256'], value)
        for key, value in self.data['external_evidence'].items():
            self.assert_rejected(['external_evidence', key, 'sha256'], '0' * 64)
        provenance = self.data['software_provenance']
        self.assertEqual(provenance['kraken']['head'], '0686cac0d9e7bd61a7d929a0b48ad6f891d1d25e')
        self.assertEqual(provenance['heimdall']['head'], '1efc252e24501a6bd091699c4f22f140ee71d901')
        self.assertEqual(self.data['external_evidence']['heimdall_config']['real_path'],
            '/home/maciejduranczyk/krakensdr/heimdall_daq_fw/Firmware/daq_chain_config.ini')

    def test_rf_frequency_cannot_drift(self):
        self.assertEqual(self.data['assessments']['rf_center_frequency_hz']['candidate'], 433250000)
        for value in [700000000, 433868160, 433.25, None]:
            self.assert_rejected(['assessments', 'rf_center_frequency_hz', 'candidate'], value)

    def test_frontend_rate_cannot_drift(self):
        self.assertEqual(self.data['assessments']['frontend_sample_rate_hz']['candidate'], 2400000)
        self.assert_rejected(['assessments', 'frontend_sample_rate_hz', 'candidate'], 25000)

    def test_channel_count_cannot_drift(self):
        self.assertEqual(self.data['assessments']['receiver_channel_count']['candidate'], 5)
        self.assert_rejected(['assessments', 'receiver_channel_count', 'candidate'], 4)

    def test_uniform_gain_cannot_drift(self):
        self.assertEqual(self.data['assessments']['receiver_gain']['candidate'],
                         {'uniform_db': 15.7, 'scope': 'all active channels'})
        for value in [0, 32, -100.0]:
            self.assert_rejected(['assessments', 'receiver_gain', 'candidate', 'uniform_db'], value)

    def test_agc_cannot_be_enabled(self):
        self.assertEqual(self.data['assessments']['agc_state']['candidate'],
            {'enabled': False, 'mode': 'manual_fixed_gain', 'auto_gain_sentinel': -100.0})
        self.assert_rejected(['assessments', 'agc_state', 'candidate', 'enabled'], True)
        self.assert_rejected(['assessments', 'agc_state', 'candidate', 'mode'], 'Auto')

    def test_decimation_chain_cannot_drift(self):
        chain = self.data['assessments']['decimation_channelizer']['candidate']
        self.assertEqual(chain, dict(adc_rate_hz=2400000, daq_decimation=1,
            post_daq_rate_hz=2400000, dsp_decimation=1, vfo_decimation_factor=96,
            vfo_effective_rate_hz=25000, vfo_bandwidth_hz=25000, vfo_fir_order_factor=2,
            active_vfos=1, output_vfo=0, heimdall_output_dtype='complex_float32'))
        self.assertEqual(chain['adc_rate_hz'] // chain['vfo_bandwidth_hz'], 96)
        for key in chain:
            with self.subTest(key=key):
                self.assert_rejected(['assessments', 'decimation_channelizer', 'candidate', key], None)

    def test_physical_bandwidth_cannot_be_fabricated(self):
        bandwidth = self.data['assessments']['rf_if_baseband_bandwidths']
        self.assertEqual(bandwidth['status'], 'PARTIALLY_SUPPORTED')
        for field in ['physical_rf_tuner_bandwidth_hz', 'if_bandwidth_hz']:
            self.assertIsNone(bandwidth['candidate'][field])
            self.assert_rejected(['assessments', 'rf_if_baseband_bandwidths', 'candidate', field], 2400000)

    def test_lna_vga_cannot_be_fabricated(self):
        for key in ['lna_gain', 'vga_baseband_gain']:
            self.assertIsNone(self.data['assessments'][key]['candidate'])
            self.assertEqual(self.data['assessments'][key]['status'], 'UNRESOLVED')
            for value in [0, 15.7, 32, 'not applicable']:
                self.assert_rejected(['assessments', key, 'candidate'], value)

    def test_historical_dtype_never_authorizes_future_writer(self):
        value = self.data['assessments']['recorder_output_conformance']
        self.assertEqual(value['status'], 'PARTIALLY_SUPPORTED')
        self.assertEqual(value['candidate'], dict(historical_dtype='<c16',
            historical_byte_order='little', future_v2_conformance=None, future_v2_authorized=False))
        for field in ['future_v2_conformance', 'future_v2_authorized']:
            self.assert_rejected(['assessments', 'recorder_output_conformance', 'candidate', field], True)
        self.assertFalse(self.data['historical_iq_interpretation']['future_recorder_conformance'])

    def test_dirty_software_is_not_reviewed(self):
        processor = self.data['external_evidence']['kraken_processor']
        self.assertEqual(processor['head_sha256'],
            '5d36bd9cf564a0f3935d5bea55ea99558062903adf491e4ddf0267fc38e37c60')
        self.assertFalse(processor['byte_identical_to_head'])
        self.assertTrue(self.data['external_evidence']['heimdall_config']['byte_identical_to_head'])
        for key in ['kraken', 'heimdall']:
            self.assertTrue(self.data['software_provenance'][key]['dirty'])
            self.assertFalse(self.data['software_provenance'][key]['reviewed_v2_execution_implementation'])
            self.assert_rejected(['software_provenance', key, 'reviewed_v2_execution_implementation'], True)

    def test_missing_runtime_logs_explicit(self):
        log = self.data['runtime_log_evidence']
        self.assertEqual(log['queries'], ['Exact sample rate', 'Exact center frequency',
            'Active antenna channels', 'ADC sampling frequency', 'IQ sampling frequency', 'IF gain'])
        self.assertIs(log['archived_matches_found'], False)
        self.assertIs(log['runtime_confirmation_available'], False)
        self.assertEqual(log['runtime_measurements'], [])
        for key in ['archived_matches_found', 'runtime_confirmation_available']:
            self.assert_rejected(['runtime_log_evidence', key], True)
        self.assert_rejected(['runtime_log_evidence', 'runtime_measurements'], [{'invented': 1}])

    def test_no_setting_promoted_to_runtime_confirmed(self):
        for key, value in self.data['assessments'].items():
            self.assertIs(value['runtime_confirmed'], False)
            self.assertIs(value['resolves_existing_lock'], False)
            self.assertNotEqual(value['status'], 'RUNTIME_CONFIRMED')
            self.assert_rejected(['assessments', key, 'status'], 'RUNTIME_CONFIRMED')

    def test_calibration_and_host_remain_partial(self):
        for key in ['calibration_synchronization', 'host_software_versions']:
            self.assertEqual(self.data['assessments'][key]['status'], 'PARTIALLY_SUPPORTED')
        self.assertIsNone(self.data['assessments']['calibration_synchronization']['candidate']['runtime_lock_sync_state'])
        self.assertIs(self.data['assessments']['host_software_versions']['candidate']['complete_dependency_driver_lock'], False)

    def test_all_lock_blockers_and_conflicts_retained(self):
        expected = sorted(k for k, v in self.lock['settings'].items() if v['status'] == 'NOT_ESTABLISHED')
        self.assertEqual(len(expected), 28)
        self.assertEqual(self.data['retained_lock_blockers'], expected)
        self.assertEqual(set(self.data['assessments']), set(expected))
        self.assertEqual(self.data['lock_conflicts_retained'], self.lock['conflicts'])
        for key in expected:
            changed = copy.deepcopy(self.data)
            changed['retained_lock_blockers'].remove(key)
            with self.assertRaises(ValueError):
                verify_checkpoint(changed)
        self.assert_rejected(['lock_conflicts_retained'], [])

    def test_protected_artifacts_byte_identical_to_base(self):
        for path, expected in self.data['protected_repository_sha256'].items():
            with self.subTest(path=path):
                self.assertEqual(digest((ROOT / path).read_bytes()), expected)
                self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(
                    ['git', 'show', BASE + ':' + path], cwd=ROOT))
        for path in self.lock['artifact_paths']:
            self.assertIn(path, self.data['protected_repository_sha256'])
        for path in self.lock['evidence_sha256']:
            self.assertIn(path, self.data['protected_repository_sha256'])

    def test_existing_lock_remains_blocked(self):
        self.assertEqual(self.lock['decision'], 'V2_ACQUISITION_LOCK_BLOCKED')
        self.assertEqual(self.lock['state'], 'BLOCKED_PENDING_ACQUISITION_SETTINGS')
        self.assertEqual(self.data['acquisition_decision'], self.lock['decision'])
        self.assertEqual(self.data['state'], self.lock['state'])
        self.assertEqual(self.data['decision'], 'V2_ACQUISITION_SETTINGS_RECOVERY_RECORDED_BLOCKED')
        self.assertIs(self.data['acquisition_authorized'], False)
        self.assertIsNone(self.data['authorizing_commit'])
        for key, value in [('state', 'READY_FOR_V2_ACQUISITION'),
                           ('decision', 'READY'), ('acquisition_authorized', True),
                           ('authorizing_commit', '1' * 40)]:
            self.assert_rejected([key], value)

    def test_no_execution_or_selection_interface(self):
        self.assertIsNone(self.data['execution_interface'])
        self.assertIs(self.data['scientific_execution'], False)
        self.assertIs(self.data['candidate_selection_changed'], False)
        for key in ['tuning', 'command', 'gain_override', 'ready', 'force', 'candidate_selection']:
            self.assert_rejected([key], True)
        # Every unknown field or changed top-level value fails closed.
        for key in self.data:
            self.assert_rejected([key], 'unapproved')

    def test_exact_versioned_descendant_paths(self):
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        manifest = recovery.validate(ROOT)
        self.assertEqual(manifest['recovery_paths'], sorted({
            'docs/' + STEM + '.md', 'results/' + STEM + '.json',
            'tests/test_episode_component_tracking_v2_v2_acquisition_settings_recovery.py'}))
        self.assertEqual(manifest['original_recovery_sha256'][recovery.TEST],
                         '105cbbd81251692bd5894685e9def96a6317f513e4b17be34c6ef1190bc2968e')

    def test_strict_json(self):
        for raw in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}']:
            with self.assertRaises(ValueError):
                read_checkpoint(raw)


class RecoveryProvenanceTests(unittest.TestCase):
    def entry_points(self):
        from provenance import v2_acquisition_lock_v1 as acquisition
        import test_episode_component_tracking_v2_v2_discrimination_preregistration as prereg
        import test_episode_component_tracking_v2_stage37_configuration_selection as selection
        import episode_component_tracking_v2_draft2_full_matrix_exact as launch
        from draft2_review_provenance import validate_review
        return (lambda: acquisition.validate(ROOT), prereg.verify_repair,
                lambda: selection.verify_provenance(selection.read('stage37-configuration-selection')),
                launch.verify_plan, lambda: validate_review('definition'),
                lambda: validate_review('feasibility'))

    def test_each_recovery_mutation_rejected_at_every_entry(self):
        from unittest.mock import patch
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        read = Path.read_bytes
        for path in recovery.RECOVERY_PATHS:
            for verify in self.entry_points():
                with self.subTest(path=path), patch.object(Path, 'read_bytes', lambda p:
                        read(p) + b' drift' if p == ROOT / path else read(p)):
                    with self.assertRaises(ValueError):
                        verify()

    def test_each_recovery_deletion_rejected_at_every_entry(self):
        from unittest.mock import patch
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        read = Path.read_bytes
        for path in recovery.RECOVERY_PATHS:
            def missing(p):
                if p == ROOT / path:
                    raise FileNotFoundError(path)
                return read(p)
            for verify in self.entry_points():
                with self.subTest(path=path), patch.object(Path, 'read_bytes', missing):
                    with self.assertRaises(FileNotFoundError):
                        verify()

    def test_fourth_tracked_or_untracked_descendant_rejected(self):
        from unittest.mock import patch
        real = subprocess.check_output
        for command in (['git', 'diff', '--name-status', BASE],
                        ['git', 'ls-files', '--others', '--exclude-standard', '-z']):
            def extra(cmd, **kwargs):
                raw = real(cmd, **kwargs)
                if cmd == command:
                    raw += (b'A\tresults/arbitrary-fourth-recovery.json\n' if '--name-status' in cmd
                            else b'results/arbitrary-fourth-recovery.json\0')
                return raw
            for verify in self.entry_points():
                with self.subTest(command=command), patch.object(subprocess, 'check_output', side_effect=extra):
                    with self.assertRaisesRegex(ValueError, 'unrecognized descendant'):
                        verify()

    def test_broken_recovery_ancestry_rejected(self):
        from unittest.mock import patch
        real = subprocess.run
        def broken(cmd, **kwargs):
            if cmd == ['git', 'merge-base', '--is-ancestor', BASE, 'HEAD']:
                raise subprocess.CalledProcessError(1, cmd)
            return real(cmd, **kwargs)
        for verify in self.entry_points():
            with patch.object(subprocess, 'run', side_effect=broken):
                with self.assertRaises(subprocess.CalledProcessError):
                    verify()

    def test_manifest_metadata_cannot_rewrite_paths_history_or_decisions(self):
        from unittest.mock import patch
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        read = Path.read_bytes
        original = json.loads(read(ROOT / recovery.BINDING))
        for field in original:
            altered = copy.deepcopy(original)
            altered[field] = {}
            with self.subTest(field=field), patch.object(Path, 'read_bytes', lambda p:
                    json.dumps(altered).encode() if p == ROOT / recovery.BINDING else read(p)):
                with self.assertRaises(ValueError):
                    recovery.validate(ROOT)

    def test_integration_helpers_are_hash_bound(self):
        from unittest.mock import patch
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        read = Path.read_bytes
        for path in (recovery.LEGACY, recovery.HELPER):
            with self.subTest(path=path), patch.object(Path, 'read_bytes', lambda p:
                    read(p) + b' drift' if p == ROOT / path else read(p)):
                with self.assertRaises(ValueError):
                    recovery.validate(ROOT)

    def test_historical_helper_hash_is_not_rewritten(self):
        from unittest.mock import patch
        from provenance import v2_acquisition_settings_recovery_v1 as recovery
        real = subprocess.check_output
        def drift(cmd, **kwargs):
            raw = real(cmd, **kwargs)
            return raw + b'drift' if cmd == ['git', 'show', BASE + ':' + recovery.LEGACY] else raw
        with patch.object(subprocess, 'check_output', side_effect=drift):
            with self.assertRaises(ValueError):
                recovery.validate(ROOT)


if __name__ == '__main__':
    unittest.main()
