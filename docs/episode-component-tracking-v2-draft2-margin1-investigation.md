# Draft 2 margin-1 counting and sidecar integration investigation

Checkpoint: `e398495`. Saved TPMS-008 E08 only. No captures, 160-arm rerun,
scientific parameter changes, production-runner changes, commit, or push.

**Margin-1 exact cardinality completes:** failed group
**9,651,994,153,789,972**; whole E08 **378,038,954,451,765,697,490**.
These are integers, not estimates or lower bounds. No retained hypothesis list
was expanded for these counts. Forward and reverse frequency column orderings
agree in both scopes. Episode composition uses one global margin.

## Provenance and files

At the start of this investigation the worktree already contained untracked
column-counter, sidecar, benchmark, test files and a column-count result directory.
Those files were treated as existing input, not newly authored here, and were
preserved byte for byte. Their reported results were independently rerun.

New files authored in this session:

- `analysis/episode_component_tracking_v2_draft2_compact_consumer_prototype.py`
- `analysis/benchmark_episode_component_tracking_v2_draft2_margin1_investigation.py`
- `analysis/measure_episode_component_tracking_v2_draft2_margin1_memory.py`
- `tests/test_episode_component_tracking_v2_draft2_margin1_investigation.py`
- this document
- `results/episode-component-tracking-v2-draft2-margin1-investigation/benchmark.json`
- `results/episode-component-tracking-v2-draft2-margin1-investigation/tests.txt`
- eleven `*.cardinality.json` sidecars and `files.sha256` in that directory
- `results/episode-component-tracking-v2-draft2-margin1-memory.json`
- `results/episode-component-tracking-v2-draft2-margin1-integrity.json`

The reused untracked implementation is
`analysis/episode_component_tracking_v2_draft2_column_count.py`, with sidecar
implementation `analysis/episode_component_tracking_v2_draft2_cardinality_sidecar.py`.
All benchmark sidecars bind their implementation, committed solver/counter,
audit runner, consumer prototype, and validation test sources by SHA-256.

## Exact method and evaluation of alternatives

| Requested avenue | Finding and evidence |
|---|---|
| Decision DAG / variable ordering | Switch from processing rows with occupied-column masks to processing columns with saturated-row masks. Forward and reverse frequency orderings both complete. Arbitrary permutations agree with exhaustive histograms on small instances. This change is restricted to the certified integer backend; the frozen IEEE fallback ordering is unchanged. |
| Separators / connected components | Reuse exact connected-component factorization after removing only edges whose nonnegative reduced cost exceeds the full margin. Expiring rows form the frontier separator. The failed group splits into 8-, 1-, and 9-row blocks at margin 0.25, but is one 18-row, 55-column block at margin 1; connected components alone do not solve the latter. No unmeasured general-purpose separator algorithm is claimed. |
| Tighter suffix bounds | For each unmatched row, take its minimum cost over remaining columns and sum. Ignoring competition and unused-column penalties makes this a lower bound. Reject only polynomial degrees that cannot complete within the cutoff. The bound-on run completes; bound-off exhausts packed storage at column 13. A more expensive residual Hungarian bound was unnecessary and was not benchmarked. |
| Matching-specific decomposition | The unchanged certificate restricts this backend to two-layer matchings saturating the smaller side. The integer Hungarian dual converts excess cost into nonnegative selected-edge costs and unmatched-column penalties. Every matching uniquely determines all remaining singletons. |
| Lossless cost-state compression | The committed lattice certificate proves agreement with the frozen binary64 acceptance predicate. GCD division is exact. Packed integer polynomial digits have width strictly exceeding a bound on every coefficient, so merging and shifting cannot cause carries between costs. No approximate cost binning. |
| Generating functions / factorization | A coefficient is the number of assignments at an exact excess cost. Independent block and episode factors use exact polynomial convolution with a global truncation cutoff, not multiplication of local retained counts. |
| Permanent / matching counting | The column recurrence is a weighted rectangular permanent computation: each column is unused or assigned to exactly one still-unmatched row. It avoids square padding and artificial dummy-row permutations. Closed-form complete rectangular matching counts validate identity multiplicity. Generic Ryser inclusion-exclusion was considered but not implemented: it would still require weighted polynomial arithmetic and careful rectangular unmatched penalties, while the measured frontier method already completes. |

The family-to-matching bijection keeps candidate identities. Each column decision
is unique for a given assignment; it does not label or permute paths. A row may
be forgotten only after its last available column and only if saturated. Forgotten
identities cannot affect any future constraint. The generating function retains
the multiplicity of distinct assignments even when they share a cost and mask.

