# V2 execution contract, reviewed preparation only

Decision: `V2_ACQUISITION_EXECUTION_CONTRACT_REVIEWED_BLOCKED`.
Acquisition remains `V2_ACQUISITION_LOCK_BLOCKED` and
`BLOCKED_PENDING_ACQUISITION_SETTINGS`. No acquisition authorization exists.
This descendant does not revise the lock, preregistration, selection, or any
scientific gate. A = grid_sigma5 / 350 Hz / connected; B = grid_sigma10 / 350 Hz /
connected. No outcomes are computed here.

`capture/v2_acquisition_runner.py` provides storage and scheduling primitives
through an explicitly synthetic push interface. Its command line always exits 3.
There is no hardware reader, SDR process launcher, transmitter, or unlock flag.
A future explicitly authorized change must integrate and review a reader and
resolve the original blockers before any bench execution. Synthetic COMPLETE
means storage conformance only; `scientific_eligible` is always false. The
embedded strict rehearsal schema is separate from the unchanged acquisition
manifest schema, which remains the scientific gate.

The JSON contract freezes VFO 0, 433868160 Hz, bandwidth 25000 Hz, manual squelch
-45, IQ enabled, effective stored rate 25000 complex samples/s, little-endian
complex128 `<c16`, 180 seconds, 30-second slots, activation +5 seconds within
each of six slots, and at least 60 seconds between end and next start.
Exactly 4,500,000 samples and 72,000,000 bytes are required. No pretrigger,
extension, rollover, or activation-triggered duration change is allowed.

Names encode experiment/version, session, capture, source, repeat and UTC with
nanoseconds. IDs cannot contain path separators. Equal identities/timestamps
are rejected, including partial-file collisions. Creation uses exclusive `xb`;
publication uses Linux renameat2 RENAME_NOREPLACE, never an overwrite-prone
rename. Data is flushed, fsynced, closed, streamed through finite/count checks,
and SHA-256 bound before publication; parent directories are fsynced. Final raw
permissions are read-only. This is application-level immutability, not a claim
that a privileged owner cannot change a file. Subsequent processing must verify
the manifest size/hash and preserve originals. No destructive cleanup occurs.
A crash before manifest publication leaves an orphan, never eligible evidence.
A `.partial` file cannot satisfy COMPLETE. Metadata also uses exclusive atomic
publication. Metadata I/O failure propagates as an error and preserves evidence.

Callers must catch write/reader exceptions and call `finish(error)`; signal
handlers raise Interrupted for SIGINT/SIGTERM and are restored by finish.
FAILED and ABORTED return nonzero exit codes and structured reasons. Hard kill
or power loss leaves INCOMPLETE partial/orphan evidence. There is deliberately
no recovery path that promotes these files. The rehearsal has an exact fake-clock
end check: an operational scheduling tolerance is not frozen and cannot be
inferred from a reported 1 ns clock resolution. A real reader must enforce an
absolute monotonic deadline even on stalled input, track sample continuity,
reject pre-start data, and establish the correspondence between sample time and
host receipt time. These are unresolved integration and bench requirements.

Activation is an ordered operator event interface, with actual realtime and
monotonic timestamps and lateness. It does not transmit or extend capture.
The source-specific activation procedure remains unresolved. Spacing uses
monotonic end-to-start time; an operational session manager must persist session
and boot identity and fail closed across restart or unknown previous end. UTC
can move backwards without changing deadlines. Runtime chrony status/offsets
must be captured when available and otherwise explicitly UNAVAILABLE. Historical
clock offsets in the contract are evidence, not current measurements or accuracy
guarantees.

All ten error counters are explicit. Only writer-local observed quantities start
at zero. Upstream underruns, overflows, dropped frames/buffers, reader failures,
and process-exit telemetry remain UNKNOWN until a reviewed adapter supplies
measurements. COMPLETE synthetic storage does not prove lossless hardware input.
The future session/capture snapshot requirements are listed in JSON.
`external_snapshot` verifies all required configuration/source file hashes, repo
HEADs and binary tracked diffs (git diff HEAD --binary --no-ext-diff), retaining
bytes, diffs and untracked inventories. Drift fails closed. The function is
read-only and never called by unit tests against real external installations.
Runner hash and contract hash are bound in every rehearsal manifest. A future
scientific manifest additionally requires the reviewed commit, start/finish
configuration, host/software, device mapping, boot ID and clock snapshots.

Historical channel semantics were inspected directly in the pinned source:
Kraken receiver lines 219–229 reshape payload into (active_ant_chs, cpi_length).
Processor line 403 copies that array; DSP decimation operates along the sample
axis; channelize lines 1379–1387 filters/decimates that axis and shifts each row.
Line 607 selects `vfo_channel[1]`: the second receiver row, not VFO 1 or a channel
combination. Lines 654 and 731 concatenate/write that selected row. The historical
writer is squelch/event buffered, so it is not adopted as the fixed-duration
recorder. Heimdall rtl_daq.c lines 493–501 assigns receiver i using serial
1000+i. A complete verified path through dirty rebuffering, synchronization,
physical receiver/connector and antenna/cable identity is not established here.
`scientific_channel_mapping` therefore remains BLOCKED. No alternate row is
selected. Historical IQ interpretation (10923/10923 finite as `<c16`, SHA-256
20561d440a122cd5f6faec2756d7979eed0d140de74760cb47fa2f691e362626) is not proof of
new writer or hardware conformance.

Implementation review resolves naming, partial-file detection, exit-status
representation and fixed trigger/buffer/rollover policy at the software-contract
level only. Recorder integration, output conformance, upstream instrumentation,
configuration snapshots, timing, hardware/software inventory and reviewed
execution identity remain partial. All original 28 lock blockers are retained.
Physical tuner bandwidth, separate LNA/VGA gains, board revision and receiver
firmware remain unknown. Activation, source inventory, geometry, cables and
environment procedures still require freezing. Bench work must later validate
continuous sample delivery, dtype/rate/count, timing, calibration/sync, physical
mapping, telemetry and end-to-end snapshots under explicit authorization.

The exact seven-path descendant provenance binding preserves historical hashes
and decisions, rejects unrelated paths, and verifies committed bytes after the
preparation checkpoint. Tests use fake clocks, bounded synthetic arrays and
temporary files only. No RF data is read or collected by the tests.
