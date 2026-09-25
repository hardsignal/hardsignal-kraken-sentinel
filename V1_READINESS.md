# Sentinel AI v1.0 readiness audit

**Verdict: NOT READY.** Audit date: 2026-09-25; Python 3.12.3; offline.

Audited working branch `audit/ai-v1-readiness`, initially clean, at
`4a08b8cc2b42745dd0443d4e331bb5f2fbc23806` (the unchanged `sentinel-ai-v0.2`
tag). Separately reviewed verifier branch `post-release/verify-ai-v0.2` at
`42ec68e237ee66a7dc199e1b8086969fdd339b79`.

This patch adds this report and `tests/readiness/test_ai_v1_readiness.py` only.
No production fixes, capabilities, broad refactors, model changes, source evidence
changes, release-artifact regeneration, or tag changes are included. Blocker fixes
below are **proposed**, not completed. The new tests expose release risks without
changing historical release expectations.

## Evidence and test accounting

| Scope | Measured result |
| --- | --- |
| Current branch, `tests/ai` | 78 passing tests |
| Verifier branch, isolated git-archive snapshot | 96 passing tests (78 + 18 v0.2 verifier tests) |
| Current v0.1 verifier | PASS, including local tag check |
| Both verifiers on isolated verifier-branch snapshot | PASS; absent snapshot tags explicitly skipped |
| v0.2 verifier tag, reference-file hash, artifact and source checks against original repository | PASS |
| New standalone readiness probes | 22 tests: 10 pass, 12 expected failures; command exits **1** |

The reported 96-test checkpoint is accurate for the verifier branch, not this
checkout. Snapshot: `/tmp/sentinel-v02-audit-ztltnfrw` (temporary audit evidence,
not required for future verification). No Ollama server, RF hardware, downloads,
or model training were used. Expected failures are open risks, not release passes.
The probe runner explicitly treats them as gate failures. It loads the reviewed
v0.2 verifier from its exact Git commit, so that object must be available locally.

## Prioritized findings

| ID | Priority | Finding and release acceptance condition |
| --- | --- | --- |
| B1 | BLOCKER | Strict prior-only isolation fails. `ai/history.py:load_formal_history` parses all matching files; `formal_session_count_total` includes future records and `ai/history_report.py` sends it into the prompt. Future presence changes the prompt; corrupt future JSON blocks an earlier target. Select eligible paths before reading; require complete prompt/bundle invariance under future addition, removal, mutation and corruption. |
| B2 | BLOCKER | Formal membership is based only on payload session number. Filename/payload mismatch, duplicate numbers, and missing formal prior records are not rejected. A 014 filename carrying a 007 payload becomes a formal 007 target; normal history CLI without saving accepts it. Use the exact frozen formal ID manifest, validate filename/top-level/feature-row identity, exclude 014 by membership and reject missing eligible records. |
| B3 | BLOCKER | Both CLI experiment guards accept identity, causality, accuracy and discrimination claims. They also accept an invented prior mean when no prior exists. Strengthen shared and history-specific guards, bind referenced quantities/comparisons to supplied evidence, and test publication rejection. Prompt instructions and a measurement verb are not evidence validation. |
| B4 | BLOCKER | Artifacts do not prove a consistent evidence snapshot. History/report, prompt, and source hashes are built from separate reads; a changed source can be hashed alongside stale interpretation. Normal ML parse and hash are separate reads too. Read eligible bytes once, parse/hash that snapshot, and derive every artifact/report/prompt field from it. |
| B5 | BLOCKER | No general saved-artifact verifier or complete v1 schema exists. v0.1 verifier accepts changed source JSON; v0.2 verifier protects one fixed reference only. Core logs and frozen ML binary/preprocessing lineage are not bound by AI artifacts. Define the contract and a read-only verifier for both v1 modes, including source checks, semantic consistency and policy versions. |
| S1 | SHOULD-FIX | CLI failure precedence, retries, publication/save boundaries and error handling differ by mode; malformed shapes escape as Python exceptions. Define and test a stable CLI contract before freezing v1. |
| S2 | SHOULD-FIX | Model inventory is checked by CLI once, but lower-level generation allows other models and does not enforce the lock; mutable Ollama tags can change between inventory and generation. Freeze the supported entry point and document/enforce model immutability across the request. |
| S3 | SHOULD-FIX | README lacks normal/history invocations, prior-only semantics, error codes and arbitrary artifact verification. Release documentation does not describe v0.2 on either reviewed branch (the verifier branch changes only script, tests and workflow). |
| S4 | SHOULD-FIX | Historical prompt repair is not retained in artifacts: stored `experiment_prompt` is the initial prompt even when the second request generated the accepted text. Record actual submitted prompt hashes and attempt/guard outcomes in v1. |
| O1 | OPTIONAL | Consolidate verifier mechanics only after release-specific compatibility fixtures exist; leave historical verifiers unchanged for now. |

