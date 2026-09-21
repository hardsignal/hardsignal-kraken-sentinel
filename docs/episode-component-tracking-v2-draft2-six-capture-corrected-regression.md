# Corrected six-capture Draft 2 regression

New bounded run at `7e38dd9`; original NOT_READY regression preserved byte-identically.

A partial startup attempt was stopped during preflight to remove repeated full-inventory checks from worker startup. It is preserved in the separate `corrected-regression-startup-attempt` archive. The final run repeated the full test gate and all 164 cases with unchanged limits.

Final decision: **READY_FOR_DRAFT2_FULL_MATRIX_REVIEW**.

Pre-run gate: 149 tests, 0 failures, 0 errors.
6 captures; frozen 41 episodes; 164 cases (41 connected, 123 compact).
Fully passed: 164/164. Exact compact cardinalities: 123/123.
Unresolved counts: 0; unresolved queries: 0; reproduction failures: 0.

All cases passed structural checks and deterministic byte-identical staged reload. Compact family bytes match the original run; all 41 connected results match historical outputs. All frozen resource limits remained unchanged.

## Distributions

Association status: `{"AMBIGUOUS_ASSOCIATION": 96, "INSUFFICIENT_SUPPORT": 31, "MULTIPLE_PERSISTENT_TRACKS": 25, "UNIQUE_PERSISTENT_TRACK": 12}`.

Non-null primary count: 12.

Persistent-track counts (count: cases): `{"0": 102, "1": 14, "2": 7, "3": 4, "4": 7, "5": 5, "6": 1, "8": 2, "9": 2, "10": 1, "13": 2, "15": 1, "16": 2, "17": 1, "18": 1, "26": 1, "39": 1, "40": 1, "44": 1, "49": 1, "54": 1, "81": 1, "124": 1, "145": 1, "146": 1, "356": 1, "528": 1}`.

## Observed maxima

| Measurement | Case | Value |
| --- | --- | --- |
| largest_cardinality | C4-E08/margin-1 | 378038954451765697490 |
| slowest_count | C6-E03/margin-0 | 2.6287965869996697 |
| slowest_full_case | C4-E08/margin-1 | 70.86846854200121 |
| slowest_execution | C4-E08/margin-1 | 35.64100802101893 |
| max_query_calls | C1-E02/margin-0 | 1110 |
| max_transitions | C6-E05/margin-1 | 63978 |
| max_live_states | C4-E08/margin-1 | 74064 |
| max_packed_bytes | C4-E08/margin-1 | 20584913 |
| max_rss_kib | C1-E06/margin-1 | 152060 |

Runtimes are seconds; full case includes execution and reload worker wall time. RSS is KiB; packed storage is bytes.

## Mandatory controls

| Case | Arm | Exact cardinality |
| --- | --- | --- |
| C1-E02 | margin-0 | 1 |
| C1-E02 | margin-0.25 | 32743 |
| C1-E02 | margin-1 | 5788836 |
| C4-E08 | margin-0 | 2 |
| C4-E08 | margin-0.25 | 17067800502243 |
| C4-E08 | margin-1 | 378038954451765697490 |
| C6-E02 | margin-1 | 217075 |
| C6-E03 | margin-0.25 | 349149 |
| C6-E03 | margin-1 | 378536340 |
| C6-E05 | margin-1 | 697122 |

Both REPL E03 margins reproduce the committed exact query/metric payload, 1,012 public calls, MULTIPLE_PERSISTENT_TRACKS, and null primary.

## Historical parity and corrected blockers

All 160 previously passing cases retain their scientific payloads. The four earlier failures now pass.

- C6-E02 margin-1: cardinality 217075; 585 query calls.
  - cardinality_counting: COMPUTATION_UNRESOLVED → EXACT.
- C6-E03 margin-0.25: cardinality 349149; 1012 query calls.
  - exact_queries: COMPUTATION_UNRESOLVED → EXACT.
  - metric_projection: BLOCKED_BY_QUERY_FAILURE → COMPLETE.
- C6-E03 margin-1: cardinality 378536340; 1012 query calls.
  - cardinality_counting: COMPUTATION_UNRESOLVED → EXACT.
  - exact_queries: COMPUTATION_UNRESOLVED → EXACT.
  - metric_projection: BLOCKED_BY_QUERY_FAILURE → COMPLETE.
- C6-E05 margin-1: cardinality 697122; 475 query calls.
  - cardinality_counting: COMPUTATION_UNRESOLVED → EXACT.

REPL E02 and E05 preserve the earlier completed query, association, and metric payloads. REPL E03 preserves every previously completed exact operation and reproduces the committed query milestone in full. Only unresolved stages and their dependent projections became exact/complete; provenance identifies this new run.

## Integrity and reproduction

All 1805 pre-existing tracked files remain byte-identical; HEAD remains `7e38dd9caeb19282ecaa7b5d8464074e77fa5986`. This covers the original NOT_READY regression and all prior solver/query investigations.
All source bindings, artifact hashes, canonical serializations, tracked diff and independent new-file whitespace checks are audited in the corrected integrity JSON.
No scientific parameters, candidate identities, denominator, path/singleton/partition semantics, or binary64 policy changed. No RF capture, detection, full matrix, device identification/discrimination claim, commit, or push.

Reproduce into a new directory:

```sh
python3 analysis/regress_episode_component_tracking_v2_draft2_six_capture_corrected.py --output results/NEW-CORRECTED-RUN
```

Artifacts: corrected plan, baseline, regression directory (per-case records and backend certificates), summary JSON, and integrity JSON under `results/episode-component-tracking-v2-draft2-six-capture-corrected-*`.
