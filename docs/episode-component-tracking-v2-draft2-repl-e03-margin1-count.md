# REPL E03 margin-1 exact cardinality investigation

Decision: **REPL_E03_MARGIN1_EXACT_SOLVED**. Exact cardinality: **378,536,340**.

Checkpoint remains `a57a5df4521485966c4b434d10d595a4acc505ea`. Target is BETWEEN-DEVICE-REPL-V1-20260919-024341, E03, margin 1. All work is in new files. No capture, detection, input regeneration, query modification, full regression, commit or push occurred. No identification or discrimination inference is made.

## Reproduction and structural diagnosis

Five original fragments contain eligible candidate counts **193, 3, 18, 2, 97** (313 total). There are 231 fixed singletons and six nontrivial connected factors, hence 237 connected groups. The immutable family SHA-256 is `5db427d4b254151b363318cbeae3c902ca573dbcd14b2347f38ca7a27de66c1f`; model SHA-256 is `e51cc3a19e5e951984c003be3ed96f413cc41a60d12cf2dcdccf644b0ca928cc`.

| Factor | Candidates by fragment | Candidates | Edges | Paths by length | Optimum links | Frozen optimum cost hex |
|---|---|---:|---:|---|---:|---|
| 0 | {'3': 1, '5': 1} | 2 | 1 | {'1': 2, '2': 1} | 1 | `0x1.0d69049bb7ec2p-2` |
| 1 | {'1': 44, '3': 8, '5': 9} | 61 | 144 | {'1': 61, '2': 144, '3': 466} | 15 | `0x1.895cda2431f8ep+2` |
| 2 | {'1': 3, '2': 1} | 4 | 3 | {'1': 4, '2': 3} | 1 | `0x1.a48b71cba6a3ap-6` |
| 3 | {'1': 9, '2': 1, '4': 1} | 11 | 10 | {'1': 11, '2': 10, '3': 9} | 2 | `0x1.01ad5ccb861d6p+0` |
| 4 | {'1': 1, '3': 1} | 2 | 1 | {'1': 2, '2': 1} | 1 | `0x1.40e7ce9fc1df6p-2` |
| 5 | {'1': 1, '3': 1} | 2 | 1 | {'1': 2, '2': 1} | 1 | `0x1.26f5270bc7ef6p+0` |

The committed pivot counter selects local IEEE histograms: the existing column certificate does not cover three-candidate paths. Stored factor order is unchanged. Factor 0 completes in 0.0000663 s with one histogram entry, multiplicity one, two transitions and two peak states. Factor 1 fails during local histogram construction at position 22, before any episode composition or pivot streaming. Later factors are not reached; no completed factor-1 histogram or multiplicity is asserted.

At 27.186247 s and transition 1,260,885, the next insertion attempts state 250,001. This comprises 129,124 entries in the current bucket (consumed entries remain allocated until the bucket ends), 120,876 future entries, and the held factor-0 histogram. The selected path is E003_F001_C0076 / E003_F003_C0009 / E003_F005_C0046. Prior mask is `0x1b060fffffc00000`, new mask `0x1a040fffff800000`, remaining links 2, remaining binary64 budget `0x1.05aa4b14bd00ap+0`, and emitted cost `0x1.87f2475f02b8cp+2`. The inserted state **would survive** the next exact prefix predicate. A post-failure diagnostic checks that predicate without continuing the count. Peak process RSS was 124,936 KiB; packed polynomial bytes were zero. Exact failure-time and post-diagnostic elapsed time are separately recorded.

Thus this is local residual-mask / remaining-budget / emitted-cost materialization, not episode-level IEEE composition, a doomed next-prefix state, or packed-polynomial exhaustion. The diagnostic preserves bucket sizes and insertion identity in `diagnostic-pivot.json`.

Two exact preliminary variants are preserved. V1 immediately releases consumed frontier entries (destinations are strictly later buckets). V2 additionally contracts forced zero-cost singleton chains. Both pass their controls but still attempt state 250,001: V1 forward/reverse at 11.789/11.645 s and 1,504,691/1,564,214 transitions; V2 at 12.300/12.321 s and 1,593,408/1,621,106 transitions. Their cardinalities remain unresolved/null. Neither resource increase nor dropping a surviving state is used.

For comparison, TPMS-004 E02 needed monotone binary64 pivot composition to avoid the episode product; REPL E02 needed exact dyadic matching arithmetic to remove expensive inverse/matching work. E03 needs a certified decomposition of the local three-candidate path-cover problem before any IEEE histogram is materialized. The V3 fallback retains those earlier exact backends and the V2 local implementation.

## General exact transformation and equivalence

