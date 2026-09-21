# Stage 37 final configuration selection

**Decision: STAGE37_V1_CONFIGURATION_SELECTION_DEFERRED**

No representation + width + association is selected. The frozen evidence is
internally coherent and computationally usable for 152 arms, but it does not
resolve the scientific tradeoffs needed to prefer one configuration. This is
not a finding that all configurations failed, nor a request to tune frozen V1.
No frozen V1 configuration file is created and no reproduction run is authorized
or performed by this decision.

## Evidence and provenance

Selection starts at `b109ede179e11021e13b8a84713439aa8a4c1ab8` on
`codex/stage37-configuration-selection`; HEAD satisfies the checkpoint ancestry
check (initially equal to the checkpoint). The Stage 36 execution commit is
`e559d63e3a88822ff5443d5a83d0ad60fc3e3348`, distinct from the evidence freeze at
`0df44abb54231d5e8bfe84fe316ebbcf10d3130c` and the selection checkpoint.

The [selection JSON](../results/episode-component-tracking-v2-stage37-configuration-selection.json)
binds the Stage 36 audit, inventory, manifest, launch plan/binding, scientific
sources, inputs, both Stage 37 reviews and reports, definition-review evidence,
and provenance repair to exact checkpoint hashes. The two reviews are unchanged.
The repair still validates the exact historical/current `.gitignore` transition
and the two explicitly bound validator changes; it does not waive arbitrary
source drift. Historical statements about nine provenance errors in the reviews
remain historical statements, superseded operationally by the valid repair.

The read-only raw checks verified **46,524 files / 8,286,982,589 bytes**, including
inventory equality, hashes, receipts, saved scientific projections and resource
reconstruction. No raw evidence changed. All pre-existing tracked files remain
unchanged from `b109ede`; no scientific constant, solver or resource limit was
modified. Accounting remains **160/160, 152 COMPLETE, 8 COMPUTATION_UNRESOLVED,
0 missing, 0 duplicates**. All 128 grid arms completed; native has 24 complete
and eight unresolved. Smoke runs remain excluded from canonical accounting.

Sources: [Stage 36 audit](../results/episode-component-tracking-v2-draft2-stage36-final-audit.json),
[scientific review](episode-component-tracking-v2-stage37-scientific-review.md),
[computational review](episode-component-tracking-v2-stage37-computational-review.md),
[provenance repair](episode-component-tracking-v2-stage37-provenance-repair.md),
and [Draft 2 definition review](episode-component-tracking-v2-draft2-full-matrix-definition-review.md).

## Decision hierarchy applied

1. **Scientific validity.** Saved outputs are coherent, but more UNIQUE outcomes,
   fewer alternatives or zero structural violations do not establish better
   association. Rebinning and smoothing change the measured candidates; their
   equivalence is not established. Real truth metrics are NOT_APPLICABLE.
2. **Stability.** Compare episode statuses, actual primary candidate IDs and
   persistent membership sets, not labels alone. Membership comparisons stay
   within representation and episode; equal IDs across representations or
   episodes do not establish shared physical identity.
3. **Negative evidence.** Retain noise false primaries, crossing switches,
   ambiguity, insufficient support, no-eligible outcomes, E07 and anomalous
   strongest bins. Historical fixtures are association-only evidence, separate
   from Stage 36 real observations.
4. **Completeness.** Complete arms have all six captures, 41 episodes and 210
   original fragments. No extraordinary exception justifies selecting an
   unresolved arm; no missing episode is inferred.
5. **Computational feasibility.** Recorded time, RSS, exact counts and queries
   support execution feasibility only. They cannot settle scientific tradeoffs.
6. **Robustness over local optimum.** Prefer a membership-stable region over an
   isolated favorable arm. Such regions exist, but do not resolve the earlier
   validity/negative-evidence questions across families.
7. **Simplicity.** A final tie-breaker only for scientifically indistinguishable
   configurations. Equal smoothed-path margins are indistinguishable on these
   saved inputs, but transformations and association rules are not thereby
   equivalent. Simplicity cannot promote one entire family past earlier issues.

No weighted score, new acceptance gate or post-hoc threshold is used.

## Candidate comparison

The shortlist covers all seven scientifically distinct candidate families.
Counts below describe 41 episodes per complete arm and are not quality scores.
The JSON retains all 160 identities/states, complete per-episode projections,
actual persistent memberships, per-capture summaries, primary memberships,
neighbor comparisons, spectral/anomaly observations and per-arm resources.

