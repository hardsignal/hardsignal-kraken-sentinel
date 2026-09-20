# Separate Draft 2 exact solver prototype

This implementation is separate from the frozen Draft 2 experiment. It does not
modify V1, Draft 1, the experiment runner, parameters or historical outputs. Its
benchmark reads only the saved native/200 Hz Draft 2 candidate artifact, selects
TPMS-008 E08, and compares solvers. It does not rerun spectral analysis or the
160-arm matrix. No raw IQ or RF hardware is accessed.

## Implementation

- `analysis/episode_component_tracking_v2_draft2_exact_solver.py`: `Solver`,
  `Family` and `EpisodeFamily`.
- `tests/test_episode_component_tracking_v2_draft2_exact_solver.py`: exact
  equivalence, complete small-family, query, boundary and serialization checks.
- `analysis/benchmark_episode_component_tracking_v2_draft2_exact_solver.py`:
  new-output-only benchmark and provenance checks.

`Solver` accepts already eligible candidates and the original fragment count.
The caller retains ownership of spectral guards, detection and unusable-input
flags. All candidate IDs remain distinct, including equal-frequency candidates.
Paths include singletons, strictly advance by one or two fragments, step no more
than 50 Hz, and span no more than 100 Hz. No amplitude or label is consulted.

The solver uses exact rational minimum-cost maximum matching on the split-node
forward graph as a cardinality and cost bound. Successive shortest augmenting
paths use rational Bellman-Ford distances, not a floating-point MILP optimality
or feasibility tolerance. Every selected matching edge has at most one outgoing
and one incoming use per candidate. Strict fragment advance precludes cycles.
If the resulting cover violates the full-path range, it remains a relaxation;
it is never accepted as a feasible path cover.

When necessary, exact-cover branch-and-bound selects an uncovered candidate and
branches over every feasible path containing it. It propagates disjointness and
uses admissible matching bounds to prune. It does not retain the old table of all
remaining-candidate subsets. There are no artificial path labels or path-order
permutations. Cardinality is optimized before cost, never traded against cost.

For two-fragment groups, feasible non-singleton paths are exactly matching edges.
If all candidates on the smaller right side have distinct unique cheapest
predecessors, their row minima certify both cardinality and minimum cost. The
smallest second-choice gap provides a uniqueness certificate when it exceeds the
conservative arithmetic bound. This is the saved 73-candidate failure case.

## Scientific and numerical preservation proof

Let P be the set of generated paths. Selecting binary variables x_p subject to
sum(x_p for p containing candidate v) = 1 gives a bijection with the frozen
candidate-disjoint partitions, including unassigned singletons. The objective
sum((len(p)-1)*x_p) is exactly the old continuation-link objective. All edge
costs and skip penalties use the unchanged formula and input binary64 values.

The proof must include finite-precision behavior. The frozen implementation
computes path costs by forward summation, its optimum by right-associated
addition in earliest-candidate path order, and emitted hypothesis costs by
left-associated addition. Its local retained-family acceptance tests each
prefix against the minimum remaining cost, subtracting the selected path cost
from the remaining budget. Episode composition applies another ordered prefix
filter with ONE global margin. These operations and the 1e-12 comparison
constant are reproduced; they are not replaced with an approximately equivalent
single floating-point inequality.

Exact rational sums are used only for optimization bounds. For n candidates,
each unrounded total is nonnegative and below 4(n+1). At most n path additions
and n partition additions separate the rational edge total from the frozen
objective. The bound (2n+4)*ulp(4(n+1)) therefore safely encloses this rounding
error. Prefix-query pruning receives an additional copy of the bound; final
membership always uses the frozen prefix predicate. When all edge constants
share a dyadic unit and the maximum total uses fewer than 53 integer bits,
addition is provably exact and that optimization bound can be zero. The bound
is not a new acceptance tolerance or parameter: it only prevents unsafe pruning.

A matching-derived incumbent is accepted immediately only with a certificate.
Otherwise all covers that could improve its frozen floating-point cost survive
branch-and-bound and are evaluated with the original addition order. Equal-cost
covers need not all be visited to establish the optimum, but remain in the
retained family and can be queried independently.

Forbidding a two-candidate path does not forbid its edge inside a longer path.
The implementation removes that edge from a matching relaxation only if no
longer feasible path containing it is available. Required paths are checked for
candidate overlap before search. Tests explicitly cover these cases.

## Lossless compact representation and exact queries