## 1. CLI contract and inconsistencies

Public entry point: `python3 -m ai.cli`, run from repository root.

| Argument | Current semantics |
| --- | --- |
| `-h`, `--help` | argparse help; exits 0 |
| `--session ID` | Required string; no parser-level canonical ID validation |
| `--save` | Save artifact after generating/printing report |
| `--history` | Historical path; formal natural sessions only |
| `--output-dir DIR` | Default `results/ai`; ignored unless saving; relative to CWD |

Argparse currently permits unambiguous option abbreviations. No CLI model, source
root, timeout, offline generation, artifact verification, or version flag exists.
Normal output labels itself v0.1; history labels itself v0.2. Normal artifacts go
to `<output-dir>/<session>/sentinel_ai_v01_<timestamp>.json`; history to
`<output-dir>/history/<session>/sentinel_ai_history_v02_<timestamp>.json`.

| Exit | Current behavior |
| --- | --- |
| 0 | Successful generation (and save when requested), or argparse help |
| 2 | argparse usage error, or caught FileNotFoundError with `SENTINEL_AI_ERROR` |
| 4 | SentinelLLMError with `SENTINEL_AI_LLM_ERROR` |
| 5 | Other caught ValueError, including invalid JSON syntax, with `SENTINEL_AI_EVIDENCE_ERROR` |
| 6 | SentinelExperimentGuardError with `SENTINEL_AI_EXPERIMENT_REJECT` |
| 1 | Typically interpreter exit for unhandled exceptions; not a stable application contract |

Normal mode builds evidence before model verification; history verifies Ollama
before validating target/evidence. Thus unavailable Ollama can mask invalid history
input. Normal mode allows a retained 014 record as an individual session; history
rejects 014 as formal target. This is not intrinsically wrong, but normal output
must not imply formal inclusion. Normal missing source logs are represented as empty
with a warning (Core behavior), not fatal missing ML evidence.

Normal suggestion gets one attempt; history gets two. Normal saving is outside the
try/except; history saving is inside. A save FileNotFoundError/ValueError therefore
has different handling; PermissionError and other OSError subclasses escape both.
Both can print a report before save fails. A normal JSON list raises AttributeError;
history missing keys or wrong numeric types raise KeyError/TypeError. Model JSON
with wrong container types can also escape as AttributeError. These are not covered
by the documented exception catches.

Freeze v1 flags, accepted IDs, abbreviation policy, CWD/source behavior, stdout and
stderr ownership, retry count, error precedence, partial-output policy, artifact
paths and overwrite/atomic-write behavior. Use one bounded error boundary without
catching arbitrary programming errors or silently publishing rejected output.

## 2. Artifacts, hashing and provenance

| Area | Normal v0.1 | History v0.2 |
| --- | --- | --- |
| Version | `artifact_version=0.1`, evidence schema 0.1 | `artifact_version=0.2`, history version 0.1 |
| Target | `session_id` | `target_session_id` |
| Common metadata | `created_at`, `model`, `model_digest`, `report_mode`, `ai_scope` | Same |
| Evidence | embedded `evidence_bundle`: Core summary, full ML record, provenance | derived `history_bundle`; source records external |
| Text | prompt, suggestion, final `report` | prompt, suggestion, deterministic `history_report` |
| Internal hashes | canonical evidence SHA256, three text SHA256s | canonical history SHA256, three text SHA256s |
| Source bindings | raw ML JSON SHA256; training dataset hash copied from ML | raw SHA256 per target/prior JSON; canonical manifest SHA256 |
| Other top-level fields | assigned cluster, novelty, training dataset hash, ML result hash | source-record map and its hash |

