# Kraken RF Sentinel V2 acquisition lock — version 1

**BLOCKED_PENDING_ACQUISITION_SETTINGS** — **V2_ACQUISITION_LOCK_BLOCKED**.

Parent: `c98ad53a6d278140c98ecbe045f2462c24f5852f`. No RF collection, candidate execution, episode construction or scoring is authorized. The frozen scientific preregistration is unchanged; Stage 37 remains DEFERRED.

## Evidence and settings

Each evidence path below is SHA-256-bound in the experiment JSON `evidence_sha256`. JSON pointers identify the exact inherited fields. Historical observations, preregistered requirements, and new administrative policies are distinguished. A complete old settings hash is not evidence of its unknown contents.

| Setting | Frozen value / status | Origin and evidence |
|---|---|---|
| vfo_bw_0 | `25000` | HISTORICAL_AND_PREREGISTERED: VFO setting only; does not establish unseen frontend settings. `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_start/values/vfo_bw_0`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_finish/values/vfo_bw_0`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition/vfo_bw_0` |
| vfo_freq_0 | `433868160` | HISTORICAL_AND_PREREGISTERED: VFO setting only; does not establish unseen frontend settings. `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_start/values/vfo_freq_0`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_finish/values/vfo_freq_0`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition/vfo_freq_0` |
| vfo_iq_0 | `"True"` | HISTORICAL_AND_PREREGISTERED: VFO setting only; does not establish unseen frontend settings. `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_start/values/vfo_iq_0`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_finish/values/vfo_iq_0`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition/vfo_iq_0` |
| vfo_squelch_0 | `-45` | HISTORICAL_AND_PREREGISTERED: VFO setting only; does not establish unseen frontend settings. `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_start/values/vfo_squelch_0`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_finish/values/vfo_squelch_0`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition/vfo_squelch_0` |
| vfo_squelch_mode_0 | `"Manual"` | HISTORICAL_AND_PREREGISTERED: VFO setting only; does not establish unseen frontend settings. `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_start/values/vfo_squelch_mode_0`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json#/settings_at_finish/values/vfo_squelch_mode_0`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition/vfo_squelch_mode_0` |
| effective_complex_sample_rate_hz | `25000` | PREREGISTERED: Preregistered recorder input rate; physical clock accuracy not characterized. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/inherited_detector_and_tracking/sample_rate_hz`; `docs/episode-component-tracking-v2-draft1.md` |
| sample_dtype | `"<c16"` | PREREGISTERED: Raw complex128: two float64 components, 16 bytes per complex sample. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/inherited_detector_and_tracking/dtype`; `docs/episode-component-tracking-v2-draft1.md` |
| byte_order | `"little"` | PREREGISTERED: Explicitly inherited; not HackRF CS8. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/numerical_policy/iq`; `docs/episode-component-tracking-v2-draft1.md` |
| vfo_index | `0` | PREREGISTERED: Index from explicit vfo_*_0 fields; not proof of physical channel selection. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/acquisition`; `docs/episode-component-tracking-v2-draft1.md` |
| capture_duration_seconds | `180` | PREREGISTERED: Fixed timing; no adaptive extension. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/acquisition_plan/capture_timing` |
| slot_duration_seconds | `30` | PREREGISTERED: Fixed timing; no adaptive extension. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/acquisition_plan/capture_timing` |
| activation_offset_seconds | `5` | PREREGISTERED: Fixed timing; no adaptive extension. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/acquisition_plan/capture_timing` |
| minimum_inter_capture_seconds | `60` | PREREGISTERED: Fixed timing; no adaptive extension. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/acquisition_plan/capture_timing` |
| file_hash_algorithm | `"SHA-256"` | HISTORICAL_AND_PREREGISTERED: Hash each original raw file; immutable after freeze. `capture/kraken_capture.py`; `captures/BETWEEN-DEVICE-REPL-V1-20260919-024341/manifest.json` |
| raw_immutable | `true` | HISTORICAL_AND_PREREGISTERED: Never edit, overwrite, reslice or replace original files. `docs/kraken-episode-grouping-v1.md`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json` |
| rf_center_frequency_hz | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: VFO frequency is established; RF tuner center is not. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| frontend_sample_rate_hz | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: ADC/frontend complex rate not recorded. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| rf_if_baseband_bandwidths | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: RF/IF filters and baseband chain beyond VFO bandwidth unknown; document exact values or hardware-supported non-applicability. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| receiver_gain | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Exact per-channel receiver gains absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| lna_gain | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Kraken LNA state/gain absent; HackRF 32 dB is inapplicable. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| vga_baseband_gain | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Exact gain or evidence-supported non-applicability absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| agc_state | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Per-stage AGC states absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| decimation_channelizer | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Frontend-to-25 ksample/s chain, factors, filters and versions absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| receiver_channel_count | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Number enabled and number recorded not established. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| scientific_channel_mapping | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: VFO 0 to physical channel or combination mapping absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| hardware_inventory | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Receiver model/revision/serial, firmware, channel serials and relevant peripherals absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| antenna_cable_inventory | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Antenna/cable identity, arrangement and connections absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| geometry_location_orientation | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Locked location, source/receiver geometry, orientation, measurements and photograph hashes absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| calibration_synchronization | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Required calibration/synchronization procedure and state, or justified non-applicability, absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| recorder_implementation | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: kraken_capture.py is a provenance wrapper, not the IQ writer. Actual writer source/binary/version/hash absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| recorder_trigger_buffer_rollover | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Trigger, buffering, pre/post-trigger, flush and file rollover behavior absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| raw_naming_convention | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Historical names are examples, not a locked implementation or timezone/collision rule. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| recorder_output_conformance | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Preregistered <c16 input is fixed, but actual writer conformance and completion detection are unverified. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| clock_source | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: RF reference, UTC clock discipline, monotonic clock identity/resolution and synchronization uncertainty absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| dropped_sample_error_instrumentation | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Dropped sample/overflow/error instrumentation and logs absent; cannot assume zero. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| exit_status_instrumentation | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Writer exit status and abnormal termination capture mechanism absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| partial_file_detection | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Close/flush/size stability and incomplete-file detection implementation absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| full_configuration_snapshot | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Historical settings hashes differ; complete bytes and explanation unavailable. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| host_software_versions | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Host identity, OS/kernel, CPU, Python, NumPy, dependencies, drivers and recorder versions absent. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| source_inventory | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: S1/S2 physical source identities/serials and batteries not locked. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| activation_procedure | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Exact activation tool/procedure, source state, idle enforcement and failure logging not established. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| environment_measurement_procedure | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Temperature, battery, interference/deviation metadata required; measurement methods and units not locked. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |
| reviewed_execution_commit | NOT ESTABLISHED — BLOCKS | NOT_ESTABLISHED: Parent requires a reviewed runner commit before capture; no execution implementation is authorized here. `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/not_established_by_committed_evidence`; `results/episode-component-tracking-v2-v2-discrimination-preregistration.json#/fixed_parameters/pre_acquisition_lock` |

