# Episode Component Tracking V2 — Draft 1

Status: development/regression specification, separate from frozen Episode
Features V1 and the completed Episode Features V2 development experiment.
This file transcribes the approved proposal before the first Draft 1 execution.
No historical artifact or algorithm may be overwritten.

## Scope and inputs

Identify narrow spectral components recurring within existing Episode Grouping
V1 episodes. Continuity does not establish carrier identity or source attribution.
Use the original manifest, episodes.json and episode-features-v1.json; verify
their capture IDs, membership, byte counts and raw SHA-256 values. Grouping
membership must contain every manifest file exactly once. Preserve recorded
episode/fragment order and mtime_ns, never regroup using live filesystem mtimes.
Read complex128 at 25000 complex samples/s, explicitly as little-endian <c16
for these captures. Record hashes of all three input artifacts and the hash list.
An integrity mismatch stops the capture before spectral extraction and emits a
PROVENANCE_MISMATCH failure record. Do not infer source labels from filenames.

## Spectrum and candidates

For every finite fragment with N >= 4, subtract its complex mean, apply
np.hanning(N), and FFT all N samples without padding, truncation or concatenation.
Shift to ascending frequency order. P = abs(FFT)**2 / (N * sum(window**2)).
Bin spacing is 25000/N Hz, not an uncertainty or accuracy claim.

Eligible intervals are [-11500,-100] and [100,11500] Hz, endpoints inclusive.
These are provisional analysis guards, not a characterized receiver passband.
Keep full spectra and original V1 observations, including excluded maxima.

For each eligible bin, take the median power of eligible bins on the same side
of DC at absolute separations 50 through 500 Hz, inclusive. At least 32 bins
and a finite positive median are required. Contrast is 10*log10(P/background),
called local spectral contrast, not calibrated SNR.

Each maximal contiguous run with estimable background and contrast >= 6 dB
is a component if its maximum contrast is >= 10 dB. The representative is
the largest-power bin, breaking ties toward lower frequency. Integrated power
is the sum across the run; width is last_frequency - first_frequency + bin_spacing.
There is no amplitude-ranked cap. A component remains recorded but is ineligible
for tracking if width > 200 Hz, it touches an eligible-region boundary, or its
adjacent bin inside that region has unestimable background. Multiple local
maxima remain one component, with their count recorded.

## Graph and selection

Nodes are track-eligible components. Edges connect different fragment indices
whose difference is 1 or 2 and whose peak frequencies differ by <= 50 Hz.
Connected components are provisional groups. A group is coherent only if it
has at most one candidate per fragment and a frequency range <= 100 Hz.
Keep incoherent groups as ambiguous; do not split them or select a strong branch.
Order group/track IDs by median frequency, earliest fragment index, candidate ID.

Support counts unique member fragments. Coverage divides by all original episode
fragments, including unusable ones. A coherent track is persistent if support
>= 3 and coverage >= 0.60. Select a primary only if exactly one track qualifies,
no other coherent track spans >= 2 fragments, and no incoherent group spans
>= 2 fragments. Never use amplitude, proximity to -5.3 kHz, source labels,
DoA, activation timing or apparent device separation for selection.

Statuses: UNUSABLE_INPUT (no usable spectra), NO_ELIGIBLE_COMPONENT,
MULTIPLE_PERSISTENT_TRACKS, AMBIGUOUS_ASSOCIATION, INSUFFICIENT_SUPPORT,
UNIQUE_PERSISTENT_TRACK. Resolve overlapping descriptions in that order.
Ambiguity requires an incoherent group spanning >= 2 distinct fragments or
more than one coherent group with >= 2 distinct fragments each. With no such
ambiguity and no qualifying track, use INSUFFICIENT_SUPPORT. Exactly one
qualifying track with competitors is AMBIGUOUS_ASSOCIATION. Primary statistics
are null unless the status is UNIQUE_PERSISTENT_TRACK.

One- and two-fragment episodes cannot demonstrate the required persistence.
Missing observations stay missing. Tracking restarts at each episode.

## Statistics

For every coherent track store unweighted median/min/max frequency, range,
MAD, support, coverage, member/missing indices, adjacent observed frequency
differences, median/minimum contrast, and median width. For singletons retain
frequency but set range, MAD and step statistics to null; flag SINGLE_OBSERVATION.
For every pair of coherent tracks sharing >= 2 fragments, order by track median
frequency and store high-minus-low frequency per shared fragment and median,
range and MAD of the signed spacings. No discrimination threshold is defined.

