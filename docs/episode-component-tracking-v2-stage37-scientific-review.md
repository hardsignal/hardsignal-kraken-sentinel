# Stage 37A independent scientific evidence review

Decision: **STAGE37_SCIENTIFIC_EVIDENCE_REVIEW_COMPLETE**

This review describes the frozen Stage 36 real-data matrix. It selects no configuration, assigns no scientific quality score or ranking, changes no threshold or semantic rule, and reruns no arm. Runtime and memory are not scientific quality measures here. V1 measures dominant non-DC FFT-bin / fragment behavior, not carrier identity or device fingerprinting.

## Provenance and integrity

The review starts at `0df44abb54231d5e8bfe84fe316ebbcf10d3130c` on `codex/stage37-scientific-review`. The Stage 36 audit separately records execution commit `e559d63e3a88822ff5443d5a83d0ad60fc3e3348`; these are different provenance roles, not a mismatch.

**Direct observation.** The committed audit and independently counted canonical identities agree: 160/160 accounted, 152 COMPLETE, eight COMPUTATION_UNRESOLVED, zero duplicates, zero missing. Native has 24 complete and eight unresolved arms; each grid representation has 32 complete arms. All **46,524 files / 8,286,982,589 bytes** listed in the committed Stage 36 SHA-256 inventory were streamed read-only and matched. All 160 selected receipt hashes match the audit; every receipt file entry agrees with the inventory. Plan and canonical-manifest digests match the audit and receipts. Referenced six-capture input files match their saved hashes. Review source/evidence bindings match bytes at the frozen checkpoint. **No raw-evidence hash mismatch was found. An inherited source-inventory mismatch was found during existing-test validation; see below.**

The external raw root is `/home/maciejduranczyk/hardsignal-kraken-sentinel/results/episode-component-tracking-v2-draft2-full-matrix-exact-v1`. No raw file was written, regenerated, renamed or removed. The hash inventory includes smoke/batch material; only the audit's 160 canonical arm/batch pairs enter scientific accounting. Every complete `arm.json` association and metric projection was cross-checked against its per-episode `result.json`. The audit's aggregate receipt-set digest is preserved as recorded; its custom aggregation algorithm was not independently reconstructed. Its 160 constituent receipt hashes were independently verified.

The older launch plan's `.gitignore` hash is `24459e7feded9172d32c80b041c4ef76fe903f720037559a0f44ff3e82ea0d7a`; the frozen review checkpoint contains `3bea5d21bee9a0982907fab3c62f8a873010c8e5d8e4722722a967ba103439ba`. Commit `0df44ab` added the raw-output ignore entry after execution. All 3,081 plan-bound files match the execution commit after applying the explicit V2 runner binding; at the review checkpoint only `.gitignore` differs from those effective bindings. Nine existing tests reject that inherited mismatch. It was reported immediately on discovery and remains unrepaired: frozen files and tests were not relaxed. Scientific interpretation can proceed from verified saved evidence, but a clean legacy provenance-suite result cannot be claimed. All nine saved batch contexts record the execution commit and a dirty flag; every recorded dirty entry is an untracked file under the Stage36 raw root, with no tracked/source modification listed.

The accompanying JSON records evidence hashes, receipts, all 160 states, complete per-arm and per-episode projections, a capture/episode catalog, factor aggregates, matched comparisons, spectral diagnostics, anomaly records and historical negative fixtures. JSON `width_hz: null` means unlimited; the width aggregate key `None` has the same meaning.

## Scope, denominators and semantics

**Direct observation.** Each complete arm contains the same six captures, 41 episodes and 210 original fragments: 6 episodes from PIPELINE-TPMS-004, 5 from 005, 8 each from 007 and 008, 7 BETWEEN-DEVICE and 7 BETWEEN-DEVICE-REPL. Thus complete arms provide 6,232 episode-arm observations, not 6,232 independent episodes. The representation/width diagnostics are identical across complete association settings and are reported once per representation/width combination. The diagnostic strongest-bin denominator is 204 per arm.

