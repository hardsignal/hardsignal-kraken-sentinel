# TPMS-004 E02 margin-1 exact cardinality investigation

Decision: **E02_MARGIN1_EXACT_SOLVED**. The exact retained-family cardinality is
**5,788,836** (`5788836`). Both independent computation orders returned this integer
under the unchanged limits. Checkpoint: `4ce37ec977c69b5816949dc9e5ebca449fb07cd0`.

This investigation uses the committed family for
`PIPELINE-TPMS-004-20260917-233423`, E02, margin 1. It changes no scientific
parameter, candidate, family, historical implementation or result. No RF capture,
FFT/component detection, full 28-case regression, commit or push was performed.

## Reproduced blocker and structure

The saved episode has five fragments with eligible candidate counts
`[189, 1, 19, 4, 71]` (284 total). Its 195 connected groups comprise 189 fixed
singletons and six nontrivial factors. The candidate frontier shared between
factors is zero: the sufficient composition boundary is the binary64 prefix cost.
Factors retain the committed median-frequency ordering and tie breaks.

| Factor (zero based) | Candidates | Candidates by fragment | Edges | Paths of lengths 1 / 2 / 3 | Optimum links | Histogram entries | Assignment multiplicity |
|---|---:|---|---:|---|---:|---:|---:|
| 0 | 3 | 3:1, 5:2 | 2 | 3 / 2 / 0 | 1 | 2 | 2 |
| 1 | 51 | 1:37, 3:3, 5:11 | 81 | 51 / 81 / 438 | 6 | 80,449 | 106,493 |
| 2 | 34 | 1:26, 3:1, 5:7 | 33 | 34 / 33 / 182 | 2 | 154 | 168 |
| 3 | 2 | 4:1, 5:1 | 1 | 2 / 1 / 0 | 1 | 1 | 1 |
| 4 | 2 | 1:1, 3:1 | 1 | 2 / 1 / 0 | 1 | 1 | 1 |
| 5 | 3 | 3:1, 5:2 | 2 | 3 / 2 / 0 | 1 | 2 | 2 |

The existing local IEEE histograms complete with 1,869,022 transitions and a
194,043-state peak. The old composition then grows as follows:

| Factor | Input states | Output states at last check | Peak simultaneous composition states | Step transitions | Cumulative transitions |
|---|---:|---:|---:|---:|---:|
| 0 | 1 | 2 | 3 | 2 | 1,869,024 |
| 1 | 2 | 157,450 | 157,452 | 160,898 | 2,029,922 |
| 2, interrupted | 157,450 | 92,551 | **250,001** | 107,318 | 2,137,240 |

The failing insertion is factor 2, prior-cost index 15,059 and right-cost index
133 (zero based). Both multiplicities are one:

```
prior: 0x1.95accfb5ea770p+1
right: 0x1.6cdbae3193ceap+0
sum:   0x1.260d53675a2f2p+2
```

That sum fails the next frozen prefix predicate, which the old composition checks
only at the next step. The blocker is materializing many distinct rounded sums
from independent factors, including doomed prefixes. Equal float states were
already merged; neither shared candidate variables nor path permutations cause
the growth. The reproduced failure occurs after 15.0694 seconds, with process
peak RSS 91,716 KiB. Full trace, source hashes, frontier and factor statistics are
in `diagnostic.json`.

## Exact transformation and equivalence

The new general counter is `KRAKEN_DRAFT2_IEEE_MONOTONE_PIVOT_COUNT_V1`.
It selects the largest group-cost histogram as a pivot, using only structure
(ties select the first factor). No target count or device label is consulted.
The unchanged local histogram counter supplies binary64 emitted costs and exact
integer multiplicities. Its canonical path partitioning preserves candidate IDs,
singletons, maximum links and unordered-path semantics.

Let `H_i(g)` be these multiplicities, `s_i = sum(optima[i:])` using the original
Python sum, and `B = sum(optima) + margin + TOLERANCE` using the original expression.
For this target, B is `0x1.590d679ebd95ep+2`. The original suffix acceptance function
obeys the recurrence below, where `fl` is the actual frozen binary64 addition:

