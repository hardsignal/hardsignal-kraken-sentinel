# REPL E03 exact-query investigation

**REPL_E03_QUERIES_EXACT_SOLVED.** Margin 0.25 and margin 1 both complete exact
queries and metric projection in forward and reverse internal traversal orders.
Every target result reloads byte-identically. HEAD remains `6b9b5bb`.

This was query-solver work only. The committed margin-0.25 cardinality remains
EXACT **349,149**; margin-1 cardinality remains **COMPUTATION_UNRESOLVED / null**.
Neither sidecar was replaced or recounted. No other unresolved counting case was
investigated, and no full regression or 160-arm matrix was run.

## Exact failure reproduction

Capture: `BETWEEN-DEVICE-REPL-V1-20260919-024341`, E03.
Five fragments contain 316 saved components, of which 313 are eligible:
`[193, 3, 18, 2, 97]`. The family contains 237 connected groups: 231 fixed
singletons and six nontrivial factors. No candidate is shared between factors.

| Factor | Candidates | Candidates by fragment | Edges | Feasible paths by length 1 / 2 / 3 |
|---|---:|---|---:|---|
| 0 | 2 | F3:1, F5:1 | 1 | 2 / 1 / 0 |
| 1 | 61 | F1:44, F3:8, F5:9 | 144 | 61 / 144 / 466 |
| 2 | 4 | F1:3, F2:1 | 3 | 4 / 3 / 0 |
| 3 | 11 | F1:9, F2:1, F4:1 | 10 | 11 / 10 / 9 |
| 4 | 2 | F1:1, F3:1 | 1 | 2 / 1 / 0 |
| 5 | 2 | F1:1, F3:1 | 1 | 2 / 1 / 0 |

There are 717 feasible paths inside nontrivial factors and 948 structurally
feasible paths including fixed singletons. Completed membership-query answers in
the reproduced failures establish 425 possible retained paths at margin 0.25 and
666 at margin 1. These totals are set unions with the fixed singleton inventory;
they do not double-count singleton answers logged again during invariance checks.

Both unchanged query runs fail identically at public call **964**, during
**invariance**, after membership operations have completed exactly. The constraint
is `required=[]`, `forbidden=[['E003_F005_C0050']]`: an existential query for a
retained hypothesis omitting this singleton path. It is not a request to omit the
candidate itself; every hypothesis must cover the candidate.

The failing local preflight is factor 1 `Family.find(forbidden=[670])`. Its
cumulative solver counter attempts search node **200,001**, exceeding the existing
`SEARCH_LIMIT=200000`. Global composition for this particular constraint has not
started, because necessary local feasibility has not yet been resolved. No local
failure was converted into a negative answer.

| Diagnostic | Margin 0.25 | Margin 1 |
|---|---:|---:|
| Instrumented staged runtime, seconds | 23.734931 | 27.142361 |
| Public calls at failure | 964 | 964 |
| Cover visits in the failing constraint | 102,369 | 82,082 |
| All instrumented cover calls | 200,692 | 200,785 |
| Local feasibility calls | 3,274 | 4,840 |
| Matching-bound invocations, including cache hits | 203,907 | 205,528 |
| Matching-call time, seconds | 17.861418 | 20.842507 |
| Maximum chosen-cover recursion depth | 46 | 46 |
| Repeated residual-key visits | 183,192 | 181,335 |
| Repeated full-key visits | 30,429 | 37,067 |
| Process peak RSS, KiB | 153,844 | 151,640 |

The diagnostic records query history, local feasibility results, all factor cache
statistics and branching/depth histograms. The residual diagnostic key is
`(solver, mask, needed_links, forbidden)`; it deliberately omits chosen costs and
is **not** asserted to be sufficient for safe memoization. The full diagnostic
key also includes chosen paths, target and rational bound. Repeated visits show
redundant work, not interchangeable retained hypotheses.

The 61-candidate factor at the margin-0.25 failure has 6,800 cached matching
results, 167 cached optima, 28,308 optimum-cache hits and 200,001 charged search
visits. The prior forbidden-singleton query for `E003_F005_C0049` itself took
33,528 cover visits before finding a witness. Thus exhaustion is cumulative over
the query stage, with especially expensive negative singleton constraints.

## Root cause and exact transformation

The existing implementation directly searches exact covers with a forbidden
path. For this three-layer factor, its matching relaxation does not propagate
forbidden-singleton coverage: `_mandatory_singletons` supplies that bound only
for at most two active fragments. Smallest-domain branching and cached matching
bounds already exist, but many covers remain to be visited. Separate required-path
queries have already established global membership for competing paths; the
negative query does not reuse those answers.

