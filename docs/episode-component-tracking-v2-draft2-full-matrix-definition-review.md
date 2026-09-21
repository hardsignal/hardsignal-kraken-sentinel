# Draft 2 full matrix definition review

**Decision: MATRIX_DEFINITION_FROZEN_AND_RECONSTRUCTED**

Review checkpoint: `6bd63ac90b9045ecb2eac3544ee63b035103428b`, branch `codex/draft2-matrix-definition-review`.
This decision reconstructs the definition. It does not authorize execution or
assert that the scientific acceptance gates pass. No matrix, capture, detection,
solver evaluation, commit, or push was performed during this review.

The review artifacts originated on `main` and were copied byte-for-byte into
this isolated worktree. Provenance was repaired and the read-only definition,
source/hash, and integrity checks were rerun here; scientific findings and
original execution history were preserved.

## Authoritative definition and provenance

The original predeclared specification is
[the Draft 2 experiment specification](episode-component-tracking-v2-draft2-experiment.md).
The source of the grid and its ordering is
[the original experiment runner](../analysis/episode_component_tracking_v2_draft2_experiment.py),
constants `REPRESENTATIONS`, `WIDTHS`, `ASSOCIATIONS`, and function `arms()`.
The original experiment had no separate plan JSON. Its specification, constants,
`arms.json`, `arms.csv`, and recorded matrix hash jointly define the plan.

[The original result bundle](../results/episode-component-tracking-v2-draft2-experiment/)
contains both arm inventories, `run.json`, `summary.md`, `review.md`,
`validation.json`, `files.sha256`, association fixtures and their summary, one
complete real result and one explicitly partial real result. `run.json` pins
42 Draft 1 input files and four implementation/control/specification/test files.

Independent checks compared the full ordered grid with source literals, JSON,
and parsed CSV at original commit `51861e1`, provenance-repair commit `f00dc2a`,
and the review checkpoint. The original runner, Draft 1 control implementation,
experiment specification, and original tests are byte-identical at all three.
All 11 current bundle hash entries and all 42 execution-input hashes verify.

- Original specification SHA-256: `3923a1f009a0c798ed97bbfdf8158b36c2673a88b0d687a67e3b921bd352e026`.
- Original runner SHA-256: `73dc27741f3ad5fd710f94a8989a930bb731cd196e32ff2d000ee48e00b9d39a`.
- Original four-field ordered matrix SHA-256: `56765a5350acbfde1712058724b711438ffa0b8cdd2cf4ef91c92b82e56785cf`.

Execution provenance records HEAD `b69d1d1db394adacf224682f235dc304a43e3f69`,
preceding the commit that added these files; the executed source hashes bind the
implementation. This review does not rewrite that historical HEAD.
The `f00dc2a` repair restored the original CSV CRLF bytes and updated provenance
metadata and its manifest. Parsed records, numerical JSON, runner, specification,
and tests did not change. The original CSV line-ending discrepancy and unknown
conversion actor remain documented in the historical validation record.

## Five scientific spectral representations

All inputs remain the same saved Draft 1 spectra. None of these choices is a
compact hypothesis encoding. Grid transformations can change scientific detector
outputs even though they leave stored source files untouched.

| Exact identifier | Representation and preprocessing | Scientific effect |
| --- | --- | --- |
| `native` | Copy native FFT-bin frequencies and powers; spacing `25000/N` Hz; no rebinning or smoothing. | Baseline spectral data; no transformation. |
| `grid_sigma0` | Exact interval-overlap power rebinning to 2.5 Hz bins; divide by 2.5 Hz for PSD; no Gaussian. | Changes the detector grid and potentially candidates. |
| `grid_sigma5` | Same PSD grid, normalized Gaussian sigma 5 Hz, radius 20 Hz, 17 discrete samples. | Scientific smoothing and potentially changed candidates. |
| `grid_sigma10` | Same PSD grid, normalized Gaussian sigma 10 Hz, radius 40 Hz, 33 discrete samples. | Scientific smoothing and potentially changed candidates. |
| `grid_sigma20` | Same PSD grid, normalized Gaussian sigma 20 Hz, radius 80 Hz, 65 discrete samples. | Scientific smoothing and potentially changed candidates. |

