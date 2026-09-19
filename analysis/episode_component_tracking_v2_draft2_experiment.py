#!/usr/bin/env python3
"""Separate, offline Draft 2 experiment. Frozen Draft 1 is a read-only control.

No IQ loading, hardware access, fitting, or parameter selection. The exhaustive
association solver stops explicitly if its declared work budget is exceeded.
"""
import argparse
from collections import Counter
from functools import lru_cache
import csv
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import episode_component_tracking_v2_draft1 as d1

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'docs/episode-component-tracking-v2-draft2-experiment.md'
REPRESENTATIONS = ('native', 'grid_sigma0', 'grid_sigma5', 'grid_sigma10', 'grid_sigma20')
WIDTHS = (200, 225, 250, 275, 300, 325, 350, None)
ASSOCIATIONS = ('connected', 'paths_margin0', 'paths_margin0.25', 'paths_margin1')
# Operational limits, declared before executing results. They do not truncate a
# scientific result: reaching any limit invalidates that arm and stops the run.
STATE_LIMIT = 200000
PATH_LIMIT = 200000
HYPOTHESIS_LIMIT = 1000000
FS = 25000.0
GRID_EDGES = np.linspace(-FS / 2, FS / 2, 10001)
ANOMALIES = {(d1.CAPTURES[0], 1, 3), (d1.CAPTURES[0], 6, 3),
             (d1.CAPTURES[4], 6, 4), (d1.CAPTURES[5], 7, 1)}


def arms():
    return [dict(arm_id=f'{r}__w{w if w is not None else "unlimited"}__{a}',
                 representation=r, width_hz=w, association=a)
            for r, w, a in itertools.product(REPRESENTATIONS, WIDTHS, ASSOCIATIONS)]


def dump(path, obj):
    path.write_bytes(d1.json_bytes(obj))


def native_intervals(frequency, power):
    """Uniform FFT-bin intervals, split at the periodic Nyquist boundary."""
    n = len(frequency)
    if n < 4 or len(power) != n or not np.all(np.isfinite(power)) or np.any(power < 0):
        raise ValueError('Invalid stored spectrum')
    expected = np.fft.fftshift(np.fft.fftfreq(n, 1 / FS))
    if not np.allclose(frequency, expected, rtol=0, atol=1e-9):
        raise ValueError('Unexpected stored frequency grid')
    spacing = FS / n
    left, right = frequency - spacing / 2, frequency + spacing / 2
    density = power / spacing
    segments = []
    for shift in (-FS, 0, FS):
        lo = np.maximum(left + shift, -FS / 2)
        hi = np.minimum(right + shift, FS / 2)
        keep = hi > lo
        segments.extend(zip(lo[keep], hi[keep], density[keep]))
    return np.asarray(sorted(segments), dtype=float)


def integrate_intervals(segments, edges):
    """Piecewise-constant cumulative integral: exact interval overlap, no interpolation of PSD."""
    lo, hi, density = segments.T
    cumulative = np.r_[0., np.cumsum((hi - lo) * density)]
    indices = np.searchsorted(hi, edges, side='right')
    safe = np.minimum(indices, len(hi) - 1)
    values = cumulative[indices] + np.where(indices < len(hi),
        np.clip(edges - lo[safe], 0, hi[safe] - lo[safe]) * density[safe], 0.)
    return np.diff(values)


def rebin(frequency, power):
    rebinned = integrate_intervals(native_intervals(frequency, power), GRID_EDGES)
    if not np.isclose(rebinned.sum(), power.sum(), rtol=1e-11, atol=1e-14):
        raise ValueError('Power conservation failure')
    return rebinned


def represent(frequency, power, representation):
    if representation == 'native':
        return frequency.copy(), power.copy(), FS / len(power)
    if representation not in REPRESENTATIONS:
        raise ValueError(representation)
    sigma = float(representation.removeprefix('grid_sigma'))
    density = rebin(frequency, power) / 2.5
    if sigma:
        offsets = np.arange(-int(4 * sigma / 2.5), int(4 * sigma / 2.5) + 1) * 2.5
        kernel = np.exp(-0.5 * (offsets / sigma) ** 2)
        density = np.convolve(density, kernel / kernel.sum(), mode='same')
    return (GRID_EDGES[:-1] + GRID_EDGES[1:]) / 2, density, 2.5


