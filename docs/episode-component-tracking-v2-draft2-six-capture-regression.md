# Draft 2 bounded six-capture regression

**Decision: NOT_READY.** All 164 predeclared cases were evaluated; 160 passed the complete gate. Of 123 compact cases, 120 have exact cardinality. Four cases have explicit unresolved stages. No failure was retried with larger limits.

Checkpoint remained `8d58ec0`. The frozen structural plan contains every one of the 41 saved episodes in the six requested captures and exactly four arms per episode. Plan SHA-256: `e6917efb66bc9eda0eddb94ec2d39a7c8c7271fcd1251b61d3eff70c17556728`. This is a 164-case validation of four fixed arms, not the prohibited 160-arm matrix.

## Frozen scope

| Capture | Episodes | Cases |
|---|---|---:|
| PIPELINE-TPMS-004-20260917-233423 | E01, E02, E03, E04, E05, E06 | 24 |
| PIPELINE-TPMS-005-20260917-235439 | E01, E02, E03, E04, E05 | 20 |
| PIPELINE-TPMS-007-20260918-002700 | E01, E02, E03, E04, E05, E06, E07, E08 | 32 |
| PIPELINE-TPMS-008-20260918-003900 | E01, E02, E03, E04, E05, E06, E07, E08 | 32 |
| BETWEEN-DEVICE-V1-20260919-022917 | E01, E02, E03, E04, E05, E06, E07 | 28 |
| BETWEEN-DEVICE-REPL-V1-20260919-024341 | E01, E02, E03, E04, E05, E06, E07 | 28 |

The plan document and JSON record original fragment counts, eligible counts by fragment, and candidate-context hashes before execution. Input: `results/episode-component-tracking-v2-draft2-experiment/native__w200__connected.json`, SHA-256 `097c48395cb5cabb639a74d697d03a431b941f9f64cfebafa2e23a2b3d8053ab`. No input, eligibility rule, scientific parameter, representation or width was changed.

## Validation and controls

- 97 tests passed; zero failures, zero errors. This includes all eight requested existing suites and seven new inventory/gate/failure tests. The suite ran before batch evaluation.
- All seven limited-regression episodes were revalidated first (28 cases), with complete scientific payload and family-byte parity. Only TPMS-004 E02 margin-1 cardinality changed as authorized.
- E08 counts: margin 0 = 2; margin 0.25 = 17,067,800,502,243; margin 1 = 378,038,954,451,765,697,490.
- TPMS-004 E02 counts: margin 0 = 1; margin 0.25 = 32,743; margin 1 = 5,788,836. Family, query output/call counts, metrics, status, primary and denominator matched the committed limited results.
- Connected saved-result parity: 41/41. Provenance verified: 164/164. Compact family construction/reconstruction complete: 123/123. Exact compact queries and metric projection: 121/123.
- Deterministic byte-identical staged reload/reproduction: 164/164, including unresolved results. Reload consumes saved sidecars without recounting.
- All 121 available compact projections passed independent path, step, coherent-range, support, coverage, candidate-alternative, invariant-disjointness and primary checks; structural violations = 0. Two query-failed projections remain unavailable, not successful structural checks.
- One-fragment REPL E07 and two-fragment E08 preserved their established status, null primary and zero persistent tracks. E08 remains AMBIGUOUS_ASSOCIATION; no persistent track was manufactured.

## Explicit unresolved cases

All four cases belong to `BETWEEN-DEVICE-REPL-V1-20260919-024341`.

| Episode / arm | Cardinality | Query / projection state | Bottleneck |
|---|---|---|---|
| E02 / margin 1 | COMPUTATION_UNRESOLVED; null | EXACT queries; complete projection | 60-second counting deadline, measured 60.000091 s; 145 peak states, 465 transitions |
| E03 / margin 0.25 | EXACT 349,149 | COMPUTATION_UNRESOLVED; projection blocked | Existing 200,000-node exact-cover search limit during queries; 964 public calls |
| E03 / margin 1 | COMPUTATION_UNRESOLVED; null | COMPUTATION_UNRESOLVED; projection blocked | IEEE prefix DAG at position 22 attempted state 250,001; 1,260,885 transitions; queries also reached the existing exact-cover search limit at 964 calls |
| E05 / margin 1 | COMPUTATION_UNRESOLVED; null | EXACT queries; complete projection | Streaming pivot join, pivot 5, attempted transition 5,000,001; 12,745 peak states |

