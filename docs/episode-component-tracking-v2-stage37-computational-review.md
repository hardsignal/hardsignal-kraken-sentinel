# Stage 37B-preselection computational/resource review

**Decision: STAGE37_COMPUTATIONAL_EVIDENCE_REVIEW_COMPLETE**

This is an independent read-only feasibility review of the frozen Draft 2 Stage 36 full matrix at `0df44abb54231d5e8bfe84fe316ebbcf10d3130c`, on `codex/stage37-computational-review`. It makes no final configuration selection or scientific ranking. Speed is not scientific quality; an unresolved computation is not evidence of scientific inferiority. No arm was executed, retried, or erased, no scientific semantics or limits were changed, and the raw tree was not modified.

## Evidence and integrity

- Raw evidence: `/home/maciejduranczyk/hardsignal-kraken-sentinel/results/episode-component-tracking-v2-draft2-full-matrix-exact-v1`.
- Bindings: [Stage 36 final audit](../results/episode-component-tracking-v2-draft2-stage36-final-audit.json), [46,524-file SHA-256 inventory](../results/episode-component-tracking-v2-draft2-stage36-files.sha256), [canonical matrix](../results/episode-component-tracking-v2-draft2-full-matrix-canonical-arms.json), [launch plan](../results/episode-component-tracking-v2-draft2-full-matrix-launch-plan.json), and [launch binding v2](../results/episode-component-tracking-v2-draft2-full-matrix-launch-binding-v2.json).
- Every archived file matches the committed inventory, with no extra or missing files. Every full-matrix receipt hash matches the final audit, and every receipt file map matches the actual archived file set. All eight original failure files, logs, partial artifacts, worker audits and terminal receipts remain hash-bound.
- Exactly 160 unique canonical arms, 152 COMPLETE and 8 COMPUTATION_UNRESOLVED; no duplicate full-matrix executions. All 128 grid arms completed. Native has 24 complete and 8 unresolved.
- Two earlier COMPLETE smoke receipts are present and excluded from full-matrix statistics. Thus “no duplicates” refers to full-matrix executions, not to every experiment in the archive. Neither smoke arm is one of the eight unresolved arms.
- The 3,081 launch-plan source entries were checked, with the two documented binding qualifications below. Batch, worker, sidecar, result and query-engine limit fields agree with the frozen limits. No solver or resource-limit drift was found.

**Provenance qualification:** the original launch-plan runner hash is intentionally superseded by the committed launch-binding-v2 runner hash, which matches current frozen code. Separately, freeze commit `0df44ab` added only the raw-result exclusion to `.gitignore`; the launch plan retains its earlier hash. Historical `.gitignore` bytes at execution commit `e559d63` match that plan hash. Current `.gitignore` bytes are pinned independently by this review. Consequently the unmodified `verify_plan()` now rejects `.gitignore` and nine existing tests error. This is a real post-execution metadata mismatch, not a solver-limit escalation; it is preserved and disclosed, not repaired or silently waived. The new test first asserts the actual rejection, then substitutes only the historical `.gitignore` digest in memory to check the remaining launch bindings. No scientific function is invoked by that check.

Continuation checkpoint selections are **not pairwise disjoint**: each contains all arms still unaccounted at that batch start, including arms not reached by earlier halted batches. Actual executions are disjoint. Each selected list exactly equals the previously unaccounted canonical suffix, each executed list is its prefix, and no already-accounted or unresolved arm appears in a later selection. The first eight batches terminate at their unresolved arm; the last completes the 128 grid arms.

| Batch | Selected remaining arms | Executed | Complete | Unresolved |
|---|---:|---:|---:|---:|
| stage36-full-v1 | 160 | 19 | 18 | 1 |
| stage36-full-v1-cont01 | 141 | 1 | 0 | 1 |
| stage36-full-v1-cont02 | 140 | 3 | 2 | 1 |
| stage36-full-v1-cont03 | 137 | 1 | 0 | 1 |
| stage36-full-v1-cont04 | 136 | 3 | 2 | 1 |
| stage36-full-v1-cont05 | 133 | 1 | 0 | 1 |
| stage36-full-v1-cont06 | 132 | 3 | 2 | 1 |
| stage36-full-v1-cont07 | 129 | 1 | 0 | 1 |
| stage36-full-v1-cont08 | 128 | 128 | 128 | 0 |

