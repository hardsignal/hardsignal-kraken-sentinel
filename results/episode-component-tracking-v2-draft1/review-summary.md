# Episode Component Tracking V2 Draft 1 — Development/regression review

New Draft 1 implementation and outputs only. V1, existing V2, capture manifests, grouping, historical results and raw IQ are unchanged. No RF operations were performed.

## Reproduction

```sh
python3 -B -m unittest discover -s tests -p test_episode_component_tracking_v2_draft1.py -v
python3 -B analysis/episode_component_tracking_v2_draft1.py --six-development-captures --output-root /path/to/new-draft1-output
```

The output root must have no existing capture subdirectories. Each capture produces run.json, spectra.npz, components.json, tracks.json, episodes.csv, summary.md and files.sha256. The extractor refuses to overwrite outputs or write inside historical capture bundles.

## Status and V1 comparison

| Capture | Episodes | Ambiguous | Insufficient support | Unique primary | Original V1 capture median Hz | Draft 1 primary median |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TPMS-004 | 6 | 6 | 0 | 0 | -5203.469743 | null |
| TPMS-005 | 5 | 5 | 0 | 0 | -5193.170374 | null |
| TPMS-007 | 8 | 7 | 1 | 0 | -5201.180994 | null |
| TPMS-008 | 8 | 8 | 0 | 0 | -5204.328023 | null |
| BETWEEN-DEVICE-V1 | 7 | 6 | 1 | 0 | -5419.756477 | null |
| BETWEEN-DEVICE-REPL-V1 | 7 | 6 | 1 | 0 | -5341.939028 | null |

Totals: 41 episodes, 38 AMBIGUOUS_ASSOCIATION, 3 INSUFFICIENT_SUPPORT, 0 unique primary tracks. All other episode status counts are zero.

All primary frequency/spread values and V2-minus-V1 differences are null. No capture-level primary frequency is imputed from coherent subtracks or V1. The V1 numbers above are medians of the preserved episode medians, not recomputed replacement V1 outputs.

## Unexpected behaviour retained

The specified detector produced 8681 components across 210 fragments. It can produce many competing associations; no episode satisfies the complete unique-primary rule. Parameters were not tuned after these outcomes.

The three insufficient-support episodes are: TPMS-007 E07: INSUFFICIENT_SUPPORT; BETWEEN-DEVICE-V1 E03: INSUFFICIENT_SUPPORT; BETWEEN-DEVICE-REPL-V1 E07: INSUFFICIENT_SUPPORT.

Replication E07 remains a single-fragment episode. Its original V1 value is -12455.369404 Hz. Draft 1 flags its global maximum as outside the edge guard, retains 38 in-band detected components, and returns INSUFFICIENT_SUPPORT with null primary statistics. No observation was deleted.

A seeded synthetic two-tone-plus-noise test initially expected a unique primary. The implementation retained the intended weaker five-fragment tone but also found a three-fragment persistent group at another frequency, despite no third tone being injected. The test was corrected to require target retention and explicit MULTIPLE_PERSISTENT_TRACKS, not forced uniqueness. No detector or tracker parameter was changed to satisfy that expectation.

## Validation

20 unit/regression tests passed. All seven artifacts for each of the six real captures reproduced byte-for-byte in a second, temporary output directory under the same source/environment/repository declaration. Raw/input integrity checks passed after both runs. All 145 previously tracked files retained identical hashes. See regression-validation.json and test-results.json.

Byte determinism is conditional on identical provenance declarations: a later Git commit or changed dirty/untracked declaration legitimately changes run.json and its hash. Generated numerical outputs use fixed ordering and NPZ metadata.

## Interpretation

This is implementation and development/regression evidence, not independent validation. Local contrast is not calibrated SNR; frequency continuity is not carrier/source identity. No improved discrimination, device identification or universal threshold is claimed.
