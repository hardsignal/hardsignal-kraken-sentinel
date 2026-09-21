# Draft 2 full-matrix computational feasibility review

Decision: **COMPUTATIONAL_BLOCKERS_REMAIN**.

Review checkpoint: `6bd63ac90b9045ecb2eac3544ee63b035103428b`, branch
`codex/draft2-matrix-feasibility-review`. This review creates no scientific outcomes
and authorizes no execution. The corrected six-capture gate is valid evidence for
native/200 saved candidates, not evidence that the full matrix entrypoint has been
converted to the corrected stack.

The immediate launch blocker is integration: the frozen experiment's `run()` still
calls its historical expanded `association()` implementation for fixtures and real
arms. It does not call the corrected counter, sidecar consumer or exact-query
adapter. The corrected runner pins only native/200 saved candidates, forbids
detection, and uses historical case parity checks. It cannot simply be pointed at
all 160 configurations. A separately authorized, versioned matrix orchestrator and
compact-output/gate adapter need implementation and review; historical files must
remain preserved. This is not a request to increase any limit.

The other material gaps are unmeasured candidate structures for 39 representation/
width combinations and the never-executed full spectral fixture workload. No
specific corrected-stack arm is proven to exceed a frozen limit. Absence of such
proof is not a guarantee of completion.

## Exact dispatch and conditions

Source entry: `analysis/regress_episode_component_tracking_v2_draft2_six_capture_corrected.py`,
`count_exact()`. This composes the following implementations for every compact
case, without examining a capture, episode, device, or expected answer:

1. `repl_e03_margin1_count_v3.count()` attempts a certified short-path matching
   polynomial. There must be factors and a positive margin. Every directed graph
   path must have at most three candidates; every edge-incidence matching block
   must have a uniform gap penalty. Residual integer weights must be nonnegative.
   Dummy columns complete deficient matchings and their factorial multiplicity
   must divide each coefficient exactly. Maximum-link decomposition and the frozen
   optimum witness must agree. The proposed rational cost lattice has authority
   only after its coefficient/rounding envelope strictly separates both adjacent
   acceptance shells, including tolerance and frozen prefix comparisons. Counts
   use column histograms, exact assignment duals and exact polynomial products.
2. If that certificate is unavailable, V3 calls V2's forced-singleton, drained
   IEEE frontier. Its histogram hook wraps the dyadic matching adapter, which
   converts actual binary64 edges via `as_integer_ratio()` to an exact common
   power-of-two denominator. This is a matching-bound optimization, not a separate
   approximate count and not an E02 identity test. It preserves rational bounds,
   traversal/ties and restores solver methods in `finally`.
3. Inside that fallback, `e02_margin1_count.count()` first attempts the older
   lattice certificate: every factor must be a two-layer matching saturating its
   smaller side, with paths of at most two nodes and a certified optimum and
   acceptance envelope. Zero margin requires the special exact-addition proof
   where applicable. Success selects `column_count.count()`; failure selects
   exact local IEEE histograms and global monotone-pivot composition. No factors
   means the single fixed-singleton partition. A group-only input needs no episode
   composition. Unique-gap/zero-link certificates can avoid frontier expansion.
4. V2 removes consumed IEEE states and contracts forced zero-cost singleton
   prefixes without changing acceptance. Monotone binary64 addition preimages
   preserve the chronological episode fold and every prefix predicate. Histogram
   size selects the pivot, not an identifier.
5. `count_exact()` installs the E05 cumulative-multiplicity composition for all
   fallback episode compositions. It selects binary-search cutoff mode precisely
   when `len(caps) * max(1, len(pivot_costs).bit_length()) < len(pivot_costs)`;
   otherwise it uses the exact streaming pivot join. Multiplicities remain
   arbitrary-precision integers. “E05” is historical module naming.
6. Every compact integration uses `repl_e03_exact_queries.integrate()`, which pins
   engine version, hash, ordering and limits. Candidate-cover disjunction rewrites
   forbidden-path queries into exact alternatives through a least-incidence
   candidate. Local preflight can reject, but all positive answers require the
   global episode predicate. Overlap, singleton, cache and required/forbidden
   checks are structural. The same cumulative 200,000 search-node limit applies;
   internal branches do not receive fresh budgets. Public calls are separately
   capped at 5,000 and query-stage wall time at 120 seconds.
