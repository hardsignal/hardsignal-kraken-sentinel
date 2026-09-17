# Kraken Activation Position V1

## Purpose

Investigate whether activation-to-recorder timing changes with activation
position during a controlled repeated-activation sequence.

This experiment follows descriptive observations from Captures 004-006.

Across those captures:

- A1-A5 produced subsequent IQ evidence in 15/15 observations.
- Their first-IQ delays ranged from 3.133755 s to 5.193033 s.
- A6 produced:
  - Capture 004: first IQ at +4.757527 s
  - Capture 005: no subsequent Capture IQ
  - Capture 006: first IQ at +10.863321 s

These observations motivate the experiment but do not define a new
classification threshold.

## Question

Does unusual activation-to-recorder timing remain associated with the
sixth activation position when the controlled sequence continues beyond
A6?

## Acquisition configuration

Use the existing Kraken configuration:

    VFO frequency:       433.868160 MHz
    VFO bandwidth:       25 kHz
    IQ recording:        True
    Squelch mode:        Manual
    Squelch threshold:   -45 dB

Do not intentionally move the Kraken antenna array or controlled-source
geometry during the experiment.

Use the same owned controlled TPMS source.

## Controlled sequence

Record eight controlled operator activation markers:

    A1 A2 A3 A4 A5 A6 A7 A8

Use:

    capture/log_activations.py

with:

    --count 8
    --quiet 15

Do not perform additional controlled activations during the sequence.

After A8, leave the capture running for at least 30 seconds before
finishing it.

## Provenance validity

Use the existing Kraken capture provenance framework.

The capture is valid for analysis only if:

- capture verification reports PASS
- Kraken settings remain unchanged
- no pre-existing IQ file is modified
- all new IQ files pass size and SHA-256 verification
- the activation logger completes all eight markers
- the relevant frozen tools remain unchanged during acquisition

Aborted or invalid captures must be preserved.

## Timing analysis

For each activation Ai, identify Capture IQ files whose modification
timestamps occur:

    after marker Ai
    and before marker A(i+1)

For A8, use the capture finish time as the upper descriptive boundary.

For every activation report:

- whether any subsequent Capture IQ file exists
- number of such files
- first-IQ delay from operator marker
- last-IQ delay from operator marker

The operator marker is not assumed to equal exact physical RF emission
time.

## Primary descriptive comparison

Report activation positions A1 through A8 individually.

Pay particular attention to A6, A7, and A8.

The experiment does not define:

- an acquisition success threshold
- a latency pass/fail threshold
- an outlier threshold
- a classifier
- a device-identification decision

No observation may be removed because its timing is inconvenient.

## Interpretation

If A6 is delayed or absent while later positions return to the earlier
timing pattern, that would provide evidence that the observed behaviour
is associated with the sixth sequence position under the tested
conditions.

If A6-A8 all become delayed or absent, that would instead motivate
investigation of sequence progression, source behaviour, acquisition
state, or another time-dependent mechanism.

If no unusual late-sequence behaviour occurs, the earlier A6 pattern
would not reproduce in this capture.

None of these outcomes alone identifies the physical mechanism.

This experiment does not establish:

- device identity
- unique RF fingerprint
- packet identity
- exact RF emission time
- transmitter location
- transmitter malfunction
- Kraken malfunction

## Freeze rule

Commit this protocol before acquisition.

Do not modify the eight-activation procedure or timing-analysis method
after inspecting the new capture.

Any changed experiment requires a new protocol version.
