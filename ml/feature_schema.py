"""Feature schema for Kraken RF Sentinel ML datasets."""

DATASET_VERSION = "0.1"

METADATA_COLUMNS = [
    "session_id",
    "start_time",
    "end_time",
    "duration_s",
]

MODEL_FEATURE_COLUMNS = [
    "burst_count",

    "stable_count",
    "multipath_count",
    "low_quality_count",
    "stable_ratio",
    "multipath_ratio",
    "low_quality_ratio",

    "bearing_circular_mean_deg",
    "bearing_circular_std_deg",

    "peak_power_mean_db",
    "peak_power_std_db",

    "max_confidence_mean",
    "median_confidence_mean",

    "doa_width_mean_deg",
    "doa_width_std_deg",

    "median_doa_peaks_mean",
    "bearing_spread_mean_deg",
    "single_peak_ratio_mean",
    "samples_mean",

    "track_event_count",
    "track_acquired_count",
    "track_reacquired_count",
    "track_shift_confirmed_count",
    "track_degraded_count",
    "track_lost_count",
    "track_recovered_count",

    "episode_event_count",
    "episode_started_count",
    "episode_closed_count",
]

CSV_COLUMNS = METADATA_COLUMNS + MODEL_FEATURE_COLUMNS