7. Connected association uses the historical connected projection explicitly;
   family counting and compact query stages are not applicable. Sidecars validate
   family/model/input/source hashes, arithmetic policy, scope, margin and schema.
   A sidecar binding check is not an independent proof of its numerical count.
   Exact counting certificates and tests supply that separate evidence.

V3 catches certificate-construction unavailability and `CountUnresolved` to enter
fallback with the same budget; failures during certified counting propagate.
Other budget/search/deadline failures produce explicit unresolved stages, null
counts where relevant, and blocked dependent projections. There is no approximate
answer, automatic budget increase or implied primary on failure. A future runner
must enforce wall time and RSS outside all certificate/family work as well.

Inspection covered the actual production functions, not just filenames. Candidate
IDs occur as inventory keys, deterministic ordering and witness membership, never
as equality tests selecting a special count algorithm. The corrected runner's
`original_parity()`, `limited_parity()` and mandatory-control tables do contain
named cases and expected counts; those validate output after general dispatch.
They must not be mistaken for solver dispatch. The exhaustive small-fixture,
permutation/reverse-order, boundary and budget tests corroborate this distinction.

## Matrix structure and risk rules

The committed `arms.json` and `experiment.arms()` define exactly 5 representations
× 8 widths × 4 associations. Representations are native and 2.5 Hz grid envelopes
with sigma 0, 5, 10, 20 Hz. Widths are 200, 225, 250, 275, 300, 325, 350 Hz and
unlimited. Associations are connected and paths at margins 0, 0.25, 1.

At fixed representation, increasing width admits previously rejected components;
it cannot remove already eligible ones. It can introduce graph bridges, merge
factors, increase feasible paths and destroy cheap uniqueness certificates.
Native/200 reported 135 width rejections across 210 fragments; this does not say
how many newly admitted candidates connect or how difficult their families are.
Rebinning/smoothing can merge or split detected runs, move peaks across edge
thresholds, change width eligibility and change the frequency lattice. Neither
smoothing nor a smaller candidate count proves easier counting. Grid frequencies
may yield simpler rational weights, but shell alignment or mixed gap penalties
can still reject a certificate. No spectra were processed for this review.

With fixed candidates, margins share graph/path structure but change retained
families, cost histograms and polynomial support. Computational time need not be
monotone in margin: positive-margin V3 may be easier than zero-margin IEEE.
Frontier complexity depends on active matching width and residual masks, not just
candidate count. Whole-path range rejection may defeat matching relaxation for
longer paths. Polynomial allocation uses `(degree_a + degree_b + 1) * digit_bytes`,
where digit width depends on the product of coefficient sums; the pre-truncation
product can exceed 32 MiB even with few sparse entries. Packed storage is not RSS.

Predeclared structural checks for a future authorized run should record candidates
per fragment/factor, edges, factor sizes, directed depth, feasible paths, active
column frontier width, gap-penalty uniformity, matching deficiency, lattice and
shell separation, histogram support and packed-product estimate. Do not use
association status, primary, truth labels or count targets for risk selection.
A completed staged membership pass makes one public call per factor path plus
witness/membership, invariance and classification calls. More than 4,997 factor
paths already precludes completion under 5,000 calls even before invariance.
No changed arm's path count can be derived from configuration metadata alone.

The manifest assigns risks conservatively before any new scientific execution:

| Category | Arms | Basis |
| --- | ---: | --- |
| LOW_COMPUTATIONAL_RISK | 1 | Completed native/200 connected control |
| MODERATE_COMPUTATIONAL_RISK | 42 | 3 demonstrated compact native/200 arms; 39 unmeasured connected arms without partition combinatorics |
| HIGH_COMPUTATIONAL_RISK | 0 | No available changed-arm graph establishes likely corrected-budget exceedance |
| UNKNOWN_WITHOUT_EXECUTION | 117 | Other path arms lack candidate graphs and certificate evidence |

Moderate connected risk includes unmeasured spectral time/storage; it is not a
claim of completed end-to-end execution. Unknown is not low risk. No arm may be
removed or scientifically ranked using these labels. Expected routes for unknown
path arms are conditional dispatch chains, not assigned successful certificates.
The machine-readable manifest includes all 160 original IDs and settings.

## Historical failures and current coverage

The original run completed native/200 connected, then stopped in native/200
margin-0 at E08: 73 candidates, 412 paths, 200,001 DP states against 200,000.
Its preceding 26 episode outputs are partial; 158 remaining arms were NOT_RUN.
The 100,800 spectral fixtures were not started. Across 40 spectral settings that
is 4,032,000 fixture/setting evaluations, not a workload exercised by this review.