## Frozen budgets and interpretation

Count budget per counting operation: 250,000 states, 5,000,000 transitions, 60 seconds and 33,554,432 polynomial bytes. Family-construction ceiling: 60 seconds. Query budget per integration: 5,000 calls and 120 seconds. Worker ceiling per arm: 400 seconds and 524,288 KiB RSS; one worker. The separate exact-cover search bound in frozen solver code is 200,000 visits, with an exception when visits exceed it. It is not the 250,000-state counting limit.

- **A — completed within frozen budget:** 152 terminal COMPLETE arms. All observed worker elapsed/RSS values and all persisted applicable count/query counters are within their ceilings. Frozen deadline checks and successful terminal states support completion under the enforced budgets. Missing inner timings prevent an independent numeric audit of every time ceiling.
- **B — exact-cover-bound unresolved:** 8 terminal COMPUTATION_UNRESOLVED arms, all with `Unresolved: Exact-cover search limit reached; result is unresolved`. They did not hit the worker timeout or observed RSS ceiling. Partial successful episodes do not make the arm complete.
- **C — not applicable / unavailable:** connected association has no exact path-family count or query budget usage (`null`, not zero). Aborted and unexecuted episodes lack downstream counters; query and family-construction durations are unavailable. These gaps must not be interpreted as spare capacity.

Elapsed time is the parent worker-audit monotonic interval for the whole arm, including startup, extraction, episode work, serialization and reload validation. It is not isolated solver CPU time. RSS is the worker audit maximum of polled VmRSS/VmHWM, augmented by the terminal worker high-water value for completed arms. There is no retained continuous trace. Distributions are descriptive observations from one run per full-matrix arm, not repeated performance benchmarks. P95 uses linear interpolation at `(n−1)×0.95`; unfinished arms are kept separate.

## Elapsed and RSS distributions

| Representation / outcome | Arms | Min s | Median s | P95 s | Max s | Peak RSS KiB |
|---|---:|---:|---:|---:|---:|---:|
| grid_sigma0 / COMPLETE | 32 | 31.451 | 34.469 | 35.930 | 36.033 | 167,068 |
| grid_sigma10 / COMPLETE | 32 | 28.699 | 29.299 | 29.997 | 30.099 | 143,052 |
| grid_sigma20 / COMPLETE | 32 | 28.243 | 28.794 | 29.550 | 29.554 | 143,288 |
| grid_sigma5 / COMPLETE | 32 | 30.008 | 30.557 | 31.178 | 31.257 | 144,264 |
| native / COMPLETE | 24 | 67.246 | 199.970 | 383.846 | 384.584 | 260,428 |
| native / COMPUTATION_UNRESOLVED | 8 | 29.155 | 31.859 | 34.612 | 34.613 | 162,028 |

Native completed arms take 67.246–384.584 seconds versus 28.243–36.033 seconds for completed grid arms. This is a computational comparison of different representations, not a claim of scientific equivalence or quality. Grid widths show modest elapsed changes; native path arms show the substantial width boundary described below. Batch timing and representation are confounded, and no variability estimate from repeated runs is available.

| Width, completed arms only (representations pooled) | n | Min s | Median s | P95 s | Max s |
|---|---:|---:|---:|---:|---:|
| 200 | 20 | 28.443 | 30.431 | 210.589 | 258.591 |
| 225 | 20 | 28.294 | 30.452 | 208.873 | 255.914 |
| 250 | 20 | 28.243 | 30.476 | 211.413 | 255.881 |
| 275 | 20 | 28.498 | 30.559 | 211.930 | 260.528 |
| 300 | 18 | 28.451 | 30.429 | 110.161 | 323.523 |
| 325 | 18 | 28.290 | 30.531 | 114.734 | 382.408 |
| 350 | 18 | 28.346 | 30.629 | 114.774 | 384.100 |
| unlimited | 18 | 28.447 | 30.677 | 114.886 | 384.584 |

| Association, completed arms only (representations pooled) | n | Min s | Median s | P95 s | Max s |
|---|---:|---:|---:|---:|---:|
| connected | 40 | 28.243 | 30.126 | 72.361 | 72.894 |
| paths_margin0 | 40 | 28.701 | 30.686 | 382.493 | 384.584 |
| paths_margin0.25 | 36 | 28.498 | 30.456 | 208.315 | 209.372 |
| paths_margin1 | 36 | 28.601 | 30.557 | 256.584 | 260.528 |

