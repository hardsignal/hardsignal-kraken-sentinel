# Draft 2 limited multi-episode regression

**Readiness: NOT_READY.** All 28 declared cases executed and reproduced. One required exact cardinality remains COMPUTATION_UNRESOLVED under the fixed budget; every family, query and metric projection completed. No limit was raised and no episode was substituted.

Checkpoint: `259e982`. This is a separate saved-candidate regression; the staged solver, counter, query adapter and consumer were used unchanged. No RF capture, FFT/component detection, full 160-arm matrix, scientific parameter change, commit or push.

## Predeclared selection

The selection plan was written before regression execution at `2026-09-20T01:31:30.824652+00:00`, SHA-256 `7abc15ebb82631adca9043640dcaeb17c7beb2cc238c53bdfd02b5ddd8e27425`. The executable pins this digest and refuses a changed plan. The batch manifest binds the same digest, original Git checkpoint, sources, tests and saved input. The only representation/width input is historical `native__w200__connected.json` (SHA-256 `097c48395cb5cabb639a74d697d03a431b941f9f64cfebafa2e23a2b3d8053ab`).

| Exact capture ID | Episode | Original fragments | Structural selection rationale |
|---|---:|---:|---|
| PIPELINE-TPMS-004-20260917-233423 | E02 | 5 | Earliest TPMS-004 multi-fragment episode outside the predeclared E01/E06 anomaly episodes. |
| PIPELINE-TPMS-004-20260917-233423 | E01 | 5 | Predeclared large V1 offset-spread anomaly at E01/F03; five-fragment episode. |
| PIPELINE-TPMS-005-20260917-235439 | E01 | 5 | Earliest multi-fragment TPMS-005 episode, adding the sixth development capture. |
| PIPELINE-TPMS-007-20260918-002700 | E01 | 5 | Earliest ordinary multi-fragment TPMS-007 episode. |
| BETWEEN-DEVICE-V1-20260919-022917 | E06 | 5 | Predeclared +261 Hz anomaly at E06/F04; five-fragment episode. |
| BETWEEN-DEVICE-REPL-V1-20260919-024341 | E07 | 1 | Required E07 one-fragment episode, testing singleton and insufficient-support semantics. |
| PIPELINE-TPMS-008-20260918-003900 | E08 | 2 | Established saved E08 integration control; two original fragments. |

“Ordinary” means outside the documented anomaly episodes, not an assumption of easy association or a particular status. Selection used episode IDs, fragment structure and existing anomaly locations, never outcomes or separation. TPMS-005 E01 was included to cover the sixth capture. The seven episodes and four association settings are the entire declared set.

The unchanged frozen limits were 250,000 live count states, 5,000,000 transitions, 60 seconds/count, 32 MiB packed polynomials; 5,000 public queries and 120 seconds/query stage. The regression additionally declared 60 seconds/family construction, 400 seconds/worker and a 512 MiB observed resident-memory limit. These are computational stop rules, not scientific parameter changes.

## Tests and stage verification

**82 tests passed; zero failures, zero errors.** Twelve new regression tests cover the fixed structural classes, anomaly references, original denominators, exact small-fixture parity, failure preparation, construction-limit propagation and rejection of incomplete batches. Seventy existing staged/solver/counter/sidecar tests were preserved and rerun. The historical detector test suite was excluded. Real-data workers guard against spectrum loading/detection, expanded solving/materialization and E08 recounting.

- Seven of seven connected projections equal the saved complete historical connected outputs.
- Twenty-one of twenty-one compact families reconstructed successfully, including candidate identities, exact frequencies and original fragment denominators.
- Twenty-eight of twenty-eight cases have VERIFIED provenance, COMPLETE metric projection, passing defined-output checks and byte-identical fresh-process reproduction.
- All 21 compact query stages are EXACT. No query failure, fabricated empty candidate set, false invariant or forced primary occurred.
- Twenty compact cardinalities are EXACT. One is COMPUTATION_UNRESOLVED with a null value and explicit reason; its complete family, exact status/primary and metrics remain valid.
- Support/coverage, persistent path definitions, invariant/alternative disjointness, per-candidate membership alternatives, path constraints and original denominators passed in every defined compact case.

## Exact and unresolved cardinalities

Counts are arbitrary-precision decimal strings in the bound sidecars. Connected cardinality is explicitly not applicable. E08 reuses committed family/count artifacts; the other six episodes have new family and sidecar files. Reload consumes the same pinned sidecar and recomputes association queries/metrics; it does not rerun counting.