Source: original `native_intervals`, `integrate_intervals`, `rebin`, `represent`,
and `detect`. Native bin power is uniform over its `25000/N`-Hz interval;
periodic Nyquist-crossing intervals split at the boundary. The common grid has
10,000 bins, edges -12,500 through +12,500 Hz, centres -12,498.75 through
+12,498.75 Hz. Rebinning conserves total power. Gaussian convolution uses
2.5-Hz offsets through inclusive +/-4 sigma, normalized weights, `same` output,
and zero extension. Smoothing may lose endpoint power; it is not periodic.
Component integrated power always uses original unsmoothed native-bin density,
and native local maxima are retained, counting plateaux once.

## Eight width settings

| Exact value | Unit | Arm token | Tracking eligibility rule |
| --- | --- | --- | --- |
| 200 | Hz | `w200` | Width <=200 |
| 225 | Hz | `w225` | Width <=225 |
| 250 | Hz | `w250` | Width <=250 |
| 275 | Hz | `w275` | Width <=275 |
| 300 | Hz | `w300` | Width <=300 |
| 325 | Hz | `w325` | Width <=325 |
| 350 | Hz | `w350` | Width <=350 |
| Unlimited (`None`, JSON `null`) | Hz ceiling disabled | `wunlimited` | No width rejection; all other eligibility checks remain |

Source: Draft 1 `detect_components` defines width as last frequency minus first
frequency plus bin spacing, so full bin intervals count. Draft 2 `detect` removes
only the baseline `BROAD_COMPONENT` flag; `apply_width` reapplies the declared
ceiling after component-run construction. Width greater than the ceiling is
ineligible; equality passes. Rejected records remain present with unchanged
component indices and IDs. Width is not a smoothing sigma, grid spacing, path
range, or synthetic FWHM.

Only 200 Hz reached the original real matrix. Its connected arm completed;
its margin-0 path arm exhausted a computational budget. That is not evidence
of a scientific defect in the width. The other seven widths have no original
real-data or synthetic spectral execution outcome.

## Four association settings

| Exact identifier | Scientific interpretation | Global margin | Corrected computational mapping |
| --- | --- | --- | --- |
| `connected` | Frozen Draft 1 connected-component selection and recurring-competitor veto. | None | Historical connected branch, unchanged. |
| `paths_margin0` | All admissible maximum-link path partitions under the original cost predicates. | 0 | Exact compact family/query/count machinery; regression label `margin-0`. |
| `paths_margin0.25` | Same path-partition semantics. | 0.25 | Same machinery; regression label `margin-0.25`. |
| `paths_margin1` | Same path-partition semantics. | 1.0 | Same machinery; regression label `margin-1`. |

Source: original `association`, `solve_group`, `path_cost`, and Draft 1
`track_episode`. Edges advance one or two fragments, with frequency step <=50 Hz.
Connected components are undirected groupings of those edges. A coherent group
has at most one candidate per fragment and range <=100 Hz. A connected primary
requires one persistent group, no incoherent group with support >=2, and no other
recurring coherent group with support >=2. Its hypothesis-specific fields are
null; a connected group must not be treated as an asserted path partition.

Path hypotheses are unordered partitions covering every eligible candidate
exactly once, including explicit unassigned singleton paths. Paths advance
strictly through fragments and have total range <=100 Hz. Optimize continuation
links first, then cost. An edge costs `((delta_f/50)**2) + 0.25` for a two-fragment
increment, otherwise `((delta_f/50)**2)`. The absolute margin is dimensionless
and shared globally across the ordered connected factors; it is not allocated
independently per factor. Retain every partition accepted by the frozen
maximum-link and binary64 prefix predicates.

Persistence requires support >=3 and coverage >=0.60. For path arms a primary
must have invariant candidate membership across every retained partition and be
the only possible persistent path in the union. No alternative persistent path
may coexist or appear in another retained partition.

The corrected general implementation uses implicit `EpisodeFamily`, the V3
short-path/matching-polynomial certificate, V2/dyadic/monotone binary64 fallback,
E05 cutoff/cumulative-multiplicity composition, and the candidate-cover exact
query engine. Dispatch depends on structure and certificates, not identities or
expected counts. Zero margin rejects the V3 certificate to its fallback. These
routes are not added arms. The original full experiment runner still contains
the original enumerator; this review does not wire in or launch a replacement.

## Complete Cartesian inventory

[Canonical arm manifest](../results/episode-component-tracking-v2-draft2-full-matrix-canonical-arms.json)
contains all **160 ordered, unique arm IDs** with their representation, width,
association, original identifier, original specification/matrix hashes,
historical state, failure, result path/hash, and completed episode count.
Each restart state is `NOT_EXECUTED`; `execution_authorized` is false.