All 113 association fixtures ran at four settings historically. Path arms had
10/100 noise false primaries and eight retained crossing/competing identity-switch
links at every margin, versus 1/100 and zero for connected. No forced primary
occurred in the crossing/competing fixtures. These are frozen synthetic behavior
records, not computational failures or device-identification evidence. Correct
exact execution does not remove these outcomes or establish scientific quality.
No scientific gate is re-evaluated here.

Superseded computational bottlenecks include expanded partition DP/materialization,
the TPMS-004 E02 margin-1 count composition, REPL E02 rational matching overhead,
REPL E03 IEEE state explosion and forbidden-path searches, and REPL E05's
5,000,001-transition join. The earlier E03 margin-1 frontier reached 250,001 states;
V1/V2 frontier changes alone did not establish that case's completion. V3 supplies
its certified route. The original E02 timeout, search failures and E05 join remain
valid historical evidence, but are not failures of the corrected regression.

The corrected result has 164/164 complete cases, 123/123 exact compact counts,
zero unresolved counts/queries and zero reproduction failures. Mandatory counts
are 5,788,836 (TPMS-004 E02/1), 217,075 (REPL E02/1), 349,149 and 378,536,340
(REPL E03/0.25 and /1), and 697,122 (REPL E05/1). E08 has 2, 17,067,800,502,243,
and 378,038,954,451,765,697,490 at the three margins.

The JSON review inventories every one of the 123 saved families, its structural
factor shapes, exact route, certificate rejection and cutoff selection. Counts
of unique factors from margin-0 artifacts (each episode once) are:

| Occupied layers / maximum feasible path nodes | Factors | Handling |
| --- | ---: | --- |
| 2 / 2 | 123 | V3 when whole episode certifies; otherwise certified two-layer column or exact IEEE fallback |
| 3 / 3 | 38 | V3 if uniform blocks and shell proof pass; otherwise IEEE fallback |
| 4 / 4 | 9 | V3 ineligible; exact IEEE fallback with dyadic matching bounds |
| 3 / 2 | 1 | Conditional incidence-block V3, otherwise IEEE fallback |

Isolated singletons and empty/factorless families use fixed partitions; one-fragment
and two-fragment episodes preserve their original persistence denominators.
Multi-factor episodes always retain one global cost allowance. All compact types
use the same exact query engine. Connected graphs use historical projection.
The seven-episode limited regression and completed/partial original real results
are native/200 subsets of these same candidate inputs; their former unresolved
E02/E08 structures are covered by corrected results. Synthetic original fixtures
include crossings, competitors, missing fragments, range/coverage boundaries,
noise, and singleton/short episodes: bounded unit tests establish small-fixture
exact parity, but the entire historical fixture output pipeline has not been
rerun with a new full-matrix compact adapter.

Across corrected compact cases, V3 handled 52 and fallback handled 71. V3 rejection
reasons were zero-margin/factorless (43), directed paths longer than three (16),
and mixed block gap penalties (12). Largest recorded factor: 73 candidates;
largest factor path inventory: 671; largest episode factor-path inventory: 835.
These are observed sizes, not safe universal thresholds. The older column route
has existing solver tests/earlier E08 evidence; V3 supersedes positive-margin E08
in the corrected composition.

Not demonstrated on all matrix configurations: newly bridged/dense factors,
longer directed chains or range-constrained covers, mixed-penalty incidence blocks,
nonseparated cost shells, large matching deficiency/frontier width, large binary64
histograms or query disjunction trees. These are supported by exact fallback in
principle where applicable, but bounded completion is unknown. Path generation
still has a 200,000-path cap and search retains its 200,000-node cap. Certificate
failure, state/transition/time/packed-byte exhaustion, query-call/search exhaustion,
RSS/worker deadlines, storage failure and provenance rejection remain possible.

## Resource envelope and tests

All maxima below were independently recomputed from the 164 committed case records
and agree exactly with the corrected summary. Times are historical measurements,
not performance measurements of a new scientific run.

| Measurement | Observed maximum | Frozen limit | Percentage |
| --- | ---: | ---: | ---: |
| Count seconds | 2.628796587 | 60 | 4.3813% |
| Full case seconds, execution plus reload | 70.868468542 | 400 per worker | 17.7171%* |
| Public query calls | 1,110 | 5,000 | 22.2000% |
| Count transitions | 63,978 | 5,000,000 | 1.2796% |
| Count live states | 74,064 | 250,000 | 29.6256% |
| Packed polynomial bytes | 20,584,913 | 33,554,432 | 61.3478% |
| Observed worker RSS KiB | 152,060 | 524,288 | 29.0031% |

