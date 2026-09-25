# Sentinel AI artifact contract 1.0

Status: implemented candidate contract; **no v1 release tag or reference release
has been created**. `ai/v1_artifact.py` is the executable semantic specification;
[sentinel-ai-artifact-v1.schema.json](sentinel-ai-artifact-v1.schema.json) describes
the envelope's structural types. Both checks are needed: JSON Schema alone does
not validate scientific semantics, source membership, derivations or hashes.

## Authority and scope

Core computes RF/DoA summaries. Frozen Sentinel ML supplies behavioural cluster,
distance and novelty observations. AI composes deterministic reporting from these
inputs and generates only the next controlled experiment. AI does not modify Core
evidence, refit ML, assign device identities, explain unsupported physical causes,
claim calibration-grade direction, or establish device discrimination.

The formal historical set remains 005–013 and 015–017. For target 015, its snapshot
contains exactly 005–013 and 015; 014 is excluded, not required, and never admitted.
Future files are filtered before reading. Target 005 has one source and no priors.
Identity validation precedes prefix completeness. Scaling/means/neighbors use only
prior records, and the snapshot manifest includes prior records plus the target.

## Version and canonical encoding

New CLI saves use `artifact_version="1.0"`,
`schema_version="sentinel-ai-artifact/1.0"`. Old constructors and retained old
artifacts keep their historical versions. The generic v1 verifier does not upgrade
or reinterpret v0.1/v0.2 artifacts.

Canonical JSON hashing uses UTF-8, sorted string keys, separators `(',', ':')` and
`ensure_ascii=False`, with **no non-finite numbers**. Object key order and JSON
formatting of the outer artifact do not affect internal hashes. Arrays retain
order. Integer and floating-point representations are distinct for hashing;
Unicode is not normalized. Duplicate keys, NaN, Infinity and overflow-to-infinity
are rejected, including inside embedded source JSON. This is the defined Python
3.12 serialization contract, not a claim of RFC 8785 interoperability.

Text hashes cover exact UTF-8 bytes. `source_records_json` preserves each source's
original UTF-8 text, including whitespace and newlines; its digest is computed
from those bytes, not from reserialized JSON. Snapshots contain immutable raw bytes
and deeply immutable parsed records. Reading several files is not an atomic
filesystem transaction; each retained record is exactly the one read for the
operation. Later mutations cannot alter that operation's snapshot.

## Required common fields

The envelope rejects missing and unknown fields. `mode` is `normal` or `history`.

| Field | Frozen contract |
| --- | --- |
| `artifact_version`, `schema_version` | Exact version strings above |
| `created_at` | ISO 8601 UTC timestamp with timezone |
| `mode`, `session_id` | Mode and one canonical target ID; history uses a fully validated natural-session ID |
| `report_mode`, `ai_scope` | Normal: `deterministic_with_ai_experiment`, `next_controlled_experiment_only`; history: `deterministic_history_with_ai_experiment`, `historical_next_controlled_experiment_only` |
| `model` | `qwen3:14b` |
| `model_digest` | `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8` |
| `scientific_policy_version` | `sentinel-ai-scientific-policy/1.0` |
| `derivation_version` | `sentinel-ai-deterministic/1.0` |
| `ml_lineage` | Exact model/record versions `0.1` and frozen training dataset SHA256 |
| `source_records_json` | Session ID → exact source JSON text |
| `source_record_sha256` | Identical session set → raw UTF-8 source digest |
| `source_record_manifest_sha256` | Canonical SHA256 of `source_record_sha256`; identifies immutable evidence snapshot |
| `experiment_prompt`, `experiment_prompt_sha256` | Initial authoritative AI experiment prompt and exact text hash |
| `experiment_suggestion`, `experiment_suggestion_sha256` | Accepted suggestion and exact text hash; must pass the frozen mode's scientific guard |
| `artifact_sha256` | Canonical SHA256 of the whole envelope **excluding this field only**, covering metadata as well as all payloads and other hashes |

The training dataset digest is
`e1a63cf6be87d85584a9201e395b1fcdd8251ee7c6cb09ce5eb502886cf76a51`.
Every embedded ML record must agree with the envelope's lineage, top-level session
and nested `feature_row.session_id`. The verifier checks cluster, novelty, numeric
types, distances and assignment/distance consistency. It does not rerun the frozen
model or infer ML assignments. The separate release gate checks the dataset,
serialized model and ML manifest file hashes using the existing frozen ML release
constants, without loading or training the model.

Hashes demonstrate consistency, not authorship or truth. A trusted release
manifest can additionally pin complete artifact files. Anyone able to replace all
source evidence and recalculate hashes can produce a different internally
consistent artifact; this format is not a signature or trusted timestamp.

## Normal mode

Required additional fields:

- `evidence_bundle` and `evidence_bundle_sha256`: deterministic Core summary, frozen
  ML result and ML source path/hash. Exactly one source is admitted: the target's
  ML prospective JSON. Its embedded ML object must equal the parsed raw source.
- `core_evidence_scope="embedded_deterministic_summary"`: the embedded Core summary
  is hashed, type checked and session checked. **Original Core log/RF bytes are
  not available as provenance in this AI evidence path and are not claimed to be
  authenticated by v1**. This scope is explicit, not a fabricated raw-log hash.
  Missing logs remain explicit in the Core summary.
