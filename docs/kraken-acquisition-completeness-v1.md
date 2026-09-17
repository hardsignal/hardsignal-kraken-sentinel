# Kraken Controlled Activation -> RF Acquisition Completeness V1

## Purpose

Test the completeness of the controlled RF acquisition path independently
of Episode Grouping V1 and Episode Features V1.

The experiment asks:

When a controlled operator activation is performed, does the existing
Kraken acquisition pipeline subsequently produce one or more new IQ
recorder files within a pre-registered observation window?

This experiment tests acquisition completeness. It does not test device
identity, RF fingerprint uniqueness, packet identity, transmitter
identity, or transmitter location.

## Motivation

Capture 005 contained six controlled operator activation markers but only
five candidate RF episodes.

A post-hoc timing audit showed:

    A1 -> E01 start +4.490 s
    A2 -> E02 start +4.694 s
    A3 -> E03 start +4.872 s
    A4 -> E04 start +3.793 s
    A5 -> E05 start +4.982 s
    A6 -> no subsequent Capture 005 IQ recorder file

Capture 005 therefore does not demonstrate that Episode Grouping V1
caused the six-to-five discrepancy.

The discrepancy occurred before a sixth candidate episode was available
to the grouper.

The Capture 005 observations are development information only and are
not retrospectively scored using the criterion defined below.

## Frozen acquisition configuration

Use the existing Kraken configuration:

    VFO frequency:       433.868160 MHz
    VFO bandwidth:       25 kHz
    IQ recording:        True
    Squelch mode:        Manual
    Squelch threshold:   -45 dB

Do not intentionally move the Kraken antenna array or controlled source
geometry during the experiment.

Use the same owned controlled TPMS source used for the immediately
preceding repeat experiment.

## Controlled activation procedure

Use:

    capture/log_activations.py

Record six controlled operator activation markers:

    A1 through A6

Use a minimum quiet interval of:

    15 seconds

The operator marker records the operator action. It is not assumed to be
the exact RF transmission time.

## Capture provenance

Use the existing frozen Kraken capture provenance framework.

The capture is valid for this experiment only if:

- capture verification reports PASS
- Kraken settings remain unchanged
- no pre-existing IQ file is modified
- all newly recorded IQ files pass size and SHA-256 verification
- the activation logger completes all six markers
- the frozen acquisition and logging tools remain unchanged during the run

Invalid or aborted captures must be preserved and must not be silently
repeated or deleted to improve the result.

## Pre-registered activation observation window

For each operator activation marker Ai, inspect newly recorded IQ file
modification timestamps.

The observation window is:

    marker time < IQ file mtime <= marker time + 10.000 seconds

The lower boundary is strictly greater than the marker time.

The upper boundary is inclusive.

The 10.000-second upper boundary was selected before the new validation
capture after examining Capture 005 development observations, where the
five observed episode starts occurred approximately 3.793 to 4.982
seconds after their corresponding operator markers.

## Activation acquisition result

An activation is ACQUIRED if at least one new Capture IQ recorder file
has an mtime inside that activation's pre-registered 10.000-second
observation window.

An activation is NOT OBSERVED if no new Capture IQ recorder file occurs
inside that window.

This terminology deliberately does not claim that the physical sensor
failed to transmit when an activation is NOT OBSERVED.

## Primary result

Report:

- number of controlled activation markers
- number ACQUIRED
- number NOT OBSERVED
- acquisition completeness = ACQUIRED / total activation markers

Report every activation individually.

No activation may be removed from the denominator after acquisition.

## Relationship to Episode Grouping V1

Episode Grouping V1 remains frozen and unchanged.

Acquisition completeness is evaluated from new IQ recorder-file
timestamps before episode grouping.

Episode grouping may subsequently be run descriptively, but its output
does not determine whether an activation is ACQUIRED under this
protocol.

## Interpretation limits

An ACQUIRED result establishes only that at least one recorder file was
observed in the pre-registered temporal window following an operator
activation marker.

A NOT OBSERVED result does not by itself establish:

- absence of RF transmission
- transmitter malfunction
- insufficient RF power
- squelch failure
- recorder failure
- packet loss
- device identity

Those mechanisms require separate evidence.

## Freeze rule

After this document is committed, the 10.000-second observation window,
six-activation procedure, denominator, terminology, and acquisition
criterion must not be changed after inspecting the new capture.

Any future methodological change requires a new protocol version.