For the carry bound, each partial matching gives each row either no column or one
of its original incident columns. Therefore the total number of partial row
assignments, and hence each coefficient, is at most `product(degree(row)+1)`.
The chosen radix exceeds this bound. Exact integer addition and bit shifts thus
implement coefficient addition and multiplication by a monomial without carries.

The original arithmetic certificate remains authoritative: quantum
`2500/119311929`, margin-1 excess cutoff `47724`, with coefficient-error and
binary64 rounding envelopes separated from the adjacent acceptance shells.
It preserves maximum links, the tolerance, prefix comparisons, emitted-cost
folding and global episode composition. A failed certificate invokes the
committed IEEE backend. No scientific frequency, tolerance or margin changes.

## Validation and measurements

**72 tests passed, zero failures/errors**, before the fresh E08 runs. This includes
the committed solver, counter and experiment test suites, the existing untracked
column/sidecar tests, and four new investigation tests. New coverage includes:

- 120 seeded weighted rectangular graphs: exhaustive assignment histograms versus
  arbitrary column permutations, both suffix-bound settings and the committed
  row counter; infeasible/empty rows and unused penalties included;
- complete equal-cost 4-by-8, 10-by-12 and 12-by-12 matchings against `n!/(n-m)!`;
- seven small episode fixtures at all three declared margins, comparing count,
  status, primary, objectives, path union/invariants, persistence, candidate
  alternatives, coverage, structural validity and downstream fixture metrics;
- exact/unresolved sidecar projections with identical non-cardinality outputs;
  explicit failure if a test consumer calls `Family.materialize()`;
- additional rejection of changed definition, noncanonical margin, path escape,
  missing limits and missing runtime statistics.

All runs declare the same limits as the committed counter: **250,000 live
container states, 5,000,000 counted transitions, 60 seconds, 33,554,432 packed
polynomial bytes**. No extra resource allowance is used.

| Scope / method, margin 1 | Result | Count seconds | Peak state containers | Transitions |
|---|---|---:|---:|---:|
| Group, committed row counter | COMPUTATION_UNRESOLVED | 0.0881 to stop | 251,135 | 433,774 |
| Group, columns + suffix bound | 9,651,994,153,789,972 | 0.3632 | 254 | 23,146 |
| Group, reversed columns + bound | same exact integer | 0.3805 | 250 | 23,058 |
| Group, columns without bound | COMPUTATION_UNRESOLVED | 0.1741 to stop | 320 | 6,414 |
| Episode, committed row counter | COMPUTATION_UNRESOLVED | 0.3247 to stop | 251,135 | 1,944,070 |
| Episode, columns + bound | 378,038,954,451,765,697,490 | 1.1616 | 73,406 | 25,441 |
| Episode, reversed columns + bound | same exact integer | 1.2017 | 73,406 | 25,196 |

State and transition counts are **not equal-work units across algorithms**. The
old counter stores `(mask,cost)` dictionary entries. The new counter stores one
packed polynomial per mask and performs many exact coefficient operations in
one integer operation. Episode convolution statistics count histogram entries;
73,406 is not the number of simultaneous matching masks. This is a measured
representation/ordering/bound improvement, not a speed ratio inferred from an
early unsuccessful run. Runtime and packed bytes provide additional evidence.

The hard block uses 10-byte coefficient digits, 11,867 final nonzero coefficients,
and peaks at **20,584,913 live packed bytes** (reverse: 20,752,271). Without the
suffix bound it requires **37,299,200 bytes** at column 13, exceeding 33,554,432.
The committed counter fails after row 5: 39,964 prior plus 211,171 next states,
with 52 future columns. Failure sidecars have null cardinality, never a partial
exact count. Limits are checked at algorithm checkpoints, not OS hard caps;
temporary arithmetic objects and dictionary/interpreter memory exceed packed
payload accounting. Transitions do not measure bit-operation work.

The first audit children all reported `ru_maxrss=77412 KiB`: fork/exec preserved
a high-water floor from the validation parent. Although each case is a fresh
process, that field is not an isolated memory estimate. The supplemental memory
probe corrects that interpretation using Linux `/proc/self/status` VmHWM from a
small parent. It includes loading, counting and sidecar query verification:

| Case | Post-exec process peak KiB |
|---|---:|
| Group committed counter, unresolved | 44,824 |
| Group column counter, exact | 45,772 |
| Episode committed counter, unresolved | 52,248 |
| Episode column counter, exact | 47,472 |