The saved E02 deadline reason literally says `Staged exact-query wall-clock limit exceeded` because the unchanged shared deadline helper uses that message. Its structured stage is `counting`; the enforced duration was 60 seconds, not the 120-second query deadline. Queries completed independently. The sub-millisecond timing overrun and first rejected state/transition are recorded as exhaustion, not additional resource allowance.

Query failures have `association=null` and `metrics=null` with explicit failure/blocking states. Their missing primary and persistent counts are unavailable values, not abstentions or zero tracks. Cardinality-only failures retain independently completed query-derived association and metrics; these are not substitutes for unresolved counting. No partial count is published.

## Distributions

| Association status | Cases |
|---|---:|
| AMBIGUOUS_ASSOCIATION | 96 |
| MULTIPLE_PERSISTENT_TRACKS | 23 |
| UNIQUE_PERSISTENT_TRACK | 12 |
| INSUFFICIENT_SUPPORT | 31 |
| UNAVAILABLE_QUERY_FAILURE | 2 |

There are **12 non-null primaries among 162 available associations**. Two further associations are unavailable. Connected arms contribute no non-null primary.

| Persistent-track count | Cases |
|---:|---:|
| 0 | 102 |
| 1 | 14 |
| 2 | 7 |
| 3 | 4 |
| 4 | 7 |
| 5 | 5 |
| 6 | 1 |
| 8 | 2 |
| 9 | 2 |
| 10 | 1 |
| 13 | 2 |
| 15 | 1 |
| 16 | 2 |
| 17 | 1 |
| 18 | 1 |
| 26 | 1 |
| 39 | 1 |
| 40 | 1 |
| 44 | 1 |
| 49 | 1 |
| 54 | 1 |
| 81 | 1 |
| 145 | 1 |
| 146 | 1 |
| 528 | 1 |
| Unavailable | 2 |

These are counts of query-derived possible persistent paths (or historical connected tracks), not a claim that all possible paths coexist in one retained hypothesis.

## Performance and unchanged limits

| Observation | Maximum | Case |
|---|---:|---|
| Public query calls | 1,110 | C1-E02 / margin-0 |
| Observed live states (includes rejection) | 250,001 | C6-E03 / margin-1 |
| Transitions (includes rejection) | 5,000,001 | C6-E05 / margin-1 |
| Worker peak RSS, KiB | 129,992 | C6-E03 / margin-1 |
| Packed polynomial bytes | 20,584,913 | C4-E08 / margin-1 |
| Execution + reload wall seconds | 113.710525 | C6-E02 / margin-1 |

The largest exact cardinality is **378,038,954,451,765,697,490**, E08 margin 1. The slowest complete execution/reload pair is REPL E02 margin 1, **113.710525 s** including subprocess startup and supervision. Peak worker RSS is **129,992 KiB** (126.95 MiB).

Limits remained: 250,000 live counting states; 5,000,000 transitions; 60 counting seconds; 33,554,432 packed-polynomial bytes; 60 family-construction seconds; 5,000 public query calls / 120 query seconds; 400 worker seconds; observed RSS ceiling 524,288 KiB. The original exact-cover search limit of 200,000 was also retained. Three counting arms exhausted limits, and two query arms exhausted the solver search limit. There were no worker wall-clock/RSS or packed-polynomial ceiling failures. No full-matrix runtime is inferred.

Per-case `case.json` includes input/context/family/model/sidecar hashes; separate stage states; cardinality state/value/reason; association status and primary availability; possible/persistent/invariant/alternative counts; timings, transitions, state and polynomial usage, RSS, and failure details. `result.json` retains the full association and exact member/path outputs where available.

## Complete case inventory

The compact values below are exact decimal cardinalities unless marked UNRESOLVED. Passing counting alone does not mean a case passed queries. All connected cases passed.

