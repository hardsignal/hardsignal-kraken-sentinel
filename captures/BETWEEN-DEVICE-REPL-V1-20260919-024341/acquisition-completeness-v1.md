# Between-Device Replication V1 — Acquisition Completeness

## Frozen rule

For each activation:

    marker time < IQ file mtime <= marker time + 10.000 seconds

## Result

Controlled activation markers: 8

ACQUIRED: 7

NOT OBSERVED: 1

Acquisition completeness:

    7/8 = 0.875000 = 87.5%

## Activation results

| Activation | Result | IQ files in window |
|---|---|---:|
| A1 | NOT OBSERVED | 0 |
| A2 | ACQUIRED | 3 |
| A3 | ACQUIRED | 3 |
| A4 | ACQUIRED | 3 |
| A5 | ACQUIRED | 4 |
| A6 | ACQUIRED | 3 |
| A7 | ACQUIRED | 4 |
| A8 | ACQUIRED | 1 |

## A1

A1 marker:

    2026-09-19T02:43:48.948044+01:00

The first subsequent new IQ file occurred at:

    2026-09-19T02:44:11.066619+01:00

Therefore no new IQ recorder file occurred inside the
pre-registered A1 observation window:

    (2026-09-19T02:43:48.948044+01:00,
     2026-09-19T02:43:58.948044+01:00]

A1 is therefore classified as NOT OBSERVED.

## A8

A8 was ACQUIRED by one IQ recorder file:

    19-Sep-2026_02h45m42s,IQ_433.868MHz,DOA_42.0.iq

Its observed DOA is retained as recorded.

No observations are removed or reclassified on the basis of this result.

## Interpretation

The replication capture demonstrates acquisition of 7 of 8 controlled
operator activations under the frozen temporal acquisition criterion.

The NOT OBSERVED A1 result does not by itself establish absence of RF
transmission, transmitter malfunction, insufficient RF power, squelch
failure, recorder failure, packet loss, or any other specific mechanism.

No change has been made to the pre-registered observation window or
activation denominator.

The result is retained as observed evidence.