## Conflicts and exclusions

Five exposed VFO values agree numerically; full settings bytes differ. No silent choice of unseen settings. Earlier full hash: `8f7b52c0b0923cae1e9781878c743bdfd309cc4e52659c1c07815507e53574c9`; later: `fccb9eaddb10467ee04128686d50e5a8586276ae09cb631a83925c9343269b4a`. All twelve Kraken manifests and four HackRF manifests were inspected and bound. Float versus integer spelling of 433868160 is numerically consistent; full-file hash disagreement remains unresolved.

Independent Wider-IQ V1: 2 MHz, 1.75 MHz filter, CS8, LNA/VGA 32 dB are NOT Kraken settings. No cross-device inheritance.
No DoA endpoint or geometry-based source identity inference. Exact geometry still matters as parent environmental control; no invented array spacing or phase-accuracy target.

## Frozen design and construction

8 sessions; starts at least 86400 seconds apart, one per day; 2 controlled sources; 3 repeats/source/session; 48 captures; 6 slots/capture; 288 slots. Capture duration 180 seconds; half-open 30-second slots; command activation at slot +5 seconds; at least 60 seconds between captures.

Odd sessions: S1-R1, S2-R1, S1-R2, S2-R2, S1-R3, S2-R3. Even sessions reverse source order within each repeat. No further randomization or adaptive ordering. Both A (grid_sigma5) and B (grid_sigma10) remain connected, width 350 Hz, and later receive byte-identical captures.