def detect(frequency, power, representation):
    f, p, spacing = represent(frequency, power, representation)
    eligible = d1.eligible_bins(f)
    background, valid, _ = d1.local_background(f, p, eligible)
    # Both native and common grid span 25 kHz, so the frozen detector's
    # 25000/len() spacing remains exact. Remove ONLY its width flag, reapplied
    # independently for every predeclared ceiling below.
    components, _, _, _ = d1.detect_components(f, p, background, valid, eligible)
    segments = native_intervals(frequency, power)
    maxima = []
    i = 0
    while i < len(power):
        end = i
        while end + 1 < len(power) and power[end + 1] == power[i]:
            end += 1
        if (i == 0 or power[i] > power[i-1]) and (end + 1 == len(power) or power[end] > power[end+1]):
            maxima.append(i)
        i = end + 1
    maxima = np.asarray(maxima, dtype=int)
    for c in components:
        low = c['first_frequency_hz'] - spacing / 2
        high = c['last_frequency_hz'] + spacing / 2
        sub = maxima[(frequency[maxima] >= low) & (frequency[maxima] < high)]
        c.update(interval_hz=[low, high], native_subpeaks=[
            {'bin': int(k), 'frequency_hz': float(frequency[k]), 'power': float(power[k])} for k in sub],
            integrated_power=float(integrate_intervals(segments, np.array([low, high]))[0]))
        c['ineligibility_reasons'] = [r for r in c['ineligibility_reasons'] if r != 'BROAD_COMPONENT']
        c['flags'] = [r for r in c['flags'] if r != 'BROAD_COMPONENT']
        c['eligible_for_tracking'] = not c['ineligibility_reasons']
    return components


def apply_width(components, width, episode, fragment):
    result = []
    for c in components:
        c = dict(c)
        reasons = list(c['ineligibility_reasons'])
        if width is not None and c['width_hz'] > width:
            reasons.append('BROAD_COMPONENT')
        c.update(ineligibility_reasons=sorted(reasons), eligible_for_tracking=not reasons,
                 flags=sorted(set(c['flags'] + reasons)), fragment_index=fragment,
                 candidate_id=f'E{episode:03d}_F{fragment:03d}_C{c["component_index"]:04d}')
        result.append(c)
    return result


class ComputationUnresolved(RuntimeError):
    def __init__(self, reason, **details):
        self.details = dict(reason=reason, **details)
        super().__init__(json.dumps(self.details, sort_keys=True))


def path_cost(path, nodes):
    return sum(((nodes[b]['frequency_hz'] - nodes[a]['frequency_hz']) / 50) ** 2
               + .25 * (nodes[b]['fragment_index'] - nodes[a]['fragment_index'] == 2)
               for a, b in zip(path, path[1:]))


def solve_group(nodes, margin, state_limit=STATE_LIMIT, hypothesis_limit=HYPOTHESIS_LIMIT):
    """Exact set-partition DP. Singletons explicitly represent unassigned nodes.

    Every partition is generated once by choosing the path containing the
    earliest remaining node. No amplitude/frequency-location preference.
    """
    nodes = sorted(nodes, key=lambda c: (c['fragment_index'], c['candidate_id']))
    n = len(nodes)
    successors = [[j for j in range(i + 1, n)
                   if nodes[j]['fragment_index'] - nodes[i]['fragment_index'] in (1, 2)
                   and abs(nodes[j]['frequency_hz'] - nodes[i]['frequency_hz']) <= 50]
                  for i in range(n)]
    paths = [[] for _ in nodes]
    path_count = 0

    def extend(path, low, high):
        nonlocal path_count
        path_count += 1
        if path_count > PATH_LIMIT:
            raise ComputationUnresolved('feasible path limit', candidates=n, limit=PATH_LIMIT)
        paths[path[0]].append((sum(1 << i for i in path), tuple(path), path_cost(path, nodes)))
        for j in successors[path[-1]]:
            f = nodes[j]['frequency_hz']
            if max(high, f) - min(low, f) <= 100:
                extend(path + [j], min(low, f), max(high, f))

    for i, c in enumerate(nodes):
        extend([i], c['frequency_hz'], c['frequency_hz'])
    states = 0

    @lru_cache(None)
    def optimum(mask):
        nonlocal states
        states += 1
        if states > state_limit:
            raise ComputationUnresolved('exact partition DP state limit', candidates=n,
                                        feasible_paths=path_count, visited_states=states, limit=state_limit)
        if not mask:
            return 0, 0.
        first = (mask & -mask).bit_length() - 1
        best_links, best_cost = -1, float('inf')
        for bits, path, cost in paths[first]:
            if bits & mask == bits:
                links, tail_cost = optimum(mask ^ bits)
                links += len(path) - 1
                cost += tail_cost
                if links > best_links or (links == best_links and cost < best_cost):
                    best_links, best_cost = links, cost
        return best_links, best_cost

    full = (1 << n) - 1
    best_links, best_cost = optimum(full)
    hypotheses = []

    def enumerate_partitions(mask, target_links, remaining_cost, chosen, cost):
        if not mask:
            if target_links == 0:
                if len(hypotheses) >= hypothesis_limit:
                    raise ComputationUnresolved('retained hypothesis limit', candidates=n,
                                                limit=hypothesis_limit, optimum_links=best_links)
                hypotheses.append({'paths': [[nodes[i]['candidate_id'] for i in p] for p in chosen],
                                   'cost': cost})
            return
        first = (mask & -mask).bit_length() - 1
        for bits, path, step_cost in paths[first]:
            if bits & mask != bits:
                continue
            links, minimum_cost = optimum(mask ^ bits)
            if len(path) - 1 + links != target_links or step_cost + minimum_cost > remaining_cost + 1e-12:
                continue
            enumerate_partitions(mask ^ bits, target_links - len(path) + 1,
                                 remaining_cost - step_cost, chosen + [path], cost + step_cost)

    enumerate_partitions(full, best_links, best_cost + margin, [], 0.)
    return {'optimum_links': best_links, 'optimum_cost': best_cost,
            'hypotheses': hypotheses, 'states': states, 'feasible_paths': path_count}


