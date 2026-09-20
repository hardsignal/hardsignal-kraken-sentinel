# Draft 2 staged runner integration revision

Checkpoint: `5ffd273` (the full commit is recorded in each result). This is a new
association-consumer revision, separate from the historical experiment runner.
It consumes saved candidates, compact family artifacts and cardinality sidecars;
it has no capture, spectrum detection, cardinality recomputation or matrix API.
No scientific parameters or historical files were changed.

## New files and entrypoints

- `analysis/episode_component_tracking_v2_draft2_staged.py`: pinned-input request,
  staged consumer, explicit metric branches, provenance and reproduction API.
- `analysis/episode_component_tracking_v2_draft2_staged_queries.py`: exact local
  feasibility preflight for global episode queries.
- `analysis/validate_episode_component_tracking_v2_draft2_staged_e08.py`: fixed
  saved TPMS-008 E08-only validator and fresh-process reload/performance harness.
- `tests/test_episode_component_tracking_v2_draft2_staged.py`: integration tests.
- this document.
- `results/episode-component-tracking-v2-draft2-staged-e08-verified/`: final input
  manifest, connected result, three compact results, tests, validation and hashes.
- `results/episode-component-tracking-v2-draft2-staged-e08/`: exploratory evidence
  exposing the unoptimized late-group-query failure, including source snapshots.
- `results/episode-component-tracking-v2-draft2-staged-integrity.json`: final
  original-file preservation, output/source hash verification and Git checks.

The historical experiment script and all solver/counting/margin-1 artifacts are
read-only dependencies. The original runner is not patched or imported as a
full-run entrypoint. Its `association(..., 'connected')` function remains the
connected control; its expanded solver is used only by small-fixture tests.

## Explicit contract and independent states

The output format is `KRAKEN_DRAFT2_STAGED_ASSOCIATION_V1`. Representation is
mandatory and one of `CONNECTED_GROUPS_HISTORICAL_V1` and
`COMPACT_EXACT_FAMILY_V1`. No branch inspects a `hypotheses` sentinel or infers the
representation from missing fields. No expanded retained-hypothesis arrays are
present in staged results.

| Stage | Success | Failure / nonapplicability |
|---|---|---|
| Provenance validation | VERIFIED | REJECTED; no scientific payload. BYTE_BINDINGS_VERIFIED means reconstruction has not completed. |
| Family construction | COMPLETE, reconstructed saved family also matches supplied candidates | COMPUTATION_UNRESOLVED; or NOT_APPLICABLE_CONNECTED |
| Exact queries | EXACT, with membership/invariance/ambiguity sub-states | COMPUTATION_UNRESOLVED with reason; dependent association and metrics unavailable, never fabricated empty sets |
| Cardinality counting | EXACT, consumed from validated sidecar | COMPUTATION_UNRESOLVED with null value/reason; NOT_APPLICABLE_CONNECTED |
| Metric projection | COMPLETE | BLOCKED_BY_QUERY_FAILURE or COMPUTATION_UNRESOLVED with reason |

The output explicitly identifies sidecar consumption as
`CONSUMED_VALIDATED_SIDECAR_NO_RECOUNT`. An unresolved count neither invalidates
the complete predicate nor changes any successful query, status or primary.
Query failure leaves independent cardinality evidence intact. A metric failure
retains the exact association. Successful query sub-states can remain recorded
when a later query stage fails, but no incomplete association projection escapes.

Compact projection reproduces status, primary, maximum links, optimum binary64
cost, persistent paths, support/coverage, invariant and alternative membership,
per-candidate alternatives and zero structural violations implied by validated
constraints. It keeps the original fragment denominator and unusable/no-candidate
status precedence. Invariants need only be tested among paths in one verified
witness: an invariant must occur in that witness. All possible-path tests and
classification use the global episode family, not independent local margins.

Connected projection retains the historical connected groups, primary/status,
persistence and support fields. Hypothesis-specific fields remain explicitly
inapplicable/null where historically defined; no new path objective is invented
for connected groups. Structural metrics distinguish coherent connected-group
diagnostics from exact complete-partition constraints.

