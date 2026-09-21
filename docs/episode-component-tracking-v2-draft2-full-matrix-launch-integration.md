# Draft 2 exact full-matrix launch integration V1

This is an execution-path review, not launch authorization or a new scientific
result. No matrix arm, capture, detector, or candidate-generation job was run.
The new entrypoint is
`analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py`.
The historical runner and all pre-existing tracked evidence remain unchanged at
`30904f3513d1c0c7354e4be02e77c35b3b28303f`.

## Scientific binding and scope

The byte-pinned canonical manifest contains exactly 160 unique arms, in the
original representation / width / association Cartesian order: five
representations, eight width ceilings (JSON null means unlimited), four
association settings. The runner checks both the complete Cartesian product and
exact equality with historical `arms()`, including ordering and identity.

Canonical SHA-256:
`d6b85599a9241f3267d91ded0b5145d208ec63f1507086e28fb14c3cd6b05b3a`.

The future worker directly calls frozen Draft 2 `load_inputs`, `detect`
(which calls its original representation implementation), `apply_width`, and
`fragment_metrics`. Candidate identities, binary64 arithmetic, scientific
thresholds, episode inventory, unusable fragments, and original fragment
counts are preserved. All 41 episodes and 210 fragments are retained. Arm-level
metrics use the historical formulas and denominators. Only computational
association machinery and its artifact representation change.

This entrypoint covers the real-data 160-arm matrix. Shared historical synthetic
and association-fixture artifacts remain pinned separate evidence. It does not
rerun those independent fixture campaigns or issue final experiment acceptance
gates. In particular, historical false-primary and crossing failures are not
converted into successes by exact computational completion.

## Exact dispatch

Connected calls the committed staged consumer's historical-connected branch.
That branch delegates to historical connected association; it constructs no
compact family or cardinality sidecar. Its scientific fields match historical
connected output; the staged envelope deliberately omits expanded-hypothesis
placeholders and adds explicit representation/provenance fields.

Every path margin uses the same pipeline:

1. Corrected exact retained-family construction over eligible candidates with
   the original fragment count and global margin.
2. The **same function object** used by the corrected six-capture regression:
   `regress_episode_component_tracking_v2_draft2_six_capture_corrected.count_exact`.
   It composes V3 short-path / matching-polynomial certification, V2 exact dyadic
   matching, column counting and exact binary64 fallback, with the E05 cutoff /
   cumulative-multiplicity composition and monotone pivot machinery.
3. A validated cardinality sidecar binding family/model/source hashes, exact
   decimal cardinality, arithmetic policy and frozen limits.
4. The committed REPL E03 exact-query adapter around staged integration.
5. Required VERIFIED provenance, COMPLETE family and metric projection, EXACT
   count and queries, structural checks, and deterministic saved-result reload.

The association adapter accepts fragments and the scientific setting; it has no
capture, episode, device, matrix arm ID, expected-cardinality or known-outcome
argument. The counter accepts only a family and budget. Its certificates inspect
path lengths, incidence blocks, gap penalties, cost lattices and rigorous
rounding separation. Certificate failure goes to the committed general exact
fallback using the same budget; it never changes the scientific question.
Candidate IDs still identify paths, as required by the frozen semantics; they
are not an algorithm-selection key.

Tests inspect this wiring, compare tiny exact examples, and relabel candidate
identities/add arbitrary case metadata while requiring identical backend and
count. Known controls are checked from committed artifact bytes, without
recounting those controls through the new launch path:

| Control | Margin | Exact cardinality |
|---|---:|---:|
| TPMS-004 E02 | 1 | 5,788,836 |
| REPL E02 | 1 | 217,075 |
| REPL E03 | 0.25 | 349,149 |
| REPL E03 | 1 | 378,536,340 |
| REPL E05 | 1 | 697,122 |
| E08 | 0 | 2 |
| E08 | 0.25 | 17,067,800,502,243 |
| E08 | 1 | 378,038,954,451,765,697,490 |

These demonstrate artifact parity and identical computational wiring. They do
not predict counts or runtimes for unexecuted matrix cases.

## Safe planning and future authorized commands

Safe, read-only validation:

```sh
python3 analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py --plan-only
```