def association(fragments, arm):
    frozen = d1.track_episode(fragments)
    if arm == 'connected':
        primary = next((g['candidate_ids'] for g in frozen['groups']
                        if g['track_id'] == frozen['primary_track_id']), None)
        return dict(status=frozen['status'], primary=primary, retained_hypothesis_count=None,
                    hypotheses=None, invariant_membership=None, alternative_membership=None,
                    persistent_tracks=[g['candidate_ids'] for g in frozen['groups'] if g['persistent']],
                    support_coverage=[{'members': g['candidate_ids'], 'support': g['support_count'],
                                      'coverage': g['coverage'], 'coherent': g['coherent']} for g in frozen['groups']],
                    structural_constraint_violations=0, connected_groups=frozen['groups'])
    margin = float(arm.removeprefix('paths_margin'))
    nodes = {c['candidate_id']: c for f in fragments for c in f['components'] if c['eligible_for_tracking']}
    solved = []
    # Independent connected groups permit exact factorisation. Margin is GLOBAL,
    # not a separate allowance for each group.
    singleton_paths = []
    for g in frozen['groups']:
        if len(g['candidate_ids']) == 1:
            singleton_paths.append(g['candidate_ids'])
        else:
            solved.append(solve_group([nodes[i] for i in g['candidate_ids']], margin))
    optimal_cost = sum(s['optimum_cost'] for s in solved)
    hypotheses = []

    def combine(k, chosen, cost):
        if cost + sum(s['optimum_cost'] for s in solved[k:]) > optimal_cost + margin + 1e-12:
            return
        if k == len(solved):
            if len(hypotheses) >= HYPOTHESIS_LIMIT:
                raise ComputationUnresolved('episode retained hypothesis limit', limit=HYPOTHESIS_LIMIT)
            hypotheses.append({'paths': sorted(chosen + singleton_paths), 'cost': cost})
            return
        for h in solved[k]['hypotheses']:
            combine(k+1, chosen + h['paths'], cost + h['cost'])

    combine(0, [], 0.)
    memberships = [set(map(tuple, h['paths'])) for h in hypotheses]
    invariant = set.intersection(*memberships)
    union = set.union(*memberships)
    fcount = len(fragments)
    persistent = {p for p in union if len(p) >= 3 and len(p) / fcount >= .6}
    primary = next(iter(persistent)) if len(persistent) == 1 and persistent <= invariant else None
    if not any(f['usable_spectrum'] for f in fragments):
        status = 'UNUSABLE_INPUT'
    elif not nodes:
        status = 'NO_ELIGIBLE_COMPONENT'
    elif primary:
        status = 'UNIQUE_PERSISTENT_TRACK'
    elif any(sum(p in persistent for p in m) > 1 for m in memberships):
        status = 'MULTIPLE_PERSISTENT_TRACKS'
    elif len(hypotheses) > 1:
        status = 'AMBIGUOUS_ASSOCIATION'
    else:
        status = 'INSUFFICIENT_SUPPORT'
    alternative_by_candidate = {i: sorted([list(p) for p in union if i in p]) for i in sorted(nodes)}
    violations = 0
    for h in hypotheses:
        flattened = [i for p in h['paths'] for i in p]
        violations += int(sorted(flattened) != sorted(nodes))
        for p in h['paths']:
            cs = [nodes[i] for i in p]
            violations += int(len({c['fragment_index'] for c in cs}) != len(cs))
            violations += int(max(c['frequency_hz'] for c in cs) - min(c['frequency_hz'] for c in cs) > 100)
            violations += sum(b['fragment_index'] - a['fragment_index'] not in (1, 2)
                              or abs(b['frequency_hz'] - a['frequency_hz']) > 50 for a, b in zip(cs, cs[1:]))
    return dict(status=status, primary=list(primary) if primary else None,
                retained_hypothesis_count=len(hypotheses), hypotheses=hypotheses,
                optimum_links=sum(s['optimum_links'] for s in solved), optimum_cost=optimal_cost,
                invariant_membership=sorted(map(list, invariant)), alternative_membership=sorted(map(list, union-invariant)),
                persistent_tracks=sorted(map(list, persistent)), candidate_membership_alternatives=alternative_by_candidate,
                structural_constraint_violations=violations,
                support_coverage=[{'members': list(p), 'support': len(p), 'coverage': len(p)/fcount,
                                   'coherent': True} for p in sorted(union)])