| Episode | Margin 0 | Margin 0.25 | Margin 1 |
|---|---:|---:|---:|
| TPMS-004 E02 | 1 | 32,743 | COMPUTATION_UNRESOLVED (null) |
| TPMS-004 E01 | 2 | 83 | 7,418 |
| TPMS-005 E01 | 1 | 19 | 86 |
| TPMS-007 E01 | 1 | 130 | 1,297 |
| BETWEEN-DEVICE E06 | 1 | 26 | 704 |
| REPL E07 | 1 | 1 | 1 |
| TPMS-008 E08 | 2 | 17,067,800,502,243 | 378,038,954,451,765,697,490 |

The sole bottleneck is **TPMS-004 E02, margin 1**, in the committed IEEE counter’s **group composition, factor index 2**. The count stopped at **250,001 live states** against 250,000, after **2,137,240 transitions** and approximately **14.286 seconds**. It did not exhaust the 60-second or 5-million-transition limits. No partial count, approximation or lower bound is published as exact. This is distinct from the previously solved two-layer E08 matching problem. The regression does not introduce unproved binary64 cost-state compression or change the cost predicate.

The unresolved sidecar is accepted as a valid cardinality-state artifact. Its family remains complete, all 1,110 public queries complete, metric projection is complete, and fresh-process reproduction is byte-identical. The stage retains MULTIPLE_PERSISTENT_TRACKS with primary null; a counting failure does not decide either field.

## Status, primary and path membership

Legend: **A** = AMBIGUOUS_ASSOCIATION; **M** = MULTIPLE_PERSISTENT_TRACKS; **U** = UNIQUE_PERSISTENT_TRACK; **I** = INSUFFICIENT_SUPPORT. Only U rows have a non-null primary.

| Episode | Connected | Margin 0 | Margin 0.25 | Margin 1 |
|---|---|---|---|---|
| TPMS-004 E02 | A | M | M | M |
| TPMS-004 E01 | A | M | M | M |
| TPMS-005 E01 | A | U | A | A |
| TPMS-007 E01 | A | M | M | M |
| BETWEEN-DEVICE E06 | A | U | A | A |
| REPL E07 | I | I | I | I |
| TPMS-008 E08 | A | A | A | A |

The two non-null primaries are exactly:

- TPMS-005 E01, margin-0: `["E001_F001_C0191","E001_F003_C0013","E001_F005_C0072"]`.
- BETWEEN-DEVICE E06, margin-0: `["E006_F001_C0127","E006_F002_C0002","E006_F003_C0003"]`.

Every other primary is null. These are within-episode candidate-path outputs, not device-identification or discrimination conclusions. Status changes across margins are the frozen retained-family semantics, not parameter selection.

| Episode | Margin | Possible paths | Invariant | Alternative | Possible persistent paths |
|---|---:|---:|---:|---:|---:|
| TPMS-004 E02 | 0 | 272 | 272 | 0 | 4 |
| TPMS-004 E02 | 0.25 | 420 | 227 | 193 | 145 |
| TPMS-004 E02 | 1 | 808 | 191 | 617 | 528 |
| TPMS-004 E01 | 0 | 280 | 276 | 4 | 5 |
| TPMS-004 E01 | 0.25 | 304 | 263 | 41 | 17 |
| TPMS-004 E01 | 1 | 345 | 249 | 96 | 40 |
| TPMS-005 E01 | 0 | 277 | 277 | 0 | 1 |
| TPMS-005 E01 | 0.25 | 287 | 267 | 20 | 2 |
| TPMS-005 E01 | 1 | 292 | 262 | 30 | 4 |
| TPMS-007 E01 | 0 | 273 | 273 | 0 | 2 |
| TPMS-007 E01 | 0.25 | 292 | 260 | 32 | 9 |
| TPMS-007 E01 | 1 | 308 | 256 | 52 | 15 |
| BETWEEN-DEVICE E06 | 0 | 221 | 221 | 0 | 1 |
| BETWEEN-DEVICE E06 | 0.25 | 234 | 210 | 24 | 4 |
| BETWEEN-DEVICE E06 | 1 | 255 | 199 | 56 | 8 |
| REPL E07 | 0 | 38 | 38 | 0 | 0 |
| REPL E07 | 0.25 | 38 | 38 | 0 | 0 |
| REPL E07 | 1 | 38 | 38 | 0 | 0 |
| TPMS-008 E08 | 0 | 181 | 177 | 4 | 0 |
| TPMS-008 E08 | 0.25 | 441 | 86 | 355 | 0 |
| TPMS-008 E08 | 1 | 666 | 69 | 597 | 0 |

“Possible persistent paths” counts the path union; it is not a count of simultaneously present tracks. Co-occurrence/status uses the exact query adapter. No expanded retained-hypothesis array was generated for a saved episode. Query witnesses are used only by exact predicates.

