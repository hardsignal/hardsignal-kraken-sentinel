# V2 acquisition-settings recovery v1

**Decision: V2_ACQUISITION_SETTINGS_RECOVERY_RECORDED_BLOCKED**

Base: `77035ae9aca0fc35d8979cca5662020f396b3c84`; branch: `codex/v2-acquisition-settings-recovery`.

**V2 acquisition remains BLOCKED:** `V2_ACQUISITION_LOCK_BLOCKED` / `BLOCKED_PENDING_ACQUISITION_SETTINGS`. This read-only evidence overlay has no execution or tuning interface and grants no acquisition authorization. It changes neither the scientific contract nor candidate selection.

## Evidence classification

CONFIGURATION_SUPPORTED means a configuration/code-supported candidate, never RUNTIME_CONFIRMED. PARTIALLY_SUPPORTED retains missing conformance or inventory facts. UNRESOLVED means no exact supporting evidence. No setting is RUNTIME_CONFIRMED. All original lock blockers remain in force.

| Setting | Classification | Candidate / limitation |
|---|---|---|
| `activation_procedure` | UNRESOLVED | Not established. Exact activation tool/procedure, source state, idle enforcement and failure logging not established. |
| `agc_state` | CONFIGURATION_SUPPORTED | {"auto_gain_sentinel": -100.0, "enabled": false, "mode": "manual_fixed_gain"}. Fixed gain sets daq_agc=False; rtl_daq selects manual tuner gain mode 1. AGC requires a separate explicit control request. This is not proof of every stage at runtime. |
| `antenna_cable_inventory` | UNRESOLVED | Not established. Antenna/cable identity, arrangement and connections absent. |
| `calibration_synchronization` | PARTIALLY_SUPPORTED | {"amplitude_cal_mode": "channel_power", "cal_frame_burst_size": 10, "cal_frame_interval": 687, "cal_track_mode": 2, "en_iq_cal": 1, "en_noise_source_ctr": 1, "gain_lock_interval": 0, "iq_adjust_source": "explicit-time-delay", "maximum_sync_fails": 10, "runtime_lock_sync_state": null}. IQ calibration and periodic tracking configured; no archived runtime lock/sync state observed. |
| `clock_source` | UNRESOLVED | Not established. RF reference, UTC clock discipline, monotonic clock identity/resolution and synchronization uncertainty absent. |
| `decimation_channelizer` | CONFIGURATION_SUPPORTED | {"active_vfos": 1, "adc_rate_hz": 2400000, "daq_decimation": 1, "dsp_decimation": 1, "heimdall_output_dtype": "complex_float32", "output_vfo": 0, "post_daq_rate_hz": 2400000, "vfo_bandwidth_hz": 25000, "vfo_decimation_factor": 96, "vfo_effective_rate_hz": 25000, "vfo_fir_order_factor": 2}. DAQ rate = ADC/decimation; ratio 1 bypasses filtering/decimation. DSP ratio 1; VFO factor = 2400000 // 25000 = 96. Configuration/code-derived chain, not measured; Heimdall intermediate dtype is not recorder dtype. |
| `dropped_sample_error_instrumentation` | UNRESOLVED | Not established. Dropped sample/overflow/error instrumentation and logs absent; cannot assume zero. |
| `environment_measurement_procedure` | UNRESOLVED | Not established. Temperature, battery, interference/deviation metadata required; measurement methods and units not locked. |
| `exit_status_instrumentation` | UNRESOLVED | Not established. Writer exit status and abnormal termination capture mechanism absent. |
| `frontend_sample_rate_hz` | CONFIGURATION_SUPPORTED | 2400000. Configured sample_rate is passed to rtlsdr_set_sample_rate and adc_sampling_freq; no archived runtime confirmation. |
| `full_configuration_snapshot` | UNRESOLVED | Not established. Historical settings hashes differ; complete bytes and explanation unavailable. |
| `geometry_location_orientation` | UNRESOLVED | Not established. Locked location, source/receiver geometry, orientation, measurements and photograph hashes absent. |
| `hardware_inventory` | UNRESOLVED | Not established. Receiver model/revision/serial, firmware, channel serials and relevant peripherals absent. |
| `host_software_versions` | PARTIALLY_SUPPORTED | {"complete_dependency_driver_lock": false, "kernel": "7.0.11-76070011-generic", "numpy": "1.26.4", "os": "Pop!_OS 24.04 LTS", "python": "3.12.3"}. Partial host inventory supplied by user; not a complete dependency, driver or execution-environment lock. |
| `lna_gain` | UNRESOLVED | Not established. Kraken LNA state/gain absent; HackRF 32 dB is inapplicable. |
| `partial_file_detection` | UNRESOLVED | Not established. Close/flush/size stability and incomplete-file detection implementation absent. |
| `raw_naming_convention` | UNRESOLVED | Not established. Historical names are examples, not a locked implementation or timezone/collision rule. |
| `receiver_channel_count` | CONFIGURATION_SUPPORTED | 5. num_ch=5; configured count does not prove connected hardware or scientific channel mapping. |
| `receiver_gain` | CONFIGURATION_SUPPORTED | {"scope": "all active channels", "uniform_db": 15.7}. Numeric uniform_gain loads daq_rx_gain; set_if_gain replicates int(gain*10) across self.M channels. Heimdall gain=0 is a startup default. |
| `recorder_implementation` | UNRESOLVED | Not established. kraken_capture.py is a provenance wrapper, not the IQ writer. Actual writer source/binary/version/hash absent. |
| `recorder_output_conformance` | PARTIALLY_SUPPORTED | {"future_v2_authorized": false, "future_v2_conformance": null, "historical_byte_order": "little", "historical_dtype": "<c16"}. iq_channel.tofile(filename) writes native array bytes without a self-describing dtype. Historical numeric interpretation strongly supports little-endian complex128, but cannot prove future V2 writer conformance. |
| `recorder_trigger_buffer_rollover` | UNRESOLVED | Not established. Trigger, buffering, pre/post-trigger, flush and file rollover behavior absent. |
| `reviewed_execution_commit` | UNRESOLVED | Not established. Parent requires a reviewed runner commit before capture; no execution implementation is authorized here. |
| `rf_center_frequency_hz` | CONFIGURATION_SUPPORTED | 433250000. center_freq 433.25 MHz multiplied by 10**6; distinct from VFO frequency 433868160 Hz. Heimdall 700000000 Hz is a startup default, not a V2 runtime value. |
| `rf_if_baseband_bandwidths` | PARTIALLY_SUPPORTED | {"adc_rate_hz": 2400000, "if_bandwidth_hz": null, "physical_rf_tuner_bandwidth_hz": null, "post_daq_rate_hz": 2400000, "vfo_bandwidth_hz": 25000}. No explicit tuner bandwidth API call in rtl_daq.c. Sample rate and VFO bandwidth do not establish physical RF/IF bandwidth. |
| `scientific_channel_mapping` | UNRESOLVED | Not established. VFO 0 to physical channel or combination mapping absent. |
| `source_inventory` | UNRESOLVED | Not established. S1/S2 physical source identities/serials and batteries not locked. |
| `vga_baseband_gain` | UNRESOLVED | Not established. Exact gain or evidence-supported non-applicability absent. |

