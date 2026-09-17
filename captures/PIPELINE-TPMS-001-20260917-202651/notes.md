# Kraken Capture Pipeline Validation 001

Date: 17 September 2026

Purpose:

Validate the Hardsignal Kraken capture-provenance framework using an
owned, controlled TPMS RF source.

Acquisition:

- Controlled source: owned TPMS sensor
- Controlled activations: 6
- Kraken VFO0: 433.868160 MHz
- VFO bandwidth: 25 kHz
- Squelch mode: Manual
- Squelch: -45 dB
- IQ recording: enabled
- IQ files before capture: 561
- IQ files after capture: 594
- New IQ files attributed to capture boundary: 33

Integrity:

- Pre-existing IQ files modified: 0
- Kraken configuration changed during capture: no
- Git HEAD changed during capture: no
- All 33 IQ files passed size and SHA-256 verification
- files.sha256 matched the manifest
- Capture verifier result: PASS

Interpretation:

The test validates the generic acquisition-provenance workflow.

The 33 recorder files must not be interpreted as 33 independent RF
transmissions. Six controlled sensor activations were performed, and
Kraken produced multiple IQ recorder files during those activations.

This capture is pipeline-validation evidence only.

It is not part of TPMS V3 validation, does not reopen V3, and makes no
RF identity or unique-fingerprint claim.

Raw IQ files remain outside Git and are referenced by cryptographic
hash from the capture manifest.