Group separately within each capture, never across captures or sessions. >4 seconds, (frozen mtime_ns, filename) order. Episode numbers 1..N per capture, fragment ordinals 1..N per episode. One original file per fragment. No minimum inclusion count; retain one/two-fragment and incomplete episodes; unusable fragments remain in denominators. Slot assignment and anomaly treatment exactly as parent; no grouping/scoring in this validator.

Fixed lexical mapping, disclosed and hash-bound; administrative labels, not concealed blinding. Acquisition sees session/source/repetition/slot only; no candidate setting or feedback. Both configurations receive identical inputs after all acquisition. Optional custodian blinding remains parent policy.

## Manifest hierarchy

A. The experiment JSON is the immutable top-level lock. All listed null mandatory values block collection. No fake settings or example observations are supplied.

B. One session manifest per session: ordinal, IDs, start/end, previous-session separation, exact settings start/end and configuration hash, commit/lock hash, capture order, operator/environment metadata, errors/warnings and completeness.

C. One capture manifest per scheduled capture: session/source/repeat IDs, six expected activation ledger entries, raw-file array (path, SHA-256, size, frozen mtime_ns, completeness), start/end UTC and monotonic time, exit status, drop count, log hashes, errors/warnings and completeness. Multiple raw files are intentional: each original recorder file is a later fragment. Raw paths are metadata only and are never opened by this validator.

The schema also defines an assembled series containing the eight session manifests and their captures for cross-manifest checking; it does not require a fourth persisted manifest. Schemas only are supplied. Separate files can be assembled in memory for validation.

Sessions V2-J01..V2-J08; captures V2-Jjj-Ss-Rr; slots capture-ID-T01..T06. Source IDs are operator inventory labels, never RF-inferred. Odd/even order is parent counterbalance. Raw file names are unresolved and cannot be inferred from capture IDs.

New operational metadata convention: ISO-8601 UTC ending Z with fractional seconds allowed, plus monotonic_ns for capture and activation markers. Recorded file mtime_ns frozen once on close. Clock source remains unresolved.

Record operator ID and notes; ambient temperature, battery states, interference, deviations, location and geometry reference, source state. Exact instruments/procedure remain unresolved. Settings snapshots start/end must equal the frozen settings object and hash. Record activation UTC/monotonic markers and failures without changing expected slots.

## Gate, abort and changes

The validator is metadata-only and imports only the Python standard library. It parses strict JSON, rejects duplicates/nonfinite values and unknown keys, pins the entire canonical experiment object and schema, checks evidence hashes, and validates structure, ID uniqueness, timing, order, settings hashes and immutable bindings. It never opens raw-file/log paths, imports scientific modules, launches a process or contacts hardware. SHA syntax validation is not proof that raw bytes match: independently reviewed provenance tooling must verify raw size/hash/completion before COMPLETE. That implementation remains a blocker.

This blocked version deliberately has no READY transition, override, tuning option or collection command. Validating the blocked contract successfully is not permission to acquire: CLI returns 2. Any series submitted against this lock is rejected even when its metadata structure is valid. Failed/aborted records must still be preserved externally; validator rejection never deletes anything.