## Bound external evidence

All following hashes were verified by read-only local file reads. Code entries in the JSON additionally bind committed HEAD hashes and byte identity.

| Evidence | Logical path | SHA-256 |
|---|---|---|
| kraken_settings | `/home/maciejduranczyk/krakensdr_doa/_share/settings.json` | `fccb9eaddb10467ee04128686d50e5a8586276ae09cb631a83925c9343269b4a` |
| kraken_ui | `/home/maciejduranczyk/krakensdr_doa/_ui/_web_interface/kraken_web_interface.py` | `02a1294198372811ca555a2f5b7d88d74a0507c71247e0e31ca1d63ceb9dfe15` |
| kraken_variables | `/home/maciejduranczyk/krakensdr_doa/_ui/_web_interface/variables.py` | `596b6fe006db307d4d34016eb24c8464103aef438eaa842597ba196c68201a5d` |
| kraken_receiver | `/home/maciejduranczyk/krakensdr_doa/_sdr/_receiver/kraken_sdr_receiver.py` | `fce64aa94478b0e8cdab27093ebf92f0f835e1db232d20e1821f117840b590fb` |
| kraken_processor | `/home/maciejduranczyk/krakensdr_doa/_sdr/_signal_processing/kraken_sdr_signal_processor.py` | `eb0187295ca0f7567a89cacf5146f0f6ee250ee0dbd122f32d054a0a802c8afb` |
| heimdall_config | `/home/maciejduranczyk/heimdall_daq_fw/Firmware/daq_chain_config.ini` | `2eed4d16bbe497647437f56b726edb236c0439f0db4de9b9b0d7628aaa550e66` |
| rtl_daq | `/home/maciejduranczyk/heimdall_daq_fw/Firmware/_daq_core/rtl_daq.c` | `793960e7c93d537187fcf8c26f1126c8efd27e4bac519a5fe2c66624694263eb` |
| fir_decimate | `/home/maciejduranczyk/heimdall_daq_fw/Firmware/_daq_core/fir_decimate.c` | `a1b426183470a63b51442975666975d9cb46f97a5f7dba9a213a1ec021eb05fb` |
| historical_iq | `/home/maciejduranczyk/krakensdr_doa/_share/records/iq/19-Sep-2026_02h31m19s,IQ_433.868MHz,DOA_90.0.iq` | `20561d440a122cd5f6faec2756d7979eed0d140de74760cb47fa2f691e362626` |