Naming is exactly `{representation}__w{width-or-unlimited}__{association}`.
Order is representation outermost, width middle, association innermost.
The inventory is **5 x 8 x 4 = 160**, with **0 duplicates, 0 missing combinations,
0 post-hoc additions, and 0 grid drift**. The original matrix digest is computed
over only its four identity fields using the original canonical JSON encoding;
additional review metadata does not redefine that digest.

## What happened in the original experiment

Two real-data arms started, as evidenced by their non-NOT_RUN states and output
files. Two produced result files, but only one produced a complete result.

| Original arm | Historical state | Evidence |
| --- | --- | --- |
| `native__w200__connected` | COMPLETE | 41 episodes, 210 fragments; 8,681 detections, 135 width rejections; 38 ambiguous and 3 insufficient-support episodes; zero primaries. |
| `native__w200__paths_margin0` | COMPUTATION_UNRESOLVED | 26 completed episode records in an explicitly partial file; failure at TPMS-008 E08, the 27th episode. |
| All other 158 combinations | NOT_RUN | No full or partial arm result; no outcome may be inferred. |

The failed group had 73 candidates and 412 feasible paths. The original exact
partition DP stopped at state 200,001 against its 200,000-state limit. The failed
arm has 15 uncompleted episodes including the failing episode; no complete-arm
metric is valid. The original safeguards were 200,000 paths, 200,000 DP states,
and 1,000,000 retained hypotheses per group/episode. They were computational
limits, not scientific truncation allowances.

The complete connected control remains valid historical diagnostic/control data.
Its diagnostic dominant retention is 83/204 (40.69%), below the 95% gate.
The partial path arm emitted seven primaries in its 26 completed episodes;
the JSON review lists all seven capture/episode pairs. There is no device truth
validation for those real primaries, so this review neither labels them proven
false nor treats them as successful full-arm evidence.

All 113 association fixtures ran at all four settings: 452 evaluations.
The full 100,800-fixture spectral matrix never started. Full decision gates were
not evaluable and no method was selected.

| Association setting | Noise false primaries | Crossing switches | Forced crossing/competing primaries | Correct recoverable primaries |
| --- | --- | --- | --- | --- |
| `connected` | 1/100 | 0 | 0 | 4/4 |
| `paths_margin0` | 10/100 | 8 | 0 | 4/4 |
| `paths_margin0.25` | 10/100 | 8 | 0 | 4/4 |
| `paths_margin1` | 10/100 | 8 | 0 | 4/4 |

Connected's false primary was `noise_58`. Each path setting's false primaries
were `noise_07`, `noise_18`, `noise_23`, `noise_27`, `noise_31`, `noise_33`,
`noise_58`, `noise_71`, `noise_92`, and `noise_96`. Their crossing switches occur
in retained paths, including alternatives; they are not device measurements.
The path settings fail both the <=1% noise false-primary gate and zero crossing
switch gate. These are shared association-only fixture results, not evidence
that all 120 path-grid cells executed. Exact computation must reproduce these
scientific failures if semantics are preserved. Partial computational failure
and failed scientific gates remain negative evidence against claiming a
successful experiment; NOT_RUN cells contain no result evidence.

## Scientific configuration that remains frozen

The canonical manifest records the complete representation, width, association,
input, detector, path, numerical, fixture, and decision-gate definitions with
source hashes. In particular:

- Stored spectra and the six capture/41 episode/210 fragment inventory remain
  fixed. Original spectra use 25 kHz, N-point Hann-window FFT, no zero padding,
  and `abs(FFT)**2/(N*sum(window**2))`; this review did not regenerate spectra.
- Frequency eligibility is inclusive `100 <= abs(f) <= 11500` Hz at bin centres.
  Same-sign eligible neighbours at discrete distances 50..500 Hz supply a
  positive finite median background, with at least 32 bins and no wrapping.
  Runs require contrast >=6 dB and maximum contrast >=10 dB. Guard-touching and
  background-unestimable neighbour flags retain their original meaning.
- Peaks use maximum envelope power with lower-frequency ties. Native maxima,
  original component power, full-interval widths, and width rejection rules
  remain fixed. The diagnostic -5500..-5100 Hz region never controls selection.