Abort on: missing mandatory field; not READY before acquisition; hardware/configuration drift; recorder version/hash mismatch; incomplete raw file; hash or size verification failure; duplicate IDs; session/capture/order/slot structure violation; session start separation below 24 hours; unexpected termination or sample loss; configuration or commit changed; unresolved evidence conflict.

Preserve failed/partial files, logs, attempted/missing ledger entries and all scheduled slots. No replacements or retries. Complete requires exit code zero and no acquisition errors; warnings retained. No-file captures can be operationally complete only with independently evidenced writer completion; zero episodes is not itself an acquisition failure.

After finalization no additions, relaxations or changes to receiver/recorder/acquisition settings or structure; especially none after capture 1. Required change invalidates the series; retain all records and require new preregistration/version and wholly new data. Never use pilots or outcomes to choose settings.

## Cryptographic binding without a self-reference

The lock binds the schema SHA-256; the validator pins the canonical lock SHA-256. The eventual Git commit binds all five exact files (including this document and tests). It cannot be embedded in its own contents. `post_commit_binding.authorizing_commit` is null deliberately, never a fabricated commit. After commit, run `V2_LOCK_COMMIT=<full commit> PYTHONPATH=analysis:tests python3 -m unittest test_episode_component_tracking_v2_v2_acquisition_lock -v`. The post-commit test checks ancestry from c98ad53, exact five-file change allowlist, each committed artifact byte against the worktree and all evidence hashes. It does not authorize this BLOCKED version. A future authorizing version must pass READY checks and bind its commit and lock hash in every session/capture before collection.

Run the metadata-only gate with `python3 analysis/validate_episode_component_tracking_v2_v2_acquisition_manifest.py`; exit 2 is the expected BLOCKED result. No RF pilot may be used to fill the gaps.

## Artifact inventory

- `docs/episode-component-tracking-v2-v2-acquisition-lock.md`
- `results/episode-component-tracking-v2-v2-acquisition-lock.json`
- `results/episode-component-tracking-v2-v2-acquisition-manifest-schema-v1.json`
- `analysis/validate_episode_component_tracking_v2_v2_acquisition_manifest.py`
- `tests/test_episode_component_tracking_v2_v2_acquisition_lock.py`

## Validation boundary and observed legacy failures

The new contract suite includes in-memory metadata fixtures only; no session or
capture manifest with fabricated observations is written to the repository.
NOT_STARTED/aborted records preserve absent actual timestamps, settings and exit
status as null, with an explicit error reason. COMPLETE requires actual timing,
settings, logs, zero exit/drop status and no acquisition error. A metadata pass
never certifies raw-byte integrity or permits acquisition under this blocked lock.

The requested legacy preregistration and Stage 37 tests were run unchanged.
Their descendant allowlist rejects the five new acquisition artifacts, as well as
the pre-existing untracked `=24` and `=24h` files. The historical Stage 36 launcher
also rejects the new validator because its frozen source inventory requires every
`analysis/*.py` path to be present in the historical plan. These failures are
reported, not repaired by changing historical evidence, plans or validators.

The Draft 2 full-matrix discovery suite was loaded with exactly two tests skipped:
`test_connected_and_compact_roundtrip_tiny_fixture` and
`test_structural_dispatch_invariant_under_identity_relabeling`. Both call scientific
association/solver code. All other tests ran under a call guard rejecting scientific
input/detection/representation/association/solver/worker entry points; no forbidden
call occurred. Discovery: 54 tests, 45 passed, 7 provenance-inventory errors,
2 skipped. Preregistration: 19 tests, 16 passed, 3 descendant-allowlist errors.
Stage 37: 18 tests, 14 passed, one test with 2 failing subtests and 3 errors,
from those same provenance checks. Draft 2 review integration: 6/6 passed.
The new suite has 22 tests, including a post-commit tree/ancestry/byte-binding check.
The two untracked user files remain untouched and are not part of this commit.