Initial resident memory in these probes was about 20,800 KiB. These are process
peaks, not incremental algorithm allocations. Margin-zero controls returned 1
and 2; margin-0.25 controls returned 191,532,581,516 and 17,067,800,502,243.

## Sidecar validation and consumer integration

**The sidecar prototype is validated.** Each audit sidecar uses
`KRAKEN_DRAFT2_RETAINED_CARDINALITY_V1` and binds the repository-relative family
path, actual family byte SHA-256, embedded model SHA-256, scope, canonical
binary64 margin hex, counting-definition version, arithmetic policy, source
hashes, limits and runtime/state statistics. Loading reconstructs and validates
the embedded frozen model. The caller must supply the expected family path.

EXACT requires an arbitrary-precision canonical decimal string and no failure.
COMPUTATION_UNRESOLVED requires null value and an explicit reason. Tests reject
a different family path even with identical bytes, changed bytes/hash/model,
scope, margin, arithmetic policy, definition and changed source. An unresolved
sidecar leaves membership, invariance and ambiguity unchanged. Exact sidecars
need no expanded hypothesis array. Hash binding verifies identity/provenance;
it does not independently prove an arbitrary asserted count. That assurance
comes from the counting proof, tests and reproducible benchmark.

The new consumer prototype is separate from the runner. It validates an episode
sidecar and uses global episode `possible`, `invariant` and `classify` queries
to derive the old non-expanded output fields. It enumerates feasible paths,
not retained hypotheses, and propagates query-limit exceptions. It handles the
caller-owned unusable-spectrum status explicitly. Small-fixture parity is proven;
full E08 path-union projection and all-arm performance have not been benchmarked.

Before a new full-runner revision can use these artifacts:

1. Adopt an explicit versioned representation discriminator and family/sidecar
   references. Preserve connected-arm behavior. Serialize decimal counts as
   strings; consumers must not coerce these values to binary64/JavaScript Number.
2. Separate family construction, exact queries, cardinality state and metric
   computation. A count timeout must not discard a complete predicate or claim
   unique association. Conversely a query timeout must not silently become an
   empty union or a false invariant. Define per-operation failure states.
3. Replace the `fixture_metrics()` `hypotheses is None` connected-group sentinel
   with an explicit representation branch. Obtain path unions, support/coverage,
   persistence, alternatives, and co-occurrence from global episode queries.
   Preserve unusable/no-candidate precedence, original fragment denominator,
   candidate identity/truth joins, and the frozen abstention/primary rules.
4. Validate structure from reconstructed constraints; record why zero structural
   violations follows for all represented partitions without iterating them.
   Add end-to-end schema/metric parity tests on tractable saved and fixture cases.
5. Update reporting, manifest/source hashes, cache keys and reload validation to
   include solver/counter/schema versions and both artifact hashes. Preserve
   historical artifacts and create a separately named revision/results tree.
6. Establish limits and behavior for general multi-fragment IEEE fallback,
   feasible-path size and expensive global query projections. E08 only validates
   the favorable certified two-layer counting case at scale, not all 160 arms.

**Original output requirement still outstanding:** the historical literal
`hypotheses` array (with each partition and its emitted cost) is not emitted by
compact families plus a cardinality sidecar. Its information is represented by
the exact predicate and frozen cost procedure, but this is an explicit schema
substitution, not compliance with an unchanged expanded-array contract. All
other derived association fields have a demonstrated small-case query projection;
cardinality alone does not supply them, and global performance remains unproven.

**Readiness:** the E08 counting blocker is resolved, and the evidence supports
starting a staged, separate runner-integration revision. It is **not yet a
validated full-runner replacement or ready for the 160-arm rerun**: schema adoption,
consumer migration and end-to-end/multi-fragment validation remain. No production
integration was performed here.

## Reproduction and integrity

Run the audit with an unused output directory:

```sh
python analysis/benchmark_episode_component_tracking_v2_draft2_margin1_investigation.py --output /tmp/kraken-margin1-new-audit
python analysis/measure_episode_component_tracking_v2_draft2_margin1_memory.py --output /tmp/kraken-margin1-new-memory.json
```

The audit hashes all pre-existing tracked and untracked nonignored files and
checks their bytes after counting. The final integrity record independently
compares all 253 files present at session entry, validates the eleven new
sidecars and their source hashes, checks the result manifest, and records
`git status --short`, unchanged HEAD, no tracked diff, and `git diff --check`.
All changes are new untracked files. No device-identification or discrimination
claim follows from these computational results.