def synthetic_specs():
    common = itertools.product((10923, 21846, 43692, 54615), (10, 40, 280),
                               (-5300, 3000), ('constant', 'exponential'), range(100))
    for n, width, centre, background, seed in common:
        base = dict(samples=n, fwhm_hz=width, centre_hz=centre, background=background, seed=seed)
        for contrast in (8, 12, 20):
            yield dict(base, kind='single', contrast_db=contrast)
        for separation, ratio in itertools.product((10, 25, 50, 100, 200, 400), (0, 6, 12)):
            yield dict(base, kind='pair', contrast_db=26, separation_hz=separation, power_ratio_db=ratio)


def synthetic_spectrum(spec):
    n = spec['samples']
    frequency = np.fft.fftshift(np.fft.fftfreq(n, 1 / FS))
    density = np.ones(n) if spec['background'] == 'constant' else np.random.default_rng(spec['seed']).exponential(size=n)
    centres = [spec['centre_hz']]
    amplitudes = [10 ** (spec['contrast_db']/10) - 1]
    if spec['kind'] == 'pair':
        centres.append(spec['centre_hz'] + spec['separation_hz'])
        amplitudes.append(amplitudes[0] / 10 ** (spec['power_ratio_db']/10))
    for centre, amplitude in zip(centres, amplitudes):
        density += amplitude * np.exp(-4*np.log(2)*((frequency-centre)/spec['fwhm_hz'])**2)
    return frequency, density*(FS/n), centres


def synthetic_metrics(components, centres, width):
    cs = [c for c in components if c['eligible_for_tracking']]
    around = [c for c in cs if c['interval_hz'][0] < centres[0]+width and c['interval_hz'][1] > centres[0]-width]
    tolerance = max(5, width/4)
    matches = [[i for i, c in enumerate(cs) if abs(c['frequency_hz']-centre) <= tolerance] for centre in centres]
    recovery = bool(matches[0]) if len(centres) == 1 else any(i != j for i in matches[0] for j in matches[1])
    return dict(split=len(around)>1, recovery=recovery,
                merge=len(centres)==2 and any(c['interval_hz'][0] <= min(centres) and c['interval_hz'][1] >= max(centres) for c in cs),
                detection_count=len(cs), frequency_error_hz=[min((abs(c['frequency_hz']-f) for c in cs), default=None) for f in centres])


def make_fragments(rows):
    # rows entries: (frequency, identity, contrast); identity only used for evaluation.
    return [{'usable_spectrum': True, 'components': [dict(candidate_id=f'F{i+1:03d}_C{j+1:03d}',
             fragment_index=i+1, frequency_hz=float(f), truth=identity, contrast_db=contrast,
             width_hz=10., eligible_for_tracking=True) for j, (f, identity, contrast) in enumerate(row)]}
            for i, row in enumerate(rows)]


def association_fixtures():
    fixtures = [
        ('stable_weaker', [[(3000, 'A', 12), (5000+i*200, f'U{i}', 26)] for i in range(5)], True),
        ('two_persistent', [[(3000, 'A', 12), (4000, 'B', 20)] for _ in range(5)], False),
        ('crossing', [[(3000+i*25, 'A', 12), (3100-i*25, 'B', 20)] for i in range(5)], False),
        ('missing_one', [[(3000, 'A', 12)] if i != 2 else [] for i in range(5)], True),
        ('missing_two', [[(3000, 'A', 12)] if i not in (2, 3) else [] for i in range(5)], False),
        ('amplitude_reversal', [[(3000, 'A', 12 if i%2 else 26), (4000, 'B', 26 if i%2 else 12)] for i in range(5)], False),
        ('single_fragment', [[(3000, 'A', 12)]], False),
        ('two_fragments', [[(3000, 'A', 12)]]*2, False),
        ('boundary_50_100', [[(3000, 'A', 12)], [(3050, 'A', 12)], [(3100, 'A', 12)]], True),
        ('outside_step', [[(3000, 'A', 12)], [(3050.000001, 'A', 12)], [(3100, 'A', 12)]], False),
        ('outside_range', [[(3000, 'A', 12)], [(3034, 'A', 12)], [(3068, 'A', 12)], [(3100.000001, 'A', 12)]], False),
        ('coverage_exact', [[(3000, 'A', 12)]]*3 + [[], []], True),
        ('coverage_below', [[(3000, 'A', 12)]]*3 + [[], [], []], False),
    ]
    for name, rows, recoverable in fixtures:
        yield name, make_fragments(rows), recoverable
    for seed in range(100):
        rng = np.random.default_rng(seed)
        rows = [[(float(rng.uniform(100, 11500))*int(rng.choice((-1, 1))), f'N{i}_{j}', 12)
                 for j in range(10)] for i in range(5)]
        yield f'noise_{seed:02d}', make_fragments(rows), False


