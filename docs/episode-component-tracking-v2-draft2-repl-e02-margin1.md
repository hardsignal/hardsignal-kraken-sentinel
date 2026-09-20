# REPL E02 margin-1 exact cardinality

**REPL_E02_MARGIN1_EXACT_SOLVED. Exact cardinality: 217,075 (`217075`).**
Both forward and reverse construction/traversal orders completed under the
unchanged frozen limits. HEAD remained `b1a0e3d`. Only this target was passed
through staged integration after counting validation; no full regression was run.

## Reproduction and structural diagnosis

Target: `BETWEEN-DEVICE-REPL-V1-20260919-024341`, E02, margin 1.
The committed family has six original fragments, eligible counts
`[0, 69, 0, 20, 2, 89]` (180 candidates), 135 connected groups, and 132 fixed
singletons. There are three nontrivial factors, with no shared candidate frontier.
The factors retain the stored order (original frequency ordering/tie breaks).

| Factor | Candidates | Candidates by fragment | Edges | Feasible paths: lengths 1 / 2 / 3 | Optimum links | Optimum binary64 cost |
|---|---:|---|---:|---|---:|---|
| 0 | 7 | F2:3, F4:1, F6:3 | 6 | 7 / 6 / 9 | 2 | `0x1.c5ef587f86498p-1` |
| 1 | 35 | F2:15, F4:10, F6:10 | 101 | 35 / 101 / 256 | 20 | `0x1.49ce9726fc2b0p+3` |
| 2 | 6 | F2:5, F4:1 | 5 | 6 / 5 / 0 | 1 | `0x1.0225486ad5c02p-2` |

The episode optimum has 23 links. The global acceptance boundary, including the
unchanged margin/tolerance expression, is `0x1.8e3eb6f24b60dp+3`.
The certified column backend is unavailable: its certificate rejects a path
having more than two candidates. The committed dispatcher therefore selects local
IEEE histograms followed by the monotone binary64 pivot composition.

The first diagnostic ran the unchanged counter with lightweight factor and
matching timers and the unchanged 60-second deadline. Factor 0 finished in
0.001457 s with nine histogram costs and nine assignments, 42 transitions and
16 reported live states. Factor 1 was interrupted after 59.998446 s; its histogram
and multiplicity remained unresolved. Factor 2 and composition had not started.
No partial histogram was published as a complete result.

**Matching calls consumed 59.609502 s of the 60-second run (about 99.3%).**
Factor 1 alone made 28,406 matching calls, including cache hits, consuming
59.608703 s. The recorded exception traceback pinpoints:
`ieee_histogram -> optimum -> _matching -> Fraction addition`.
The last budget location was the IEEE prefix DAG, position 3. Total observed
transitions were 813 and peak live states 260; process peak RSS was 50,536 KiB.
This reproduces the time failure, although progress at the deadline differs from
the earlier bounded run's 145-state observation.

This was local suffix-optimum computation, not binary64 inverse/preimage work or
pivot streaming. Neither composition nor the certified column backend ran before
the deadline. Repeated sorting, suffix calculations and composition dictionary
work cannot explain the observed 99.3% matching time. The matching timer includes
its residual-graph operations and rational arithmetic; the deadline stack locates
an actual Fraction allocation/addition. Full source-bound diagnostics and traceback
are in `diagnostic.json`. The inherited deadline message says “Staged exact-query
wall-clock limit exceeded”; here it was explicitly applied to **counting for 60 s**.

## Exact optimization and proof

New adapter version: `KRAKEN_DRAFT2_DYADIC_MATCHING_BOUND_COUNT_V1`.
It changes only the implementation of the solver's rational matching bound while
counting. The local IEEE histogram, optimum/cover logic, counter dispatcher,
preimages, composition pivot and frozen binary64 predicates remain unchanged.

Every finite binary64 edge cost is exactly a dyadic rational `p_e / q_e`, with
`q_e` a power of two. For one factor choose `Q = max(q_e)` and store the exact
integer `W_e = p_e * (Q // q_e)`. Scale every residual-network cost by Q, including
negative reverse edges and the mandatory-node reward `(2*n+1)*Q`. Source and sink
costs remain zero. No rounding or approximation is involved.