| Label | Margin 0 | Margin 0.25 | Margin 1 | Full-gate cases passed / 4 |
|---|---:|---:|---:|---:|
| C1-E01 | 2 | 83 | 7418 | 4 / 4 |
| C1-E02 | 1 | 32743 | 5788836 | 4 / 4 |
| C1-E03 | 1 | 38 | 399 | 4 / 4 |
| C1-E04 | 1 | 105 | 3186 | 4 / 4 |
| C1-E05 | 1 | 9 | 31 | 4 / 4 |
| C1-E06 | 1 | 2 | 8 | 4 / 4 |
| C2-E01 | 1 | 19 | 86 | 4 / 4 |
| C2-E02 | 1 | 14 | 39 | 4 / 4 |
| C2-E03 | 1 | 25 | 726 | 4 / 4 |
| C2-E04 | 2 | 4 | 26 | 4 / 4 |
| C2-E05 | 1 | 3723 | 416900 | 4 / 4 |
| C3-E01 | 1 | 130 | 1297 | 4 / 4 |
| C3-E02 | 1 | 13 | 101 | 4 / 4 |
| C3-E03 | 1 | 3 | 6 | 4 / 4 |
| C3-E04 | 1 | 388 | 3511 | 4 / 4 |
| C3-E05 | 1 | 12 | 52 | 4 / 4 |
| C3-E06 | 1 | 4 | 23 | 4 / 4 |
| C3-E07 | 1 | 1 | 1 | 4 / 4 |
| C3-E08 | 1 | 21 | 167 | 4 / 4 |
| C4-E01 | 1 | 1 | 2 | 4 / 4 |
| C4-E02 | 1 | 6 | 72 | 4 / 4 |
| C4-E03 | 1 | 1 | 2 | 4 / 4 |
| C4-E04 | 1 | 3 | 15 | 4 / 4 |
| C4-E05 | 1 | 54 | 169 | 4 / 4 |
| C4-E06 | 1 | 2 | 7 | 4 / 4 |
| C4-E07 | 1 | 2 | 12 | 4 / 4 |
| C4-E08 | 2 | 17067800502243 | 378038954451765697490 | 4 / 4 |
| C5-E01 | 1 | 397 | 101884 | 4 / 4 |
| C5-E02 | 1 | 682 | 12911 | 4 / 4 |
| C5-E03 | 1 | 1 | 1 | 4 / 4 |
| C5-E04 | 1 | 7 | 23 | 4 / 4 |
| C5-E05 | 1 | 14 | 86 | 4 / 4 |
| C5-E06 | 1 | 26 | 704 | 4 / 4 |
| C5-E07 | 1 | 29 | 157 | 4 / 4 |
| C6-E01 | 1 | 24 | 294 | 4 / 4 |
| C6-E02 | 1 | 379 | UNRESOLVED | 3 / 4 |
| C6-E03 | 1 | 349149 | UNRESOLVED | 2 / 4 |
| C6-E04 | 1 | 34 | 1667 | 4 / 4 |
| C6-E05 | 1 | 2429 | UNRESOLVED | 3 / 4 |
| C6-E06 | 1 | 84 | 2670 | 4 / 4 |
| C6-E07 | 1 | 1 | 1 | 4 / 4 |

C1 through C6 follow the capture ordering in the frozen scope table. All anomalies are retained.

## Integrity, artifacts and next decision

All **519 pre-existing tracked files are byte-identical** to the pre-execution snapshot. Checkpoint remains `8d58ec0`; tracked diff is empty. The old limited-regression NOT_READY artifacts and E02 investigation are unchanged. Ordinary `git diff --check` and independent whitespace checks for new untracked files pass; the final integrity JSON records the independent audit.

New files:

- `analysis/regress_episode_component_tracking_v2_draft2_six_capture.py`
- `tests/test_episode_component_tracking_v2_draft2_six_capture.py`
- `docs/episode-component-tracking-v2-draft2-six-capture-plan.md`
- This regression report.
- `results/episode-component-tracking-v2-draft2-six-capture-plan.json`
- `results/episode-component-tracking-v2-draft2-six-capture-regression/`: batch/source/hash manifest, test log, preflight gate, all case artifacts and logs, complete regression JSON and SHA-256 file manifest.
- `results/episode-component-tracking-v2-draft2-six-capture-integrity.json`

Reproduction command (requires a new output directory):

```sh
python3 analysis/regress_episode_component_tracking_v2_draft2_six_capture.py --output results/NEW-OUTPUT-DIRECTORY
```

No scientific parameter, counter implementation or historical runner was changed. The new regression wrapper only adds orchestration, frozen limits, provenance, measurement, parity checks and explicit failure reporting. Detection, input loading/regeneration entrypoints and expanded-family materialization are forbidden in worker processes.

The decision is **NOT_READY**. The four listed computational blockers need separate investigation before a full-matrix review can pass. This run does not authorize or execute the 160-arm matrix. No RF capture, FFT/component detection, device-identification/discrimination claim, commit or push occurred.
