#!/usr/bin/env python3
"""Offline component tracking; new Draft 1 artifacts only, no RF operations."""

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
import zipfile
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np


FORMAT = "HARDSIGNAL_KRAKEN_EPISODE_COMPONENT_TRACKING_V2_DRAFT1"
ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/episode-component-tracking-v2-draft1.md"
PARAMETERS = {
    "sample_rate_hz": 25000, "dtype": "<c16", "minimum_samples": 4,
    "window": "numpy.hanning(N)", "fft_length": "N", "zero_padding": False,
    "normalization": "abs(FFT)**2/(N*sum(window**2))",
    "eligible_abs_frequency_hz": [100, 11500],
    "background_separation_hz": [50, 500], "background_minimum_bins": 32,
    "component_run_contrast_db": 6.0, "component_max_contrast_db": 10.0,
    "maximum_component_width_hz": 200.0,
    "association_maximum_frequency_difference_hz": 50.0,
    "association_fragment_index_differences": [1, 2],
    "maximum_track_range_hz": 100.0,
    "minimum_track_support": 3, "minimum_track_coverage": 0.60,
    "competing_group_minimum_support": 2,
    "primary_selection": "unique persistent track; no recurring competitor or ambiguous group",
    "frequency_estimator": "largest-power component bin; lower-frequency tie",
    "summary_weighting": "equal per supporting fragment",
}
CAPTURES = (
    "PIPELINE-TPMS-004-20260917-233423",
    "PIPELINE-TPMS-005-20260917-235439",
    "PIPELINE-TPMS-007-20260918-002700",
    "PIPELINE-TPMS-008-20260918-003900",
    "BETWEEN-DEVICE-V1-20260919-022917",
    "BETWEEN-DEVICE-REPL-V1-20260919-024341",
)


class ProvenanceError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def load_json(path):
    raw = path.read_bytes()
    return json.loads(raw), digest(raw)


def verify_inputs(bundle):
    """Check the complete capture before extraction; never change its artifacts."""
    try:
        manifest, mh = load_json(bundle / "manifest.json")
        grouping, gh = load_json(bundle / "episodes.json")
        v1, vh = load_json(bundle / "episode-features-v1.json")
        for obj, expected in (
            (manifest, "HARDSIGNAL_KRAKEN_CAPTURE_MANIFEST_V1"),
            (grouping, "HARDSIGNAL_KRAKEN_EPISODES_V1"),
            (v1, "HARDSIGNAL_KRAKEN_EPISODE_FEATURES_V1"),
        ):
            if obj["format"] != expected or obj["capture_id"] != bundle.name:
                raise ProvenanceError("Input format/capture ID mismatch")
        if grouping["episode_gap_seconds"] != 4.0 or grouping["comparison"] != ">":
            raise ProvenanceError("Unexpected grouping metadata")
        if v1["sample_rate_hz"] != 25000 or v1["iq_dtype"] != "complex128":
            raise ProvenanceError("Unexpected V1 IQ interpretation")
        records = manifest["files"]
        inventory = {f["path"]: f for f in records}
        if len(inventory) != len(records) or manifest["new_iq_file_count"] != len(records):
            raise ProvenanceError("Duplicate manifest path or inconsistent count")
        members = [f for ep in grouping["episodes"] for f in ep["files"]]
        if Counter(f["path"] for f in members) != Counter(inventory.keys()):
            raise ProvenanceError("Grouping omits or duplicates manifest files")
        if grouping["file_count"] != len(members):
            raise ProvenanceError("Grouping file count mismatch")
        if any(not isinstance(f["mtime_ns"], int) for f in members):
            raise ProvenanceError("Missing recorded mtime_ns")
        for f in members:
            source = inventory[f["path"]]
            if any(f[k] != source[k] for k in ("size_bytes", "sha256")):
                raise ProvenanceError("Grouping/raw manifest metadata mismatch")
        episodes = grouping["episodes"]
        if [e["episode"] for e in episodes] != list(range(1, len(episodes) + 1)):
            raise ProvenanceError("Episode order/IDs inconsistent")
        if grouping["episode_count"] != len(episodes) or v1["episode_count"] != len(episodes):
            raise ProvenanceError("Episode count mismatch")
        if len(v1["episodes"]) != len(episodes):
            raise ProvenanceError("V1 episode count mismatch")
        for ep, old in zip(episodes, v1["episodes"]):
            if ep["episode"] != old["episode"] or ep["file_count"] != len(ep["files"]):
                raise ProvenanceError("Episode metadata mismatch")
            if [f["path"] for f in ep["files"]] != [f["path"] for f in old["fragments"]]:
                raise ProvenanceError("V1 membership/order mismatch")
            if old["fragment_count"] != len(ep["files"]):
                raise ProvenanceError("V1 fragment count mismatch")
            for f, prior in zip(ep["files"], old["fragments"]):
                if prior["size_bytes"] != f["size_bytes"] or prior["samples"] * 16 != f["size_bytes"]:
                    raise ProvenanceError("V1 fragment size mismatch")
        hash_data = (bundle / "files.sha256").read_bytes()
        if hash_data.decode().splitlines() != [f"{f['sha256']}  {f['path']}" for f in records]:
            raise ProvenanceError("files.sha256 disagrees with manifest")
        for f in records:
            raw = Path(f["path"]).read_bytes()
            if len(raw) != f["size_bytes"] or len(raw) % 16 or digest(raw) != f["sha256"]:
                raise ProvenanceError(f"Raw integrity mismatch: {f['path']}")
        return manifest, grouping, v1, {
            "manifest.json": mh, "episodes.json": gh, "episode-features-v1.json": vh,
            "files.sha256": digest(hash_data),
        }
    except (OSError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProvenanceError):
            raise
        raise ProvenanceError(str(exc)) from exc