Kraken HEAD `0686cac0d9e7bd61a7d929a0b48ad6f891d1d25e`, software 1.8.1: DIRTY. Processor HEAD SHA-256 `5d36bd9cf564a0f3935d5bea55ea99558062903adf491e4ddf0267fc38e37c60` differs from current bytes; local debug prints and Hardsignal JSON output are not a reviewed V2 implementation.

Heimdall HEAD `1efc252e24501a6bd091699c4f22f140ee71d901`: DIRTY elsewhere. Active config is byte-identical to HEAD and resolves to `/home/maciejduranczyk/krakensdr/heimdall_daq_fw/Firmware/daq_chain_config.ini`. Startup tune 700 MHz and gain 0 dB are not V2 runtime values. Kraken UI override semantics support the candidate tune/gain; successful application was not observed.

## Runtime and historical limits

The supplied read-only search for Exact sample rate, Exact center frequency, Active antenna channels, ADC sampling frequency, IQ sampling frequency and IF gain returned no archived matches. Runtime confirmation is unavailable. Absence of logs establishes no positive runtime fact. No runtime measurements were collected.

Historical writer evidence is `iq_channel.tofile(filename)`. The supplied interpretation of the hash-bound historical file gives `<c8`: 21,846 samples, 21,773 finite, absurd magnitudes up to approximately 3.39e38; `<c16`: 10,923 samples, all finite, median magnitude approximately 0.0030159 and maximum approximately 0.57967. This strongly supports historical little-endian complex128, not future V2 recorder conformance. No new IQ/scientific analysis was performed.

Host inventory supplied by the user: Pop!_OS 24.04 LTS, kernel 7.0.11-76070011-generic, Python 3.12.3, NumPy 1.26.4. This is partial, not a complete dependency/driver lock.

## Retained blockers

All 28 original NOT_ESTABLISHED settings remain acquisition-lock blockers. Configuration support is recorded separately from operational resolution. `activation_procedure`, `agc_state`, `antenna_cable_inventory`, `calibration_synchronization`, `clock_source`, `decimation_channelizer`, `dropped_sample_error_instrumentation`, `environment_measurement_procedure`, `exit_status_instrumentation`, `frontend_sample_rate_hz`, `full_configuration_snapshot`, `geometry_location_orientation`, `hardware_inventory`, `host_software_versions`, `lna_gain`, `partial_file_detection`, `raw_naming_convention`, `receiver_channel_count`, `receiver_gain`, `recorder_implementation`, `recorder_output_conformance`, `recorder_trigger_buffer_rollover`, `reviewed_execution_commit`, `rf_center_frequency_hz`, `rf_if_baseband_bandwidths`, `scientific_channel_mapping`, `source_inventory`, `vga_baseband_gain`.

The earlier full-settings hash `8f7b52c0b0923cae1e9781878c743bdfd309cc4e52659c1c07815507e53574c9` and current `fccb9eaddb10467ee04128686d50e5a8586276ae09cb631a83925c9343269b4a` remain an unresolved snapshot conflict. Dirty implementations, unknown physical bandwidths and separate LNA/VGA gains, unobserved sync/runtime state, incomplete inventories and recorder/instrumentation evidence prevent finalization.

## Verification scope

The companion tests pin the entire recovery JSON and this Markdown, reject mutations, and check protected repository bytes against the base commit. Tests use repository evidence only and do not require mutable external repositories or hardware. The JSON records external hashes as a checkpoint, not a live dependency.

Existing acquisition-lock/preregistration provenance validation has a closed descendant allowlist at the base commit. These three additive recovery paths are outside that allowlist. The unchanged acquisition-lock suite ran 22 tests with 2 failures and 3 errors; the unchanged preregistration suite ran 19 tests with 3 failures and 5 errors (including subtest reports). All reported failures/errors arose from rejection of the three recovery paths, including expected-error-message mismatches. The recovery suite passes 21 tests. `git diff --check` passes. These are not all-green regression results. This checkpoint does not alter or bypass that gate.