Persistence retains the frozen minimum of three fragments and 60% of original episode fragments. A path primary must have invariant candidate membership and exclude competing persistent paths in every retained hypothesis. `MULTIPLE_PERSISTENT_TRACKS` requires jointly possible persistent paths in a retained hypothesis. A union of alternative persistent memberships is not a count of simultaneous signals. The connected method retains its historical group/coherence veto; its ambiguous label and persistent-group count are not interchangeable with path partition labels. A saved `INSUFFICIENT_SUPPORT` or `NO_ELIGIBLE_COMPONENT` is an outcome, not missing data.

**Interpretation.** Factor differences below are paired changes on reused development evidence. Higher unique counts, fewer candidates, less fragmentation, larger cardinalities or lower ambiguity are not independently measures of scientific correctness.

**Limitation.** All real-data truth fields are `NOT_APPLICABLE` with null truth metrics. Between-device evidence remains descriptive only. Neither device-ID accuracy nor real false-primary, crossing or switching rates can be inferred. No independent holdout or full synthetic spectral matrix is supplied by Stage 36; its launch code explicitly executes the real-data matrix only.

## A. Direct observations from Stage 36

Across complete arms there are **2,334 unique, 904 ambiguous, 2,427 insufficient, 291 multiple-persistent and 276 no-eligible** outcomes. There are 3,898 null-primary observations. Native's incomplete positive-margin arms contribute no invented outcomes.

| Factor | Complete episode-arm observations | Unique | Ambiguous | Insufficient | Multiple persistent | No eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 984 | 96 | 533 | 125 | 230 | 0 |
| grid_sigma0 | 1312 | 431 | 351 | 469 | 61 | 0 |
| grid_sigma5 | 1312 | 605 | 8 | 683 | 0 | 16 |
| grid_sigma10 | 1312 | 609 | 8 | 647 | 0 | 48 |
| grid_sigma20 | 1312 | 593 | 4 | 503 | 0 | 212 |

Association marginals have different denominators because the two positive-margin native methods are incomplete above 275 Hz:

| Factor | Complete episode-arm observations | Unique | Ambiguous | Insufficient | Multiple persistent | No eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| connected | 1640 | 482 | 527 | 562 | 0 | 69 |
| paths_margin0 | 1640 | 698 | 16 | 697 | 160 | 69 |
| paths_margin0.25 | 1476 | 601 | 147 | 602 | 57 | 69 |
| paths_margin1 | 1476 | 553 | 214 | 566 | 74 | 69 |

The full interaction is visible in this table of unique outcomes per 41 episodes. Rows follow the frozen factor order; these are outcome counts, not scores. `U` denotes COMPUTATION_UNRESOLVED and never zero. All other status counts remain in the per-arm JSON.