V3 dispatch depends only on graph structure and an arithmetic certificate, never capture labels, candidate identities or expected counts.

1. Certify that the longest directed path has at most three candidates. The original graph is acyclic, each edge respects fragment and 50-Hz rules, and two edges imply range at most 100 Hz. Thus any edge set with at most one incoming and one outgoing edge per candidate defines exactly one feasible unordered path partition, with all unused candidates as singletons. Conversely every feasible partition defines one such edge set.
2. Split each candidate into incoming/outgoing computational roles. Connected components in this bipartite incidence graph are independent matching factors. A middle candidate may have both an incoming and an outgoing edge; these form a single three-candidate path. This does not duplicate or merge original assignments.
3. Require a uniform fragment-gap penalty per matching component. At maximum cardinality its total penalty is fixed. For a deficient matching with smaller side m and maximum cardinality k, add d=m-k labelled dummy columns. Every original maximum matching has exactly d! completions. Divide each integer coefficient by d! and require divisibility. These are computation vertices only; the family is unchanged.
4. Propose a rational quantum q from the existing lattice function, but measure the exact rational error of every original binary64 edge coefficient against its proposed integer weight plus exact quarter penalty. Verify that each frozen optimum witness lies in the integer optimum shell and that component maximum links reproduce the original factor maximum.
5. With n nontrivial candidates and m original factors, use U=16(n+m+1) and the envelope `4*n*epsilon + 64*(n+m+1)*ulp(U)`. Costs, residual budgets and comparison intermediates have magnitude below U. Selected edges number at most n; path additions, optimum folds, prefix subtractions and comparisons use O(n+m) operations. The conservative envelope includes coefficient error on both sides, path-cost additions, right-folded optima, left-folded emitted costs and prefix arithmetic. Each operation's rounding error is bounded by one ulp(U). Require q > 2*envelope and both neighboring margin-shell distances greater than envelope plus the frozen tolerance.
6. For a full maximum matching, any chosen prefix leaves a maximum residual matching in each component: otherwise improving that residual would improve the whole matching. Uniform gap penalties therefore cancel in residual comparisons too. Integer prefix excess cannot exceed total excess. All hypotheses with integer excess at most floor(margin/q) pass every frozen local and episode prefix predicate; those above it fail the terminal/global predicate. Shell separation certifies these statements against the actual binary64 comparisons.
7. Count integer excess coefficients with the existing exact column-frontier matching backend and arbitrary-precision generating-function products. Distinct assignments retain their multiplicity. Scientific floating-point additions are neither reordered nor reassociated: the certificate proves equality of acceptance sets before replacing their evaluation with integer counting. Forward/reverse orders change only this equivalent integer computation. A failed certificate falls back to the exact IEEE/pivot/dyadic implementation. Margin zero explicitly uses the existing fallback.

For this target, q=15625/119311929, maximum links=21, fixed penalty=19/4, and cutoff=7635. Maximum coefficient error is 12303573917/268666579492627537723392. The rounding envelope is 43998894375973/33583322436578442215424 (about 1.31e-9). Lower and upper shell distances are 5018/39770643 (about 1.262e-4) and 571/119311929 (about 4.786e-6), safely separated. The full certificate is saved with both count outcomes and the sidecar.

## Certified factors and product growth

The local histogram sizes/multiplicities below are truncated at the global excess cutoff, not claims about all unretained matchings. Block 2 has one computational dummy column (factorial divisor one). Other blocks need none.

| Block | Original factor | Left/right | Edges | Max links | Integer optimum | Histogram entries | Assignment multiplicity | Transitions (forward) | Product entries |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 1/1 | 1 | 1 | 100 | 1 | 1 | 2 | 1 |
| 1 | 1 | 44/8 | 119 | 8 | 154 | 7385 | 5972241 | 1341 | 7385 |
| 2 | 1 | 8/9 | 25 | 7 | 18144 | 66 | 71 | 144 | 7417 |
| 3 | 2 | 3/1 | 3 | 1 | 196 | 3 | 3 | 10 | 7417 |
| 4 | 3 | 9/1 | 9 | 1 | 1 | 9 | 9 | 34 | 7440 |
| 5 | 3 | 1/1 | 1 | 1 | 5776 | 1 | 1 | 2 | 7440 |
| 6 | 4 | 1/1 | 1 | 1 | 484 | 1 | 1 | 2 | 7440 |
| 7 | 5 | 1/1 | 1 | 1 | 6889 | 1 | 1 | 2 | 7440 |

Forward order is 0..7; reverse is 7..0. Reverse product sizes are 1, 1, 1, 9, 23, 714, 7440, 7440. Both end at 7,440 excess coefficients and cardinality 378,536,340. The largest internal column frontier has 32 masks. Per-block transitions and backend checkpoints are saved; individual V3 block runtimes were not separately instrumented (whole certified construction/count runtime is below).