## Flags

- Input: PROVENANCE_MISMATCH, NONFINITE_IQ, TOO_SHORT, ZERO_SPECTRAL_POWER.
- Spectrum: BACKGROUND_UNESTIMABLE, GLOBAL_MAX_IN_DC_EXCLUSION,
  GLOBAL_MAX_IN_EDGE_EXCLUSION.
- Component: BROAD_COMPONENT, REGION_BOUNDARY_COMPONENT, MULTIPLE_LOCAL_MAXIMA;
  BACKGROUND_UNESTIMABLE also identifies contact with unsupported background.
- Association: MULTIPLE_CANDIDATES_SAME_FRAGMENT, TRACK_RANGE_EXCEEDED,
  ONE_FRAGMENT_GAP, SINGLE_OBSERVATION.
- Episode: SINGLE_FRAGMENT, TWO_FRAGMENTS, LOW_COVERAGE, COMPETING_TRACKS,
  NO_PRIMARY_TRACK. Flags never delete episodes.

Do not claim ADC clipping from processed complex128 without a separate scale.

## Artifacts and determinism

Format: HARDSIGNAL_KRAKEN_EPISODE_COMPONENT_TRACKING_V2_DRAFT1.
Create an exclusive new output directory per capture, outside historical bundles.
Output filenames are run.json, spectra.npz, components.json, tracks.json,
episodes.csv, summary.md and files.sha256. Never overwrite existing outputs.

- run.json: revision/parameters, protocol and extractor hashes, Git commit and
  dirty/untracked declaration, Python/NumPy versions, input hashes, raw inventory,
  byte order and processing status.
- spectra.npz: per-fragment float64 frequency/power/background/contrast arrays,
  eligibility and validity masks and integer component labels. Unavailable
  background/contrast uses zero plus a false validity mask (never a fabricated
  usable value). Nonpositive power has undefined finite contrast and fails detection.
- components.json: all fragments, ordering/recorded timing, path, hash, sizes,
  duration/resolution, flags, V1 diagnostic and all detected components with
  bin bounds, representative bin/frequency/power/background/contrast, maximum
  contrast, integrated power, width, maxima count and eligibility reasons.
- tracks.json: all edges, groups, coherence tests, summaries, pairwise spacings,
  episode statuses and primary ID or null.
- episodes.csv: one row per original episode; counts/status, primary support,
  coverage and statistics (blank means null), original V1 median/spread and
  difference from V1 only when a primary exists.
- summary.md: dataset scope, status counts, missing/ambiguous outcomes, V1
  comparisons and limitations, without identity or improvement verdicts.
- files.sha256: all six generated artifacts above, using relative filenames.

JSON uses null, never NaN/Infinity. Keys, flags, IDs, arrays and hash entries have
deterministic ordering. NPZ members have fixed archive timestamps/attributes;
the output contains no run clock or output path. Given identical inputs,
implementation, environment and repository declaration, artifact bytes repeat.
Hashing the manifest records its current identity, not independent authentication.

## Implementation conventions where the proposal left encoding unspecified

Use one-based fragment indices and zero-based shifted FFT bin indices. Count a
flat local-maximum plateau once, at its lower-frequency end; endpoints of a
component compare against the neighbouring spectral bin. Store masked arrays
for unusable fragments too. A file with non-finite IQ or N < 4 stays in the
denominator, but has no detected components. Invalid/zero spectral power does
not become a candidate. NumPy computations use float64/complex128.
For V1's global-max diagnostic apply its exact-DC exclusion; record the original
V1 value separately. No frozen V1 calculation is changed.

## Development and tests

Run unchanged on PIPELINE-TPMS-004-20260917-233423,
PIPELINE-TPMS-005-20260917-235439, PIPELINE-TPMS-007-20260918-002700,
PIPELINE-TPMS-008-20260918-003900, BETWEEN-DEVICE-V1-20260919-022917 and
BETWEEN-DEVICE-REPL-V1-20260919-024341. All are development/regression evidence,
not independent validation; all 41 episodes remain included.

Tests cover recurring weak components vs stronger unrelated components; two
persistent components; branching/crossing; one vs longer missing-fragment gaps;
inclusive frequency/width/contrast/coverage boundaries; varied lengths and known
tones; DC/edge-only signals; weak/degenerate inputs; single/two-fragment episodes;
provenance failures; deterministic artifacts and unchanged historical inputs.
Further parameter changes require another development revision.