def eligible_bins(frequency):
    lo, hi = PARAMETERS["eligible_abs_frequency_hz"]
    return (np.abs(frequency) >= lo) & (np.abs(frequency) <= hi)


def local_background(frequency, power, eligible):
    """Batch exact same-side medians; mask padding instead of wrapping the FFT."""
    n = len(frequency)
    spacing = PARAMETERS["sample_rate_hz"] / n
    lo, hi = PARAMETERS["background_separation_hz"]
    distances = np.arange(1, int(np.floor(hi / spacing)) + 1)
    distances = distances[(distances * spacing >= lo) & (distances * spacing <= hi)]
    offsets = np.concatenate((-distances[::-1], distances))
    background = np.zeros(n)
    valid = np.zeros(n, dtype=bool)
    counts = np.zeros(n, dtype=np.int64)
    candidates = np.flatnonzero(eligible)
    for start in range(0, len(candidates), 128):
        indices = candidates[start:start + 128]
        neighbours = indices[:, None] + offsets
        inside = (neighbours >= 0) & (neighbours < n)
        safe = np.clip(neighbours, 0, n - 1)
        mask = inside & eligible[safe] & (np.sign(frequency[safe]) == np.sign(frequency[indices, None]))
        count = np.sum(mask, axis=1)
        counts[indices] = count
        enough = count >= PARAMETERS["background_minimum_bins"]
        if np.any(enough):
            medians = np.nanmedian(np.where(mask[enough], power[safe[enough]], np.nan), axis=1)
            good = np.isfinite(medians) & (medians > 0)
            selected = indices[enough][good]
            background[selected] = medians[good]
            valid[selected] = True
    return background, valid, counts


def local_maxima_count(power, left, right):
    """Count flat maxima once; use neighbouring spectral bins at run endpoints."""
    count = 0
    k = left
    while k <= right:
        end = k
        while end + 1 <= right and power[end + 1] == power[k]:
            end += 1
        before = power[k - 1] if k else -np.inf
        after = power[end + 1] if end + 1 < len(power) else -np.inf
        if power[k] > before and power[k] > after:
            count += 1
        k = end + 1
    return count