This verifies the manifest, source/evidence hashes, historical review decisions,
configuration, frozen limits and output namespace, and prints the plan hash and
160 prospective output paths. It calls no detector, input loader, family
constructor, association solver or scientific worker. Backend certificates for
new cases remain unknown until their candidate structures exist.

No arguments are rejected by argparse. The following are **future command
forms only**, not commands executed or authorized by this integration:

```sh
python3 analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py \
  --arm native__w200__paths_margin1 --batch approved-single \
  --confirm-frozen-plan PLAN_SHA256

python3 analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py \
  --arm-list explicitly-approved-arm-ids.json --batch approved-bounded \
  --confirm-frozen-plan PLAN_SHA256

python3 analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py \
  --execute-full-matrix --batch approved-full \
  --confirm-frozen-plan PLAN_SHA256

python3 analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py \
  --resume approved-full --confirm-frozen-plan PLAN_SHA256
```

The arm-list file is a nonempty JSON list of unique canonical arm IDs. Selected
arms always execute in canonical order, regardless of list ordering. A 160-arm
list is rejected: initial full selection requires the dedicated flag. Every
execution form requires the exact reviewed plan hash. Source or manifest drift
requires review, not regeneration of a permissive runtime configuration.

## Process, output and resume contract

The controller starts exactly one isolated process per selected arm, sequentially.
Concurrency is hard-capped at **one**; this is within the review's initial-one,
conditional-maximum-two recommendation. There is no two-worker switch and no
scientific concurrent-worker test was performed. Enabling a second worker
requires a separate reviewed change and authorization.

All new batches are confined to
`results/episode-component-tracking-v2-draft2-full-matrix-exact-v1/<batch>/`.
Simple batch names, resolved-path checks, exclusive directory creation and
exclusive file writes prevent historical collisions or completed-arm overwrite.
A controller lock prevents concurrent controllers for a batch. Atomic `mkdir`
reserves each arm directory. A final receipt marks completion only after worker
success and records hashes of every arm artifact, including failures and logs.
An interrupted directory without a receipt is not treated as complete.

Immutable `batch.json` records canonical selection, source-bound plan hash,
manifest hash, frozen limits and batch-start Git context. Resume reconstructs
selection from that checkpoint, validates it against the current pinned plan,
checks all completed artifact hashes, and skips completed arms. Failed,
incomplete, or drifted arms stop resume and preserve their evidence. There is no
automatic retry, deletion, larger-limit retry, or post-hoc parameter adjustment.
An interrupted controller's stale lock requires explicit human review.

| Resource | Frozen maximum |
|---|---:|
| Live counting states | 250,000 |
| Counting transitions | 5,000,000 |
| Count time | 60 s |
| Packed polynomial bytes | 33,554,432 (32 MiB) |
| Public query calls | 5,000 |
| Query time | 120 s |
| Family construction / reconstruction scope | 60 s |
| Whole arm worker, including reloads | 400 s |
| Observed worker RSS / high-water mark | 524,288 KiB (512 MiB) |

Count/query/family bounds apply using the same corrected integration scopes as
the regression. The whole-arm timeout is an additional enclosing bound. RSS is
observed through `/proc` at 50 ms polling and the successful worker's final
high-water mark; this is the specified observed ceiling, not a kernel memory
reservation. A killed or unresolved arm is never certified complete. No limit
has a CLI override. Frozen limits may leave previously unexecuted arms unresolved;
readiness of the launch path is not a promise of full-matrix completion.

## Verification and preserved evidence

The accompanying JSON integration report records final test counts, source and
artifact hashes, tracked-file integrity and decision. Tests run with historical
`detect` and `load_inputs` blocked; tiny constructed association fixtures and
committed artifacts exercise the exact machinery without new detection.
The old experiment detector tests are excluded because they execute detection;
all requested exact-stack and review suites are included.

All 3,079 pre-existing tracked files were hashed before work and checked after
work. The launch plan pins that inventory plus the new entrypoint and tests.
Original one-complete / one-partial / 158-NOT_RUN evidence and prior NOT_READY
results remain byte-identical. The committed decisions remain
`MATRIX_DEFINITION_FROZEN_AND_RECONSTRUCTED` and
`COMPUTATIONAL_BLOCKERS_REMAIN`. This new integration does not edit either review.
No capture, detection, matrix launch, commit or push occurred.