`KRAKEN_DRAFT2_EXACT_IMPLICIT_FAMILY_V1` records candidates, all feasible paths,
hexadecimal binary64 path costs, the optimum and witness, margin, original
fragment count, and the frozen numerical predicate. Its content hash covers the
model. `Family.from_artifact` reconstructs and verifies it. Episode artifacts
store the independent factors, fixed singletons and global ordered filter;
`EpisodeFamily.from_artifact` verifies their reconstruction.

These are complete **implicit** solution-family descriptions. They do not claim
to be counted or materialized families. Equal-cost assignments remain different
sets of candidate paths. The executable membership predicate plus its hashed
implementation must accompany an archived artifact; the human-readable
constraint strings alone are not a replacement implementation.

- `contains`: verifies membership in the full retained family.
- `find(required=..., forbidden=...)`: exact constrained existence query.
- `possible` / `invariant`: existence with a path required / nonexistence with
  that path forbidden, respectively.
- `alternative`: every maximum-link cover has n-L* paths, so any different cover
  omits at least one witness path; checking this disjunction is exact.
- `classify`: tests persistent-path existence and invariance and joint
  feasibility of competing persistent paths. It preserves >=3 fragments and
  >=60% coverage using the original denominator. It does not promote an
  optimizer's single witness to a primary.
- `materialize`: complete expansion for small validation cases; exceeding a
  resource limit raises instead of returning a truncated family.

For a two-fragment query forbidding a singleton, that candidate must be matched.
The matching network enforces this through an exact integer reward 2n+1 per
required incident candidate. This exceeds the maximum total original edge cost
(1.25n), so any solution missing a required candidate is dominated by every
feasible solution covering them all. Among valid solutions the reward is a
constant; the declared cost and selected feasible family are unchanged. The
reward is removed from returned costs, and infeasible mandatory coverage is
reported as infeasible. This encoding is used only where a candidate has at most
one selected incident edge (two fragment layers). Generic graphs retain the
exact-cover fallback. Matching subproblems are cached by their entire constraints.

The original limits of 200,000 feasible paths and 200,000 exact-cover search
nodes are retained as computational safeguards. They do not prune scientific
solutions. Any exhausted query raises `Unresolved`; callers must report an
unresolved computation and null primary, not assume uniqueness. The separate
explicit-expansion safeguard remains one million hypotheses. Implicit models
have no artificial cap on the number of hypotheses they denote.

## Validation and benchmark

Run validation with:

```sh
python3 -B -m unittest discover -s tests -p test_episode_component_tracking_v2_draft2_exact_solver.py -v
```

Run only the saved-case benchmark into a new directory:

```sh
python3 -B analysis/benchmark_episode_component_tracking_v2_draft2_exact_solver.py --output results/episode-component-tracking-v2-draft2-exact-solver-benchmark
```

Tests compare the exact optimum cost and complete retained sets with the frozen
exhaustive solver at all three margins on 50 deterministic random small graphs.
They additionally cover crossings, equal-cost assignments, one/two-fragment
abstention, skip and range boundaries, nonassociative addition, margin boundaries,
original-denominator coverage, required/forbidden paths, global margin sharing,
all deterministic association fixture classifications, no silent truncation,
input-order determinism and artifact round trips. Test and benchmark results
are recorded in the separate benchmark directory, including old/new source and
input hashes. Timing metadata is observational and is not claimed deterministic;
family models and scientific outputs are deterministic.

## Complexity and what remains before a full experiment

A rational matching instance uses O(V+E) graph storage; Bellman-Ford successive
augmentation uses O(KVE) rational operations for K selected edges. Exact bit
arithmetic adds operand-size cost. General range-constrained exact cover and
retained-family existence can still take exponential time. Generating all paths
can also be exponential. This prototype reports resource exhaustion explicitly.
It does not claim a polynomial algorithm for general exact counting.

The compact representation solves storage of the family definition and supports
exact membership/ambiguity queries. It does NOT compute the exact number of
positive-margin hypotheses. `retained_hypothesis_count` is explicitly null and
`count_state` is NOT_EVALUATED. This is not permission to omit a required metric
from the frozen experiment.

Before a complete run, the artifact contract must explicitly accept/version the
implicit representation and resolve the original exact-count requirement:
implement and verify exact counting, or explicitly revise that output requirement.
Neither change is silently made here. A separate runner/validator adapter must
preserve the original numerical/global-margin policy and resource-failure states.
The unchanged 160-arm matrix needs completion testing; success on E08 alone does
not establish its computational feasibility. Historical status remains 1/160
complete, one unresolved arm, 158 NOT_RUN and spectral fixtures NOT_STARTED.
No parameter selection or device-discrimination claim follows from this work.