Canonical JSON currently means Python `json.dumps(sort_keys=True,
separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. Text hashes cover exact
UTF-8 bytes, not normalized whitespace. Source hashes cover raw file bytes; even an
added newline invalidates the v0.2 source check. Timestamp variability means whole
new artifacts are not byte-identical across runs.

This is deterministic for the supported Python value representation, not a declared
cross-language canonical JSON standard. NaN/Infinity are currently permitted by
Python JSON defaults, duplicate keys silently collapse on load, numeric shapes and
finite values are insufficiently validated, and `1` versus `1.0` hashes differently.
Freeze these rules explicitly for v1 and reject duplicate keys/non-finite values.
Do not change historical hash semantics retroactively.

The v0.1 verifier checks four embedded hashes and mode/scope/model metadata, but
not artifact version, session consistency, top-level duplicated ML values, raw
source JSON hash against disk, or a pinned whole reference file. A self-consistent
rewrite of its content and hashes can pass. Hashes establish content consistency,
not authorship or scientific truth.

The v0.2 verifier pins the reference artifact's entire file SHA256 and exact ten
source IDs, verifies their raw bytes, four internal hashes and manifest hash. This
protects the retained reference; it does not reconstruct arbitrary history or
validate arbitrary new artifacts. The generator only checks the history target
matches its argument; arbitrary history/report/prompt or wrong digest can be saved
through the builder API.

Unbound or incomplete lineage:

- Normal Core burst, track and episode source log bytes are not hashed. The derived
  summary is internally hashed, but cannot authenticate/reconstruct its inputs.
- Neither AI format binds frozen model binary and preprocessing assets directly.
  The copied training dataset digest is not checked against frozen assets here.
- History binds prospective JSON bytes, including their feature rows and dataset
  claims, but not the original RF/log evidence from which those rows were derived.
- No generation code commit, formal-set policy digest, feature-distance definition
  version, guard/prompt version, generation settings or complete retry trace is bound.
- Normal metadata/duplicated fields and history metadata lack an enclosing content
  hash in general artifacts. The historical v0.2 reference's externally pinned hash
  covers this for that one file only.

Proposed stable v1 contract: retain model+digest, UTC creation time, mode+AI scope,
exact target ID, embedded authoritative evidence or a complete content-addressed
source manifest, deterministic report, exact generation prompt(s), accepted
suggestion, and their hashes. Use one target field name in v1, while preserving
versioned readers for old formats. Bind Core input snapshots, target/prior ML JSON,
frozen ML asset/dataset digests, formal membership policy, code/schema/guard/prompt
versions, settings and attempt provenance. Missing original evidence must be
explicitly marked unavailable, never given a fabricated hash. Validate all types,
enums, units, finite numbers, target alignment and derived duplicate fields.

For history freeze the six `HISTORY_FEATURES`, population-standard-deviation
scaling over **prior records only**, zero-scale omission, RMS normalization,
nearest-three limit, deterministic tie order, six-decimal distance presentation,
cluster counts, same-cluster means/deltas and no-prior representation. Replace the
future-dependent total with an explicitly as-of count in a new version; do not
reinterpret `formal_session_count_total` in a frozen artifact.

## 3. Historical leakage: what can and cannot be proved

Reviewed all `ai/history*.py`, their CLI call paths, historical fixtures and verifier.
For correctly identified unique records, the comprehension in `build_history_bundle`
selects `session_number(record) < session_number(target)`. Scales, same-cluster means,
counts and nearest distances are all computed from that `prior` list. Source hashes
select `<= target`, appropriately binding target plus prior. 014 is not in
`FORMAL_SESSION_NUMBERS={5..13,15,16,17}`. The tests confirm that changing future
feature values does not change prior statistics, honest 014 is excluded, and target
005 has empty counts/neighbors/deltas and an explicit unavailable comparison.

**A proof that N cannot consume later formal sessions is currently impossible.**
The loader parses those sessions, counts them in a field sent to the LLM, and can
fail on their corrupt JSON. The frozen 015 artifact itself contains total 12 while
only 9 prior plus target are in its source manifest; its total depends on 016/017,
whose bytes are deliberately not bound. This is metadata leakage, not observed use
of future features in the distance calculation.

014 exclusion can be bypassed accidentally through a mislabeled payload. The
filename is not checked, the session regex accepts a prefix rather than full ID,
and any timestamp suffix with an allowed numeric prefix is admitted. Duplicate
numbers/IDs can inflate statistics or overwrite the `by_id` target. A missing prior
file silently shrinks the sample. A missing history target raises ValueError (5
through CLI after model verification), unlike normal missing target FileNotFoundError
(2). Future sessions above 017 are filtered out only after parsing.

Required proof after B1/B2: for every formal target, compare full bundle, report,
LLM prompt and source manifest against a directory containing only its eligible
snapshot. Add/change/delete/corrupt all later and excluded files: output must be
identical and those bytes must not be read. Then test ID mismatches, duplicate
formal numbers, missing eligible records and non-finite features fail closed.
The earliest session must not let an accepted suggestion invent a nonexistent
prior mean, nearest neighbor or demonstrated discrimination.

## 4. Failure-handling test matrix

| Requested case | Observed result / test evidence |
| --- | --- |
| Missing prospective JSON | Existing normal loader test passes; audit also exercises real missing input. Missing history target rejects, but missing required prior silently succeeds (expected failure). |
| Corrupt prospective JSON | Normal malformed syntax rejects as ValueError; corrupt future history JSON blocks an earlier target (expected failure). Nonobject normal ML input escapes AttributeError (expected failure). |
| Mismatched IDs | Existing and new normal loader tests reject. History filename/payload mismatch admitted (expected failure); nested feature-row ID not checked. |
| Malformed artifact | Audit tests both reference verifiers with `{`, `[]`, `null`, `{}`: rejected. v0.2 branch tests also include invalid UTF-8. No arbitrary saved-artifact command exists. |
| Source changed after artifact | Audit confirms v0.2 reference rejection even for newline change. v0.1 source change is undetected (expected failure). Change between history construction and artifact hashing admits stale bundle (expected failure). |
| Wrong model digest | Existing client and CLI tests reject; CLI produces no report. Builder APIs do not enforce digest validity. |
| Ollama unavailable | New mocked URLError tests exercise inventory and generation: SentinelLLMError. CLI maps this to 4. No real network access. |
| Empty LLM response | Existing `test_empty_response_fails` rejects as SentinelLLMError. |
| Two rejected AI attempts | New history CLI integration probe verifies exactly two calls, exit 6, empty stdout and no save. Normal CLI has only one attempt. |
| Excluded target | Honest 014 rejected; new test repeats it. Mislabeled 014 source can supply an eligible target without saving (expected failure). |
| Future source-manifest entry | New probe adds 017 and recomputes manifest hash; v0.2 exact-source-set check rejects it. It is a fixed-reference check, not a generic target-N policy. |

Critical remaining branches: duplicate JSON keys/IDs, finite numeric validation,
unreadable files and output directory, interrupted/partial writes, malformed Ollama
inventory/generation containers, full CLI error precedence in both modes, mutation
between each read, retry provenance, forged cross-field hashes, prompt/source
injection via unvalidated novelty/ID strings, and all-target future independence.
Only safety-relevant audit tests were added; no implementation-mirroring test count
inflation or live model tests.

## 5. Scientific boundaries

The active CLI deterministically reports completed-session facts. Frozen ML assigns
regimes. Only the proposed experiment is model-generated. That separation is useful,
but the experiment text is still published verbatim after a weak guard.

The new probes establish that **both** suggestion validators accept all four:

- `Repeat the capture. This is device ABC123.`
- `Repeat the capture. Interference caused the observed variability.`
- `Repeat the capture. Bearing is calibrated to within 0.1 degrees.`
- `Repeat and compare to prove reliable device classification.`

`experiment_guard.py` recognizes just two tightly phrased goals plus a measurement
word. History adds reflectivity/propagation/reflection/scattering and two accuracy
phrases, but not device classification, interference causation or paraphrased
calibration claims. Repair instructions mention discriminative language but are
only reached after a rejection; they are not enforcement. Neither guard checks
that claimed numerical facts or historical comparisons occur in the evidence.

The unused-by-CLI full-report API (`prompts.py`, `report.py`,
`llm_client.generate_report`, `output_guard.py`) is also not a scientific contract:
it checks headings and selected phrases, excludes experiment/boundary sections from
claim scanning, and does not compare generated measurements/assignments with input.
Do not present it as a supported v1 fact-generation surface. No new capability is
needed: restrict the documented API to the existing deterministic report path.

`analyst.py` calls C0 “multipath-heavy”; preserve Core's literal MULTIPATH class but
clarify that it is a quality/regime label, not proof of a physical propagation cause.
The saved v0.1 suggestion assumes unchanged “environmental conditions” without
recorded environmental measurements. The saved history report lacks an explicit
scientific boundary paragraph. Add that deterministic paragraph for v1; preserve
old evidence verbatim. Temperature zero and a locked model do not prove safe or
bitwise reproducible prose. Finite regex tests are also not a proof over arbitrary
language; the release must define a bounded accepted output contract and reject
unsupported text without fallback publication.

## 6. Release verification and minimal v1 gate

Both verifiers duplicate tag resolution, AST model-constant inspection, required
files, in-memory compilation, subprocess test execution and PASS/FAIL aggregation.
Canonical/text hashing is duplicated again with artifact modules. Safe future
consolidation is limited to pure byte/hash helpers and parameterized mechanics;
keep release commit, reference hash, schema and source allowlist release-specific.
There is no blocker requiring consolidation now. Preserve the original scripts and
run them against their matching immutable snapshots; do not make them recompute
historical references under new v1 semantics.

v0.2 `EXCLUDED_SESSIONS` contains timestamp suffixes different from the actual
014/016/017 files. Its exact ten-ID allowlist still rejects those actual IDs, so this
is redundant misleading data, not a demonstrated bypass in the verifier. Both
verifiers permit missing tags with an explicit skip and check a tag's target, not
that the checked-out source tree equals that release commit.

Minimum proposed `scripts/verify_ai_v1_release.py`:

1. Read-only offline execution; standard-library artifact checks; compile modules;
   run focused tests with no skipped/expected-failure release requirements.
2. Require the v1 tag/manifest for release mode and verify candidate source identity;
   keep absent-tag development checks clearly distinct from a release PASS.
3. Verify qwen3:14b and digest
   `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`,
   plus frozen ML assets/dataset without loading/training an LLM.
4. Validate both v1 artifact schemas, every hash and cross-field invariant; compare
   source snapshots with disk, regenerate deterministic projections, and verify the
   exact eligible manifest from the bound formal policy. Reject future/excluded IDs
   even if all attacker-supplied internal hashes are recomputed.
5. Pin representative normal, history and earliest/no-history fixtures. Run guard
   rejection/publication tests and all-target isolation tests; verify old references
   separately using historical verifiers. Never regenerate old fixtures to get PASS.
6. Support a general saved-artifact verification entry point with explicit artifact
   and source-root arguments, stable errors and exit 0/1. This is verification of
   existing output, not a new AI reasoning capability.

## 7. Minimal proposed patch set, in dependency order

1. **B1/B2 — history input boundary:** exact formal manifest + eligible-path selection
   before reads; ID/type/finite-value validation; explicit missing-prior errors;
   remove future-derived metadata from new history prompt/schema. Promote related
   expected-failure probes to ordinary tests and add all-target metamorphic cases.
2. **B4 — snapshot consistency:** pass one parsed-and-hashed snapshot through bundle,
   report, prompt and artifact builders. Keep deterministic algorithms unchanged;
   include tests changing disk bytes between stages. Reject inconsistent supplied
   bundles instead of merely hashing them.
3. **B3 — scientific rejection:** shared strict experiment contract for both modes,
   history evidence-reference validation including no-prior behavior; retain or
   strengthen every existing guard. Add rejection paraphrases and safe repeatability
   controls. No generated fact reporting and no new model capability.
4. **B5/S4 — versioned provenance and verification:** v1 schema plus minimal general
   verifier, source/ML/Core bindings and exact attempt provenance. Leave v0.1/v0.2
   scripts/fixtures unchanged. Replace the historical v0.1 negative source-check
   probe with a passing v1 verifier test; do not “fix” an old release in place.
5. **S1/S2/S3 — freeze and document:** consistent CLI errors/save behavior, explicit
   lock boundary, README usage/contracts and release gate workflow. Add tests only
   for failure/publication behavior and documented guarantees.

No blocker fix is claimed in this audit. The 12 expected-failure probes are initial
acceptance tests, not a complete test plan or a reason to release with exceptions.
When implementing fixes, remove their decorators and retain direct assertions;
unexpected successes currently fail unittest so a changed invariant gets reviewed.

## 8. Exact documentation gaps

README already describes Core, frozen ML, 014's exclusion reason, v0.1 hybrid
reporting, the locked digest and the v0.1 verifier. It still needs:

| Topic | Required addition |
| --- | --- |
| Architecture | One Core → frozen ML → deterministic AI analysis/report → guarded local experiment diagram; identify authoritative evidence and read-only boundaries. Separate this pipeline from fingerprinting research and the legacy full-report helper. |
| Claims/non-claims | No transmitter/device identity, unsupported physical cause, calibrated absolute bearing or demonstrated discrimination claim; exploratory C0/C2 limitations; MULTIPATH is a label; cluster recurrence is not device identity. |
| Normal CLI | Exact invocation below, repository-root requirement, three default home log paths, prospective JSON prerequisite, missing-log semantics, stdout/save layout, flags and exit table. |
| History CLI | Exact invocation, eligible formal IDs, 014 exclusion, source directory, numeric acquisition order policy, target/prior distinction, distance/scaling definition and earliest/no-prior behavior. |
| Saved verification | Current release-reference commands are not arbitrary artifact checks. Document the future v1 artifact/source-root verifier only after implementation, including missing sources, mutation, hash scope and integrity versus authenticity. |
| Model locking | Locked model name and full digest; local Ollama endpoint, inventory check, mismatch/unavailable behavior, temperature 0/think false, timeouts (10s inventory, 180s generation), supported API boundary and no bitwise-output promise. |
| Prior-only semantics | No future metadata in reasoning, no source reads beyond eligible snapshot, exact formal manifest/version, target excluded from scaling/means, target included in provenance. Explain that current v0.2 fails the stronger v1 invariant. |
| Release notes | Separate Core v1.0.0, ML 1.0, AI v0.1/v0.2 versions; unchanged release commits and verification branch; actual test count per ref; schema migration, changed history total semantics, compatibility and unresolved blockers. |

Current generation examples (require local locked Ollama; **not offline audit checks**):

```bash
python3 -m ai.cli --session TPMS-NATURAL-015-20260925-020456
python3 -m ai.cli --session TPMS-NATURAL-015-20260925-020456 --save --output-dir results/ai
python3 -m ai.cli --session TPMS-NATURAL-015-20260925-020456 --history --save --output-dir results/ai
```

## Final command list

From `~/hardsignal-kraken-sentinel`, current offline checks:

```bash
python3 -B -m unittest discover -s tests/ai -p 'test_*.py'
python3 -B scripts/verify_ai_release.py
python3 -B tests/readiness/test_ai_v1_readiness.py
git diff --check
git status --short
git rev-parse 'sentinel-ai-v0.2^{commit}'
```

Expected now: 78 legacy tests pass; v0.1 verifier passes; readiness command exits 1
with 12 expected failures; v0.2 resolves to
`4a08b8cc2b42745dd0443d4e331bb5f2fbc23806`. Do not interpret unittest's
`OK (expected failures=12)` as readiness: the standalone runner returns failure.

To reproduce the 96-test checkpoint without switching or modifying this checkout:

```bash
audit_dir=$(mktemp -d /tmp/sentinel-ai-v02-verify.XXXXXX)
git archive 42ec68e237ee66a7dc199e1b8086969fdd339b79 | tar -x -C "$audit_dir"
git -C "$audit_dir" init -q
(cd "$audit_dir" && python3 -B scripts/verify_ai_release.py)
(cd "$audit_dir" && python3 -B scripts/verify_ai_v02_release.py)
git rev-parse 'sentinel-ai-v0.1^{commit}' 'sentinel-ai-v0.2^{commit}'
```

The archive verifiers explicitly skip missing tags; the last command checks the
real repository refs (v0.1 expected `b11760688cd8f9bbb3f8eacde5261f5223712ac1`).
For a formal historical release gate use a checkout with its release tags present.

After proposed fixes, the same readiness tests must pass with **zero** expected
failures, both v1 artifact modes must pass the new offline v1 verifier, historical
release snapshots must retain their existing passes, and frozen ML hashes must
still pass `scripts/verify_ml_release.py` in its documented dependency environment.
The v1 verifier is proposed and does not exist yet; there is no honest v1 release
PASS command at this audit checkpoint.