| Representation / association | 200 | 225 | 250 | 275 | 300 | 325 | 350 | unlimited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| native / connected | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| native / paths_margin0 | 11 | 11 | 9 | 10 | 14 | 12 | 12 | 12 |
| native / paths_margin0.25 | 1 | 1 | 1 | 2 | U | U | U | U |
| native / paths_margin1 | 0 | 0 | 0 | 0 | U | U | U | U |
| grid_sigma0 / connected | 0 | 0 | 0 | 3 | 10 | 10 | 10 | 10 |
| grid_sigma0 / paths_margin0 | 1 | 1 | 1 | 7 | 36 | 35 | 35 | 35 |
| grid_sigma0 / paths_margin0.25 | 0 | 0 | 0 | 7 | 34 | 33 | 33 | 33 |
| grid_sigma0 / paths_margin1 | 0 | 0 | 0 | 4 | 24 | 23 | 23 | 23 |
| grid_sigma5 / connected | 0 | 0 | 0 | 0 | 35 | 37 | 37 | 37 |
| grid_sigma5 / paths_margin0 | 0 | 0 | 0 | 0 | 36 | 39 | 39 | 39 |
| grid_sigma5 / paths_margin0.25 | 0 | 0 | 0 | 0 | 36 | 39 | 39 | 39 |
| grid_sigma5 / paths_margin1 | 0 | 0 | 0 | 0 | 36 | 39 | 39 | 39 |
| grid_sigma10 / connected | 0 | 0 | 0 | 0 | 36 | 37 | 37 | 37 |
| grid_sigma10 / paths_margin0 | 0 | 0 | 0 | 0 | 37 | 39 | 39 | 39 |
| grid_sigma10 / paths_margin0.25 | 0 | 0 | 0 | 0 | 37 | 39 | 39 | 39 |
| grid_sigma10 / paths_margin1 | 0 | 0 | 0 | 0 | 37 | 39 | 39 | 39 |
| grid_sigma20 / connected | 0 | 0 | 0 | 0 | 32 | 38 | 38 | 38 |
| grid_sigma20 / paths_margin0 | 0 | 0 | 0 | 0 | 32 | 39 | 39 | 39 |
| grid_sigma20 / paths_margin0.25 | 0 | 0 | 0 | 0 | 32 | 39 | 39 | 39 |
| grid_sigma20 / paths_margin1 | 0 | 0 | 0 | 0 | 32 | 39 | 39 | 39 |

### Representation, detection and width

At unlimited width the total detections / eligible candidates over 210 fragments are respectively: native **8,681 / 8,679**; grid_sigma0 **2,103 / 2,103**; grid_sigma5 **322 / 322**; grid_sigma10 **287 / 287**; grid_sigma20 **254 / 253**. Width filtering changes eligibility rather than the pre-filter detector count. Resolution strata remain 143 fragments at N=10,923, 44 at 21,846, 22 at 43,692 and one at 54,615; these unequal strata and reused captures do not support a causal resolution-only claim.

The following pairs are **eligible candidates / retained diagnostic strongest bins out of 204**. They expose the width–representation interaction without counting the same spectra four times.

| Representation | 200 Hz | 275 Hz | 300 Hz | 325 Hz | 350 Hz | unlimited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 8544 / 83 | 8589 / 117 | 8664 / 190 | 8679 / 204 | 8679 / 204 | 8679 / 204 |
| grid_sigma0 | 1945 / 60 | 1994 / 98 | 2087 / 189 | 2103 / 204 | 2103 / 204 | 2103 / 204 |
| grid_sigma5 | 108 / 6 | 146 / 32 | 266 / 149 | 320 / 201 | 322 / 202 | 322 / 202 |
| grid_sigma10 | 72 / 4 | 102 / 22 | 232 / 149 | 285 / 201 | 287 / 202 | 287 / 202 |
| grid_sigma20 | 35 / 0 | 55 / 9 | 185 / 137 | 250 / 200 | 252 / 201 | 253 / 202 |

At 200 Hz, broad-component rejections are 135, 158, 214, 215 and 218 in the same representation order. At unlimited width they are zero; guard/background eligibility restrictions still apply. Smoothing at sigma 5/10/20 gives zero persistent tracks at every width from 200 through 275 Hz. At 200 Hz, sigma20 has 19/41 no-eligible episodes per association method, versus one for sigma5 and five for sigma10. All three smoothed representations acquire many persistent tracks between 275 and 300 Hz, but their unique outcomes differ at 300 Hz. At 325 Hz all three path margins produce 39 unique plus two insufficient outcomes for each smoothed representation.