The JSON also provides distributions by outcome, representation × width, representation × association, and the full representation × width × association combination. Pooled summaries change composition at widths 300 and above because eight native arms are unresolved.

**Worker headroom:** the slowest complete arm is `native__wunlimited__paths_margin0`, at 384.584470 s (96.146% of 400 s), leaving 15.415530 s. Widths 325 and 350 on the same association take 382.407938 and 384.099677 s. This is limited observed timeout headroom, not a guarantee of future completion. The largest observed RSS is 260,428 KiB on `native__w225__connected`, 49.673% of the frozen ceiling, leaving 263,860 KiB. No complete arm exceeds either observed worker ceiling.

## Neighboring widths and localization

| Native width | Connected s | paths_margin0 s | paths_margin0.25 s / class | paths_margin1 s / class |
|---|---:|---:|---:|---:|
| 200 | 68.601 | 193.543 | 208.063 / A | 258.591 / A |
| 225 | 72.195 | 169.630 | 206.397 / A | 255.914 / A |
| 250 | 72.894 | 169.786 | 209.073 / A | 255.881 / A |
| 275 | 72.353 | 172.426 | 209.372 / A | 260.528 / A |
| 300 | 72.509 | 323.523 | 34.613 / B | 29.155 / B |
| 325 | 67.497 | 382.408 | 34.612 / B | 29.344 / B |
| 350 | 67.246 | 384.100 | 34.375 / B | 29.197 / B |
| unlimited | 67.292 | 384.584 | 34.515 / B | 29.304 / B |

The unresolved pattern is localized to native widths 300, 325, 350 and unlimited × margins 0.25 and 1: 8/160 overall (5%), 8/32 native (25%), 0/128 grid. Both positive-margin native pathways complete at 200–275. Native connected and margin0 complete at every width. The margin0 runtime rises from 172.426 s at width 275 to 323.523 s at 300 and approximately 382–385 s thereafter. Connected native remains around 67–73 s. The evidence identifies a localized computational boundary; it does not prove what scientific configuration should be selected.

Every unresolved arm retains all eight episode-001 artifacts and only `candidates.json` and `family.json` for episode-002. Frozen control flow puts that terminal boundary after family serialization and before count-outcome persistence. Neither final failed-search counters nor a traceback identifying the precise inner suboperation is available. The reported exact-cover exception and the code’s 200,000-visit guard establish the failure class; no measured terminal visit count is invented. The 29.155–34.613 s failed-arm durations reflect early termination and are not comparable completion times.

## Inner resources, exact cardinality and dispatch

There are 6,240 retained successful episode results: 152×41 from complete arms plus one from each of the eight unresolved arms. Of these, 1,640 are connected (40×41, exact path counting/query metrics not applicable); 4,600 have validated exact count/cardinality sidecars (4,592 in complete arms plus 8 partial successes). Each sidecar count matches its count-outcome and consumed result; count statistics and limits match as well. The range is 1 to 378038954451765697490, with that maximum at native width 200, margin1, episode-027. Large exact cardinalities are represented symbolically and do not imply enumeration of that many assignments.

| Recorded per-episode resource | Maximum | Frozen ceiling | Ceiling used |
|---|---:|---:|---:|
| Count peak states | 74,064 | 250,000 | 29.626% |
| Count transitions | 385,664 | 5,000,000 | 7.713% |
| Count elapsed s | 44.584254 | 60 | 74.307% |
| Polynomial bytes | 20,584,913 | 33,554,432 | 61.348% |
| Public query calls | 1,695 | 5,000 | 33.900% |

The peak states occur at native width 275, margin1, episode-027; peak transitions at the same arm, episode-039. Maximum count elapsed and query calls occur at native width 325, margin0, episode-036. The polynomial maximum occurs at native width 200, margin1, episode-027. Polynomial usage is the recursive maximum of recorded packed/polynomial byte fields, following the frozen checker, not total process memory. Summing byte/state maxima across episodes is not a simultaneous memory measure. Query-call totals cover recorded forward integrations only; reload repetitions are not separately counted in those totals.

Observed count methods across the 4,600 exact outcomes:

