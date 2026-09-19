# Draft 2 execution review

Implemented separate spectral rebinning/envelopes, the unchanged 160-arm matrix, exact path-partition hypotheses, synthetic spectral and association fixtures, diagnostics and gate evaluation. V1 and committed Draft 1 are unchanged. No RF, IQ loading, commit or push was performed.

**Execution stopped at the declared computational limit. This is not a complete Draft 2 experiment.**

- 18 unit tests passed, including an independent exhaustive-edge check of the exact path solver.
- All 113 association fixtures ran at all four association settings: 452 evaluations.
- One real-data arm completed across all six captures, 41 episodes and 210 fragments.
- The next arm (`native__w200__paths_margin0`) stopped at TPMS-008 E08: a 73-candidate connected group had 412 feasible paths and exhausted the 200,000-state exact partition DP budget at state 200,001. Twenty-six prior episode results are explicitly partial; no complete-arm metric is asserted.
- Remaining 158 real-data arms are NOT_RUN. All 160 are listed in arms.csv/arms.json and summary.md.
- The full 100,800-fixture spectral matrix was not started. Fixture generation, inventory, Gaussian shape, power ratio and deterministic RNG were unit tested.
- The limit applies to this implementation; it is not proof that a different exact solver could not finish the experiment. No hypothesis truncation or parameter reduction was substituted.

## Measured results

The native/200 Hz/connected arm exactly reproduced all 210 fragments' detection counts, candidate identities, peak frequencies, widths and eligibility. Its 8,681 detections yielded 38 AMBIGUOUS_ASSOCIATION and 3 INSUFFICIENT_SUPPORT episodes, two persistent tracks and zero primaries. There were 135 width rejections. Diagnostic-region dominant retention was 83/204 (40.69%).

| Association fixture arm | Noise false primaries | Crossing/competing identity switches | Constraint violations | Correct recoverable primaries |
|---|---:|---:|---:|---:|
| connected | 1/100 | 0 | 0 | 4/4 |
| paths_margin0 | 10/100 | 8 | 0 | 4/4 |
| paths_margin0.25 | 10/100 | 8 | 0 | 4/4 |
| paths_margin1 | 10/100 | 8 | 0 | 4/4 |

All arms abstained from forcing a primary in the crossing/competing fixtures. The path arms nevertheless retain identity-switching paths, and their 10% noise false-primary rate exceeds the 1% gate. Identity-switch counts include links in retained alternative paths; these are not device-identity measurements. Full fixture records, denominators, ambiguity retention and abstention are available in association-fixtures.json and association-fixture-summary.json.

All four anomalous fragments are explicit diagnostics in the completed control artifact. +5550.215, -1403.003 and +260.917 Hz are retained in eligible native components; -12455.369 Hz remains outside the fixed guard. None is used to select a primary.

## Decision gates and review status

The measured noise and crossing gates fail for all three path-association arms. The full representation/association decision gates cannot be evaluated because the real matrix and spectral fixtures are incomplete. No parameter set is selected and no discrimination or identification claim is made.

At initial execution validation, all committed-input hashes and generated-artifact hashes verified; git diff --check and source whitespace checks passed. The statements about untracked new files below describe that original pre-commit validation. The later CSV line-ending mismatch and its repair are documented separately below.

New files: analysis/episode_component_tracking_v2_draft2_experiment.py; docs/episode-component-tracking-v2-draft2-experiment.md; tests/test_episode_component_tracking_v2_draft2_experiment.py; this separate Draft 2 result directory. No historical file was modified.

## Provenance-only repair (2026-09-20)

The initial CSV writer uses the default csv.DictWriter dialect with newline='',
which emits CRLF. The successful local-session hash check completed at
2026-09-19 23:09:50.990 UTC (2026-09-20 00:09:50.990 BST). The first Draft 2
commit, 51861e1a9ef264f9edf9a902f38e9d3aff0acfb9, at 23:13:31 UTC
(00:13:31 BST), contains LF bytes but the earlier CRLF hash. The exact byte
transformation was removal of all 161 CR bytes preceding LF. Available history
bounds the conversion to that interval but does not record its command, actor
or exact timestamp. Current Git configuration and attributes do not establish
that Git performed the conversion; that attribution would be speculation.

Canonical arms.csv is deliberately restored to the original generated CRLF
bytes. Reconstructing CRLF exactly reproduces the original recorded SHA-256:

- Before repair (committed LF): cbb5dc963ccd8234eb190a7485c2b94a080a96d8c29c8d072108da72babbe721
- After repair (original CRLF): af5cff213682d14696a2c8a2880b1082861ea92b3ce051359b5600b2b72ac904

The parsed CSV records are identical. A scoped .gitattributes entry disables
Git text conversion for this CSV and recognizes CR at end of line for whitespace
checking. The frozen writer, methodology, parameters, solver and all numerical
results are unchanged. files.sha256 is regenerated only because canonical
artifact bytes and provenance metadata were intentionally changed; its arms.csv
entry remains the original hash. It covers every bundle file except itself,
including the new .gitattributes. Prior metadata hashes are retained in
validation.json under provenance_repair.original_file_sha256.

Verification covers all 11 bundle entries, all 42 execution-input hashes and
the four recorded implementation/control/specification/test hashes. CSV/JSON
arm records agree. git diff --check passes. These are provenance checks; the
18 recorded unit tests were not rerun and the experiment was not rerun.

Execution remains incomplete: 1/160 real arms COMPLETE, the next arm
COMPUTATION_UNRESOLVED at the exact solver's 200,000-state limit, 158 arms
NOT_RUN, and the spectral fixture matrix NOT_STARTED. run.json, arms.json,
summary.md and numerical result files remain byte-for-byte unchanged.
No RF capture, exact-cover implementation, commit or push was performed.
