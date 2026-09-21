# REPL E05 margin-1 exact cardinality investigation

Scope: `BETWEEN-DEVICE-REPL-V1-20260919-024341`, E05, margin 1, committed family from `C6-E05/margin-1`. Base commit: `a57a5df4521485966c4b434d10d595a4acc505ea`. All implementation and evidence are new files. The original family, queries, components, parameters, and historical results remain unchanged.

## Reproduced failure

The committed monotone-pivot backend fails at transition **5,000,001**, phase `IEEE streaming pivot join`, pivot **5** (zero based), with **12,745 live states** and **0 packed-polynomial bytes**. The instrumented initial reproduction took 4.595 seconds at failure, with process peak RSS 82,380 KiB. These timings include diagnostic instrumentation. The committed failure has the identical transition, phase, pivot, and state count.

There are five fragments with eligible counts **173, 4, 15, 1, 86**, totaling **279** candidates. There are **228 fixed singletons** and **six nontrivial connected factors**. Episode optimum: **18 links**, cost **6.118532472976763**. The certified column backend is unavailable because feasible paths have more than two candidates.

| Factor | Candidates by fragment | Edges | Feasible paths by length | Optimum links | Optimum cost | Histogram entries | Assignment multiplicity | Local transitions |
|---|---|---:|---|---:|---:|---:|---:|---:|
| 0 | 1:2, 3:3 | 6 | 1:5, 2:6 | 2 | 0.7625732838499286 | 6 | 6 | 19 |
| 1 | 1:1, 3:1, 5:2 | 3 | 1:4, 2:3, 3:2 | 2 | 0.7033797056453611 | 2 | 2 | 6 |
| 2 | 1:1, 3:1, 5:1 | 2 | 1:3, 2:2, 3:1 | 2 | 0.7771097599134489 | 1 | 1 | 3 |
| 3 | 1:2, 2:2 | 3 | 1:4, 2:3 | 2 | 1.5475453841669085 | 1 | 1 | 4 |
| 4 | 1:11, 3:4 | 33 | 1:15, 2:33 | 4 | 1.3249098839060731 | 535 | 543 | 2,807 |
| 5 | 1:14, 2:2, 3:3, 4:1 | 46 | 1:20, 2:46, 3:53, 4:11 | 6 | 1.0030144554950424 | 3,670 | 4,019 | 21,491 |

Local DAG generation costs 24,330 transitions. Prefix construction costs 6,462; its widths are 1 → 6 → 12 → 12 → 12 → 2,428. The final pivot has 3,670 distinct costs, making 8,910,760 potential join pairs. There is one terminal acceptance threshold and no suffix-transform stage: binary64 preimage searches, repeated preimages, suffix composition, and certified polynomial work each contribute zero transitions on this target. Local histograms are generated once, and immutable buffers are sorted once per stage. Neither repeated local work nor matching bounds causes the transition exhaustion.

Transition 5,000,001 is join pair 4,969,209: prefix index 1,354, pivot-cost index 28 (zero based). It evaluates `5.944359071589555 + 1.064434340844491 = 7.008793412434046`, below boundary `7.118532472977763`. It therefore cannot be omitted as a rejected pair. Monotonicity does permit counting the entire accepted pivot prefix at once, including this pair, without testing every member. The JSON diagnostics include per-factor runtimes, matching request counts/times, cache misses, peak states, and exact float encodings.

## Exact optimization and proof

Keep local histograms, structural largest-histogram pivot selection, chronological prefix fold, suffix thresholds, and every scientific predicate unchanged. Reuse the existing exact dyadic matching adapter without changing ties or path costs.

For each prefix cost `c` and suffix cap `t`, binary-search the sorted pivot histogram for the first cost `g` that fails **the actual binary64 expression** `c + g <= t`. Nonnegative binary64 addition is monotone, including rounding ties and overflow. Consequently all accepted costs form an initial interval. A cumulative integer multiplicity table yields its total weight exactly.

The old join sums `prefix_weight * pivot_weight * suffix_weight` over every accepted triple. The new join sums the same integers by accepted pivot intervals. Only integer summation is rearranged. No floating addition is reassociated, no threshold is approximated, and no distinct candidate assignment is discarded. Local DAG partition semantics and singleton handling remain the committed implementation. Equal costs merge integer multiplicities, never hypothesis identity. Path ordering does not multiply the result.

Select cutoff work only when histogram/cap sizes predict fewer predicate probes than the existing pair scan; otherwise retain the existing scan. This decision is structural and consults neither capture identity nor an expected answer. No new preimage or monotone-sweep implementation is introduced; the existing scalar preimage implementation is reused unchanged.

## Transition and storage policy

The inherited Budget counts local DAG branch attempts, scalar preimage probes, and composition operations, rather than every Python instruction or every matching arithmetic operation. Existing histogram generation, sorting, matching, and fallback composition retain their accounting.