- 271 certified short-path matching counts (`KRAKEN_DRAFT2_CERTIFIED_SHORT_PATH_MATCHING_COUNT_V3`).
- 4,304 forced-singleton frontier counts with IEEE monotone pivot composition.
- 25 forced-singleton frontier counts with certified column-frontier exact generating functions.

All count outcomes record the same configured dispatch: certified short-path matching backend, forced-singleton frontier fallback, and weighted cutoff pivot composition backend. The actual method field distinguishes which path produced the outcome. The connected association bypasses this path-family counting route. The frozen runner dispatches on association and candidate structure, without capture/episode/arm identity or expected-count dispatch.

Exact queries use the forward candidate-cover disjunction engine. Public query calls range 3–1,695 (median 31, P95 365), totaling 371,086 across retained integrations. Internal `find_calls` range 1–3,658 and are not interchangeable with budgeted public calls. Recorded factor search-node counts peak at 43,276; these are successful query-engine snapshots, not terminal counters from the eight failures. The predicate-family artifact’s `NOT_EVALUATED` count state is expected: exact cardinality is stored in a separate sidecar and consumed without recount, not written back into the family artifact.

## Missing fields, limits of inference and verification

All expected worker audit fields, terminal receipts and complete-episode count/query sidecars were present. Expected connected null metrics are separated from missing metrics after a failure. The main audit gaps are absent query elapsed times, absent family-construction elapsed times, absent failed-search counters, and no counters for unexecuted later episodes. A successful bounded execution supports feasibility on this recorded run, but the evidence cannot independently quantify every inner time headroom or predict repeat-run performance. Partial native failures must not be pooled into complete native timing summaries.

The new review tests bind the full JSON payload, source/evidence hashes, canonical accounting, continuation selections, terminal receipts, all raw bytes and frozen limits; mutation cases reject altered limits, worker timing, query aggregates and retry counts. Raw reconstruction explicitly skips if the external archive is absent; it ran against the real archive for this review. No tests rerun any full-matrix arm.

- New review tests: 4 passed.
- Existing exact-solver/count tests: 39 passed.
- Existing full-matrix definition/feasibility/launch tests: 43 run, 34 passed, 9 errors, all due to the pre-existing frozen `.gitignore` mismatch described above. The review does not claim an entirely green historical test suite.
- `git diff --check`: passed.

Commands: `PYTHONPATH=analysis python -m unittest discover -s tests -p "test_episode_component_tracking_v2_stage37_computational_review.py"`; equivalent discovery with `test_episode_component_tracking_v2_draft2_exact*.py` and `test_episode_component_tracking_v2_draft2_full_matrix*.py`; `git diff --check`.

## Per-arm elapsed and observed RSS

Full precision, receipt identity, batch, headroom, per-arm inner resource summaries and grouped distributions are in the [machine-readable review](../results/episode-component-tracking-v2-stage37-computational-review.json). A and B have the meanings above; connected inner metrics are C even when the arm is A.