*The full-case sum has no separately frozen aggregate deadline; this is a
conservative comparison to one worker's ceiling, not a change in enforcement.
Execution and reload are separate workers. Family construction remains 60 seconds,
query stage 120 seconds. Internal search calls differ from public query calls.
RSS includes allocations not represented in the packed-polynomial metric.

Command: `python -B -m unittest discover -s tests -p 'test_episode_component_tracking_v2*.py' -v`.
All 187 existing test invocations passed in 26.754 seconds: zero failures/errors.
This covers Draft 1 control tests, original Draft 2 unit fixtures, exact solver,
counting/column/pivot/dyadic/V1/V2/V3/cutoff, query, staged, sidecar, limited and
six-capture regression tests. Imported TestCase classes can create repeated test
invocations; this is the runner's count, not a claim of 187 distinct scenarios.
The review JSON preserves the complete test log. New review-only consistency tests
check manifest completeness, source integrity, resource maxima and saved-family
coverage without detection or solving. All five passed (zero failures/errors); their log is preserved in the JSON.

## Future authorized execution control

First implement and review the new matrix integration without altering historical
sources or scientific settings. Pin the corrected dispatch and query engine
explicitly; bare `staged.integrate()` still defaults to the older query adapter.
Validate compact outputs, fixture metrics and gate consumers without expanding
astronomical families. Freeze all source/specification/input hashes, environment,
RNG policy, matrix order and computational limits before execution.

Use committed arm order: representation, width, association as in `arms.json`;
within each arm, fixed capture/episode order and deterministic candidate ordering.
Perform integrity and unit gates, bounded saved controls, then the predeclared
association fixtures, real matrix and spectral fixture stages. No silent change
of the original stop-on-first-unresolved policy. Checkpoint atomically after each
episode's family/count/query/reload stages and each completed arm; use predetermined
spectral batches (for example 100 fixtures) so restart never depends on outcomes.
Only validated stage hashes mark completion. Keep partials, stderr, exception,
resource location and limit, certificates and failed requests in unique directories.
Never label a partial arm complete or recompute it under larger limits.

Resume must verify identical source, input, spec, limits, configuration and prior
checkpoint hashes. It must skip only complete validated work. Distinguish a crash
from declared computation-unresolved: the latter stops the experiment for review,
with subsequent rows explicitly NOT_RUN. Crash restarts need an explicit recorded
policy and attempt directory; no silent retries. Count failure and query failure
remain independent states, with dependent metrics blocked rather than fabricated.
Preserve the original denominator and global margin through every restart.

Recommend **one worker initially**, with **at most two isolated processes** only
after serial controls pass and host resources are measured. Two workers can consume
1 GiB at their 512 MiB ceilings, plus parent, OS, inputs and filesystem-cache
headroom; observed 149 MiB usage is not a reservation target. Require two available
CPU cores and separate output directories. Module-level temporary patches and
POSIX timers make same-process threads unsafe. Wall-clock limits are immutable and
contention can change completion. Safest first launch stays serial to preserve
stop-on-first-failure semantics. A later two-worker policy must predeclare ordered
publication and retain/cancel speculative later-arm work without publishing it as
a completed post-failure arm. Do not parallelize a single mutable family or share
query caches. This recommendation does not start workers.

## Integrity

Before review, SHA-256 was recorded for all 3,068 tracked files with HEAD/branch;
the complete baseline is embedded in the review JSON. Final verification requires
all those files byte-identical, unchanged HEAD/branch and tracked inventory, clean
`git diff --check`, and independent LF/trailing-whitespace checks on the four new
review files. The JSON records the final checks and historical bundle hash audit. All 2,594
present entries in the four historical bundle manifests match their recorded hashes.
There are 712 absent `.log` entries (56 limited, 328 original six-capture, 328
corrected six-capture); these are not tracked files and were absent in this checkout.
Their historical bytes cannot be reverified here. No log was recreated or changed.
Only the new report, review JSON, risk manifest and review tests are untracked.
No historical experiment was overwritten, no matrix/detection/capture was run,
no scientific parameter or computational limit changed, and no commit/push occurred.