| Order | Count seconds | Transitions | Peak live states | Packed bytes | Process peak RSS KiB |
|---|---:|---:|---:|---:|---:|
| Forward | 0.032820407 | 1,537 | 15,128 | 919,972 | 43,916 |
| Reverse | 0.031625930 | 1,598 | 15,799 | 831,688 | 43,628 |

Family load is separate (about two seconds); certified construction is included in count timing. State accounting includes immutable computation vertices/weights, held histograms and backend frontier states. Packed storage follows the existing column/convolution accounting. All unchanged limits hold: 60 s, 250,000 live states, 5,000,000 transitions and 33,554,432 packed bytes. Artificial exhaustion remains explicit and null-valued. Failed variants stopped at their first exceeding state and did not publish a partial count.

## Validation and controls

Final suite: **118 passed, zero failures, zero errors**. It includes the exact solver/count, column, pivot, dyadic, sidecar, staged, limited/six-capture, margin-1 investigation, committed E03 query and three new counter suites. New tests compare exhaustive small graphs in both orders, full local IEEE histograms, forced singletons, disconnected/equal-cost cases, certified three-layer random graphs, deficient matchings with a nontrivial 2! divisor, structural certificate rejection, margin-zero fallback and resource exhaustion. Existing weighted tests cover duplicate costs, large multiplicities, threshold neighbors, ties and nonassociative binary64 folds; provenance/tamper tests pass.

A development test caught a double subtraction of the integer optimum: the existing matching backend already emits excess costs. This was corrected before any target counting run. Final saved test logs have no failures.

Before target evaluation, all 120 previously exact bounded-regression compact cases plus the corrected REPL E02 margin-1 family passed in both orders: **121 families, 242 exact counting-only evaluations**. Mandatory values reproduced:

| Control | Margin 0 | Margin 0.25 | Margin 1 |
|---|---:|---:|---:|
| TPMS-004 E02 | 1 | 32,743 | 5,788,836 |
| TPMS-008 E08 | 2 | 17,067,800,502,243 | 378,038,954,451,765,697,490 |
| REPL E02 | Included in saved controls | Included in saved controls | 217,075 |
| REPL E03 | 1 | 349,149 | 378,536,340 (new) |

These are counting controls, not a rerun of the 164-case association regression. No broader readiness decision follows from this target result.

## Target-only staged parity and reproduction

A new KRAKEN_DRAFT2_RETAINED_CARDINALITY_V1 sidecar binds the unchanged family/model, exact margin, counting definition, arithmetic policy, counter/source hashes, limits and statistics. The unchanged committed E03 query implementation then performs target-only integration. Family bytes/completeness, candidate identities, denominator 5, exact query outputs/operations, **1,012 public calls**, association, primary, membership, persistent paths, metrics and computational limits match the committed E03 query milestone.

Status remains **MULTIPLE_PERSISTENT_TRACKS**, primary **null**. Invariant membership count is 234; alternative count 432; possible total 666; persistent paths 356. The only scientific change is cardinality from unresolved/null to EXACT/378536340. Sidecar/counter provenance metadata changes as expected. Integration took 24.860277 s; deterministic reload took 24.625371 s and reproduced canonical serialized bytes. Integration process peak RSS was 173,584 KiB. Existing family/sidecar validation and tamper rejection remain passing.

## New files and integrity

The investigation creates the diagnostic script, three versioned counter implementations, three matching benchmark drivers, three test modules, this document, an independent integrity report, and the new result directory. V1 results occupy its root, V2 results `v2/`, and successful results `v3/`. Failed attempts remain explicitly unresolved. The successful sidecar is `v3/target-margin-1.cardinality.json`; integration is `v3/target-staged-result.json`. Each benchmark records source hashes and has an artifact `files.sha256` manifest. `v3/tests.txt` and `v3/control-counts.json` record validation.

A snapshot of all 1,754 pre-existing tracked files was taken before work. The independent integrity report verifies their byte identity, all investigation source/artifact hashes, sidecar binding, staged parity, unchanged HEAD, ordinary `git diff --check`, and independent whitespace checks on new files. Historical six-capture NOT_READY artifacts and both REPL milestones are untouched. Git status contains only new untracked investigation files.

Reproduction entry point: `python3 analysis/benchmark_episode_component_tracking_v2_draft2_repl_e03_margin1_count_v3.py`. It requires a fresh output directory and refuses to overwrite existing results; use a separate checkout/output revision for another recorded run. Existing result artifacts suffice for independent hash and sidecar validation.