- Candidate IDs are `E{episode:03d}_F{fragment:03d}_C{component_index:04d}`.
  Component numbering precedes width rejection. Capture/episode/representation
  supplies context; equal strings across representations do not establish the
  same candidate. Distinct equal-frequency IDs are never merged.
- Fragment increments 1/2, step <=50 Hz, whole-path range <=100 Hz, support >=3,
  coverage >=0.60, and equal support weights remain fixed. The denominator is
  every original episode fragment, including empty/unusable fragments.
- Candidate-disjoint unordered partitions and singleton semantics remain fixed;
  no labelled-path permutations or dropped singleton multiplicities are allowed.
  No amplitude, DoA, source-label, expected-frequency, or cross-episode preference.
- Binary64 inputs and cost arithmetic retain forward path summation, right-fold
  local optimum, left-fold emitted cost, local remaining-budget subtraction,
  and ordered episode-prefix filtering. The fixed `1e-12` tolerance applies to
  cost only, never frequency. An algebraically equivalent real inequality does
  not authorize a different floating-point acceptance predicate.
- Synthetic fixtures remain 14,400 singles plus 86,400 pairs, across 40 spectral
  cells: 4,032,000 evaluations. N values 10923/21846/43692/54615; FWHM
  10/40/280 Hz; centres -5300/+3000 Hz; constant/exponential backgrounds;
  PCG64 seeds 0..99; single contrasts 8/12/20 dB; stronger pair contrast 26 dB;
  separations 10/25/50/100/200/400 Hz and ratios 0/6/12 dB. Association fixtures
  and all declared metrics/gates remain hash-pinned.
- Preserve the existing gate implementation: `evaluate_gates` specifically
  requires correct-primary recovery strictly greater than connected. The
  original prose also mentions fewer unjustified vetoes; this review records
  both and does not silently substitute a new gate. This is an existing
  specification/implementation detail, not drift introduced by later work.

Computational replacements may alter enumeration, bounds, caching, count joins,
serialization, and exact query algorithms only while preserving those meanings.
Rational/dyadic/integer arithmetic is admissible only under certificates or safe
bounds proving preservation of the frozen binary64 predicate. Compact lossless
families may replace expanded arrays, but cannot drop hypotheses, round inputs,
change primary rules, suppress failures, or turn unavailable metrics into empty
sets. Original computational limits and corrected regression limits are recorded
separately in the manifest; this review does not authorize a new execution policy.

## Comparison with corrected six-capture milestone

The corrected run contains 164 episode cases: 41 episodes times the same four
association settings, entirely within native/200 Hz. It is four original matrix
arms evaluated on saved candidates, not a new 164-arm grid.

Independent artifact inspection verified all 41 original candidate-context
hashes and denominators, all 123 compact families' candidate inventory and
binary64 frequencies/margins/numerical policy, all 41 historical connected
association payloads, and all 1,521 corrected bundle hash entries. The original
spectral/detector source and specification remain byte-identical.

No representations, widths, association semantics, scientific thresholds, or
candidate construction changed. Compact/connected in the staged consumer is a
family-consumption distinction, not an alteration of the five spectral choices.
The correction does not prove performance, computational completion, or
scientific gate success for the other 156 grid arms. The original incomplete
run and synthetic failures remain unchanged.

## Tests, integrity, and artifacts

Ten read-only review tests passed with zero failures/errors. They check the
independent Cartesian grid, reject missing/duplicate/added/changed/reordered
arms, compare historical commits and CSV/JSON, verify provenance and saved
fixture failures, check the corrected slice, and audit all pre-existing bytes.
No original detector test suite was executed because that would perform
synthetic detection during a review-only task.

All 3,068 pre-existing tracked files remain byte-identical to the pre-work hash
snapshot. HEAD and branch remain `6bd63ac` and `codex/draft2-matrix-definition-review`. Only these four new
untracked review files were created. Tracked diff, `git diff --check`, and
independent whitespace validation are clean. The JSON review stores the full
before snapshot, checks, source history, test log, and final integrity evidence.

- [Definition review JSON](../results/episode-component-tracking-v2-draft2-full-matrix-definition-review.json)
- [Canonical 160-arm manifest](../results/episode-component-tracking-v2-draft2-full-matrix-canonical-arms.json)
- [Read-only review tests](../tests/test_episode_component_tracking_v2_draft2_full_matrix_definition_review.py)
- This definition review document.

The canonical manifest is ready for a separately authorized restart design to
consume without changing the original scientific arm grid. No execution is
authorized by this review decision.
