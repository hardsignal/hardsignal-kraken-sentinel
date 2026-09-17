# Kraken Episode Features V2 — Development Result

## Status

COMPLETE — NO FEATURE FAMILY ADVANCED TO VALIDATION

## Development boundary

The Episode Features V2 development search space was frozen before
implementation.

The deterministic V2 extractor was then implemented, hashed, committed,
and pushed before its first execution on development captures.

Extractor SHA-256:

    d72d85a2c1542f173c240f02e77e8486dd90e05cea9dd486fda7cea6092f8d30

Development specification SHA-256:

    71c0b60eeb4dfd4c98336313bbc54735af3713fdadc36516c393367f6bbda260

## Development data

S1:

    PIPELINE-TPMS-004-20260917-233423
    PIPELINE-TPMS-005-20260917-235439
    PIPELINE-TPMS-007-20260918-002700

S2:

    PIPELINE-TPMS-008-20260918-003900

S3 was not inspected with Episode Features V2 and remains outside this
development analysis.

## Output hashes

Capture 004:

    a168a5aca47b3b68e4ab8b6dcb8a4198c38b7b4d778523145ee2ee473f3e126d

Capture 005:

    d5fb34e4495394a2c3b50b59e910c17c68733052583e2d5bd739ed8af6acee44

Capture 007:

    94f51569c2399843636df7830896883bcf5ed7a2725ed012384608174441956c

Capture 008:

    1fb01486873d2d51281e95a7a95785629b18444b038be2042ca65bfa3f065453

## Capture-level development summary

| Source | Capture | Episodes | Centroid Hz | Spread Hz | Entropy | Width90 Hz | Relative peak Hz | Adjacent spacing Hz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 004 | 6 | -3158.069 | 5226.590 | 0.732693 | 19069.672 | 10.681 | 10.300 |
| S1 | 005 | 5 | -3119.267 | 5319.362 | 0.732919 | 19233.704 | 7.629 | 9.918 |
| S1 | 007 | 8 | -3154.603 | 5236.295 | 0.730255 | 19130.707 | 8.392 | 10.300 |
| S2 | 008 | 8 | -3063.655 | 5304.412 | 0.729667 | 18870.544 | 9.918 | 11.635 |

## Development interpretation

The implemented V2 feature families show substantial overlap between
the repeated S1 observations and the held development S2 observation.

No individual feature family provides a sufficiently clear,
non-outlier-driven descriptive S1/S2 difference while also preserving
reasonable S1 repeatability to justify advancement under the
predeclared feature-selection rule.

Therefore no Episode Features V2 feature or compact feature set is
selected for independent S3 validation from this development run.

## Extreme observation retained

S2 Capture 008 Episode 08 produced:

    nearest relative peak offset median = 270.081 Hz
    median adjacent peak spacing = 1574.707 Hz

The observation is retained.

It is not removed from the development evidence.

It is also not promoted to a device-discrimination feature because it
is an isolated episode-level extreme observation and does not satisfy
the predeclared requirement that apparent separation not be solely
explained by one isolated outlier.

Episode 08 contained two recorder fragments.

No causal interpretation is assigned to this observation.

## Validation decision

S3 will not be used to validate this V2 feature set because no feature
set satisfied the development advancement rule.

This preserves S3 from unnecessary inspection and avoids converting
development exploration into post-hoc validation.

## Result

Episode Features V2, as implemented in the frozen extractor above, did
not demonstrate a sufficiently clear S1/S2 separation to justify
independent validation.

This is a negative discrimination result for these feature definitions
under the tested conditions.

It does not invalidate the previously observed same-source
repeatability.

## Limits

This result does not establish:

- that S1 and S2 transmitters are equivalent;
- that no RF feature can discriminate them;
- unique device identity;
- universal TPMS fingerprinting performance;
- packet identity;
- transmitter location;
- performance under other receiver configurations or environments.

No observations were removed to improve separation.

No numerical discrimination threshold was fitted after observing these
results.

The frozen V1 evidence and the held-out V1 discrimination result remain
unchanged.