Inductively, every reachable distance in the integer residual algorithm equals
Q times the original rational distance. Since Q is positive, all strict
comparisons and equality ties agree. Graph construction, vertex/edge iteration,
relaxation order, predecessor updates, augmentation and capacity updates are
identical. Therefore each selected edge set and ordered cover is identical.
The returned lower bound is converted back using
`Fraction(sum(W_e for selected edges), Q)`, exactly the original rational cost.
Infeasible/mandatory-cover outcomes are unchanged too.

Consequently the existing optimum solver receives the same bounds and witnesses;
it performs the same binary64 folded-cost comparisons and retained-prefix checks.
This proves preservation of the original unordered candidate path partitions,
maximum-link objective, singleton semantics, distinct equal-cost assignment
multiplicities, global margin, tolerance and floating arithmetic order. The method
is not a conversion of the retained-family cost predicate to integer arithmetic.
It only removes repeated Fraction operations from an already exact rational oracle.

The adapter caches 112 immutable integer edge weights for this target, charges
those entries plus preprocessing temporaries to the existing state budget, and
restores solver methods on both success and failure. No solver source or family
artifact is modified. It applies structurally to all factors; no capture ID,
device label or expected target count is used by the counter. The sidecar binds
the adapter source hash; its method also identifies the unchanged pivot composition.

A different pivot, inverse cache, factor reorder or new packed representation was
not needed: diagnosis showed that those stages were not the blocker. The existing
certificate-driven column route remains available where valid. Reverse evaluation
reverses independent factor construction/traversal, never the binary64 sum order.

## Validation before target trust

**102 tests passed, zero failures/errors**, before target evaluation. This includes
all previously relevant solver, exact-count, column-count, sidecar, staged,
margin-1, E02-counter, limited-regression and bounded-regression suites plus five
new tests:

- 12 small graphs, all candidate masks and four requested-flow modes: original
  rational matching versus integer matching, including exact ties, forbidden
  edges, mandatory nodes, selected paths and rational bound equality.
- Dyadic extremes, neighboring binary64 costs, subnormals, zeros and mixed scales.
- 24 small graphs at three margins in both orders against exhaustive retained
  hypothesis enumeration; artifacts unchanged and solver adapters restored.
- Weighted Cartesian histogram enumeration with huge integer multiplicities,
  equal costs, boundary neighbors, tolerance neighbors and nonassociative scales.
- Artificial state, transition and time exhaustion: explicit failure, no returned
  partial count, and restoration of the solver.

Existing tests additionally cover scalar inverse ties/subnormals, equal-cost
candidate identities, unordered paths, singleton/global-margin semantics and
family/sidecar tamper rejection.

All **120 already solved compact cardinalities** from the bounded regression were
then reproduced in both orders: **240 counting-only controls**, all exact and equal.
This includes the exact count from a query-failed case; a query failure does not
invalidate its separately completed counting result. No association regression
was rerun for these controls.

| Required control | Margin 0 | Margin 0.25 | Margin 1 |
|---|---:|---:|---:|
| TPMS-004 E02 | 1 | 32,743 | 5,788,836 |
| TPMS-008 E08 | 2 | 17,067,800,502,243 | 378,038,954,451,765,697,490 |

Only after all controls passed were the two target counts evaluated. They agreed
exactly at 217,075, without an expected target count being supplied to the counter.

## Completed factor and composition statistics

Forward order, including retained prior histograms and adapter entries in reported
live-state usage:

| Factor | Local histogram costs | Assignment multiplicity | Seconds | Transitions | Peak reported live states |
|---|---:|---:|---:|---:|---:|
| 0 | 9 | 9 | 0.001141 | 42 | 128 |
| 1 | 9,987 | 26,641 | 12.528327 | 306,988 | 44,240 |
| 2 | 5 | 5 | 0.000554 | 20 | 10,118 |

Reverse construction visited factors 2, 1, 0: respective times 0.000518,
12.472326 and 0.001134 s; state peaks 122, 44,236 and 10,120. Histogram costs,
assignment multiplicities and transitions per factor were identical.

The unchanged largest-histogram pivot is factor 1. Its left prefix has nine states;
the right suffix has five acceptance thresholds. The join streams 89,883 pairs.
The composition's own container accounting is 20,022 entries, with the adapter's
112 retained weights additionally charged by the outer budget. Integer-weight
preprocessing took 0.000073 s in the forward run. Packed-polynomial usage is zero.