def fixture_metrics(fragments, result, recoverable):
    nodes = {c['candidate_id']: c for f in fragments for c in f['components']}
    paths = (result['invariant_membership'] or []) + (result['alternative_membership'] or [])
    if result['hypotheses'] is None:
        paths = [g['candidate_ids'] for g in result['connected_groups'] if g['coherent']]
    switches = sum(nodes[a]['truth'] != nodes[b]['truth'] for p in paths for a, b in zip(p, p[1:]))
    links = sum(max(0, len(p)-1) for p in paths)
    primary = result['primary']
    correct = bool(primary and recoverable and len({nodes[i]['truth'] for i in primary}) == 1)
    return dict(false_primary=bool(primary and not correct), identity_switches=switches, link_count=links,
                identity_switch_rate=switches/links if links else None, correct_primary=correct,
                ambiguity_retained=not bool(primary) if not recoverable else None,
                abstained=not bool(primary), recoverable=recoverable,
                structural_constraint_violations=result['structural_constraint_violations'])


def fragment_metrics(frequency, power, components, old_max):
    cs = sorted(components, key=lambda c: c['interval_hz'])
    good = [c for c in cs if c['eligible_for_tracking']]
    region = (-5500., -5100.)  # Diagnostics ONLY; no selection call reads this.
    overlapping = [c for c in cs if c['interval_hz'][0] < region[1] and c['interval_hz'][1] > region[0]]
    segments = native_intervals(frequency, power)
    total = float(integrate_intervals(segments, np.array(region))[0])
    retained = sum(float(integrate_intervals(segments, np.array([max(c['interval_hz'][0], region[0]),
                       min(c['interval_hz'][1], region[1])]))[0]) for c in good
                   if c['interval_hz'][0] < region[1] and c['interval_hz'][1] > region[0])
    containing = [c for c in good if old_max is not None and c['interval_hz'][0] <= old_max < c['interval_hz'][1]]
    return dict(detection_count=len(cs), eligible_count=len(good), fragmentation_count=len(overlapping),
                fragmentation_interpretation='intervals intersecting diagnostic region; not physical truth',
                small_gaps_hz=[b['interval_hz'][0]-a['interval_hz'][1] for a, b in zip(cs, cs[1:])],
                diagnostic_small_gaps_hz=[b['interval_hz'][0]-a['interval_hz'][1] for a, b in zip(overlapping, overlapping[1:])],
                width_rejection=sum('BROAD_COMPONENT' in c['ineligibility_reasons'] for c in cs),
                dominant_in_diagnostic_region=old_max is not None and region[0] <= old_max <= region[1],
                dominant_retained=bool(containing), regional_power_retention=retained/total if total else None,
                frequency_displacement_hz=containing[0]['frequency_hz']-old_max if containing else None,
                native_reference_hz=old_max, samples=len(power))