def detect_components(frequency, power, background, valid, eligible):
    contrast = np.zeros(len(power))
    defined = valid & (power > 0)
    contrast[defined] = 10 * np.log10(power[defined] / background[defined])
    active = eligible & defined & (contrast >= PARAMETERS["component_run_contrast_db"])
    boundaries = np.diff(np.r_[False, active, False].astype(int))
    runs = zip(np.flatnonzero(boundaries == 1), np.flatnonzero(boundaries == -1) - 1)
    labels = np.zeros(len(power), dtype=np.int64)
    components = []
    spacing = PARAMETERS["sample_rate_hz"] / len(power)
    for left, right in runs:
        maximum_contrast = float(np.max(contrast[left:right + 1]))
        if maximum_contrast < PARAMETERS["component_max_contrast_db"]:
            continue
        peak = int(left + np.argmax(power[left:right + 1]))
        width = float(frequency[right] - frequency[left] + spacing)
        reasons = []
        if width > PARAMETERS["maximum_component_width_hz"]:
            reasons.append("BROAD_COMPONENT")
        for neighbour in (left - 1, right + 1):
            if neighbour < 0 or neighbour >= len(power) or not eligible[neighbour]:
                reasons.append("REGION_BOUNDARY_COMPONENT")
            elif not valid[neighbour]:
                reasons.append("BACKGROUND_UNESTIMABLE")
        maxima = local_maxima_count(power, left, right)
        flags = sorted(set(reasons + (["MULTIPLE_LOCAL_MAXIMA"] if maxima > 1 else [])))
        number = len(components) + 1
        labels[left:right + 1] = number
        components.append({
            "component_index": number, "first_bin": int(left), "last_bin": int(right),
            "first_frequency_hz": float(frequency[left]), "last_frequency_hz": float(frequency[right]),
            "peak_bin": peak, "frequency_hz": float(frequency[peak]),
            "peak_power": float(power[peak]), "integrated_power": float(np.sum(power[left:right + 1])),
            "peak_background": float(background[peak]), "contrast_db": float(contrast[peak]),
            "maximum_contrast_db": maximum_contrast, "width_hz": width,
            "local_maxima_count": maxima, "eligible_for_tracking": not reasons,
            "ineligibility_reasons": sorted(set(reasons)), "flags": flags,
        })
    return components, contrast, defined, labels


def analyse_spectrum(iq):
    n = len(iq)
    fs = PARAMETERS["sample_rate_hz"]
    frequency = np.fft.fftshift(np.fft.fftfreq(n, 1 / fs)) if n else np.array([], dtype=float)
    eligible = eligible_bins(frequency)
    arrays = {"frequency_hz": frequency, "power": np.zeros(n), "background": np.zeros(n),
              "contrast_db": np.zeros(n), "eligible": eligible,
              "background_estimable": np.zeros(n, dtype=bool),
              "contrast_defined": np.zeros(n, dtype=bool),
              "background_bin_count": np.zeros(n, dtype=np.int64),
              "component_labels": np.zeros(n, dtype=np.int64)}
    flags = []
    if n < PARAMETERS["minimum_samples"]:
        flags.append("TOO_SHORT")
    if not np.all(np.isfinite(iq)):
        flags.append("NONFINITE_IQ")
    if flags:
        return [], arrays, sorted(flags), False, None
    window = np.hanning(n)
    with np.errstate(over="ignore", invalid="ignore"):
        power = np.abs(np.fft.fftshift(np.fft.fft((iq - np.mean(iq)) * window))) ** 2
        power /= n * np.sum(window ** 2)
    if not np.all(np.isfinite(power)) or np.sum(power) <= 0:
        return [], arrays, ["ZERO_SPECTRAL_POWER"], False, None
    arrays["power"] = power
    diagnostic = power.copy()
    diagnostic[int(np.argmin(np.abs(frequency)))] = -np.inf
    global_frequency = float(frequency[int(np.argmax(diagnostic))])
    if abs(global_frequency) < PARAMETERS["eligible_abs_frequency_hz"][0]:
        flags.append("GLOBAL_MAX_IN_DC_EXCLUSION")
    if abs(global_frequency) > PARAMETERS["eligible_abs_frequency_hz"][1]:
        flags.append("GLOBAL_MAX_IN_EDGE_EXCLUSION")
    background, valid, counts = local_background(frequency, power, eligible)
    if np.any(eligible & ~valid):
        flags.append("BACKGROUND_UNESTIMABLE")
    components, contrast, defined, labels = detect_components(frequency, power, background, valid, eligible)
    arrays.update(background=background, contrast_db=contrast, background_estimable=valid,
                  contrast_defined=defined, background_bin_count=counts, component_labels=labels)
    return components, arrays, sorted(flags), True, global_frequency