```
F_n(x) = 1[x <= B]
F_i(x) = 1[fl(x + s_i) <= B] * sum_g H_i(g) * F_(i+1)(fl(x + g))
```

For any fixed suffix assignment, this predicate is downward closed on finite
nonnegative binary64 prefix costs. Nonnegative floating addition is monotone;
intersecting upper-bound predicates preserves downward closure. Represent each
such acceptance set by its largest accepted prefix T, weighted by assignment
multiplicity. The exact inverse of an addition is:

```
U(T, g) = max {finite binary64 x >= 0: fl(x + g) <= T}
```

The implementation computes U by binary search over ordered nonnegative binary64
bit patterns, evaluating the original addition and comparison at every probe.
It never substitutes rounded subtraction. An empty preimage contributes nothing.
Backward elimination maps each weighted pair `(T, g)` to
`min(U(T, g), U(B, s_i))` and multiplies its integer weights. Equal thresholds
can be merged because their acceptance predicates are identical for every prefix;
their multiplicities are added, so different assignments still count separately.
This proves the backward recurrence by induction from F_n.

The left prefix is accumulated in its original order, with the exact next prefix
guard applied before insertion. At the pivot, each original-order sum is streamed
into a sorted threshold lookup and multiplied by prefix, pivot and suffix weights.
Every original tuple of group assignments contributes exactly once iff it passes
the original predicates. The method never constructs expanded hypotheses and
never reorders or reassociates the floating cost fold.

For E02 the pivot is factor 1. The left side has two costs. Backward suffix
threshold widths are `1 -> 2 -> 2 -> 2 -> 308`, across factors 5, 4, 3, 2.
The join streams 160,898 pairs, retaining 161,987 charged containers instead of
materializing their cost product. The largest live-state usage remains local
histogram construction. Previously retained histograms, maps and iteration buffers
are charged to the same state budget; each inverse predicate probe is charged as
a transition.

Forward/reverse runs reverse independent histogram construction and traversal
orders, while retaining the original arithmetic operand order. The certified
column-frontier backend remains available for suitable cases, including E08;
its two evaluation orders are frequency and reverse-frequency.

## Applicability of alternatives

Connected-component factorization already exists and is retained. There is no
cross-component candidate separator to shrink further. Scalar-boundary backward
elimination and a streaming pivot join provide the useful decomposition here.
Canonical equivalent-threshold merging and earlier exact prefix guards are valid;
no nearest-cost merging, heuristic pruning or assignment symmetry quotient is used.
Reordering independent construction is valid, but reordering the binary64 sum
would change the definition. Sparse additive polynomials or matching/permanent
techniques require their existing exact arithmetic/structure certificate: the
target's three-candidate paths prevent using the two-layer matching certificate.
The new scalar acceptance formulation avoids assuming such a certificate.
The existing local decision DAG remains unchanged. This result does not guarantee
that every future episode fits the frozen budgets; resource failure stays explicit.

## Validation before evaluating the target

All **78 tests passed**, zero failures/errors: eight new tests plus the existing
solver, exact counter, column counter, sidecar, margin-1 and staged integration
suites. New coverage includes 35 seeded small exhaustive graphs at all three
margins in both orders, 100 weighted histogram products at all three margins in
both orders, disconnected factors/global margin, singletons, equal-cost identities,
unordered paths, arbitrary-precision multiplicity, nonassociative boundaries,
ties/subnormals/overflow, inverse-neighbor checks and fail-closed budgets.
Existing family/sidecar tamper and binding tests remain passing.

Before either target run, all 20 already solved compact regression cases matched
their committed counts in both orders (40 counting-only evaluations):