The replacement explicitly charges one transition for each cumulative pivot-weight entry, each reversed buffer entry in reverse traversal, each prefix guard, each actual cutoff predicate probe, and each weighted cutoff accumulation. Thus replacing thousands of pair tests with a binary search charges all probes actually performed, plus construction and accumulation work. Integer multiplication/addition within a weighted accumulation follows the existing one-transition composition convention. The new cumulative weight array, including its initial zero, is included in live states; dyadic edge storage is also charged by the inherited adapter. There are no packed polynomials on E05.

Forward and reverse construction visit factors and prefix maps in opposite orders; both retain the same scientific chronological fold. Cutoff buffers must be ascending in both modes, so reverse mode explicitly reverses its inherited descending buffer and charges that work.

## Validation and artifacts

The benchmark runs the exact solver, exact count, column count, staged integration, cardinality sidecar, E02 monotone-pivot, REPL E02 dyadic, REPL E03 query, six-capture regression unit suites, and new cutoff tests. It does not launch the 164-case regression or the 160-arm matrix.

New tests inherit explicit small-graph hypothesis-enumeration parity, singleton-only and disconnected factors, equal-cost assignments, binary64 nonassociativity, boundary neighbors, and fail-closed budget exhaustion. A deterministic 250-seed weighted grid compares both traversal orders with explicit histogram products and the old scalar-preimage composer. It includes huge integer multiplicities and repeated thresholds/addends. A separate fixture asserts the exact number of charged cutoff operations.

`results/episode-component-tracking-v2-draft2-repl-e05-margin1-count-investigation/` contains baseline diagnostics, unit test logs, control counts, target counts, the new cardinality sidecar, and target-only staged result. The initial E08 control launcher ran separately before target evaluation because these limited-regression requests reference external committed family paths; the final benchmark source includes those requests directly. `mandatory-e08-controls.json` records those six successful evaluations.

## Final outcome

**REPL_E05_MARGIN1_EXACT_SOLVED** — exact retained-family cardinality **697,122**.

| Traversal | Exact count | Count seconds | Transitions | Peak live states | Packed-polynomial bytes | Process peak RSS KiB |
|---|---:|---:|---:|---:|---:|---:|
| Forward | 697,122 | 0.224539 | 68,128 | 16,509 | 0 | 43,260 |
| Reverse | 697,122 | 0.223489 | 71,798 | 16,509 | 0 | 43,084 |

All four frozen limits pass: 250,000 states, 5,000,000 transitions, 60 seconds, and 33,554,432 packed-polynomial bytes. The join uses **28,810 actual binary-search probes**, **2,428 weighted cutoffs**, and zero individually scanned pivot pairs. Forward accounting is 24,330 local + 6,462 prefix + 3,670 cumulative entries + 2,428 guards + 28,810 probes + 2,428 accumulations = **68,128**. Reverse adds 3,670 charged buffer entries. The 16,416 composition containers plus 93 retained dyadic edge entries produce the reported 16,509-state peak.

**113 tests passed, zero failures/errors.** All **120 committed exact six-capture compact families** matched in both orders. The original benchmark batch additionally checked the saved anomaly control and REPL E02 margin 1: 122 family evaluations in both orders, totaling 244. Six separately recorded mandatory E08 evaluations also passed before E05, for **250 successful control evaluations** overall. This is counting-only control validation, not a rerun of the staged regression.

| Mandatory control | Margin 0 | Margin 0.25 | Margin 1 |
|---|---:|---:|---:|
| TPMS-004 E02 | 1 | 32,743 | 5,788,836 |
| REPL E02 | — | — | 217,075 |
| E08 | 2 | 17,067,800,502,243 | 378,038,954,451,765,697,490 |
| REPL E03 | 1 (committed) | 349,149 | — |

Every listed mandatory value matched in forward and reverse construction before evaluating E05. No expected E05 cardinality was used.

Target-only unchanged staged integration completed in 0.698 seconds; deterministic reload took 1.052 seconds and produced canonically identical bytes. All non-cardinality scientific fields are equal, including family completeness, association/status/primary, paths and membership, persistent tracks, metrics, denominator, computational parameters, query outputs and **475 query calls**. Only cardinality and its counting-stage status changed scientifically, from unresolved/null to exact/697122. Provenance changed for the new sidecar/source binding and current checkpoint context.

Family SHA-256 remains `25482c430012768675f80ee32e243353ac339f51f4a6f72e64e4e9fcbb114bfb`. New sidecar SHA-256: `057e42a767d466b50de131ffabca6e7fca0433393747cc3fa3d40d657a5aee93`. New staged-result SHA-256: `06b29fc262a4f4dd0dd9a086d5482f044a4e1fb5cec448713550efad9af147e6`.

Final integrity evidence is `results/episode-component-tracking-v2-draft2-repl-e05-margin1-count-integrity.json`: all 1,754 initially tracked files must match the initial SHA-256 snapshot, including the six-capture regression, REPL E02 count milestone, and REPL E03 query milestone. It verifies source/result hashes, sidecar/model/family binding, only allowed untracked investigation paths, unchanged HEAD, `git diff --check`, and an independent untracked-file whitespace scan. No RF capture, detection, query modification, parameter change, merge, commit, or push occurred. No identification or discrimination claim is made.