def statistics(values):
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    return {"median_hz": median, "minimum_hz": float(np.min(values)),
            "maximum_hz": float(np.max(values)), "range_hz": float(np.max(values) - np.min(values)),
            "mad_hz": float(np.median(np.abs(values - median)))}


def track_episode(fragments):
    fcount = len(fragments)
    nodes = sorted([c for f in fragments for c in f["components"] if c["eligible_for_tracking"]],
                   key=lambda c: (c["fragment_index"], c["candidate_id"]))
    adjacency = {c["candidate_id"]: set() for c in nodes}
    by_id = {c["candidate_id"]: c for c in nodes}
    edges = []
    for a, b in combinations(nodes, 2):
        gap = b["fragment_index"] - a["fragment_index"]
        difference = b["frequency_hz"] - a["frequency_hz"]
        if gap in PARAMETERS["association_fragment_index_differences"] and abs(difference) <= PARAMETERS["association_maximum_frequency_difference_hz"]:
            adjacency[a["candidate_id"]].add(b["candidate_id"])
            adjacency[b["candidate_id"]].add(a["candidate_id"])
            edges.append({"from": a["candidate_id"], "to": b["candidate_id"],
                          "fragment_index_difference": gap, "frequency_difference_hz": difference})
    groups = []
    unseen = set(by_id)
    while unseen:
        pending = [min(unseen)]
        ids = set()
        while pending:
            current = pending.pop()
            if current in ids:
                continue
            ids.add(current)
            pending.extend(sorted(adjacency[current] - ids, reverse=True))
        unseen -= ids
        members = sorted((by_id[i] for i in ids), key=lambda c: (c["fragment_index"], c["candidate_id"]))
        indices = [c["fragment_index"] for c in members]
        support = len(set(indices))
        coverage = support / fcount
        measured = statistics([c["frequency_hz"] for c in members])
        unique = len(indices) == support
        bounded = measured["range_hz"] <= PARAMETERS["maximum_track_range_hz"]
        coherent = unique and bounded
        flags = []
        if not unique:
            flags.append("MULTIPLE_CANDIDATES_SAME_FRAGMENT")
        if not bounded:
            flags.append("TRACK_RANGE_EXCEEDED")
        if any(e["fragment_index_difference"] == 2 and e["from"] in ids and e["to"] in ids
               and by_id[e["from"]]["fragment_index"] + 1 not in indices for e in edges):
            flags.append("ONE_FRAGMENT_GAP")
        summary = None
        if coherent:
            summary = {**measured,
                       "adjacent_observed_frequency_differences_hz":
                           [b["frequency_hz"] - a["frequency_hz"] for a, b in zip(members, members[1:])],
                       "median_contrast_db": float(np.median([c["contrast_db"] for c in members])),
                       "minimum_contrast_db": float(min(c["contrast_db"] for c in members)),
                       "median_width_hz": float(np.median([c["width_hz"] for c in members]))}
            if support == 1:
                summary.update(range_hz=None, mad_hz=None, adjacent_observed_frequency_differences_hz=None)
                flags.append("SINGLE_OBSERVATION")
        groups.append({"candidate_ids": [c["candidate_id"] for c in members],
                       "member_fragment_indices": sorted(set(indices)),
                       "missing_fragment_indices": sorted(set(range(1, fcount + 1)) - set(indices)),
                       "support_count": support, "coverage": coverage,
                       "coherent": coherent, "one_candidate_per_fragment": unique,
                       "frequency_range_within_limit": bounded, "observed_group_range_hz": measured["range_hz"],
                       "group_median_frequency_hz": measured["median_hz"],
                       "persistent": coherent and support >= PARAMETERS["minimum_track_support"] and coverage >= PARAMETERS["minimum_track_coverage"],
                       "summary": summary, "flags": sorted(flags)})
    groups.sort(key=lambda g: (g["group_median_frequency_hz"], min(g["member_fragment_indices"]), min(g["candidate_ids"])))
    for i, group in enumerate(groups, 1):
        group["track_id"] = f"T{i:03d}"
    qualified = [g for g in groups if g["persistent"]]
    recurring = [g for g in groups if g["coherent"] and g["support_count"] >= 2]
    ambiguous = [g for g in groups if not g["coherent"] and g["support_count"] >= 2]
    usable = sum(f["usable_spectrum"] for f in fragments)
    if not usable:
        status = "UNUSABLE_INPUT"
    elif not nodes:
        status = "NO_ELIGIBLE_COMPONENT"
    elif len(qualified) > 1:
        status = "MULTIPLE_PERSISTENT_TRACKS"
    elif ambiguous or len(recurring) > 1:
        status = "AMBIGUOUS_ASSOCIATION"
    elif not qualified:
        status = "INSUFFICIENT_SUPPORT"
    else:
        status = "UNIQUE_PERSISTENT_TRACK"
    primary = qualified[0] if status == "UNIQUE_PERSISTENT_TRACK" else None
    flags = []
    if fcount == 1:
        flags.append("SINGLE_FRAGMENT")
    if fcount == 2:
        flags.append("TWO_FRAGMENTS")
    if any(g["coverage"] < PARAMETERS["minimum_track_coverage"] for g in groups):
        flags.append("LOW_COVERAGE")
    if len(recurring) + len(ambiguous) > 1:
        flags.append("COMPETING_TRACKS")
    if primary is None:
        flags.append("NO_PRIMARY_TRACK")
    spacings = []
    for a, b in combinations([g for g in groups if g["coherent"]], 2):
        am = {by_id[c]["fragment_index"]: by_id[c]["frequency_hz"] for c in a["candidate_ids"]}
        bm = {by_id[c]["fragment_index"]: by_id[c]["frequency_hz"] for c in b["candidate_ids"]}
        common = sorted(set(am) & set(bm))
        if len(common) >= 2:
            values = [bm[i] - am[i] for i in common]
            spacings.append({"lower_track_id": a["track_id"], "higher_track_id": b["track_id"],
                             "fragment_indices": common, "signed_spacings_hz": values,
                             "summary": statistics(values)})
    return {"fragment_count": fcount, "usable_fragment_count": usable,
            "component_count": sum(len(f["components"]) for f in fragments),
            "eligible_component_count": len(nodes), "track_count": sum(g["coherent"] for g in groups),
            "persistent_track_count": len(qualified), "edges": edges, "groups": groups,
            "pairwise_spacings": spacings, "status": status, "flags": sorted(flags),
            "primary_track_id": primary["track_id"] if primary else None,
            "primary_support_count": primary["support_count"] if primary else None,
            "primary_coverage": primary["coverage"] if primary else None,
            "primary_summary": primary["summary"] if primary else None}


