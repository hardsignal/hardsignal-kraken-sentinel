# Episode Features V1 — Capture 004

## Status

DESCRIPTIVE WITHIN-CAPTURE RESULT

Episode Features V1 was pre-registered and its analyzer implementation
was frozen before first execution against Capture 004.

## Capture

Capture ID:

    PIPELINE-TPMS-004-20260917-233423

Candidate episodes:

    6

Recorder IQ files:

    30

Total recorded IQ:

    21.846 seconds

Capture provenance verification:

    PASS

## Frozen components

Episode Grouping V1 SHA-256:

    c14586d6304eca3ea906b320f43607ffe6a982929b6bdacd9adb71f973fe98e6

Episode Features V1 specification SHA-256:

    f0bbc8f8c0dd179486979e9aee904bf3db5fee2717073a3406b65e6c636bc7dc

Episode Features V1 analyzer SHA-256:

    4528ccf87557426adf50be6cf2678597d320977b046011c38f8ab0103b371259

Episode Features V1 result SHA-256:

    2bd617d51a8b5ef24c5575e18e2fcaea2520ffc84685cdd224a4eb1f37582fe1

## Episode spectral medians

    E01  -5187.449 Hz
    E02  -5193.170 Hz
    E03  -5206.903 Hz
    E04  -5204.614 Hz
    E05  -5202.325 Hz
    E06  -5214.627 Hz

Observed range of episode medians:

    approximately 27.18 Hz

The episode-level median strongest-component offset was therefore
tightly clustered around -5.2 kHz within this controlled capture.

## Fragment-level exceptions

E01 contained one fragment whose strongest component was:

    +5550.215 Hz

while its other four fragment measurements were approximately:

    -5172.572 to -5208.619 Hz

E06 contained one fragment whose strongest component was:

    -1403.003 Hz

while its other three fragment measurements were approximately:

    -5208.619 to -5222.924 Hz

These measurements are retained without filtering or exclusion.

They explain the large V1 spectral spreads for E01 and E06.

## Amplitude observation

Episode RMS magnitude varied substantially:

    0.027602 to 0.058502

Episode median magnitude was narrower:

    0.002719 to 0.002808

Amplitude remains contextual and is not interpreted as a device
identity feature.

## Interpretation

Across six controlled candidate episodes in Capture 004, the median
strongest-component offset was tightly clustered around -5.2 kHz,
while two episodes contained individual fragments whose strongest
component occurred elsewhere.

Episode-level median behaviour was therefore substantially more stable
than fragment-level minimum/maximum spread under these tested
conditions.

This is a descriptive within-capture repeatability observation.

It does not establish:

- unique device identity
- packet identity
- transmitter identity
- transmitter location
- between-device discrimination
- a validated RF fingerprint
