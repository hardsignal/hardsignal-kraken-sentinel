# Between-Device Discrimination V1 — Result

## Status

COMPLETE — NO USEFUL BETWEEN-DEVICE SEPARATION OBSERVED

## Experiment

Protocol:

    docs/kraken-between-device-discrimination-v1.md

Held-out selection:

    experiments/between-device-v1-heldout-selection.md

Held-out source:

    S2

Capture:

    PIPELINE-TPMS-008-20260918-003900

## Provenance

Capture verification:

    PASS

IQ boundary:

    757 -> 796

New IQ files:

    39

Changed pre-existing IQ files:

    0

Kraken settings remained unchanged.

Git start and finish:

    bfc72c4543e5f9b290fd49983a1aa84a3176e0f7

Eight controlled operator activation markers were completed.

## Frozen Episode Grouping V1

Input IQ files:

    39

Frozen grouping threshold:

    inter-file gap > 4.000 seconds

Candidate episodes:

    8

Episode fragment counts:

    E01  5
    E02  5
    E03  5
    E04  6
    E05  5
    E06  6
    E07  5
    E08  2

The eight controlled activation markers and eight candidate episodes are
count-concordant in this capture.

A candidate episode is not automatically equivalent to one RF packet,
one physical transmission, or one independently verified activation.

## Frozen Episode Features V1

Primary quantity:

    median_strongest_component_offset_hz

Held-out S2 episode values:

    E01  -5184.015380 Hz
    E02  -5197.747871 Hz
    E03  -5195.459123 Hz
    E04  -5204.041930 Hz
    E05  -5210.335988 Hz
    E06  -5204.614117 Hz
    E07  -5208.047240 Hz
    E08  -5218.346608 Hz

S2 capture-level median:

    -5204.328023 Hz

S2 minimum:

    -5218.346608 Hz

S2 maximum:

    -5184.015380 Hz

S2 episode-median range:

    34.331228 Hz

## Episode spreads

    E01  27.464982 Hz
    E02  13.732491 Hz
    E03  21.743111 Hz
    E04  11.443743 Hz
    E05   6.866246 Hz
    E06  25.176234 Hz
    E07  9263.709604 Hz
    E08   9.154994 Hz

E07 is retained without post-hoc filtering.

## Pre-registered S2 vs S1 comparison

Prior S1 capture-level medians:

    Capture 004  -5203.469743 Hz
    Capture 005  -5193.170374 Hz
    Capture 007  -5201.180994 Hz

Held-out S2:

    Capture 008  -5204.328023 Hz

Differences from S2:

    S2 - Capture 004  = -0.858280 Hz
    absolute          =  0.858280 Hz

    S2 - Capture 005  = -11.157649 Hz
    absolute          =  11.157649 Hz

    S2 - Capture 007  = -3.147029 Hz
    absolute          =  3.147029 Hz

Nearest prior S1 capture-level median:

    Capture 004

Nearest absolute difference:

    0.858280 Hz

Previously observed range among the three S1 capture-level medians:

    10.299368 Hz

## Interpretation

The held-out S2 capture overlaps closely with the existing S1
capture-level measurements.

Therefore the frozen Episode Features V1 primary spectral quantity did
not demonstrate useful between-device separation between S1 and S2 in
this held-out controlled test.

The result does not invalidate the previously observed same-source
repeatability. Instead, it shows that repeatability of this feature alone
is insufficient for S1/S2 discrimination under the tested conditions.

No identity threshold was defined or fitted after observing S2.

No observations were removed to improve separation.

## Limits

This result does not establish:

- unique device identity;
- absence of other discriminative RF features;
- equivalence of S1 and S2 transmitters;
- packet identity;
- exact RF emission time;
- transmitter location;
- universal performance across TPMS devices.

The conclusion applies specifically to the frozen Episode Features V1
primary spectral quantity and this controlled S1/S2 experiment.