`fixture_metrics()` now branches explicitly on representation. Its formulae
match the historical implementation on fixtures. Real E08 has no fixture truth;
truth-dependent metrics are `NOT_APPLICABLE`, never fabricated. E08 query-derived
metrics include possible/invariant/alternative path counts, union link count,
persistent path count, coverage, original denominator and structural status.
The union link count is not the maximum-link objective: links in different
alternatives can all contribute to the union.

## Exact preflight and its validation

The initial staged run exposed a genuine search-order problem. At positive
margins, an impossible constraint in a later factor was tested only after
enumerating many completions in earlier factors. It hit the unchanged 200,000
exact-cover search-node limit. The initial integration correctly returned
COMPUTATION_UNRESOLVED queries and blocked metric projection, while preserving
EXACT cardinality and the complete family predicate.

The new query adapter first asks every constrained group whether its required
and forbidden paths admit a local retained completion. If any answer is no,
the episode answer must also be no. Required fixed singletons and forbidden
singletons retain their original semantics. Unknown required paths are impossible;
unknown forbidden paths impose no restriction. Results cache exact query answers.
Positive answers still call the unchanged episode `find` procedure and retain
its frozen global cost predicate. Local feasibility is never treated as sufficient.
Classification uses the frozen persistence/co-occurrence/ambiguity rules with
queries routed through this adapter. Query witnesses are not an expanded family
and are not used to derive cardinality.

Tests compare required pairs, required/forbidden combinations, possibility and
invariance against exhaustive complete partitions of disconnected competing
groups at every declared margin. In particular, locally feasible expensive paths
in separate groups still cannot each consume the whole global margin. Another
test proves that an impossible later-group singleton is rejected before the
global search begins. General multi-fragment performance is not established by
this optimization or by the favorable two-fragment E08 case.

The stage declares 5,000 public query calls and a 120-second query deadline.
The underlying 200,000 search-node and feasible-path limits remain unchanged.
POSIX deadlines raise an unresolved exception; they never supply a Boolean
answer. This prototype runs on the main thread of a worker process. A 150-second
outer subprocess timeout is an operational harness failure, not a successful or
partial scientific result. It causes the validation run to fail visibly.

## Provenance and deterministic reproduction

Every result embeds a pinned request with the exact saved-input byte hash,
canonical fragment-context hash, family path/byte SHA-256, cardinality sidecar
path/byte SHA-256, and experiment specification path/hash. The embedded model
SHA-256 is checked and recorded. Versions and SHA-256 values cover the solver,
both counting backends, sidecar schema, staged consumer, query adapter, historical
Draft 2 control and Draft 1 connected implementation. The counter/solver source
hashes in the sidecar must match the pinned implementation sources.

Source validation is followed by the committed sidecar validator and model
reconstruction. Rebuilding the episode from supplied saved candidates verifies
the original denominator, candidate identity/frequency/fragment fields and the
isolation of singleton IDs whose frequencies are not embedded in the episode
artifact. A different family, cross-paired sidecar, altered bytes/hash/model,
changed source or input context is rejected. Hashes establish identity and
provenance, not a proof for an arbitrary invented cardinality; the committed
counting certificate and validated sidecar are the counting evidence.

Git commit, dirty state and detailed status are frozen at batch start, recorded
and hashed. Current HEAD must still match. Newly created outputs do not rewrite
that historical batch context. Timing and memory observations are kept outside
the deterministic association artifacts. `reproduce()` rechecks pinned inputs,
source hashes and the checkpoint, recomputes all queries/metrics and compares
canonical bytes using the archived batch context. It does not claim that the
current dirty-file listing is unchanged since the batch began.

## Validation scope and readiness

**READY_FOR_LIMITED_MULTI_EPISODE_REGRESSION.** Final validation passed **70 tests,
zero failures, zero errors**: 16 staged tests plus 54 existing solver, counter,
sidecar and small-projection tests. The full historical experiment test suite was
not invoked because it contains a stored-spectrum detector test. No saved spectra
were processed here. Coverage includes all 13 declared deterministic association
fixtures at all three margins, ten additional seeded competing fixtures, connected
parity, exact/unresolved cardinality, separate construction/query/metric failures,
query call/time limits, unusable/no-candidate precedence, source/hash/cross-pair
rejection, byte-deterministic reload and historical-file preservation.