def load_inputs():
    base = ROOT / 'results/episode-component-tracking-v2-draft1'
    hashes, episodes = {}, []
    for capture in d1.CAPTURES:
        directory = base / capture
        manifest = directory / 'files.sha256'
        hashes[str(manifest.relative_to(ROOT))] = d1.digest(manifest.read_bytes())
        for line in manifest.read_text().splitlines():
            expected, filename = line.split('  ', 1)
            if Path(filename).name != filename:
                raise ValueError('Unexpected Draft 1 artifact path')
            path = directory / filename
            actual = d1.digest(path.read_bytes())
            if actual != expected:
                raise ValueError(f'Draft 1 hash mismatch: {path}')
            # Verify committed identity as well as self-consistency.
            committed = subprocess.check_output(['git', 'show', f'HEAD:{path.relative_to(ROOT)}'], cwd=ROOT)
            if d1.digest(committed) != actual:
                raise ValueError(f'Draft 1 differs from committed evidence: {path}')
            hashes[str(path.relative_to(ROOT))] = actual
        records = json.loads((directory/'components.json').read_text())
        old = json.loads((directory/'tracks.json').read_text())
        with np.load(directory/'spectra.npz', allow_pickle=False) as spectra:
            for ep, prior in zip(records['episodes'], old['episodes']):
                fragments = []
                for f in ep['fragments']:
                    prefix = f'E{ep["episode"]:03d}_F{f["fragment_index"]:03d}'
                    frequency, power = spectra[prefix+'_frequency_hz'], spectra[prefix+'_power']
                    native_intervals(frequency, power)
                    fragments.append(dict(metadata=f, frequency=frequency, power=power))
                episodes.append(dict(capture=capture, episode=ep['episode'], fragments=fragments, prior=prior))
    if len(episodes) != 41 or sum(len(e['fragments']) for e in episodes) != 210:
        raise ValueError('Unexpected development inventory')
    return episodes, hashes


def summarize_fixtures(records):
    summary = {}
    for arm in ASSOCIATIONS:
        rows = [r for r in records if r['association'] == arm]
        noise = [r for r in rows if r['name'].startswith('noise_')]
        recoverable = [r for r in rows if r['metrics']['recoverable']]
        ambiguous = [r for r in rows if not r['metrics']['recoverable']]
        switches = sum(r['metrics']['identity_switches'] for r in rows)
        links = sum(r['metrics']['link_count'] for r in rows)
        special = [r for r in rows if r['name'] in ('crossing', 'two_persistent', 'amplitude_reversal')]
        summary[arm] = dict(
            trials=len(rows), noise_trials=len(noise),
            noise_false_primary_count=sum(r['metrics']['false_primary'] for r in noise),
            noise_false_primary_rate=sum(r['metrics']['false_primary'] for r in noise)/len(noise),
            false_primary_rate=sum(r['metrics']['false_primary'] for r in rows)/len(rows),
            identity_switch_count=switches, link_count=links,
            identity_switch_rate=switches/links if links else None,
            ambiguity_trials=len(ambiguous),
            ambiguity_retention_rate=sum(r['metrics']['ambiguity_retained'] for r in ambiguous)/len(ambiguous),
            abstention_rate=sum(r['metrics']['abstained'] for r in rows)/len(rows),
            recoverable_trials=len(recoverable),
            recoverable_abstention_rate=sum(r['metrics']['abstained'] for r in recoverable)/len(recoverable),
            correct_primary_count=sum(r['metrics']['correct_primary'] for r in recoverable),
            structural_constraint_violations=sum(r['metrics']['structural_constraint_violations'] for r in rows),
            crossing_competing_switches=sum(r['metrics']['identity_switches'] for r in special),
            crossing_competing_forced_primaries=sum(r['result']['primary'] is not None for r in special))
    return summary


def accumulate_synthetic(counts, record):
    # Full stratification keeps close/unresolved pairs and resolution effects
    # visible; aggregate gates never replace these cells or fixture records.
    spec = {k: v for k, v in record['fixture'].items() if k != 'seed'}
    description = dict(spec, representation=record['representation'], width_hz=record['width_hz'])
    key = json.dumps(description, sort_keys=True)
    if key not in counts:
        counts[key] = dict(cell=description, trials=0, splits=0, recoveries=0, merges=0,
                           detection_count=0, frequency_error_sum_hz=0., frequency_error_count=0,
                           missing_frequency_count=0)
    c, m = counts[key], record['metrics']
    c['trials'] += 1
    c['splits'] += m['split']
    c['recoveries'] += m['recovery']
    c['merges'] += m['merge']
    c['detection_count'] += m['detection_count']
    for error in m['frequency_error_hz']:
        if error is None:
            c['missing_frequency_count'] += 1
        else:
            c['frequency_error_sum_hz'] += error
            c['frequency_error_count'] += 1