REPL E07 has one original fragment: 38 fixed singleton paths, zero links, no persistent path, primary null, cardinality 1 and INSUFFICIENT_SUPPORT at all margins. E08 has two original fragments: no persistent path or primary at any margin. Its ambiguity remains AMBIGUOUS_ASSOCIATION, as required by the frozen status precedence; lack of persistence must not incorrectly erase ambiguity. Coverage is support divided by 1 and 2 respectively, never by a filtered denominator.

## Parity and provenance findings

The four available historical margin-zero derived outputs (TPMS-004 E01/E02, TPMS-005 E01, TPMS-007 E01) match in all defined association fields and exact count. Only stored derived fields are compared; historical expanded hypothesis arrays are not enumerated. E08 connected and all three compact scientific payloads match the committed staged E08 results, including metrics, path memberships, statuses, primaries and cardinalities.

Other positive-margin saved-episode projections have no complete historical compact reference, so no independent saved-output parity is claimed for them. Their exact query semantics are supported by unchanged validated infrastructure, exhaustive small-fixture tests, structural checks and deterministic reload. The test suite preserves crossing/competing, anomaly-shaped, one-/two-fragment, unusable and no-candidate cases and injected query/cardinality failures.

Every staged result pins saved-input and fragment-context SHA-256, family byte and embedded-model SHA-256, sidecar byte SHA-256, solver/counter/query/schema/consumer versions and hashes, experiment specification hash and batch Git context. New sidecars additionally bind the regression source/test hashes. Sidecar validation reconstructs the family and verifies the exact counter sources; staged integration also reconstructs from supplied candidates, including singleton isolation. The batch records the predeclared plan hash and all original tracked hashes. Source identity/hash binding is not itself a proof of a fabricated count; exact counts use the validated unchanged counter and its certificate/frozen-IEEE backend.

## Performance

Each row aggregates its four declared settings. First-pass worker wall time includes process startup, input loading, artifact preparation/counting where needed, integration, and checks. Reload wall time separately includes source/input verification, family reconstruction and recomputation of queries/metrics. Parent monitoring samples at 0.2-second intervals, so short worker times are quantized; precise phase timings are in each audit. Query calls below count public calls in the initial compact integrations, not internal search nodes.

| Episode | First-pass worker seconds | Reload worker seconds | Initial public query calls | Peak process KiB (either pass) |
|---|---:|---:|---:|---:|
| TPMS-004 E02 | 44.245 | 16.018 | 3,330 | 140,036 |
| TPMS-004 E01 | 2.005 | 1.605 | 1,266 | 119,496 |
| TPMS-005 E01 | 1.605 | 1.606 | 975 | 119,568 |
| TPMS-007 E01 | 1.605 | 1.604 | 1,062 | 119,492 |
| BETWEEN-DEVICE E06 | 1.605 | 1.605 | 864 | 119,288 |
| REPL E07 | 1.604 | 1.605 | 123 | 118,708 |
| TPMS-008 E08 | 79.884 | 80.681 | 2,520 | 119,148 |

Memory is Linux `/proc/self/status` VmHWM, including Python, JSON input loading and artifacts. It is a whole-process high-water mark, not incremental solver allocation. The maximum was 140,036 KiB (about 136.8 MiB). The 512 MiB observed-memory guard and 400-second worker timeout were not reached. E08 count time is not included because its committed sidecars were reused. No full-160-arm runtime or memory extrapolation is made.

## Readiness and outstanding work

**NOT_READY**, under the predeclared gate requiring all 21 compact cardinalities to complete exactly. The only outstanding scientific-output computation is TPMS-004 E02 margin-1 cardinality; provenance, query/metric correctness and reload checks passed. A separate exact general multi-fragment/IEEE-composition counting investigation is needed before advancing this gate. Keep the saved unresolved sidecar and all successful family/query outputs as evidence. No episode substitution, selective omission, approximate counting or resource-limit increase was used to change this decision.

This limited run spans all six development captures but is not the broader bounded six-capture regression and not the full matrix. No additional episodes or representation/width combinations were run.

## New files and integrity

- `analysis/regress_episode_component_tracking_v2_draft2_limited.py`
- `tests/test_episode_component_tracking_v2_draft2_limited_regression.py`
- `docs/episode-component-tracking-v2-draft2-limited-regression-plan.md`
- this report
- `results/episode-component-tracking-v2-draft2-limited-regression-plan.json`
- `results/episode-component-tracking-v2-draft2-limited-regression/`: batch manifest, test log, per-case family/cardinality/preparation/integration/reload/check/performance artifacts and logs, aggregate regression report and hash manifest
- `results/episode-component-tracking-v2-draft2-limited-regression-integrity.json`: final input/source/result hash verification and Git checks

All 300 pre-existing tracked files remain byte-identical to session entry. HEAD remains `259e982`. Git status contains only new untracked regression files; no tracked diff exists. `git diff --check` and new-source whitespace checks pass. The final integrity artifact records the exact status, hashes and inventory. No commit or push.