| Candidate family / widths | Saved scientific behavior and neighboring-width evidence | Why not selected |
| --- | --- | --- |
| Native connected, all eight widths | All COMPLETE; no primary at any width. 38 ambiguous/3 insufficient through 275; 40/1 from 300. Emitted and persistent memberships stabilize at 325/350/unlimited; 1,196 incoherent groups across widths remain. | Preserves native bins and has connected's better fixture behavior, but stable abstention does not demonstrate correct recovery or superiority to grid alternatives. |
| Native margin0, all widths | All COMPLETE; UNIQUE 14 at 300 then 12 at 325, while MULTIPLE rises 23 to 27. Memberships stabilize at 325/350/unlimited. | More candidates can introduce competitors. Historical path negatives persist; wide-arm observed runtime leaves little headroom. Neither fact proves scientific inferiority, but no unique selection advantage is established. |
| Native margins 0.25/1 | 200–275 COMPLETE, eight wider arms unresolved. At 200, 457/1,383 persistent memberships versus 1/0 primaries for margins 0.25/1. | Alternatives encode uncertainty; more persistence is not less ambiguity. Wide-region scientific comparisons are unavailable. Complete narrow arms retain path-fixture failures. |
| Grid sigma0 connected, all widths | All COMPLETE; at 325/350/unlimited, 10 UNIQUE, 30 ambiguous, 1 insufficient, with stable memberships. Two primary memberships change from 300 to 325 despite constant labels. | Rebinning changes candidates, incoherent groups remain, and lower primary yield is not validated as more correct than smoothed connected. |
| Grid sigma0 paths, all widths/margins | All COMPLETE. Margin0: 36 UNIQUE at 300, 35 at 325 with four MULTIPLE; wider plateau stable. Positive margins change both statuses and memberships and retain more alternatives. | Historical false primaries/switches prevent interpreting additional primaries as validated recovery; no margin resolves those failures. |
| Grid sigma5/10/20 connected, especially 325/350/unlimited | All COMPLETE. Sigma5/10: 37 UNIQUE, 2 ambiguous, 2 insufficient; sigma20: 38/1/2. Primary/persistent memberships change at 325→350 for every sigma and again at 350→unlimited for sigma20. Sigma5/10 stabilize at 350/unlimited. | Strongest conservative alternatives, given connected's fixture advantage. But the evidence does not validate smoothing-induced removal of competitors or distinguish sigma5/10 scientifically; higher UNIQUE yield cannot decide. |
| Grid sigma5/10/20 paths, especially 325/350/unlimited | All COMPLETE. All margins: 39 UNIQUE, 2 insufficient. Margins have identical memberships; every one of the 2,952 complete smoothed-path episode-arm results has exact cardinality one. Primary/persistent changes still occur at the width boundaries above. | Attractive status plateau does not override 10/100 fixture false primaries and eight crossing switches. Margin simplicity can settle only an internal saved-input tie, not representation or association validity. |

Narrow smoothed widths 200–275 have zero persistent tracks. The 275→300 transition
changes 36, 37 and 34 path statuses for sigma5, sigma10 and sigma20 respectively.
At 300, smoothed path UNIQUE counts are 36/37/32, rather than the later common
39. Selecting an isolated transition point or the largest count would violate
the hierarchy. Tight filtering can suppress competitors; broad filtering can
admit them. Neither is independently a correctness measure.

There are 132 comparable neighboring-width pairs out of 140. Of 63 pairs with
identical statuses, 43 change emitted membership sets. The selection additionally
extracts **actual persistent memberships** from hash-verified saved `arm.json`
files, rather than treating an all-path hash or persistent count as a persistent
membership identity. Primary and persistent changes at 325→350 occur in TPMS-007
E05 for sigma5 and BETWEEN-DEVICE-REPL E06 for sigma10/20; sigma20 changes again
in TPMS-005 E05 at unlimited. These changes occur in every association method.
The JSON records the exact changed episode indices and members.

All six captures remain in each complete arm's comparison. Their per-capture
summaries and episode denominators are preserved; there is no cross-episode
candidate identity claim or independent replication claim from repeated arms.
BETWEEN-DEVICE-REPL E07 remains insufficient in all 152 complete arms, with its
one original fragment. No candidate abundance supplies missing temporal support.

## Decisive negative evidence and reason for deferral

Historical association fixtures give connected **1/100 noise false primaries,
zero crossing switches, 4/4 correct recoverable primaries**. Each path setting
gives **10/100, eight switches, 4/4**, respectively. Forced crossing/competing
primaries are zero for all methods, which does not erase switches in retained
paths. Connected's `noise_58` false primary also remains. These observations are
not estimates of Stage 36 real-data false-primary or identity-switch rates.

The paths fail the historical <=1% noise and zero-crossing-switch gates. The
saved 4/4 recovery counts do not meet the committed implementation's requirement
for strictly greater recovery than connected. We do not substitute the looser
prose about fewer unjustified vetoes for that implementation. Connected's better
association-fixture evidence is relevant, but is shared across all its spectral
cells; it does not validate sigma5/350, sigma10/350 or any other exact cell.
The full synthetic spectral matrix did not run in Stage 36, leaving the declared
spectral recovery/merge/split comparisons unevaluated. This is missing robustness
evidence within V1's spectral scope, not a demand for carrier/device truth as a
prerequisite for describing FFT fragments.

At unlimited width native retains the strongest bins in the three anomalous
fragments TPMS-004 E01/F03, TPMS-004 E06/F03 and BETWEEN-DEVICE E06/F04; sigma0
retains only the third; all smoothed grids retain none and have no eligible
candidate in those three fragments. High retention in the diagnostic
−5500..−5100 Hz region is not evidence of universal retention or correctness.
All four predeclared anomalous fragment records, including E07, remain in JSON.