def evaluate_gates(matrix, synthetic, fixtures):
    def rate(rep, width, kind, field, predicate=lambda c: True):
        cells = [c for c in synthetic.values() if c['cell']['representation']==rep
                 and c['cell']['width_hz']==width and c['cell']['kind']==kind and predicate(c['cell'])]
        numerator, denominator = sum(c[field] for c in cells), sum(c['trials'] for c in cells)
        return dict(numerator=numerator, denominator=denominator,
                    rate=numerator/denominator if denominator else None)
    gates = []
    baseline = fixtures['connected']
    for arm in matrix:
        r, w = arm['representation'], arm['width_hz']
        split = rate(r,w,'single','splits')
        native = rate('native',w,'single','splits')
        single = rate(r,w,'single','recoveries',lambda c:c['contrast_db']==20)
        pair_filter = lambda c:c['fwhm_hz']==10 and c['separation_hz']>=100
        pair = rate(r,w,'pair','recoveries',pair_filter)
        merge = rate(r,w,'pair','merges',pair_filter)
        a = fixtures[arm['association']]
        denominator = arm['metrics']['diagnostic_dominant_denominator']
        dominant = arm['metrics']['diagnostic_dominant_retained']/denominator if denominator else None
        checks = dict(split_reduction_50_percent=(split['rate'] <= native['rate']*.5 if native['rate'] else None),
                      single_20db_recovery=single['rate']>=.95, separated_pair_recovery=pair['rate']>=.95,
                      separated_pair_merge=merge['rate']<=.01,
                      dominant_retention=dominant>=.95 if dominant is not None else None,
                      structural_constraints=a['structural_constraint_violations']==0 and arm['metrics']['structural_constraint_violations']==0,
                      crossing_competing=a['crossing_competing_switches']==0 and a['crossing_competing_forced_primaries']==0,
                      noise_false_primary=a['noise_false_primary_rate']<=.01,
                      improved_correct_recovery=a['correct_primary_count']>baseline['correct_primary_count'])
        gates.append(dict(arm_id=arm['arm_id'], checks=checks,
                          all_gates_pass=all(v is True for v in checks.values()),
                          split=split, native_split=native, single_recovery=single,
                          separated_pair_recovery=pair, separated_pair_merge=merge,
                          diagnostic_dominant_retention=dominant,
                          note='Zero baseline splits makes relative split-reduction undefined; no winner selected.'))
    return gates


