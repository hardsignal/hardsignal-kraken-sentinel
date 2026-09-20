# Separate Draft 2 exact-solver benchmark

Only saved TPMS-008 E08 candidates were used. This is not a new experiment run.
Validation: 22 tests passed.
Old DP: COMPUTATION_UNRESOLVED after 0.210903 s.
New 73-candidate group optimum: 18 links, cost 0.068727411154337045, 0.030562 s.
New optimum search statistics: {"augmentations": 18, "matching_calls": 1, "matching_certificates": 1, "optimum_cache_hits": 0, "search_nodes": 0}

| Scope | Margin | Maximum links | Minimum cost | Status | Primary | Compact bytes | Seconds |
|---|---:|---:|---:|---|---|---:|---:|
| Failed group | 0.0 | 18 | 0.068727411154337045 | INSUFFICIENT_SUPPORT | null | 74911 | 0.546063 |
| Failed group | 0.25 | 18 | 0.068727411154337045 | AMBIGUOUS_ASSOCIATION | null | 74912 | 0.056461 |
| Failed group | 1.0 | 18 | 0.068727411154337045 | AMBIGUOUS_ASSOCIATION | null | 74911 | 0.003506 |
| Entire E08 | 0.0 | 48 | 4.0168866937019194 | AMBIGUOUS_ASSOCIATION | null | 163737 | 5.045670 |
| Entire E08 | 0.25 | 48 | 4.0168866937019194 | AMBIGUOUS_ASSOCIATION | null | 163751 | 1.078233 |
| Entire E08 | 1.0 | 48 | 4.0168866937019194 | AMBIGUOUS_ASSOCIATION | null | 163737 | 1.066010 |

Times are one local measurement, not a full-matrix runtime forecast. All membership and ambiguity decisions are exact; no selected assignment is promoted to a primary.
The serialized model defines the complete retained family. It does not enumerate that family or establish its cardinality. Positive-margin counts remain explicitly NOT_EVALUATED.
The original expanded schema and exact-count output requirement must be addressed explicitly before a complete Draft 2 run. No scientific parameter change is proposed.
Original experimental status is unchanged: 1/160 real arms complete, one resource-limit failure, 158 NOT_RUN, spectral matrix NOT_STARTED. No RF or raw IQ was used.