| Canonical arm | Class | Elapsed s | Observed peak RSS KiB |
|---|:---:|---:|---:|
| `native__w200__connected` | A | 68.601466 | 257,188 |
| `native__w200__paths_margin0` | A | 193.543456 | 222,628 |
| `native__w200__paths_margin0.25` | A | 208.063039 | 226,504 |
| `native__w200__paths_margin1` | A | 258.591309 | 230,908 |
| `native__w225__connected` | A | 72.195326 | 260,428 |
| `native__w225__paths_margin0` | A | 169.629643 | 218,432 |
| `native__w225__paths_margin0.25` | A | 206.396793 | 222,736 |
| `native__w225__paths_margin1` | A | 255.914323 | 231,404 |
| `native__w250__connected` | A | 72.894107 | 257,924 |
| `native__w250__paths_margin0` | A | 169.785993 | 219,836 |
| `native__w250__paths_margin0.25` | A | 209.072570 | 223,680 |
| `native__w250__paths_margin1` | A | 255.881435 | 232,412 |
| `native__w275__connected` | A | 72.353083 | 255,876 |
| `native__w275__paths_margin0` | A | 172.425843 | 220,408 |
| `native__w275__paths_margin0.25` | A | 209.371756 | 226,048 |
| `native__w275__paths_margin1` | A | 260.527673 | 233,852 |
| `native__w300__connected` | A | 72.508700 | 258,088 |
| `native__w300__paths_margin0` | A | 323.522540 | 222,180 |
| `native__w300__paths_margin0.25` | B | 34.612605 | 161,512 |
| `native__w300__paths_margin1` | B | 29.155047 | 154,536 |
| `native__w325__connected` | A | 67.497363 | 252,476 |
| `native__w325__paths_margin0` | A | 382.407938 | 226,388 |
| `native__w325__paths_margin0.25` | B | 34.612289 | 162,028 |
| `native__w325__paths_margin1` | B | 29.343652 | 154,500 |
| `native__w350__connected` | A | 67.246392 | 253,300 |
| `native__w350__paths_margin0` | A | 384.099677 | 226,624 |
| `native__w350__paths_margin0.25` | B | 34.375143 | 161,916 |
| `native__w350__paths_margin1` | B | 29.197444 | 154,744 |
| `native__wunlimited__connected` | A | 67.291794 | 252,352 |
| `native__wunlimited__paths_margin0` | A | 384.584470 | 226,632 |
| `native__wunlimited__paths_margin0.25` | B | 34.515235 | 162,024 |
| `native__wunlimited__paths_margin1` | B | 29.303569 | 154,844 |
| `grid_sigma0__w200__connected` | A | 31.451190 | 166,236 |
| `grid_sigma0__w200__paths_margin0` | A | 31.912272 | 157,952 |
| `grid_sigma0__w200__paths_margin0.25` | A | 33.172208 | 157,332 |
| `grid_sigma0__w200__paths_margin1` | A | 34.071751 | 157,512 |
| `grid_sigma0__w225__connected` | A | 33.511345 | 165,932 |
| `grid_sigma0__w225__paths_margin0` | A | 34.164725 | 156,604 |
| `grid_sigma0__w225__paths_margin0.25` | A | 34.017544 | 156,604 |
| `grid_sigma0__w225__paths_margin1` | A | 34.219837 | 157,624 |
| `grid_sigma0__w250__connected` | A | 33.858693 | 165,716 |
| `grid_sigma0__w250__paths_margin0` | A | 34.056835 | 157,696 |
| `grid_sigma0__w250__paths_margin0.25` | A | 34.222320 | 157,156 |
| `grid_sigma0__w250__paths_margin1` | A | 34.370115 | 157,396 |
| `grid_sigma0__w275__connected` | A | 33.957214 | 166,224 |
| `grid_sigma0__w275__paths_margin0` | A | 35.176015 | 157,808 |
| `grid_sigma0__w275__paths_margin0.25` | A | 34.567652 | 157,016 |
| `grid_sigma0__w275__paths_margin1` | A | 34.822394 | 157,304 |
| `grid_sigma0__w300__connected` | A | 33.565646 | 167,068 |
| `grid_sigma0__w300__paths_margin0` | A | 35.219508 | 157,812 |
| `grid_sigma0__w300__paths_margin0.25` | A | 35.011939 | 158,132 |
| `grid_sigma0__w300__paths_margin1` | A | 35.222635 | 158,528 |
| `grid_sigma0__w325__connected` | A | 33.620555 | 166,596 |
| `grid_sigma0__w325__paths_margin0` | A | 35.927983 | 157,620 |
| `grid_sigma0__w325__paths_margin0.25` | A | 35.932277 | 158,356 |
| `grid_sigma0__w325__paths_margin1` | A | 36.032761 | 158,244 |
| `grid_sigma0__w350__connected` | A | 34.932799 | 166,404 |
| `grid_sigma0__w350__paths_margin0` | A | 35.423704 | 158,292 |
| `grid_sigma0__w350__paths_margin0.25` | A | 35.354716 | 158,244 |
| `grid_sigma0__w350__paths_margin1` | A | 35.330165 | 158,380 |
| `grid_sigma0__wunlimited__connected` | A | 33.770350 | 166,144 |
| `grid_sigma0__wunlimited__paths_margin0` | A | 35.319824 | 157,708 |
| `grid_sigma0__wunlimited__paths_margin0.25` | A | 35.221994 | 157,916 |
| `grid_sigma0__wunlimited__paths_margin1` | A | 35.225835 | 158,076 |
| `grid_sigma5__w200__connected` | A | 30.052890 | 143,152 |
| `grid_sigma5__w200__paths_margin0` | A | 30.407429 | 142,168 |
| `grid_sigma5__w200__paths_margin0.25` | A | 30.455136 | 142,724 |
| `grid_sigma5__w200__paths_margin1` | A | 30.558310 | 142,596 |
| `grid_sigma5__w225__connected` | A | 30.302708 | 142,552 |
| `grid_sigma5__w225__paths_margin0` | A | 30.449442 | 142,544 |
| `grid_sigma5__w225__paths_margin0.25` | A | 30.453575 | 142,508 |
| `grid_sigma5__w225__paths_margin1` | A | 30.554749 | 142,848 |
| `grid_sigma5__w250__connected` | A | 30.053985 | 143,424 |
| `grid_sigma5__w250__paths_margin0` | A | 30.399649 | 142,632 |
| `grid_sigma5__w250__paths_margin0.25` | A | 30.603306 | 142,480 |
| `grid_sigma5__w250__paths_margin1` | A | 30.552624 | 142,296 |
| `grid_sigma5__w275__connected` | A | 30.102730 | 143,088 |
| `grid_sigma5__w275__paths_margin0` | A | 30.660656 | 142,324 |
| `grid_sigma5__w275__paths_margin0.25` | A | 30.457707 | 142,060 |
| `grid_sigma5__w275__paths_margin1` | A | 30.707725 | 142,600 |
| `grid_sigma5__w300__connected` | A | 30.150325 | 142,968 |
| `grid_sigma5__w300__paths_margin0` | A | 30.710707 | 142,480 |
| `grid_sigma5__w300__paths_margin0.25` | A | 30.708625 | 142,760 |
| `grid_sigma5__w300__paths_margin1` | A | 30.919702 | 142,020 |
| `grid_sigma5__w325__connected` | A | 30.007537 | 142,660 |
| `grid_sigma5__w325__paths_margin0` | A | 31.053684 | 142,276 |
| `grid_sigma5__w325__paths_margin0.25` | A | 31.153368 | 143,704 |
| `grid_sigma5__w325__paths_margin1` | A | 31.256999 | 142,872 |
| `grid_sigma5__w350__connected` | A | 30.149790 | 143,240 |
| `grid_sigma5__w350__paths_margin0` | A | 31.107504 | 142,412 |
| `grid_sigma5__w350__paths_margin0.25` | A | 31.156477 | 142,412 |
| `grid_sigma5__w350__paths_margin1` | A | 31.203340 | 142,836 |
| `grid_sigma5__wunlimited__connected` | A | 30.295552 | 144,264 |
| `grid_sigma5__wunlimited__paths_margin0` | A | 31.140616 | 143,476 |
| `grid_sigma5__wunlimited__paths_margin0.25` | A | 31.157765 | 142,652 |
| `grid_sigma5__wunlimited__paths_margin1` | A | 31.058453 | 143,536 |
| `grid_sigma10__w200__connected` | A | 28.901563 | 142,032 |
| `grid_sigma10__w200__paths_margin0` | A | 29.305614 | 142,008 |
| `grid_sigma10__w200__paths_margin0.25` | A | 29.398434 | 141,668 |
| `grid_sigma10__w200__paths_margin1` | A | 29.250914 | 142,536 |
| `grid_sigma10__w225__connected` | A | 28.851479 | 142,588 |
| `grid_sigma10__w225__paths_margin0` | A | 29.295044 | 142,692 |
| `grid_sigma10__w225__paths_margin0.25` | A | 29.249446 | 141,848 |
| `grid_sigma10__w225__paths_margin1` | A | 29.250457 | 141,944 |
| `grid_sigma10__w250__connected` | A | 28.698962 | 142,492 |
| `grid_sigma10__w250__paths_margin0` | A | 29.192347 | 142,604 |
| `grid_sigma10__w250__paths_margin0.25` | A | 29.206617 | 142,664 |
| `grid_sigma10__w250__paths_margin1` | A | 29.399574 | 142,508 |
| `grid_sigma10__w275__connected` | A | 28.854262 | 141,716 |
| `grid_sigma10__w275__paths_margin0` | A | 29.303665 | 142,564 |
| `grid_sigma10__w275__paths_margin0.25` | A | 29.255765 | 143,032 |
| `grid_sigma10__w275__paths_margin1` | A | 29.199239 | 142,252 |
| `grid_sigma10__w300__connected` | A | 28.799230 | 142,364 |
| `grid_sigma10__w300__paths_margin0` | A | 29.696513 | 142,452 |
| `grid_sigma10__w300__paths_margin0.25` | A | 29.501831 | 142,352 |
| `grid_sigma10__w300__paths_margin1` | A | 29.551910 | 142,484 |
| `grid_sigma10__w325__connected` | A | 28.946612 | 142,224 |
| `grid_sigma10__w325__paths_margin0` | A | 29.949154 | 141,808 |
| `grid_sigma10__w325__paths_margin0.25` | A | 29.846036 | 142,660 |
| `grid_sigma10__w325__paths_margin1` | A | 29.950456 | 142,336 |
| `grid_sigma10__w350__connected` | A | 28.895856 | 143,052 |
| `grid_sigma10__w350__paths_margin0` | A | 29.900018 | 141,860 |
| `grid_sigma10__w350__paths_margin0.25` | A | 29.855731 | 142,596 |
| `grid_sigma10__w350__paths_margin1` | A | 30.099496 | 142,160 |
| `grid_sigma10__wunlimited__connected` | A | 28.900477 | 142,196 |
| `grid_sigma10__wunlimited__paths_margin0` | A | 29.847458 | 142,156 |
| `grid_sigma10__wunlimited__paths_margin0.25` | A | 30.054816 | 142,584 |
| `grid_sigma10__wunlimited__paths_margin1` | A | 29.803584 | 142,952 |
| `grid_sigma20__w200__connected` | A | 28.442793 | 141,688 |
| `grid_sigma20__w200__paths_margin0` | A | 28.789224 | 141,708 |
| `grid_sigma20__w200__paths_margin0.25` | A | 28.497540 | 141,552 |
| `grid_sigma20__w200__paths_margin1` | A | 28.700144 | 141,596 |
| `grid_sigma20__w225__connected` | A | 28.293965 | 141,600 |
| `grid_sigma20__w225__paths_margin0` | A | 28.900031 | 141,604 |
| `grid_sigma20__w225__paths_margin0.25` | A | 28.798302 | 141,708 |
| `grid_sigma20__w225__paths_margin1` | A | 28.600586 | 142,156 |
| `grid_sigma20__w250__connected` | A | 28.242733 | 141,892 |
| `grid_sigma20__w250__paths_margin0` | A | 28.897888 | 141,660 |
| `grid_sigma20__w250__paths_margin0.25` | A | 28.801032 | 142,096 |
| `grid_sigma20__w250__paths_margin1` | A | 28.698255 | 141,504 |
| `grid_sigma20__w275__connected` | A | 28.497768 | 142,396 |
| `grid_sigma20__w275__paths_margin0` | A | 28.700908 | 141,800 |
| `grid_sigma20__w275__paths_margin0.25` | A | 28.749537 | 141,464 |
| `grid_sigma20__w275__paths_margin1` | A | 28.699005 | 141,660 |
| `grid_sigma20__w300__connected` | A | 28.450606 | 141,460 |
| `grid_sigma20__w300__paths_margin0` | A | 29.041518 | 142,460 |
| `grid_sigma20__w300__paths_margin0.25` | A | 28.949037 | 142,108 |
| `grid_sigma20__w300__paths_margin1` | A | 28.903117 | 142,044 |
| `grid_sigma20__w325__connected` | A | 28.289666 | 141,596 |
| `grid_sigma20__w325__paths_margin0` | A | 29.440082 | 142,568 |
| `grid_sigma20__w325__paths_margin0.25` | A | 29.350199 | 142,184 |
| `grid_sigma20__w325__paths_margin1` | A | 29.549492 | 142,652 |
| `grid_sigma20__w350__connected` | A | 28.346387 | 142,120 |
| `grid_sigma20__w350__paths_margin0` | A | 29.554463 | 142,036 |
| `grid_sigma20__w350__paths_margin0.25` | A | 29.499624 | 142,272 |
| `grid_sigma20__w350__paths_margin1` | A | 29.499522 | 141,932 |
| `grid_sigma20__wunlimited__connected` | A | 28.447013 | 142,608 |
| `grid_sigma20__wunlimited__paths_margin0` | A | 29.449529 | 142,160 |
| `grid_sigma20__wunlimited__paths_margin0.25` | A | 29.456155 | 141,964 |
| `grid_sigma20__wunlimited__paths_margin1` | A | 29.550249 | 143,288 |