Only E08 is selected from committed candidate records; the detector,
spectrum loader, expanded-family materializer and counter are explicitly guarded
against calls in the real-data validation worker.

| Saved E08 case | Cardinality (consumed exact decimal) | Possible paths | Invariant | Alternative | First integration seconds | Reload seconds | First process peak KiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Connected | not applicable | 69 coherent groups | not applicable | not applicable | 0.0291 | 0.0417 | 94,176 |
| Margin 0 | 2 | 181 | 177 | 4 | 13.9837 | 14.2472 | 94,656 |
| Margin 0.25 | 17,067,800,502,243 | 441 | 86 | 355 | 26.4022 | 27.9856 | 94,648 |
| Margin 1 | 378,038,954,451,765,697,490 | 666 | 69 | 597 | 36.7313 | 36.3704 | 94,836 |

Every compact case has VERIFIED provenance, COMPLETE family reconstruction,
EXACT queries/cardinality and COMPLETE metric projection. Each made 840 public
query calls. All have 227 eligible candidates, the original two-fragment
denominator, 48 maximum links, optimum binary64 cost `4.016886693701919`, no
persistent path, `AMBIGUOUS_ASSOCIATION`, and primary null. Status, primary,
objectives and persistence agree with the committed exact-solver benchmark.
The connected projection agrees with the complete stored connected association.
Exact decimal strings and family/model/sidecar binding match the committed
margin-1 investigation sidecars. All four result artifacts reload and reproduce
byte-for-byte in separate processes.

Historical expanded E08 path results never completed; there is no complete old
expanded result against which to claim E08 path-union parity. Full field parity
is established exhaustively on the small fixtures; E08 compares the previously
validated compact status/objectives/cardinality, and obtains new path-union and
invariance projections by exact queries. Structural validity follows from model
reconstruction and complete disjoint-partition constraints, not from sampling.

Timing covers integration (hash checks, family reconstruction, exact queries and
metric projection) after Python imports, manifest loading and saved E08 input
selection. Reload timing also includes provenance reproduction checks and result
comparison. Memory is Linux `/proc/self/status` VmHWM for the current process,
including imports and reading/parsing the entire committed candidate JSON before
selecting E08. The approximately 92–93 MiB high-water mark is already reached
during that input loading, so it is not an incremental query-memory estimate.
Final resident memory was approximately 67–73 MiB. These are local observations;
no full-matrix time or memory inference is made.

The first exploratory run's 68 tests passed, but positive-margin E08 projections
were unresolved. Margin 0.25 failed during membership call 150 (a required edge
in factor 2); margin 1 failed at call 125 (an impossible singleton in factor 1).
Those files are preserved as failure-semantics evidence. Their archived source
snapshots match their original hashes; their old live-source pins are intentionally
superseded by the final implementation. The final verified directory is the
authoritative result of this revision. No protected pre-existing artifact was
rewritten to erase or amend the earlier investigation evidence.

The expanded-array output contract remains an explicit schema substitution in
this separate revision. It does not retroactively alter the original Draft 2
experiment specification or make old array-consuming software compatible.
The next regression must use a small predeclared saved-candidate episode set,
covering varying fragment counts, crossing/competition, isolated candidates and
query resource limits. It must retain these separate failure states and compare
small cases exhaustively. No full-matrix runtime forecast is justified by E08.

Outstanding limits are general multi-fragment cost/search complexity, feasible
path/union size, main-thread POSIX deadline portability, and production consumers
outside this staged association interface. Unknown failures are not silently
converted into scientific results. No remaining unresolved stage occurs in the
final E08 run. This is sufficient for a bounded, predeclared multi-episode
regression; it is not readiness for the full 160-arm matrix.

All **274 pre-existing tracked files** remain byte-identical to session entry.
Final integrity verification checks the result manifests, pinned sources and
inputs, archived exploratory source snapshots, and source whitespace. HEAD is
unchanged at `5ffd273`; Git status contains only new untracked integration files
and results. `git diff --check` passes and there is no tracked diff.

Reproduce with a NEW output directory:

```sh
python analysis/validate_episode_component_tracking_v2_draft2_staged_e08.py --output /tmp/kraken-staged-e08-new
```

No capture, spectrum detection, full 160-arm matrix, scientific-parameter change,
commit or push was performed. No device-identification or discrimination claim.
