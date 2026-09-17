# Kraken Recorder Episode Grouping V1

## Purpose

Define a deterministic, non-destructive method for grouping Kraken IQ
recorder files into candidate RF acquisition episodes.

This mechanism is an acquisition/provenance tool. It is not an RF
identity classifier.

## Development dataset

Capture:

PIPELINE-TPMS-001-20260917-202651

Controlled procedure:

- one owned TPMS source
- six deliberate activations
- fixed physical geometry
- Kraken configuration unchanged
- 433.868160 MHz
- 25 kHz VFO bandwidth
- manual squelch -45 dB
- IQ recording enabled

The capture produced 33 Kraken IQ recorder files.

## Development observation

Inter-file modification-time gaps separated into two non-overlapping
regions.

Largest observed within-episode gap:

2.194 seconds

Smallest observed gap separating controlled activations:

6.977 seconds

No observed gap occurred between 2.194 and 6.977 seconds.

## Frozen V1 grouping rule

Sort capture IQ files by recorded filesystem modification timestamp.

Start a new candidate episode whenever:

    inter_file_gap > 4.000 seconds

Otherwise assign the file to the current episode.

Threshold:

    EPISODE_GAP_SECONDS = 4.000

The comparison is strictly greater-than.

## Expected development result

Applying the frozen rule to the development capture is expected to
produce seven candidate groups because six observed large gaps exceed
4.000 seconds.

The number of candidate groups must be reported mechanically from the
rule and must not be changed to force agreement with the operator's
reported number of activations.

## Validation

The 4.000-second threshold must be frozen before collection of the next
controlled capture.

Capture 002 will be treated as unseen validation for the grouping rule.

The threshold must not be changed after inspecting Capture 002 merely
to improve agreement.

## Interpretation limits

A candidate episode is a temporal grouping of Kraken recorder files.

It is not automatically equivalent to:

- one RF packet
- one protocol frame
- one physical transmission
- one sensor activation
- one device identity

Agreement with controlled activation timing may support the usefulness
of the grouping method under the tested acquisition conditions.

Raw IQ files remain immutable external evidence.
