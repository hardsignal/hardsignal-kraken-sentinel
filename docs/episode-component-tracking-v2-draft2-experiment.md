# Episode Component Tracking V2 Draft 2 experiment

This is a separate implementation of the predeclared development experiment.
V1, committed V2 Draft 1, capture evidence and historical results are immutable.
No IQ is read and no hardware is accessed. The only real-data inputs are the six
committed Draft 1 artifact sets and their stored spectra. All six captures are
development data; none supplies independent validation of a selected method.

## Frozen matrix

Exactly 160 arms: native representation and 2.5 Hz grid envelopes with Gaussian
sigma 0, 5, 10, 20 Hz; width ceilings 200, 225, 250, 275, 300, 325, 350 Hz and
unlimited; Draft 1 connected groups and candidate-disjoint path hypotheses with
cost margins 0, 0.25, 1.0. No winner is selected and no matrix cell is dropped.

Native bin power is uniformly distributed over its bin interval (25,000/N Hz).
Intervals crossing the periodic FFT boundary are split. Exact overlap integration
rebins power into 10,000 bins with edges -12,500 through +12,500 Hz. Their centres
are -12,498.75 through +12,498.75 Hz. Rebinning conserves total power. Division by
2.5 Hz gives PSD. A normalized discrete Gaussian, truncated at ±4 sigma, smooths
PSD with zero extension. Endpoint smoothing can lose power to the exterior;
this must not be confused with a rebinning conservation failure. Component power
always integrates the original unsmoothed spectrum, not the smoothed PSD.

The same Draft 1 background and contrast definitions apply: same-side eligible
bins 50–500 Hz away, median with at least 32 bins, runs at >=6 dB with maximum
>=10 dB. Guards are 100 <= |f| <= 11,500 Hz at bin centres. Guard-touching and
unestimable-background components remain ineligible. Run width includes the
entire bin intervals. Peak frequency is the maximum envelope bin, lower-frequency
tie. Native local maxima (plateaux counted once) and original power are retained.

Path edges allow fragment increments 1 or 2 and displacement <=50 Hz. Whole-path
range must be <=100 Hz. Hypotheses partition eligible candidates into disjoint
paths, including explicit unassigned singletons. Maximize continuation links,
then minimize sum((delta_f/50)^2 + 0.25 for an increment of 2). Retain **all**
maximum-link hypotheses within the declared absolute cost margin of the optimum.
Independent connected groups are factorized, with one global cost allowance.
IEEE float comparisons use a fixed 1e-12 cost tolerance (not a frequency tolerance).

Persistence requires >=3 fragments and >=60% coverage, using the original episode
fragment denominator. A primary must have identical candidate membership in every
retained hypothesis, be persistent, and have no other persistent path in any
hypothesis. Support weights are equal. No cross-episode tracking or amplitude,
DoA, source-label or expected-frequency preference is used. The connected arm
uses the frozen Draft 1 selection rule directly. Its hypothesis-specific fields
are null because connected groups are not path partitions.

## Synthetic fixture conventions declared before execution

Full factorial spectral fixtures use N=10923,21846,43692,54615; FWHM=10,40,280 Hz;
centres -5300,+3000 Hz; constant unit PSD or unit-mean exponential background;
seeds 0–99. Single Gaussian peaks have total peak/background contrasts 8,12,20 dB,
so additive peak PSD is 10^(contrast/10)-1. Pairs use a 26 dB stronger component
at the declared centre and a second at centre+separation, for separations
10,25,50,100,200,400 Hz and additive-power ratios 0,6,12 dB. Both have the declared
FWHM. Ratios are also integrated signal power ratios because widths are equal.
The Gaussian is evaluated at native bin centres. The background RNG is NumPy
PCG64 via default_rng(seed); seeds also enumerate identical constant-background
replicates. These are spectral models, not purported measurements of TPMS signals.
There are 14,400 single and 86,400 paired fixtures (100,800 total), each evaluated
at every one of 40 representation/width combinations. Association is separately
exercised at all four settings, since the spectral fixtures contain one fragment.

Association fixtures cover stable weaker signals with unrelated stronger signals,
two persistent signals, crossings (including coincident candidates), missing one
or two fragments, amplitude reversals, one/two-fragment episodes, exact and just
outside 50/100 Hz limits, exact 60% and below coverage, and 100 noise-only seeds.
Noise fixtures have five fragments, ten independent candidates per fragment,
uniform absolute frequencies 100–11500 Hz, equiprobable signs, contrast 12 dB,
and independent truth identities. Truth labels are used only after association.

## Metrics and decision gates

Every real arm records every fragment's detections, width rejection, interval gaps,
native maxima/subpeaks, original V1 maximum retention and displacement, and
resolution stratum N. The -5500 to -5100 Hz interval is **diagnostic only**:
fragmentation is the count of intersecting intervals, not a physical split label;
power retention is original power covered by eligible intervals divided by
original interval power. No diagnostic region affects detection or tracking.
The four anomalous fragments (004 E01/F03, 004 E06/F03, BETWEEN-DEVICE E06/F04,
REPL E07/F01) retain explicit records, including rejected/out-of-guard maxima.

Every association result records persistent paths, primary/null, all retained
hypotheses, invariant and alternative path membership, structural violations,
support/coverage and status transitions from committed Draft 1. Structural
violations mean violations of emitted path constraints; incoherent connected
components remain diagnostics rather than asserted valid paths.
Synthetic metrics include single splits (multiple eligible intervals intersect
centre ±FWHM), matched frequency errors and recovery within max(5,FWHM/4), pair
merges (one interval contains both centres), and two distinct matched recoveries.
Keep close/unresolved separation strata separate. Association fixtures report
false primary, identity switches per continuation, ambiguity retention, abstention
and correct-primary recovery; report denominators and null undefined rates.

The predeclared gates are: >=50% lower synthetic split rate than matched native;
>=95% 20 dB single recovery; >=95% pair recovery and <=1% merge for FWHM 10 Hz,
separation >=100 Hz; diagnostic dominant retention >=95% of the 204 eligible V1
reference cases (development diagnostic, not identity evidence). Association
requires zero structural violations, no switches/forced primary in deterministic
crossing/competing fixtures, <=1% false primary in noise trials, and improved
correct synthetic recovery or fewer unjustified vetoes, not simply more real
primaries. Publish all passing arms, without selecting one. Incomplete experiment
means gates cannot be evaluated; no passing arm or unresolved merge interpretation
means current evidence does not justify selecting a method.

## Operational completeness

Exact path enumeration/partition dynamic programming is bounded at 200,000 feasible
paths and 200,000 DP states per connected group; retained hypotheses at 1,000,000
per group and per episode. These are computational safeguards, not scientific
caps. At the first exceeded bound the arm is COMPUTATION_UNRESOLVED, its partial
results are explicitly incomplete, remaining cells are NOT_RUN, and execution
stops. No incomplete subset is used as an approximation to the retained set.
All 160 rows are still reported. Input integrity, association fixtures, real matrix,
then full synthetic spectral matrix run in that order. No timing or RNG-dependent
ordering affects scientific results.

Run with `python3 -B analysis/episode_component_tracking_v2_draft2_experiment.py
--output results/episode-component-tracking-v2-draft2-experiment` (one command).
The output directory must not exist. JSON, CSV, Markdown, source/spec/input hashes,
environment and artifact hashes are recorded. Failures exit nonzero. Existing
output and historical files are never overwritten.