def write_npz(path, arrays):
    """Fixed ZIP metadata, sorted NPY members, and no object/pickle arrays."""
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, array in sorted(arrays.items()):
            stream = io.BytesIO()
            np.lib.format.write_array(stream, np.asarray(array), allow_pickle=False)
            member = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.create_system = 3
            member.external_attr = 0o100644 << 16
            archive.writestr(member, stream.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def repository_provenance():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    tracked = git("status", "--porcelain=v1", "--untracked-files=no").splitlines()
    # These declarations stay fixed across a batch; output paths and clocks are not identity inputs.
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return {"git_commit": git("rev-parse", "HEAD"), "tracked_dirty": bool(tracked),
            "tracked_changes": tracked, "untracked_at_batch_start": untracked,
            "dirty_or_untracked": bool(tracked or untracked),
            "python_version": platform.python_version(), "numpy_version": np.__version__,
            "numpy_byteorder": "little" if np.little_endian else "big",
            "protocol_file": str(SPEC.relative_to(ROOT)), "protocol_sha256": digest(SPEC.read_bytes()),
            "extractor_file": str(Path(__file__).resolve().relative_to(ROOT)),
            "extractor_sha256": digest(Path(__file__).read_bytes())}


def failure_output(bundle, output, provenance, error):
    output.mkdir(parents=True, exist_ok=False)
    failure = {"format": FORMAT, "revision": "draft1", "capture_id": bundle.name,
               "parameters": PARAMETERS, "provenance": provenance, "processing_status": "FAILED",
               "flags": ["PROVENANCE_MISMATCH"], "error": str(error)}
    (output / "run.json").write_bytes(json_bytes(failure))
    (output / "files.sha256").write_text(f"{digest((output / 'run.json').read_bytes())}  run.json\n")
    return failure


def extract_capture(bundle, output, provenance):
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite output: {output}")
    resolved = output.resolve()
    for protected in (ROOT / "captures", bundle.resolve()):
        if resolved == protected or protected in resolved.parents:
            raise ValueError("Output must be outside historical capture bundles")
    try:
        manifest, grouping, old, inputs = verify_inputs(bundle)
    except ProvenanceError as exc:
        return failure_output(bundle, output, provenance, exc)
    all_arrays = {}
    components_output = []
    tracks_output = []
    rows = []
    for ep, v1 in zip(grouping["episodes"], old["episodes"]):
        fragments = []
        for index, (entry, old_fragment) in enumerate(zip(ep["files"], v1["fragments"]), 1):
            try:
                raw = Path(entry["path"]).read_bytes()
            except OSError as exc:
                return failure_output(bundle, output, provenance, exc)
            if digest(raw) != entry["sha256"] or len(raw) != entry["size_bytes"]:
                return failure_output(bundle, output, provenance, "Raw changed after preflight")
            iq = np.frombuffer(raw, dtype=PARAMETERS["dtype"])
            components, arrays, flags, usable, global_frequency = analyse_spectrum(iq)
            prefix = f"E{ep['episode']:03d}_F{index:03d}"
            for c in components:
                c.update(fragment_index=index, candidate_id=f"{prefix}_C{c['component_index']:04d}")
            all_arrays.update({prefix + "_" + key: value for key, value in arrays.items()})
            fragments.append({"fragment_index": index, "fragment_id": prefix, "path": entry["path"],
                              "sha256": entry["sha256"], "size_bytes": len(raw), "samples": len(iq),
                              "recorded_mtime_ns": entry["mtime_ns"],
                              "duration_seconds": len(iq) / PARAMETERS["sample_rate_hz"],
                              "bin_spacing_hz": PARAMETERS["sample_rate_hz"] / len(iq) if len(iq) else None,
                              "usable_spectrum": usable, "flags": flags,
                              "global_non_dc_maximum_hz": global_frequency,
                              "v1_strongest_component_offset_hz": old_fragment["strongest_component_offset_hz"],
                              "components": components})
        result = track_episode(fragments)
        result["episode"] = ep["episode"]
        tracks_output.append(result)
        components_output.append({"episode": ep["episode"], "fragments": fragments})
        primary = result["primary_summary"]
        row = {"capture_id": bundle.name, "episode": ep["episode"],
               **{k: result[k] for k in ("fragment_count", "usable_fragment_count", "component_count",
                                         "eligible_component_count", "track_count", "persistent_track_count", "status",
                                         "primary_track_id", "primary_support_count", "primary_coverage")}}
        for k in ("median_hz", "minimum_hz", "maximum_hz", "range_hz", "mad_hz",
                  "median_contrast_db", "minimum_contrast_db", "median_width_hz"):
            row["primary_" + k] = primary[k] if primary else None
        row.update(v1_median_hz=v1["median_strongest_component_offset_hz"],
                   v1_spread_hz=v1["strongest_component_offset_spread_hz"],
                   primary_minus_v1_hz=primary["median_hz"] - v1["median_strongest_component_offset_hz"] if primary else None,
                   flags=";".join(result["flags"]))
        rows.append(row)
    counts = dict(sorted(Counter(row["status"] for row in rows).items()))
    run = {"format": FORMAT, "revision": "draft1", "capture_id": bundle.name,
           "parameters": PARAMETERS, "provenance": provenance, "input_artifact_sha256": inputs,
           "raw_inventory": [{k: f[k] for k in ("path", "size_bytes", "sha256")} for f in manifest["files"]],
           "processing_status": "COMPLETED", "status_counts": counts,
           "episode_count": len(rows), "scope": "development/regression; not independent validation"}
    output.mkdir(parents=True, exist_ok=False)
    for filename, obj in (
        ("run.json", run),
        ("components.json", {"format": FORMAT, "capture_id": bundle.name, "episodes": components_output}),
        ("tracks.json", {"format": FORMAT, "capture_id": bundle.name, "episodes": tracks_output}),
    ):
        (output / filename).write_bytes(json_bytes(obj))
    write_npz(output / "spectra.npz", all_arrays)
    with (output / "episodes.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = [f"# Component Tracking V2 Draft 1 — {bundle.name}", "",
             "Development/regression evidence only. V1 and existing V2 remain unchanged.", "",
             "Status counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()) + ".", "",
             "| Episode | Status | V1 median Hz | V1 spread Hz | Primary median Hz | Primary minus V1 Hz |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        primary = "null" if row["primary_median_hz"] is None else f"{row['primary_median_hz']:.6f}"
        delta = "null" if row["primary_minus_v1_hz"] is None else f"{row['primary_minus_v1_hz']:.6f}"
        lines.append(f"| E{row['episode']:02d} | {row['status']} | {row['v1_median_hz']:.6f} | {row['v1_spread_hz']:.6f} | {primary} | {delta} |")
    lines += ["", "All original episodes/fragments remain represented. Blank CSV fields mean null. "
              "Missing or ambiguous primary tracks are not imputed. Component flags and all "
              "competing groups are retained in components.json and tracks.json.", "",
              "Frequency continuity does not establish carrier or source identity. Local contrast "
              "is not calibrated SNR. No improved discrimination, device identification, or universal "
              "threshold is established. Candidate-region boundaries are analysis guards, not "
              "a characterized usable receiver passband.", ""]
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    names = sorted(p.name for p in output.iterdir())
    (output / "files.sha256").write_text("".join(f"{digest((output / name).read_bytes())}  {name}\n" for name in names), encoding="utf-8")
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path, nargs="?")
    parser.add_argument("--six-development-captures", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.capture_dir) == args.six_development_captures:
        parser.error("Choose capture_dir or --six-development-captures")
    bundles = [ROOT / "captures" / c for c in CAPTURES] if args.six_development_captures else [args.capture_dir.resolve()]
    provenance = repository_provenance()
    for bundle in bundles:
        output = args.output_root / bundle.name
        if output.exists():
            parser.error(f"Refusing existing output: {output}")
    failed = False
    for bundle in bundles:
        try:
            run = extract_capture(bundle, args.output_root / bundle.name, provenance)
        except (OSError, ValueError) as exc:
            parser.exit(1, f"ERROR: {exc}\n")
        print(bundle.name, run["processing_status"], json.dumps(run.get("status_counts", {}), sort_keys=True), flush=True)
        failed |= run["processing_status"] == "FAILED"
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