| Order | Exact count | Counting seconds | Transitions | Peak live states | Process peak RSS, KiB | Packed bytes |
|---|---:|---:|---:|---:|---:|---:|
| Forward | 217,075 | 12.641578 | 397,325 | 44,240 | 68,076 | 0 |
| Reverse | 217,075 | 12.574094 | 397,325 | 44,236 | 68,268 | 0 |
| Frozen limits | — | 60 | 5,000,000 | 250,000 | No counting-specific RSS limit | 33,554,432 |

Family loading is separately recorded and excluded from counting time. No frozen
limit was increased. The old method timed out before completing factor 1; the new
method completes the entire target in under 13 s. Because the baseline did not
complete, these observations do not establish a full-run speedup ratio. Process
RSS includes imports and caches, not just DP states or polynomial storage.

## Target-only staged validation

The new sidecar was created only after both target orders completed exactly.
The unchanged staged integration took 24.972148 s; reload/reproduction took
24.930037 s. Process peak RSS for that benchmark/integration process was
166,172 KiB. Its larger footprint includes the preceding test suite, so it is
reported separately from isolated counting-worker RSS.

The original family bytes/hash, family completeness, exact query stage, query
operations, **585 query calls**, association, status, primary, persistent paths,
all membership outputs, original six-fragment denominator, metrics and scientific
computational parameters are unchanged. The query-derived status remains
AMBIGUOUS_ASSOCIATION, primary null, with zero persistent paths. This is independent
of counting completion. The only scientific payload change is cardinality:
`COMPUTATION_UNRESOLVED/null` to `EXACT/"217075"/null reason`.

The new sidecar/source hashes and current checkpoint context are expected
provenance differences. Forged family and model hashes were rejected. Reload
reproduced the entire staged result byte-identically.

- Family SHA-256: `b5c5503b910cc8940a6a08310f52117b56bd41add94d0f47980208918d737aa6`.
- Embedded model SHA-256: `563cd0d5ba71e7bd7594e65c29b1a670492df1d35f84233e4a7ab8b21c0266e0`.
- New sidecar SHA-256: `135ce3a09449d6930f5cd3630c41203f7b319adc7799edfd9c6b7988483c27fc`.

## New artifacts and integrity

New files only:

- `analysis/diagnose_episode_component_tracking_v2_draft2_repl_e02_margin1.py`
- `analysis/episode_component_tracking_v2_draft2_repl_e02_margin1_count.py`
- `analysis/benchmark_episode_component_tracking_v2_draft2_repl_e02_margin1.py`
- `tests/test_episode_component_tracking_v2_draft2_repl_e02_margin1.py`
- This document.
- `results/episode-component-tracking-v2-draft2-repl-e02-margin1-investigation/`:
  diagnostic, test log, 240 control measurements, both target outcomes, new sidecar,
  staged result, benchmark/source/hash manifest and `files.sha256`.
- `results/episode-component-tracking-v2-draft2-repl-e02-margin1-integrity.json`:
  independent final integrity/provenance audit.

The diagnostic was executed first; the benchmark then ran tests, solved controls,
both target orders and target-only integration, in that order. Both scripts refuse
existing result outputs. Use a fresh checkout/output location for full reproduction;
do not overwrite these recorded artifacts. To repeat only the new tests:

```sh
PYTHONPATH=analysis python3 -m unittest discover -s tests -p 'test_episode_component_tracking_v2_draft2_repl_e02_margin1.py'
```

All **1,719 pre-existing tracked files remain byte-identical**. The committed
six-capture NOT_READY regression and every prior E02 investigation are untouched.
HEAD remains `b1a0e3d`; tracked diff is empty. Source/artifact manifests and sidecar
bindings validate; `git diff --check` and independent new-file whitespace checks
pass. The final integrity JSON records these checks.

This resolves only REPL E02 margin-1 counting. No other unresolved case was rerun,
no broader readiness is claimed, and the 164-case regression and 160-arm matrix
were not run. No capture, detection, candidate regeneration, scientific tuning,
identification/discrimination claim, commit or push occurred.