def run(output):
    if output.exists():
        raise ValueError('Output must be a new directory; overwriting results is prohibited')
    output.mkdir(parents=True)
    matrix = [dict(a, state='NOT_RUN', metrics=None, failure=None) for a in arms()]
    provenance = dict(format='KRAKEN_COMPONENT_V2_DRAFT2_EXPERIMENT',
        git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        python=platform.python_version(), numpy=np.__version__, platform=platform.platform(),
        code_sha256=d1.digest(Path(__file__).read_bytes()),
        frozen_control_code_sha256=d1.digest(Path(d1.__file__).read_bytes()),
        test_sha256=d1.digest((ROOT/'tests/test_episode_component_tracking_v2_draft2_experiment.py').read_bytes()), spec_sha256=d1.digest(SPEC.read_bytes()),
        matrix_sha256=d1.digest(d1.json_bytes(arms())), limits=dict(states=STATE_LIMIT, paths=PATH_LIMIT, hypotheses=HYPOTHESIS_LIMIT))
    failure = None
    phase = 'input_verification'
    try:
        episodes, provenance['inputs'] = load_inputs()
        phase = 'association_fixtures'
        fixture_results = []
        for name, fragments, recoverable in association_fixtures():
            for a in ASSOCIATIONS:
                result = association(fragments, a)
                fixture_results.append(dict(name=name, association=a, result=result,
                                           metrics=fixture_metrics(fragments, result, recoverable)))
        dump(output/'association-fixtures.json', fixture_results)
        fixture_summary = summarize_fixtures(fixture_results)
        dump(output/'association-fixture-summary.json', fixture_summary)
        phase = 'real_matrix'
        cached = {}
        for row in matrix:
            arm = row['arm_id']
            print(f'RUN {arm}', flush=True)
            results = []
            anomalies = []
            for ep in episodes:
                fs, fm = [], []
                for source in ep['fragments']:
                    meta = source['metadata']
                    key = (row['representation'], ep['capture'], ep['episode'], meta['fragment_index'])
                    if key not in cached:
                        cached[key] = detect(source['frequency'], source['power'], row['representation'])
                    cs = apply_width(cached[key], row['width_hz'], ep['episode'], meta['fragment_index'])
                    fs.append(dict(usable_spectrum=meta['usable_spectrum'], components=cs))
                    fm.append(fragment_metrics(source['frequency'], source['power'], cs,
                                               meta['v1_strongest_component_offset_hz']))
                    if (ep['capture'], ep['episode'], meta['fragment_index']) in ANOMALIES:
                        anomalies.append(dict(capture=ep['capture'], episode=ep['episode'],
                                              fragment=meta['fragment_index'], metrics=fm[-1], components=cs))
                try:
                    result = association(fs, row['association'])
                except ComputationUnresolved as exc:
                    row.update(state='COMPUTATION_UNRESOLVED', failure=dict(exc.details, capture=ep['capture'], episode=ep['episode']))
                    dump(output/(arm+'.partial.json'), dict(complete=False, episodes=results, failed_episode=row['failure'], anomalous_fragments=anomalies))
                    raise
                results.append(dict(capture=ep['capture'], episode=ep['episode'], fragments=fm,
                                    components=fs, association=result, prior_status=ep['prior']['status'],
                                    primary_after_connected_veto=(result['primary'] is not None and d1.track_episode(fs)['primary_track_id'] is None)))
            allfm = [f for e in results for f in e['fragments']]
            statuses = Counter(e['association']['status'] for e in results)
            metrics = dict(detection_count=sum(f['detection_count'] for f in allfm),
                width_rejection=sum(f['width_rejection'] for f in allfm),
                primary_tracks=sum(e['association']['primary'] is not None for e in results),
                null_primary_episodes=sum(e['association']['primary'] is None for e in results),
                persistent_tracks=sum(len(e['association']['persistent_tracks']) for e in results),
                statuses=dict(statuses), diagnostic_dominant_denominator=sum(f['dominant_in_diagnostic_region'] for f in allfm),
                diagnostic_dominant_retained=sum(f['dominant_in_diagnostic_region'] and f['dominant_retained'] for f in allfm),
                resolution_dependence={str(n):dict(fragments=sum(f['samples']==n for f in allfm),
                    detections=sum(f['detection_count'] for f in allfm if f['samples']==n)) for n in sorted({f['samples'] for f in allfm})},
                status_transitions=dict(Counter(e['prior_status']+' -> '+e['association']['status'] for e in results)),
                structural_constraint_violations=sum(e['association']['structural_constraint_violations'] for e in results))
            row.update(state='COMPLETE', metrics=metrics)
            dump(output/(arm+'.json'), dict(arm=row, episodes=results, anomalous_fragments=anomalies))
        phase = 'synthetic_matrix'
        # Stream all 100800 fixtures, all 40 detector cells. Association fixtures
        # above independently exercise each association rule; no fitting occurs.
        synthetic_counts = {}
        with (output/'synthetic.jsonl').open('x') as stream:
            for spec in synthetic_specs():
                f, p, centres = synthetic_spectrum(spec)
                for representation in REPRESENTATIONS:
                    components = detect(f, p, representation)
                    for width in WIDTHS:
                        cs = apply_width(components, width, 1, 1)
                        record = dict(fixture=spec, representation=representation, width_hz=width,
                                      metrics=synthetic_metrics(cs, centres, spec['fwhm_hz']))
                        stream.write(json.dumps(record, sort_keys=True, allow_nan=False)+'\n')
                        accumulate_synthetic(synthetic_counts, record)
        dump(output/'synthetic-summary.json', list(synthetic_counts.values()))
        dump(output/'decision-gates.json', evaluate_gates(matrix, synthetic_counts, fixture_summary))
        phase = 'complete'
    except ComputationUnresolved as exc:
        failure = dict(phase=phase, **exc.details)
    except Exception as exc:
        failure = dict(phase=phase, exception=type(exc).__name__, reason=str(exc))
    dump(output/'run.json', dict(provenance=provenance, phase=phase, failure=failure,
                                synthetic_complete=phase=='complete', gates_evaluable=phase=='complete'))
    dump(output/'arms.json', matrix)
    with (output/'arms.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['arm_id', 'representation', 'width_hz', 'association', 'state', 'metrics', 'failure'])
        writer.writeheader()
        for row in matrix:
            writer.writerow({k: json.dumps(v, sort_keys=True) if k in ('metrics', 'failure') else v for k, v in row.items()})
    completed = sum(r['state']=='COMPLETE' for r in matrix)
    summary = ['# Draft 2 experiment execution', '', f'Real-data arms completed: {completed}/160.',
               f'Synthetic spectral matrix complete: {phase == "complete"}.',
               'All six captures are development data. V1 and Draft 1 remain frozen controls.',
               'No parameter set selected. No discrimination or identification inference.', '',
               'Failure: '+(json.dumps(failure, sort_keys=True) if failure else 'none'), '',
               'Decision gates: '+('See decision-gates.json; all arms reported without selection.' if phase=='complete' else 'NOT EVALUABLE: experiment incomplete.'), '',
               '| Arm | State |', '|---|---|'] + [f'| {r["arm_id"]} | {r["state"]} |' for r in matrix]
    (output/'summary.md').write_text('\n'.join(summary)+'\n')
    paths = sorted(p for p in output.iterdir() if p.is_file())
    (output/'files.sha256').write_text(''.join(f'{d1.digest(p.read_bytes())}  {p.name}\n' for p in paths))
    print(json.dumps(dict(completed=completed, failure=failure), sort_keys=True))
    return 2 if failure else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    sys.exit(run(parser.parse_args().output))
