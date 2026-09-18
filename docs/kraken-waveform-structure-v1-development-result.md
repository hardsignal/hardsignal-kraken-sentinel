# Kraken Waveform Structure V1 — Development Result

## Status

COMPLETE — NO FEATURE FAMILY ADVANCED TO VALIDATION

## Development boundary

The Waveform Structure V1 development search space was frozen before
implementation.

The deterministic analyzer was then implemented, hashed, committed,
and pushed before its first execution on development data.

Development specification SHA-256:

    88a01cab50ca8874370cadf411694aefc90282b5e55a9dcf6a3b30b2a8ab5be1

Analyzer SHA-256:

    7c752127aaa52050cfc2978a11fdcb55b9b46a43ebca1f1082b68db16603d138

Analyzer freeze commit:

    b6319d736d7dce2bfed6ba174d39718ecce91467

## Development data

S1:

    PIPELINE-TPMS-004-20260917-233423
    PIPELINE-TPMS-005-20260917-235439
    PIPELINE-TPMS-007-20260918-002700

S2:

    PIPELINE-TPMS-008-20260918-003900

S3 was not inspected with Waveform Structure V1 and remained outside
this development analysis.

## Output hashes

Capture 004:

    f790ecf2784cda8b202e962f8a340f38e85588ec3f496a12ebbce1c2504e7204

Capture 005:

    30b66be09a6cb708d9b8d9a0964089fee2d20cc7f22b3439f1f3df24315c3dce

Capture 007:

    db889e8531d250c757269c6211605dc17b79b4bd39f0d12c1ac6eb340e44d709

Capture 008:

    c97bb34821673f2afc6c90b24b794450d5463a997c490dbd30dda3870ed971bb

## Capture-level development summary

| Source | Capture | Episodes | IF median Hz | IF MAD Hz | STFT median Hz | STFT step Hz | Occupied bins | Envelope CV | Active fraction | Transitions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 004 | 6 | -64.433 | 5642.424 | -534.058 | 0.000 | 40.75 | 4.74815 | 0.19849 | 0.00 |
| S1 | 005 | 5 | -56.815 | 5668.176 | -329.590 | 0.000 | 40.50 | 4.53373 | 0.19531 | 0.00 |
| S1 | 007 | 8 | -39.120 | 5647.837 | -579.834 | 0.000 | 41.00 | 6.03185 | 0.19580 | 1.00 |
| S2 | 008 | 8 | -38.097 | 5633.915 | -817.871 | 0.000 | 40.25 | 5.24064 | 0.19531 | 2.00 |

## Development interpretation

The implemented waveform feature families show substantial overlap
between repeated S1 observations and S2 Capture 008.

Instantaneous-frequency spread is similar across the development
captures.

The median STFT step is zero in every capture-level summary.

Occupied-frequency-bin counts overlap closely for the ordinary
episodes.

Normalized envelope active fractions overlap closely.

Envelope coefficient of variation does not provide stable separation
between repeated S1 captures and S2.

No implemented feature satisfies the predeclared advancement rule.

## Extreme S2 Episode 08 retained

S2 Capture 008 Episode 08 produced, among other measurements:

    fragment count = 2
    occupied-frequency-bin count median = 129.5
    envelope active-state transition count median = 10.0

This observation is retained.

It is not removed from the evidence.

It is not promoted to a device-discrimination feature because the
apparent difference is concentrated in one episode and therefore does
not satisfy the predeclared requirement that separation not be solely
caused by one isolated fragment or episode.

No causal interpretation is assigned to this episode.

## Validation decision

No Waveform Structure V1 feature or compact feature set advances to S3
validation.

S3 therefore remains uninspected by this analyzer.

No numerical discrimination threshold is fitted after observing the
development results.

## Result

Waveform Structure V1, as implemented in the frozen analyzer, did not
demonstrate a sufficiently clear and repeatable S1/S2 difference to
justify independent validation.

This is a negative discrimination result for these waveform feature
definitions under the tested conditions.

## Limits

This result does not establish:

- that S1 and S2 transmitters are equivalent;
- that no RF waveform feature can discriminate them;
- unique device identity;
- universal TPMS fingerprinting performance;
- decoded bits, symbols, packets, or protocol fields;
- transmitter location;
- performance under other receivers, bandwidths, or sample rates;
- robustness across geometry, temperature, voltage, ageing, or
  production lots.

No observations were removed to improve separation.

Episode Features V1 and V2 and their prior results remain unchanged.
