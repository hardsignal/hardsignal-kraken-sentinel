# Between-Device Discrimination V1 — Held-Out Source Selection

Protocol:

    docs/kraken-between-device-discrimination-v1.md

Protocol commit:

    9406c9de7898220185dfef0c487378351a59b48b

Protocol SHA-256:

    bfba460e7e51a98c86e6bb1307413dabbab39a86113dad25b43fcb33bb125c46

## Source roles

Reference source:

    S1

S1 is the owned controlled TPMS source used for the existing
same-source Episode Features V1 measurements in Captures 004, 005,
and 007.

Held-out source:

    S2

S2 is a physically different owned controlled TPMS sensor.

S2 is selected as the held-out source before Capture 008 acquisition
and before inspection of any new Episode Features V1 output from S2.

## Experimental controls

The Kraken antenna array will not be intentionally moved.

S2 will be placed at the same controlled source position and orientation
used for the current S1 repeatability captures as closely as practicable.

Any unavoidable geometry difference will be recorded.

No S2 Episode Features V1 result has been inspected before this
selection record is frozen.
