# Stage 37 provenance repair

Decision: `STAGE37_GITIGNORE_PROVENANCE_REPAIR_COMPLETE`

Baseline: `9d9d3b1312e793da519cc08f430f821de9870078` on
`codex/stage37-review-integration`; frozen Stage 36 checkpoint:
`0df44abb54231d5e8bfe84fe316ebbcf10d3130c`.

The historical launch plan remains byte-identical. Its `.gitignore` digest
`24459e7feded9172d32c80b041c4ef76fe903f720037559a0f44ff3e82ea0d7a`
is verified against execution commit `e559d63e3a88822ff5443d5a83d0ad60fc3e3348`.
The current file must equal the freeze checkpoint bytes, digest
`3bea5d21bee9a0982907fab3c62f8a873010c8e5d8e4722722a967ba103439ba`.
Those bytes must equal the execution bytes plus exactly one blank line and
`results/episode-component-tracking-v2-draft2-full-matrix-exact-v1/` with its
trailing newline. Freeze ancestry is required. Historical bytes alone are not
accepted as current bytes: removing the raw-result ignore rule fails.

## Exact repair files and purpose

- `analysis/provenance/stage37_gitignore_v1.py`: shared read-only transition
  verification and explicit hash binding of the two updated provenance validators.
  All other source digests pass through unchanged.
- `analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py`: connect
  `verify_plan()` to that helper while preserving the original launch binding.
- `tests/draft2_review_provenance.py`: apply the same transition to the older
  definition/feasibility inventories without rewriting their baseline hashes.
- `results/episode-component-tracking-v2-stage37-provenance-repair-v1.json`:
  versioned binding of execution/freeze commits and hashes, original/current
  validator hashes, and helper hash. Its complete bytes are pinned by regression.
- `tests/test_episode_component_tracking_v2_draft2_full_matrix_gitignore_provenance.py`:
  11 regressions covering acceptance, historical truth, mutations, rule removal,
  ancestry, repair binding/source drift, non-execution, unchanged runner semantics,
  frozen evidence, and review payloads.
- `tests/test_episode_component_tracking_v2_stage37_scientific_review.py`:
  distinguish the two hash-bound validator repairs from historical scientific
  sources; retain all original payload/report and checkpoint hash assertions.
- `tests/test_episode_component_tracking_v2_stage37_computational_review.py`:
  use the same historical/current distinction and expect repaired verification
  to succeed; preserve the original review's recorded failure and conclusion.
- `docs/episode-component-tracking-v2-stage37-provenance-repair.md`: this record.

## Validation

Commands use `PYTHONPATH=analysis:tests`.

- Baseline full-matrix discovery: 43 tests, exactly 9 errors, all `.gitignore`.
- `python -m unittest discover -s tests -p 'test_episode_component_tracking_v2_draft2_full_matrix*.py'`:
  54 passed (all original 43 plus 11 new regressions). Existing adversarial tests
  retain rejection of scientific source, runner, plan, manifest, launch binding,
  and resource-limit drift.
- `STAGE37_VERIFY_RAW=1 python -m unittest discover -s tests -p 'test_episode_component_tracking_v2_stage37*review.py'`:
  13 passed, no skips, including read-only raw inventory/projection verification
  and computational aggregate reconstruction.
- `python -m unittest test_episode_component_tracking_v2_draft2_review_integration`:
  6 passed, including mutation/missing/untracked rejection for every older
  baseline path.
- `git diff --check`: passed.

73 distinct tests passed. The earlier default review run also passed (12 passed,
1 opt-in raw test skipped); the explicit raw run above supersedes that skip.

No matrix arm was launched or rerun. Raw evidence was only read. The regression
mocks all matrix execution entry points to fail during provenance acceptance.
An AST comparison against Stage 36 proves all runner code outside the added
provenance import and `verify_plan()` is unchanged, including configuration,
resource limits, solver calls, worker behavior, and output handling.

The frozen plan, canonical manifest, launch binding V2, Stage 36 tracked evidence,
scientific sources/outputs, `.gitignore`, and both Stage 37 review JSON/report
payloads remain byte-identical. Raw archive hashes were verified by the review
suites. The only result artifact added is the provenance repair binding above;
no scientific result was changed. Neither review conclusion changes.