The new engine is `KRAKEN_DRAFT2_CANDIDATE_COVER_DISJUNCTION_QUERIES_V1`.
It builds immutable candidate-to-path incidence lists and eliminates each
forbidden path through an exact cover disjunction:

For any candidate c in forbidden path p, a complete retained partition omits p
**if and only if** it contains one of the other feasible paths q containing c.
Choose c with the smallest incidence list, preserving candidate identity.
Each branch requires q, keeps all existing required constraints, and retains
all other forbidden constraints. q overlaps p, so p is then necessarily absent.
A required path already overlapping p likewise proves that p is absent. Unknown
forbidden paths are vacuous; forbidden fixed singletons are impossible.

Proof: every retained hypothesis covers c exactly once. If it omits p, its unique
covering path q is one of the listed alternatives. Conversely, selecting q != p
containing c excludes p because candidates cannot be covered twice. Therefore the
union of branches is exactly the original constrained family. The recursion
removes one forbidden path each time. Overlapping or invalid required paths are
still rejected by the unchanged exact solver.

Every branch is a **global episode query**, using the existing frozen prefix and
binary64 acceptance predicates. Cached answers are complete global witnesses or
proven absence. Local feasibility alone never suffices for a positive answer.
Candidate assignments are not merged, floating operations are not reassociated,
and no arithmetic tolerance, path order, margin, singleton or partition semantic
changes. This is Boolean existential reasoning, not cardinality counting.

All new disjunction expansions and attempted branches call the same factor
solver's `_visit()`, sharing its existing cumulative 200,000 search limit. No
counter is reset. Failed searches are not cached as absence. Public-call and
wall-clock budgets remain 5,000 and 120 seconds. The membership stage fills much
of the needed global cache before invariance begins, making the disjunction cheap.

Forward and reverse evaluations reverse only the competing-path traversal order.
They return identical scientific answers while charging slightly different search
work. No new component separation, floating residual dominance, approximate bound,
or larger resource allowance is needed. The original matching and exact-cover
implementations remain unchanged.

## Validation before trusting targets

**107 tests passed, zero failures/errors.** Existing solver, count, column,
cardinality sidecar, staged, limited/bounded regression, previous margin-1 and
REPL E02 milestone suites remain passing. Five new tests cover:

- All supported query forms against complete small-family enumeration: possible
  and impossible paths, forbidden/required pairs, invariance, alternatives,
  persistent classification and primary-related predicates. Candidate alternatives
  are represented by incident possible paths, including singleton possibilities.
- Twelve seeded random graphs at three margins in both traversal orders, with
  original-query and exhaustive parity; crossing, disconnected and singleton cases.
- Artificial search exhaustion: an exception remains explicit and its unresolved
  constraint is not entered in the answer cache as absent.
- Reuse of globally validated membership answers during invariance.
- Query-engine hash, search-limit and query-limit tampering rejected before queries.

All **121 previously completed compact query cases** from the bounded regression
were then re-evaluated in both internal orders: **242 query-only controls**, all
with identical query operations, public call counts, association, metrics,
cardinality and other scientific fields. This includes E08 at all margins, the
seven limited-regression episodes' compact arms, and REPL E03 margin 0. Connected
arms and counting were not rerun. The committed sidecars, including unresolved
sidecars on otherwise completed query controls, were consumed without recounting.
Counting entrypoints were blocked in benchmark child processes.

## Per-margin target results

| Result | Margin 0.25 | Margin 1 |
|---|---|---|
| Family construction / provenance | COMPLETE / VERIFIED | COMPLETE / VERIFIED |
| Exact queries | EXACT | EXACT |
| Membership / invariance / ambiguity operations | All EXACT | All EXACT |
| Metric projection | COMPLETE | COMPLETE |
| Original fragment denominator | 5 | 5 |
| Public query calls | 1,012 | 1,012 |
| Association status | MULTIPLE_PERSISTENT_TRACKS | MULTIPLE_PERSISTENT_TRACKS |
| Primary | null | null |
| Possible retained paths | 425 | 666 |
| Invariant paths | 255 | 234 |
| Alternative paths | 170 | 432 |
| Possible persistent tracks | 124 | 356 |
| Structural violations | 0 | 0 |
| Cardinality, reused unchanged | EXACT 349149 | COMPUTATION_UNRESOLVED / null |

These possible persistent paths need not all coexist in one hypothesis. The
status is the existing exact classifier's result. Candidate membership alternatives
were checked against the possible-path union; invariant and alternative sets are
disjoint. Each available path satisfies fragment uniqueness, step/gap, coherence,
support and coverage rules. The null primary is computed from exact classification,
not inferred from failure.