Mean diagnostic fragmentation over 210 fragments is **9.519 native, 2.676 grid_sigma0, 0.981 grid_sigma5, 0.962 grid_sigma10 and 0.962 grid_sigma20**. This counts all detected intervals intersecting −5500 to −5100 Hz, including width-rejected intervals, so it is unchanged across widths. It is not a measured physical split rate. Mean per-fragment regional original-power retention changes from approximately **0.382/0.274/0.028/0.018/0.000 at 200 Hz** to **0.941/0.939/0.938/0.938/0.940 at unlimited**, in the same order. These are unweighted means of fragment ratios, not pooled power fractions.

### Association, persistence and structural constraints

Native connected emits no primary at any width: 38 ambiguous and three insufficient outcomes through 275 Hz, then 40 ambiguous and one insufficient. Its emitted incoherent groups total 1,196 across eight widths, affecting 312 episode-arm observations. Grid_sigma0 has 223 incoherent groups in 162 episode-arm observations. The smoothed grids have none. These connected diagnostics are retained; they are not reclassified as violations of asserted path constraints.

All 6,232 complete episode results report zero structural-constraint violations. An independent check of **201,222 emitted possible path memberships** across complete path arms also found zero violations of eligibility, one candidate per fragment, fragment increments 1 or 2, step displacement ≤50 Hz, whole-path range ≤100 Hz, support/coverage consistency, and the persistence minimum. This checks emitted memberships, not a new enumeration or proof of every hypothesis partition; exact-family completeness remains bound to the frozen solver and tests. Structural validity is not truth identity validity.

There are 11,155 persistent memberships across complete episode-arm observations, with at least one in 2,867 observations. These totals include alternatives and repeated arms. By method the counts are connected 582, margin0 1,211, margin0.25 2,594 and margin1 6,768; the last two use fewer complete arms. Native at 200 Hz alone has 2 connected persistent groups, 41 margin0 persistent memberships, 457 margin0.25 and 1,383 margin1; their primary counts are 0, 11, 1 and 0. More possible persistent paths can coexist with stronger abstention.

In matched connected-to-path comparisons there are **406 primary-after-connected-veto** observations: native 96, grid_sigma0 259, grid_sigma5 21, grid_sigma10 21 and grid_sigma20 9. This is a change in the decision rule's outcome, not 406 validated corrections. Every comparison uses the same representation, width and episode, and incomplete pairs are marked unavailable.

### Neighboring widths and path margins

There are 140 planned neighboring-width family pairs (seven transitions × five representations × four methods); **132 are fully comparable**, and eight cross or lie within unresolved native positive-margin regions. Of the 132, 63 have identical 41-episode status vectors. In **43 of those 63**, the set of emitted candidate memberships changes despite identical statuses. Only 20 pairs have identical emitted membership sets throughout. Comparisons canonicalize candidate-ID sets within a representation; candidate IDs are not matched across representations.

Every one of the **18 complete families** has identical episode status vectors at 325, 350 and unlimited widths. This plateau has qualifications: sigma5/10/20 each changes a primary's membership in one episode per association method from 325 to 350, and sigma20 does so again from 350 to unlimited. Sigma0 connected also keeps the same status vector from 300 to 325 while two primary memberships change. A constant number of unique outcomes is therefore an especially weak stability criterion.

The 275→300 transition is large: native margin0 changes 20/41 statuses; grid_sigma0 margin0 changes 31/41; smoothed path methods change 36/41 (sigma5), 37/41 (sigma10) and 34/41 (sigma20). Width effects need not monotonically increase unique outcomes: native margin0 moves from 14 unique at 300 to 12 at 325, while multiple-persistent outcomes rise from 23 to 27. Grid_sigma0 margin0 similarly moves from 36 to 35 unique and three to four multiple-persistent outcomes.

