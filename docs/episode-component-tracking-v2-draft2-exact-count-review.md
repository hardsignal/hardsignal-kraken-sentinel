# Draft 2 retained-family cardinality: implementation and schema review

This is a new, separate counting investigation against committed solver checkpoint
`495b797440d5c693d70ab65818220fcb56c9120f`. It does not amend the experiment,
adopt a replacement output schema, or integrate the counter into the experiment.
Only the saved TPMS-008 E08 compact models were benchmarked. No IQ, RF capture,
full-matrix run, parameter selection, or historical-file modification was involved.

## What is one hypothesis?

Within one association group, a hypothesis is an **unordered partition of all
eligible candidate IDs into feasible, forward-ordered paths**, including every
unmatched candidate as its own singleton path. Paths have no interchangeable
track labels. Changing candidate assignments changes the hypothesis even if all
frequencies and costs agree; merely reordering paths does not.

The partition must maximize total continuation links and pass the frozen retained
cost predicate at the declared margin. The committed implementation's arithmetic
is part of this comparison: its optimum uses a right fold, its emitted hypothesis
cost a left fold, and retention uses canonical earliest-candidate prefix tests
with binary64 subtraction and the existing tolerance. The counter does not replace
that predicate by a mathematically similar but numerically different sum.

An episode hypothesis chooses one partition per connected association group and
includes the fixed isolated singletons. It must also satisfy the frozen episode
**global** margin, in original group order. Multiplying independent local retained
counts would generally overcount. A completely singleton partition has cardinality
one; singletons are not optional or independently labelable.

## Exact implementation

New implementation: `analysis/episode_component_tracking_v2_draft2_exact_count.py`.
New runner: `analysis/benchmark_episode_component_tracking_v2_draft2_exact_count.py`.
New tests: `tests/test_episode_component_tracking_v2_draft2_exact_count.py`.

The general backend merges identical nodes of a prefix decision DAG, storing the
remaining candidate mask, required links, exact binary64 remaining budget, and
exact emitted cost. Each node carries an arbitrary-precision integer multiplicity.
It reuses the committed feasible paths, optimum queries, ordering, and comparisons.
Different partitions reaching the same state add their multiplicities; no path
ordering is enumerated. Group cost histograms are combined using the original
episode prefix comparisons. This is exact-cover counting with memoized equivalent
computation states, not an assumption that equivalent costs mean identical paths.

For suitable two-layer groups there is a faster weighted bipartite matching
backend. All smaller-side candidates must be matched in the saved E08 groups.
Thus a maximum matching uniquely determines its non-singleton paths and all
remaining singleton assignments. An exact integer Hungarian primal/dual solution
rewrites excess cost as selected nonnegative reduced-edge costs plus penalties
for unmatched columns. The implementation verifies dual feasibility, primal-dual
equality, and the sign of column potentials. An edge whose reduced cost alone
exceeds the entire margin cannot occur in an accepted matching.

Removing only such impossible edges can factor the graph. Inside each block,
frontier DP records occupied columns that can still occur in future rows and
accumulated cost. Expiring an unused column charges its unmatched penalty. Each
row chooses exactly one unused column; different choices contribute separate
multiplicities. Discarding expired column identities therefore loses neither
counts nor constraints. The committed compact model remains the source for
membership queries; a count histogram is not used as a replacement model.

Block and group histograms are combined by exact, truncated polynomial
convolution. Costs are nonnegative excess costs and the cutoff is applied to the
**sum**, preserving the global margin. Coefficients use arbitrary-precision
integers. Carry-free packed integer multiplication accelerates convolution without
floating-point FFT rounding. Fixed singletons contribute the polynomial 1.

### Arithmetic preservation certificate

Frequency rational reconstruction proposes a cost quantum; it has no authority
to change stored frequencies or costs. Every actual binary64 path coefficient is
compared, as an exact rational, with its proposed integer multiple. The certificate
bounds coefficient residuals and all relevant floating-point operations, including
optimum folds, local prefixes, emitted costs, and episode prefixes. It requires
both adjacent integer cost shells to be separated from the margin by more than
this bound plus the frozen tolerance, and separately certifies cost ordering.
If any test fails, the counter uses the original IEEE prefix-state backend.

For saved E08 the certified quantum is `2500/119311929`. At margin 0.25 the excess
cutoff is 11931; at margin 1 it is 47724. Integer gcd normalization inside a block
can further divide these computational weights. The positive-margin shell gaps
exceed the group/episode rounding bounds. Margin zero uses the IEEE backend.
The rational lattice is a proved computational transformation, not a new rounding
rule or scientific parameter.

Together these bijections and state-merging invariants preserve the feasible set,
maximum-link objective, cost predicate, singleton membership, assignment
distinctions, and episode margin. They do not choose a primary. Existing exact
membership, invariance, and ambiguity functions remain in the unchanged solver.

## Validation and measurements