| Margin / order | Staged runtime, s | Reload runtime, s | Maximum factor search visits | Total factor search visits | Process peak RSS, KiB |
|---|---:|---:|---:|---:|---:|
| 0.25 / forward | 17.789373 | 17.803073 | 21,782 | 21,923 | 105,744 |
| 0.25 / reverse | 17.887273 | 17.879517 | 21,770 | 21,908 | 105,500 |
| 1 / forward | 22.094236 | 22.029417 | 43,276 | 43,442 | 110,068 |
| 1 / reverse | 21.917860 | 22.082641 | 43,244 | 43,403 | 110,044 |

Reported runtime includes unchanged staged family validation/reconstruction,
queries and metric projection; the query stage is shorter than this total.
Search visits include the new disjunction charges and existing solver visits;
the frozen limit is cumulative per factor solver, not a reset per public query.
No query/search limit was exceeded in the new target runs. RSS includes process
imports and saved control metadata; diagnostic instrumentation has a different
footprint, so this is not a controlled memory-speed comparison.

| Internal work | 0.25 forward / reverse | 1 forward / reverse |
|---|---|---|
| Disjunctions | 61 / 61 | 61 / 61 |
| Attempted disjunct branches | 322 / 307 | 127 / 88 |
| Global-base query invocations | 956 / 956 | 971 / 971 |
| Cache hits | 858 / 843 | 663 / 624 |
| Maximum disjunction depth | 1 / 1 | 1 / 1 |

The different branch work with identical outputs provides an independent internal
order check. Detailed matching/optimum caches and factor search statistics are
recorded separately in each target audit.

## Provenance, unchanged fields and reproduction

The new query module adds an explicit source-hashed `query_engine` declaration to
the staged result, including adapter version, ordering and frozen search/query
limits. It wraps the unchanged staged consumer; it does not silently claim that
the old query engine produced the new outputs. Reproduction validates this adapter
binding, request digest and Git-context digest before recomputation.

Each margin's forward and reverse scientific payload hashes agree. Each of the
four saved results reproduces byte-identically under its own recorded engine
order and source bindings. Fields previously available in the committed bounded
result remain equal: representation, family completeness, cardinality, computational
limits, provenance-validation/family/cardinality stage states and the completed
membership operation. Association/metrics and later query operations become
available solely because exact query computation now completes. The public count
increases from the failed prefix's 964 to the completed stage's 1,012.

Both committed family and sidecar files remain byte-identical:

| Margin | Family SHA-256 | Existing sidecar SHA-256 |
|---|---|---|
| 0.25 | `a011e756b107d3583a3ee77f0a2ba8df0132e381babe02d2f50b83237d80e3b4` | `33faa62b36bc62f9c15e5ffddbd2c73402991bd5164a0bcbd887ea04ee62b499` |
| 1 | `5db427d4b254151b363318cbeae3c902ca573dbcd14b2347f38ca7a27de66c1f` | `7859b94f6d362199959881ae2478ca6c1d64d65535491f23e1c25c95388d701e` |

Margin 1 retains the original 250,001-state counting-failure reason and null
value. Its improved query status does not assert a count or resolve that blocker.

## New files and integrity

- `analysis/diagnose_episode_component_tracking_v2_draft2_repl_e03_queries.py`
- `analysis/episode_component_tracking_v2_draft2_repl_e03_exact_queries.py`
- `analysis/benchmark_episode_component_tracking_v2_draft2_repl_e03_queries.py`
- `tests/test_episode_component_tracking_v2_draft2_repl_e03_queries.py`
- This document.
- `results/episode-component-tracking-v2-draft2-repl-e03-query-investigation/`:
  both original-failure diagnostics, test log, 242 control audits, four new target
  staged results and audits, benchmark/source manifest and `files.sha256`.
- `results/episode-component-tracking-v2-draft2-repl-e03-query-integrity.json`:
  independent final integrity, provenance and scientific-parity checks.

The diagnostics ran first, then tests and all controls, then targets and their
reloads. Benchmark output must be new. To run the new tests alone:

```sh
PYTHONPATH=analysis python3 -m unittest discover -s tests -p 'test_episode_component_tracking_v2_draft2_repl_e03_queries.py'
```

All **1,734 pre-existing tracked files remain byte-identical**. The committed
six-capture NOT_READY result and REPL E02 milestone are untouched. HEAD remains
`6b9b5bb`; git status contains new untracked artifacts only. Source/artifact hashes,
sidecar bindings, deterministic reproduction, `git diff --check` and independent
new-file whitespace checks pass.

No RF capture, FFT/detection, input regeneration, scientific parameter change,
margin-1 cardinality fix, full 164-case rerun, 160-arm matrix, identification or
discrimination claim, commit or push occurred. This decision resolves the two
specified query stages only; broader regression readiness is not asserted.