- `deterministic_report` and `deterministic_report_sha256`: normal deterministic
  report composition with the experiment slot empty. This separates generated
  prose from completed-session evidence.
- `report` and `report_sha256`: complete deterministic composition with the accepted
  AI suggestion inserted into the designated experiment slot.

The verifier reconstructs both report forms and the initial experiment prompt.
The normal evidence loader retains the exact ML source text and computes its hash
from the same read. The v1 builder requires that captured text; it never rereads
an ML file while saving. A source path in the evidence bundle is informational;
its basename must agree with the target. It is never followed by the verifier.

Normal source snapshots authenticate the ML record and embedded Core summary at
the AI boundary, not the derivation of original features from hardware logs.

## History mode

Required additional fields:

- `history_bundle` and `history_bundle_sha256`.
- `history_report` and `history_report_sha256` (entirely deterministic).

The bundle also contains `source_record_manifest_sha256`, equal to the enclosing
snapshot manifest hash. It binds derived values even when a source changes only
in formatting or in a field unused by history statistics. The generator requires
an explicit snapshot and rejects an old bundle/report/prompt paired with a new
snapshot. The verifier reconstructs a snapshot from embedded raw source bytes,
revalidates identity and the complete formal prefix, and recomputes the entire
bundle, deterministic report and initial prompt. It rejects 014, future records,
duplicate acquisition numbers, missing priors, and rehashed false counts/means/
neighbors. A complete 015 bundle has total 10 and prior count 9.

The six features, population-standard-deviation scaling, zero-scale omission,
RMS distance, deterministic ordering and nearest-three limit retain the existing
history algorithm. Historical records retain their frozen model/dataset lineage.
No future source file is read by the v1 verifier's optional source check: it opens
only the already validated manifest members.

## Scientific-policy and prompt reproducibility

The versioned policy identifies the current shared/history experiment guards.
Verification reruns them; unsafe generated text cannot pass by merely rehashing it.
Derivation/policy changes require a new supported contract version or maintenance
of a version-specific implementation. Do not silently reinterpret v1 under new
rules. A release manifest pins the corresponding implementation commit.

`experiment_prompt` means the initial authoritative prompt. History may perform
its existing bounded repair attempt; this contract does not retain rejected draft
text or claim to be a complete Ollama request/response transcript. The verifier
reproduces deterministic prompt/report derivation and validates the accepted
suggestion; it does not regenerate AI text or promise bitwise LLM output replay.
Model temperature zero and a matching digest are not evidence of scientific
validity. All generation capabilities and guards remain unchanged.

## Generic verification

From the repository root, with Python 3.12 and no third-party packages:

```bash
python3 -B scripts/verify_ai_artifact.py /path/to/saved-v1.json
python3 -B scripts/verify_ai_artifact.py /path/to/saved-v1.json --source-dir results/ml/prospective
```

Default checks only the self-contained artifact and its embedded sources.
`--source-dir` additionally checks current `<session_id>.json` files against
recorded raw-byte hashes. Missing, changed and out-of-directory symlink sources
fail. Artifact-supplied paths are never used to select filesystem inputs.
Future/excluded files outside the manifest are irrelevant. A valid snapshot can
pass embedded-only verification after disk mutation, while current-source checks
correctly fail. There is no dependency on one retained reference artifact.

Exit 0 = PASS, 1 = validation/read failure, 2 = argparse usage error. Output states
whether current sources were checked. Verification is read-only, performs no
network calls, loads no ML binary and runs no LLM. Save filenames are
`results/ai/<session>/sentinel_ai_v1_<timestamp>.json`, or under `history/<session>`.

## Separate candidate/release gate

```bash
python3 -B scripts/verify_ai_v1_release.py --candidate
python3 -B scripts/verify_ai_v1_release.py --manifest /path/to/release-manifest.json
```

Candidate mode checks frozen ML file hashes, compilation and the full readiness
suite; it explicitly does **not** claim tagged release verification. Release mode
additionally requires this release manifest shape:

```json
{
  "schema_version": "sentinel-ai-release/1.0",
  "tag": "sentinel-ai-v1.0",
  "commit": "<full eventual release commit>",
  "references": {
    "results/ai/<normal-reference>.json": "<raw file SHA256>",
    "results/ai/history/<history-reference>.json": "<raw file SHA256>"
  }
}
```

Placeholders above are documentation, not usable pins. No reference or tag is
created automatically. Release mode requires pinned references covering both
modes, their current ML sources, the exact tag target, matching HEAD, a clean
checkout, and the candidate checks. An external release manifest can pin the
release commit without a self-referential in-repository commit hash.

## Accepted historical limitation

**Sentinel AI v0.1 did not bind all source records, and that historical release
remains unchanged.** Its retained reference verifier checks embedded hashes but
does not detect changed external ML source JSON. This is an accepted documented
legacy limitation, not a v1 invariant and not retrofitted into the v0.1 verifier.
The old test now characterizes that accepted behavior. The v1 gate instead runs
current-source corruption tests against the generic v1 verifier.

Both `sentinel-ai-v0.1` and `sentinel-ai-v0.2` tags, retained artifacts and historical
verifiers stay intact. New contract tests never rewrite them. Readiness requires
all current probes **and the entire tests/ai suite**, with no failures, expected
failures or skips; documenting the old limitation alone cannot turn a broken v1
verifier into a readiness PASS.
