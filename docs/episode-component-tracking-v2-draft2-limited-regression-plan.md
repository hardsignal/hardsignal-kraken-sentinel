# Limited saved-episode regression: predeclared selection

Checkpoint `259e982`. This selection was fixed before any regression solver,
counter, query or metric execution. Only saved episode IDs, fragment counts,
candidate-count structure and already documented anomaly locations were used.
No association outcome or separation result was used to select or replace cases.

Input: committed `native__w200__connected.json` in the historical Draft 2 results.
The machine-readable plan binds the input, specification and selected candidate
contexts by SHA-256 in
`results/episode-component-tracking-v2-draft2-limited-regression-plan.json`.

| Capture | Episode | Original fragments | Structural reason |
|---|---|---:|---|
| PIPELINE-TPMS-004-20260917-233423 | E02 | 5 | Earliest ordinary multi-fragment episode outside the documented E01/E06 anomalies |
| PIPELINE-TPMS-004-20260917-233423 | E01 | 5 | Known large V1 offset-spread anomaly, E01/F03 |
| PIPELINE-TPMS-005-20260917-235439 | E01 | 5 | Earliest multi-fragment episode; covers the sixth capture |
| PIPELINE-TPMS-007-20260918-002700 | E01 | 5 | Earliest ordinary multi-fragment TPMS-007 episode |
| BETWEEN-DEVICE-V1-20260919-022917 | E06 | 5 | Known +261 Hz anomaly, E06/F04 |
| BETWEEN-DEVICE-REPL-V1-20260919-024341 | E07 | 1 | Required single-fragment case |
| PIPELINE-TPMS-008-20260918-003900 | E08 | 2 | Established integration control and required two-fragment coverage |

Each receives connected, margin 0, margin 0.25 and margin 1 association: **28
cases**, all on the existing native/200 Hz candidate inputs. No width/representation
sweep. E08 reuses committed families and sidecars; other episodes use the unchanged
exact solver and counter. No FFT, component detection or expanded saved-episode
retained-hypothesis arrays. All pre-existing tracked files must remain byte-identical.

Frozen computational limits: 250,000 count states, 5,000,000 count transitions,
60 seconds/count, 32 MiB packed polynomials; 5,000 public query calls and 120
seconds/query stage; 60 seconds/family construction; 400 seconds/worker and
512 MiB observed worker resident-memory limit. These are computational stop rules,
not scientific parameters. No substitutions or limit increases after outcomes.
Failures remain explicit and do not prevent executing the remaining declared cases.

The success gate requires all selected compact families, counts, queries and
metrics to complete exactly, connected saved-result parity, validated provenance,
and deterministic reload/reproduction. Otherwise the decision is NOT_READY.
Successful completion permits only READY_FOR_BOUNDED_SIX_CAPTURE_REGRESSION.
No full-matrix readiness, identification or discrimination claim is authorized.
