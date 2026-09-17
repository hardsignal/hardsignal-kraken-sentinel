# Kraken Activation Position V1 — Capture 007

## Capture

PIPELINE-TPMS-007-20260918-002700

## Pre-registration

Protocol:

    docs/kraken-activation-position-v1.md

Protocol commit:

    675902e097617aa9365733d35e15185e96b4e3c5

Protocol SHA-256:

    70b4621fb0e474ad173f7b9477177117a8e17a84b86b341fd8e6be64ab989729

The protocol was committed and pushed before Capture 007 began.

## Provenance

Capture verification: PASS

IQ files before: 715
IQ files after: 757
New IQ files: 42
Changed pre-existing IQ files: 0
Kraken settings unchanged: True

Git HEAD at capture start and finish:

    675902e097617aa9365733d35e15185e96b4e3c5

The controlled activation logger completed all eight operator markers.

## Activation-position results

A1:
    files: 5
    first IQ: +4.437400 s
    last IQ:  +8.804561 s

A2:
    files: 5
    first IQ: +5.517683 s
    last IQ:  +9.881198 s

A3:
    files: 6
    first IQ: +3.861133 s
    last IQ:  +9.532842 s

A4:
    files: 5
    first IQ: +5.135846 s
    last IQ:  +9.491585 s

A5:
    files: 6
    first IQ: +3.566053 s
    last IQ:  +9.236104 s

A6:
    files: 6
    first IQ: +4.168226 s
    last IQ:  +9.867815 s

A7:
    files: 5
    first IQ: +5.809819 s
    last IQ:  +9.727220 s

A8:
    files: 4
    first IQ: +6.972265 s
    last IQ:  +10.907049 s

Positions with subsequent Capture IQ:

    8 / 8

Positions without subsequent Capture IQ:

    0 / 8

## Descriptive first-IQ statistics

Minimum:

    3.566053 s

Maximum:

    6.972265 s

Mean:

    4.933553 s

Median:

    4.786623 s

## Late-sequence observations

A6:

    +4.168226 s

A7:

    +5.809819 s

A8:

    +6.972265 s

A6 therefore returned to the same general first-IQ timing region observed
for the earlier positions in this capture.

A7 and A8 showed progressively larger first-IQ delays in this capture.
This is a descriptive observation only. One capture is insufficient to
establish a systematic late-sequence trend.

## Relation to Captures 004-006

Before Capture 007, the observed A6 results were:

    Capture 004: +4.757527 s
    Capture 005: no subsequent Capture IQ
    Capture 006: +10.863321 s

Capture 007:

    Capture 007: +4.168226 s

The unusual A6 behaviour seen in Captures 005 and 006 therefore did not
reproduce as a deterministic sixth-position effect in Capture 007.

This result does not identify the mechanism responsible for the earlier
A6 observations.

Possible mechanisms are not distinguished by this experiment and include
source behaviour, acquisition timing, received signal conditions,
squelch/gating, recorder behaviour, operator-marker timing, or other
time-dependent effects.

## Interpretation limits

The operator marker is an operator-action timestamp and is not assumed
to equal exact physical RF emission time.

A Capture IQ recorder file is evidence of recorder output within the
capture boundary; it is not automatically equivalent to one RF packet,
one transmission, or one physical activation.

This experiment does not establish:

- device identity
- unique RF fingerprint
- packet identity
- exact RF emission time
- transmitter location
- transmitter malfunction
- Kraken malfunction

No new latency threshold, classifier, or acceptance criterion is defined
from Capture 007.

Episode Grouping V1 and Acquisition Completeness V1 remain unchanged.