Of 80 planned adjacent path-margin pairs, 72 are fully comparable. The 48 smoothed-grid pairs have identical status and emitted membership sets. The remaining 24 native/grid_sigma0 pairs change both. All **2,952 smoothed-grid path episode-arm results have exact cardinality one**; no margin-induced alternative appears in those saved families. Native has 325 single-hypothesis results among 656 complete path episode-arm observations; grid_sigma0 has 734 among 984. Their maximum cardinalities are respectively **378,038,954,451,765,697,490** and **1,504**. The native maximum occurs for the two-fragment PIPELINE-TPMS-008 E08 at margin1 across 200–275 Hz: it remains ambiguous and cannot reach the three-fragment persistence minimum. Cardinality is a count of retained combinatorial hypotheses, not a confidence score, probability or count of physical sources.

### Retained anomalies and incomplete interpretations

BETWEEN-DEVICE-REPL E07 is retained in all 152 complete arms, always `INSUFFICIENT_SUPPORT`, with its original one-fragment denominator. It is not removed to improve summaries. Its strongest bin is about −12,455.37 Hz, outside the tracking guard, and is not retained even at unlimited width. Its eligible candidates at unlimited width remain 38/25/6/4/2 across native/grid_sigma0/5/10/20; candidates do not create temporal support.

All four predeclared anomalous fragment records are included once per representation/width in the JSON (160 records). At unlimited width native retains the original strongest bin for 004 E01/F03, 004 E06/F03 and BETWEEN-DEVICE E06/F04. Sigma0 retains only the third of those three; sigma5/10/20 retain none and emit zero eligible candidates for those three fragments. Thus high diagnostic-region retention does not mean that anomalous strongest bins elsewhere survive. The diagnostic denominator must not be silently expanded into an all-fragment success claim.

The eight COMPUTATION_UNRESOLVED arms are precisely native × {300, 325, 350, unlimited} × {paths_margin0.25, paths_margin1}. Every receipt gives `Unresolved: Exact-cover search limit reached; result is unresolved`. Each arm has one saved episode result, whose path is retained as partial provenance; it is never used as a substitute for an arm-level summary. No conclusion about their full status distributions, persistence, width stability or comparative scientific quality is possible. These remain negative computational evidence, neither failed science, passed science nor excluded data.

## B. Interpretation and scientific tradeoffs

The observed simplification from native to grid_sigma0, and then to smoothed grids, removes many detector intervals and alternative associations. At permissive widths the smoothed grids yield fewer ambiguous/multiple outcomes and many more unique persistent outcomes. At narrow widths the same representations predominantly lack persistent support and sometimes lack any eligible candidate. This is a coupled detector-width effect, not an association-only improvement.

Increasing width admits previously rejected broad components and recovers more diagnostic strongest bins. It can also introduce competitors or alter the candidate membership of a primary. Native and sigma0 examples show additional multiple-persistent outcomes as widths widen. Conversely, tighter widths can make an episode look simpler by withholding candidates. Neither direction alone establishes scientific improvement.

Larger cost margins preserve uncertainty that margin0 suppresses on native and sigma0 inputs. The rise in possible persistent memberships while primary counts fall is consistent with uncertainty being represented, not necessarily tracking becoming worse. Smoothed-grid cardinality one makes margins observationally indistinguishable on these saved families, but at narrow widths even that single partition lacks persistence. Uniqueness of a partition and uniqueness of a persistent track are different assertions.

A primary after connected veto may reflect useful handling of competition or a newly forced association. Stage 36 truth-free real outputs cannot distinguish those explanations. Historical fixture negatives below prevent treating more real primaries or zero constraint violations as validated recovery. No winner, recommendation, rank, aggregate score or Stage 37B decision is made.

## C. Historical negatives, limitations and uncertainty

The following are **direct observations from separately frozen historical association fixtures**, not new Stage 36 real-data observations. There are 113 fixtures per method (452 evaluations), including 100 noise trials, four recoverable trials and crossing/competing cases. Their committed detailed and summary files were checked at the frozen checkpoint.