The final suite passed **17 tests**, including 40 seeded small graphs at all three
margins against the committed exhaustive solver, explicit equal-cost assignments,
singleton handling, path-order invariance, disconnected factors, and global margin
semantics. Other tests cover numeric boundary fallback, exact convolution,
Hungarian dual and unmatched-column penalties against brute-force assignments,
resource failure, and unchanged compact-model queries. A complete 10-by-10
equal-cost matching graph counted **3,628,800** assignments with fewer than 3,000
DP states, without enumerating its hypotheses.

Final measured results are in
`results/episode-component-tracking-v2-draft2-exact-count-dual-benchmark/`:

| Scope | Margin | Exact cardinality | Counting seconds |
|---|---:|---:|---:|
| Previously failed group | 0 | 1 | 0.506 |
| Previously failed group | 0.25 | 191,532,581,516 | 0.444 |
| Previously failed group | 1 | unresolved | 0.088 to stop |
| Whole E08 episode | 0 | 2 | 1.605 |
| Whole E08 episode | 0.25 | 17,067,800,502,243 | 0.503 |
| Whole E08 episode | 1 | unresolved | 0.316 to stop |

Loading each model took a further approximately 0.03 seconds for a group or
0.20 seconds for an episode. Process peak RSS reached 68,184 KiB (66.6 MiB);
this is a cumulative process high-water mark, not an isolated per-case estimate.
The group margin-zero result equals the earlier exact value 1. The margin-0.25
result exceeds the earlier lower bound 1,935,360. The margin-1 lower bound
74,680,704 remains a lower bound only; no exact value or approximation is reported.

The first counter and its results are preserved separately in the new
`episode_component_tracking_v2_draft2_exact_count_baseline.py` and
`results/episode-component-tracking-v2-draft2-exact-count-benchmark/` files. Its
row-minimum formulation independently obtained the same group margin-0.25 count
but exhausted its state budget on the episode. The exact assignment-dual
transformation completed the latter without increasing limits. The baseline test
source is archived with those results, so their recorded source hashes remain
verifiable rather than referring to the later modified test suite.

## Precise unresolved computation

Limits were declared before saved-case counting: 250,000 live states, 5,000,000
transitions, 60 seconds per count, and 32 MiB of packed polynomial storage. These
are computational fail-closed limits, not scientific parameter changes.

Both margin-1 runs stopped in the same 18-row matching block after processing row
5. The current and next frontiers contained 39,964 and 211,171 states respectively,
or 251,135 live states, with 52 columns still relevant. The group run had executed
433,774 transitions; the episode run had executed 1,944,070 including earlier
factors. No partial cardinality was published. Positive margin connects candidates
that could be pruned/factored at 0.25, leaving many distinct occupied-column/cost
states. Those are not duplicate path orderings.

This demonstrates a limit of this implementation **under its declared budget**,
not that exact margin-1 counting is intrinsically impossible or that machine
memory was exhausted. Counting matchings contains permanent counting as a special
case; a universally small exact representation of the counting computation cannot
be assumed. Exact decision-diagram variable ordering, separator decomposition,
or tighter admissible suffix bounds could be investigated separately. No estimate,
sampling, truncated family, raised budget, or forced-primary decision substitutes
for the unresolved result here.

## Minimal explicit schema proposal and readiness

Propose a new sidecar format, **KRAKEN_DRAFT2_RETAINED_CARDINALITY_V1**, alongside
each unchanged compact family artifact. Required fields are:

- `format`, `scope`, `margin_hex`, and a versioned definition/arithmetic policy
  identifying the unordered candidate-path partition and frozen IEEE predicate;
- `family_artifact` (relative path), its actual `family_sha256`, and the embedded
  `model_sha256`, binding the count to the exact family and margin;
- `cardinality.state`: `EXACT` or `COMPUTATION_UNRESOLVED`;
- `cardinality.value_decimal`: arbitrary-precision decimal string only for
  `EXACT`, and explicit null otherwise;
- counter/source hashes, method, arithmetic certificate where applicable,
  computational limits, runtime/state statistics, and an explicit failure reason
  for an unresolved count.

A lower bound, if stored, must be separately named and must never populate the
exact-cardinality field. The definition must say that an unresolved cardinality
does not make the compact family incomplete or invalidate successful exact
membership queries, but does fail an output requirement demanding an exact count.
The frozen membership/invariance/ambiguity API and compact family predicate remain
authoritative; the counter adds cardinality only. This is a proposed versioned
schema revision, not an implicit amendment to historical JSON outputs.

A compact family plus exact cardinality can replace expanded hypothesis lists
semantically, after explicit schema adoption and consumer validation: the model
specifies every assignment, queries preserve identity and ambiguity, and the count
states its size. It is not a drop-in replacement for the old JSON arrays. Consumers
that iterate all hypotheses must be adapted to exact queries/aggregations; required
track, support, quality, and alternative/invariant membership outputs still need
integration tests. Cardinality alone does not supply those metrics.

**Not ready to integrate and rerun all 160 arms.** Margin-1 cardinalities remain
unresolved, general multi-fragment performance is not established by this saved
case, and the versioned schema/consumer contract has not been adopted or validated
end to end. No existing scientific definition or parameter needs to change to
continue investigating exact counting. No identification or discrimination claim
follows from these computational results.
