# RF Acquisition Completeness V1 — Capture 006

## Capture

PIPELINE-TPMS-006-20260918-001713

## Pre-registration

Protocol:

    docs/kraken-acquisition-completeness-v1.md

Protocol commit:

    1a442f1fd93af01161a88fddb677c3d14e48859a

Protocol SHA-256:

    98966288321d95c34f7111b10fba64f0061866b557dddc60840d839ab8eb5427

The protocol was committed and pushed before Capture 006 began.

## Provenance

Capture verification: PASS

IQ files before: 686
IQ files after: 715
New IQ files: 29
Changed pre-existing IQ files: 0
Kraken settings unchanged: True

Git HEAD at capture start and finish:

    1a442f1fd93af01161a88fddb677c3d14e48859a

Activation logger completed all six controlled operator markers.

## Frozen observation criterion

An activation is ACQUIRED when at least one new Capture IQ recorder file
has an mtime satisfying:

    marker time < IQ file mtime <= marker time + 10.000 seconds

The criterion was frozen before Capture 006.

## Primary result

A1: ACQUIRED
A2: ACQUIRED
A3: ACQUIRED
A4: ACQUIRED
A5: ACQUIRED
A6: NOT OBSERVED

Controlled activation markers: 6
ACQUIRED: 5
NOT OBSERVED: 1

Acquisition completeness:

    5 / 6 = 83.3%

## First observed IQ delay

A1: +4.974 s
A2: +3.134 s
A3: +4.714 s
A4: +5.136 s
A5: +3.846 s

These values are descriptive observations.

## Post-window A6 evidence

The first Capture 006 IQ recorder file after the A6 operator marker
occurred at:

    +10.863321 s

This is 0.863321 s beyond the frozen 10.000-second observation boundary.

Five Capture 006 IQ recorder files occurred after A6, at:

    +10.863321 s
    +11.725423 s
    +12.602212 s
    +13.895192 s
    +14.776986 s

These files are descriptive post-window evidence only.

They do not change A6 from NOT OBSERVED under the pre-registered
criterion, and they do not independently establish the exact physical
RF emission time or the cause of the observed delay.

## Interpretation

Capture 006 produced a pre-registered acquisition completeness result of
5/6 (83.3%) under the frozen 10.000-second observation criterion.

A6 is formally NOT OBSERVED under that criterion.

Any recorder evidence occurring after the 10.000-second A6 boundary is
descriptive late evidence only and does not change the primary result.

A NOT OBSERVED result does not establish that the controlled source
failed to transmit. The experiment does not independently distinguish
between RF emission timing, received signal level, squelch/gating,
recorder behaviour, or other acquisition-path mechanisms.

This experiment does not establish device identity, RF fingerprint
uniqueness, packet identity, transmitter identity, or transmitter
location.

Episode Grouping V1 remains unchanged.
