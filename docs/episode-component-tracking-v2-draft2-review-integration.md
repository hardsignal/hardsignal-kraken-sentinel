# Draft 2 review integration provenance

The immutable `review_checkpoint` for both independent reviews is
`6bd63ac90b9045ecb2eac3544ee63b035103428b`. The validation/integration HEAD for
this repair is `7392556eb45a969abdd8ad83185ecb3c0cf887c5` on
`codex/draft2-review-integration-fix`. Later validation may use a descendant HEAD
and a different branch. This does not relocate the original reviews in history.

The definition test previously equated current HEAD and branch with `before.head`
and `before.branch`. The feasibility test equated current HEAD with both a literal
checkpoint and `integrity.before.head`. Those checks now require the recorded
checkpoint to equal the immutable checkpoint and `git merge-base --is-ancestor`
to succeed against the current validation HEAD. Branch names remain historical
metadata, not current validation constraints.

Both original JSON reviews, both original reports, the canonical arm manifest,
and the risk manifest remain byte-identical. The definition report's closing
HEAD/branch and four-untracked-files statements describe its original review
worktree. The feasibility report's closing unchanged HEAD/branch/inventory
requirements and JSON `tracked_inventory_unchanged` likewise describe original
review validation. Neither dedicated test contained a present-inventory count
comparison; those historical records must not be interpreted as a requirement
that later integration add no tracked files. Historical test counts and logs,
including the feasibility review's earlier 187-test evidence, remain unchanged.

`tests/draft2_review_provenance.py` validates exactly the recorded path-to-SHA-256
inventory: 3,068 paths in each review. Every path must still be tracked, present,
and byte-identical. The recorded path set must equal the checkpoint tree, not the
current tree. Additional tracked review artifacts are explicitly allowed. No
baseline source, result, specification, or test file is exempted.

Review artifacts are bound independently by SHA-256 comparison with their exact
bytes at the pinned integration commits:

- Definition: `43d2ebe395c12e40454836b02a03b503b6d8f865`.
- Feasibility: `7392556eb45a969abdd8ad83185ecb3c0cf887c5`.

These commits identify storage of the original review artifacts, not when the
reviews were performed. Full-byte validation covers each review JSON, its report,
and its manifest, protecting the complete scientific payload, recorded baseline,
and original evidence without self-referential hashes. Original hashes of review
test files describe the historical test versions at these commits; the current
review tests intentionally implement the repaired integration semantics.

Read-only integration tests reject mutation, absence, or loss of tracking of every
baseline path; wrong checkpoints; non-descendant validation history; changed
review decisions/evidence/resources; and changed arm inventories, scientific
configuration, or risk distribution. Unchanged serialized artifacts are accepted
before mutation checks. The actual descendant integration worktree passes both
original dedicated suites. All checks read saved artifacts or Git objects; none
imports scientific runners or executes capture, detection, or solving.

Scientific payload changes: **NONE**. The 5 representations, 8 width ceilings,
4 association settings, 160 arms, original execution history, resource envelope,
dispatch analysis, and risk distribution (1 LOW / 42 MODERATE / 0 HIGH /
117 UNKNOWN) remain unchanged. The full matrix entrypoint still uses the
historical expanded solver; the corrected stack remains integrated into the
bounded corrected-regression runner. Decisions remain
`MATRIX_DEFINITION_FROZEN_AND_RECONSTRUCTED` and `COMPUTATIONAL_BLOCKERS_REMAIN`.
No launch authorization, resource-limit change, scientific execution, commit,
or push is part of this repair.