The nearest alternatives are therefore **sigma5/350/connected** and
**sigma10/350/connected**, their unlimited counterparts, and the corresponding
smoothed path arms. Sigma20 has an additional membership change at unlimited.
Native/sigma0 wide plateaus preserve a different candidate/ambiguity structure.
No saved evidence establishes that these scientifically different choices are
equivalent or resolves which alteration is preferable. Simpler transformations,
more UNIQUE outcomes and faster execution cannot settle that prior question.
A unique choice would therefore require an unsupported preference.

Any additional independent spectral recovery/merge/split or association-robustness
validation belongs to separately predeclared **V2/future work**. This decision
proposes no tuning, matrix retry, changed limit, new score or alteration of V1.

## Computational feasibility and unresolved treatment

All grid arms completed in 28.243–36.033 seconds, peak observed RSS <=167,068 KiB.
Sigma5/350/connected took 30.149790 s and 143,240 KiB; sigma10/350/connected took
28.895856 s and 143,052 KiB. Sigma5/350/margin0 took 31.107504 s and 142,412 KiB.
These candidates are feasible on the saved run, but timing is not a scientific
ranking. Native complete arms took 67.246–384.584 s; the slowest left only
15.416 s of its 400 s worker ceiling. Repeated-run variability was not measured.

Frozen limits remain: count 250,000 states, 5,000,000 transitions, 60 s and
33,554,432 polynomial bytes; family construction 60 s; queries 5,000 calls and
120 s; one worker, 400 s and 524,288 KiB RSS. The distinct exact-cover bound is
200,000 visits. Saved maxima are 74,064 count states, 385,664 transitions,
44.584254 count seconds, 20,584,913 polynomial bytes and 1,695 public query calls.
Exact cardinalities can be enormous without explicit enumeration; they are not
confidence scores. Connected count/query fields are inapplicable, not zero.
Missing query/family durations and failed-search counters are not spare capacity.

Exactly native × {300, 325, 350, unlimited} × {paths_margin0.25, paths_margin1}
remain COMPUTATION_UNRESOLVED, retaining:
`Unresolved: Exact-cover search limit reached; result is unresolved`.
Their saved episode-001 results remain partial provenance, not full-arm summaries.
Missing episodes are never inferred. **Unresolved computation is neither a
scientific failure nor a scientific success.** No unresolved arm is selected.

## V1 claims boundary

| Claim | Category | Exact scope |
| --- | --- | --- |
| Dominant non-DC FFT-bin / fragment behavior | SUPPORTED | Saved observations under each complete configuration on these six captures; no final configuration is selected. |
| Persistence observations | SUPPORTED | Candidate memberships under >=3 fragments and >=60% of original episode fragments, including unusable fragments in the denominator. No physical-source persistence claim. |
| Between-device comparison | DESCRIPTIVE ONLY | Capture differences; no validated device discrimination. |
| Carrier identity | NOT SUPPORTED | Dominant bins/fragments do not establish carrier identity. |
| Device identity / fingerprinting | NOT SUPPORTED | No device-identity accuracy or validated fingerprint. |
| Universal threshold claims | NOT SUPPORTED | No universal width, smoothing or detection threshold established by reused development captures. |
| Source association correctness | NOT SUPPORTED | Zero structural violations, uniqueness and stable memberships do not prove correct source association. |
| Computational feasibility | SUPPORTED | Recorded completion of 152 arms within frozen budgets; no future timing guarantee or scientific quality implication. |

More persistent memberships do not automatically mean less ambiguity. A union
of alternative memberships is not a simultaneous source count. Stable status
labels can conceal changing primary memberships. These limitations survive
regardless of any later configuration decision.

## Reproduction disposition and validation

There is no selected configuration and therefore no frozen V1 reproduction
specification. The JSON preserves inherited scientific constants, resource
limits, source/input bindings and the expected saved-evidence scope for audit;
it is not an executable selection or permission to rerun the experiment.

Commands use `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=analysis:tests`:

- Selection tests: `STAGE37_VERIFY_RAW=1 python -m unittest discover -s tests -p 'test_episode_component_tracking_v2_stage37_configuration_selection.py'` — 12 passed.
- Stage 37 reviews: `STAGE37_VERIFY_RAW=1 python -m unittest discover -s tests -p 'test_episode_component_tracking_v2_stage37*review.py'` — 13 passed, no skips.
- Draft 2 full matrix: `python -m unittest discover -s tests -p 'test_episode_component_tracking_v2_draft2_full_matrix*.py'` — 54 passed.
- Review integration: `python -m unittest test_episode_component_tracking_v2_draft2_review_integration` — 6 passed.
- `git diff --check` — passed.

**85 tests passed.** Selection regressions bind the full payload/report, reject
candidate/decision/negative-evidence/limit drift, reconstruct persistent
memberships without scientific execution, check conservative claims, and verify
the original manifest, accounting, unchanged reviews and provenance repair.
Only this report, its selection JSON and its regression test are added.