| Association | Noise false primary | Crossing switches | Forced crossing/competing primary | Correct recoverable primary |
| --- | ---: | ---: | ---: | ---: |
| connected | 1/100 | 0 | 0 | 4/4 |
| paths_margin0 | 10/100 | 8 | 0 | 4/4 |
| paths_margin0.25 | 10/100 | 8 | 0 | 4/4 |
| paths_margin1 | 10/100 | 8 | 0 | 4/4 |

The eight path crossing switches occur in the `crossing` fixture's retained path union, including alternatives, over 32 union links (8/32); they are not eight physical devices or eight real-world events. The all-fixture switch/link totals are 292/324 connected, 312/372 margin0, 318/380 margin0.25 and 328/390 margin1. Those denominators include noise and retained alternative links and must not be confused with crossing-only rates or independent continuations sampled in the field. Connected's zero crossing switches does not imply no false associations in noise.

Connected's noise false primary is `noise_58`; each path setting retains `noise_07`, `noise_18`, `noise_23`, `noise_27`, `noise_31`, `noise_33`, `noise_58`, `noise_71`, `noise_92` and `noise_96`. These historical path results violate the frozen ≤1% noise false-primary and zero-crossing-switch conditions. All methods recover 4/4 designated recoverable fixtures, so these fixtures show no gain in that count to offset the path negatives. This preserves historical scientific failures without relabeling the eight computationally unresolved Stage 36 arms. Association-only fixtures do not provide representation/width-specific false-primary estimates.

The unexecuted full synthetic spectral matrix leaves physical split/merge, close-pair recovery and full acceptance gates unresolved. Diagnostic fragmentation is not physical splitting, and strongest-bin retention is not carrier recovery. The six captures are development evidence; no universal threshold, device identity, carrier identity or out-of-sample reliability claim follows. Stable status vectors across adjacent sampled widths do not establish stability between those widths, beyond them, or on other captures. No missing evidence is imputed.

## Verification and deliverables

The review JSON and this report are pinned by canonical-payload and report digests in the new tests. Tests also check the frozen checkpoint and source bindings, exact inventory, denominators, E07 retention, persistence, aggregate arithmetic, matched comparisons, historical negatives and adversarial review mutations. Opt-in `STAGE37_VERIFY_RAW=1` streams the entire external hash inventory and checks saved projections without executing science. Default tests can run without the external raw tree; the opt-in audit fails if requested evidence is missing.

Validation: **9/9 new review tests pass**, including the opt-in full raw hash/projection audit. The seven relevant existing modules ran **80 tests: 71 passed and nine errored**, all on the inherited `.gitignore` mismatch. The affected checks are two definition/feasibility baseline-inventory checks, six launch-integration checks and one launch-provenance check. No error is suppressed or reclassified as a pass. `git diff --check` and `git diff --cached --check` pass.

Commands (temporary files remain within this worktree):

```sh
mkdir -p .stage37-review/tmp
TMPDIR="$PWD/.stage37-review/tmp" PYTHONPATH=analysis:tests STAGE37_VERIFY_RAW=1 python3 -B -m unittest discover -s tests -p test_episode_component_tracking_v2_stage37_scientific_review.py -v
TMPDIR="$PWD/.stage37-review/tmp" PYTHONPATH=analysis:tests python3 -B -m unittest -v test_episode_component_tracking_v2_draft2_experiment test_episode_component_tracking_v2_draft2_full_matrix_definition_review test_episode_component_tracking_v2_draft2_full_matrix_feasibility_review test_episode_component_tracking_v2_draft2_full_matrix_launch_integration test_episode_component_tracking_v2_draft2_full_matrix_launch_provenance test_episode_component_tracking_v2_draft2_review_integration test_episode_component_tracking_v2_draft2_six_capture_corrected
git diff --check
git diff --cached --check
``` Only this report, the review JSON and `tests/test_episode_component_tracking_v2_stage37_scientific_review.py` are intended changes.

Final decision: **STAGE37_SCIENTIFIC_EVIDENCE_REVIEW_COMPLETE**