| Control label | Margin 0 | Margin 0.25 | Margin 1 |
|---|---:|---:|---:|
| TPMS004 ordinary E02 | 1 | 32,743 | Target evaluated afterward |
| TPMS004 anomaly | 2 | 83 | 7,418 |
| TPMS005 ordinary | 1 | 19 | 86 |
| TPMS007 ordinary | 1 | 130 | 1,297 |
| BETWEEN anomaly | 1 | 26 | 704 |
| REPL single fragment | 1 | 1 | 1 |
| TPMS008 E08 control | 2 | 17,067,800,502,243 | 378,038,954,451,765,697,490 |

## Target performance and staged validation

| Evaluation | Exact count | Counting seconds | Transitions | Peak live states | Process peak RSS, KiB | Packed polynomial bytes |
|---|---:|---:|---:|---:|---:|---:|
| Forward | 5,788,836 | 14.862752 | 2,050,270 | 194,045 | 105,700 | 0 |
| Reverse | 5,788,836 | 16.600687 | 2,050,270 | 194,201 | 105,132 | 0 |
| Frozen limits | — | 60 | 5,000,000 | 250,000 | No separate RSS cap | 33,554,432 |

All frozen limits were respected without an increase. Counting time excludes
family loading (recorded separately). Local histogram construction dominates
runtime. RSS measures the whole process, including imports; it is not packed
polynomial usage. The instrumented baseline and new subprocess differ in imports,
so their RSS numbers are observations, not a controlled memory-speed comparison.

Only E02 margin-1 was passed through the unchanged staged integration after solving.
Integration took 7.230443 seconds and deterministic reload/reproduction 7.260599
seconds; the integration process high-water RSS was 139,796 KiB. Assertions prove
unchanged family bytes, family completeness, exact query states/operations/counts,
association, metrics, computational limits and all non-cardinality stage states.
This includes original fragment denominator, membership, paths, status and primary.
The only scientific payload change is cardinality state/value/reason:
`COMPUTATION_UNRESOLVED/null` becomes `EXACT/"5788836"/null`.
The new sidecar path/hash, counter source binding and checkpoint metadata necessarily
change. Reproduced staged serialization is byte-identical. Deliberately forged
family/model hashes are rejected.

The family SHA-256 remains
`c13cce11dd0e5ba1ec5bbcf6a130b762ab896bf91678e196fbba5c9aace3a01a`.
The new sidecar SHA-256 is
`739038e2026606a71dced45dab50381e7c9dbecae89b9ba1d7a7df6db809416b`.
Source, embedded model, limits, arithmetic policy, counting definition and runtime
bindings are recorded in the sidecar and benchmark. All 504 pre-existing tracked
files remain byte-identical. The committed limited-regression `NOT_READY` report
is untouched. No broader runner readiness or full-matrix runtime is inferred.

## New files and reproduction

- `analysis/diagnose_episode_component_tracking_v2_draft2_e02_margin1.py`
- `analysis/episode_component_tracking_v2_draft2_e02_margin1_count.py`
- `analysis/benchmark_episode_component_tracking_v2_draft2_e02_margin1_count.py`
- `tests/test_episode_component_tracking_v2_draft2_e02_margin1_count.py`
- This document.
- `results/episode-component-tracking-v2-draft2-e02-margin1-investigation/`:
  `diagnostic.json`, `tests.txt`, `control-counts.json`, `target-forward.json`,
  `target-reverse.json`, `target-margin-1.cardinality.json`,
  `target-staged-result.json`, `benchmark.json`, `files.sha256`.
- `results/episode-component-tracking-v2-draft2-e02-margin1-integrity.json`:
  final independent integrity audit.

The diagnostic and benchmark scripts were run in that order with Python 3; the
benchmark refuses an existing benchmark output. To reproduce the unit tests:

```sh
PYTHONPATH=analysis python3 -m unittest discover -s tests -p 'test_episode_component_tracking_v2_draft2_e02_margin1_count.py'
```

Use a fresh checkout/output location for a complete benchmark reproduction; do
not overwrite the recorded artifacts. `benchmark.json` includes the full source
manifest, test totals, per-control resources and original tracked-file hashes.
`files.sha256` covers its result artifacts. The final integrity audit also checks
new-file whitespace because ordinary `git diff --check` excludes untracked files.
