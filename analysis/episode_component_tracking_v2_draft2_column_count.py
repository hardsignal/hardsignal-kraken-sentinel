"""Separate exact column-frontier counting prototype; no historical mutations."""
from collections import defaultdict
from fractions import Fraction
import math
import episode_component_tracking_v2_draft2_exact_count as previous


def column_histogram(rows, cap, budget, label, penalties=None, order=None, suffix_bound=True):
    """Rectangular permanent with nonnegative integer costs, packed exactly.

    Process each column once (unused, or assigned to one unmatched row).
    Forget rows only after their last column, requiring saturation. Polynomial
    digits count partial assignments; the bound product(degree+1) prevents carries.
    """
    penalties = penalties or {}
    columns = sorted({c for row in rows for c, w in row}) if order is None else list(order)
    if len(set(columns)) != len(columns) or set(columns) != {c for row in rows for c, w in row}:
        raise ValueError('Column order must be an exact permutation')
    if any(w < 0 or not isinstance(w, int) for row in rows for c, w in row):
        raise ValueError('Nonnegative integer weights required')
    if any(w < 0 or not isinstance(w, int) for w in penalties.values()):
        raise ValueError('Nonnegative integer penalties required')
    if any(len(dict(row)) != len(row) for row in rows):
        raise ValueError('Duplicate column in a row')
    if cap < 0 or any(not row for row in rows): return {}
    by_column = {c: [] for c in columns}
    for i, row in enumerate(rows):
        for c, w in row: by_column[c].append((1 << i, w))
    # Every prefix is an injective partial row assignment. The independent-row
    # relaxation (unassigned OR one of degree options) bounds all coefficients.
    coefficient_bound = math.prod(len(row) + 1 for row in rows)
    byte_width = max(1, (coefficient_bound.bit_length() + 7) // 8)
    lane_bits = 8 * byte_width
    if (cap + 1) * byte_width > budget.max_polynomial_bytes:
        raise previous.CountUnresolved('Single polynomial exceeds byte budget')
    mask = (1 << ((cap + 1) * lane_bits)) - 1
    future = [0] * (len(columns) + 1)
    minimum = [{} for _ in range(len(columns) + 1)]
    for k in range(len(columns) - 1, -1, -1):
        future[k] = future[k+1]
        minimum[k] = dict(minimum[k+1])
        for bit, w in by_column[columns[k]]:
            future[k] |= bit
            minimum[k][bit] = min(w, minimum[k].get(bit, w))
    active = 0
    states = {0: 1}
    peak_bytes = 0
    peak_masks = 1
    for k, c in enumerate(columns):
        active |= sum(bit for bit, w in by_column[c])
        expiring = active & ~future[k+1]
        new = {}
        lower_cache = {}
        transitions = 0
        for used, poly in states.items():
            choices = [(0, penalties.get(c, 0))] + by_column[c]
            for bit, w in choices:
                transitions += 1
                if bit & used or w > cap: continue
                chosen = used | bit
                if expiring & ~chosen: continue
                dest = chosen & future[k+1]
                if dest not in lower_cache:
                    # Independent minima ignore row competition and unused-column
                    # penalties: admissible, never an overestimate of completion.
                    lower_cache[dest] = sum(v for b, v in minimum[k+1].items() if not b & dest) if suffix_bound else 0
                remaining = cap - lower_cache[dest]
                if remaining < w: continue
                truncation = mask >> ((cap - remaining) * lane_bits)
                value = (poly << (w * lane_bits)) & truncation
                if value: new[dest] = new.get(dest, 0) + value
        stored = sum((p.bit_length()+7)//8 for p in states.values()) + sum((p.bit_length()+7)//8 for p in new.values())
        peak_bytes = max(peak_bytes, stored)
        peak_masks = max(peak_masks, len(states)+len(new))
        budget.check(states=len(states)+len(new), transitions=transitions,
                     phase='column polynomial frontier', component=label, column=k+1,
                     columns=len(columns), active_rows=(active & future[k+1]).bit_count(),
                     polynomial_bytes=stored, prior_masks=len(states), next_masks=len(new))
        if stored > budget.max_polynomial_bytes:
            raise previous.CountUnresolved('Live packed polynomial byte budget exceeded',
                bytes_required=stored, limit=budget.max_polynomial_bytes, component=label, column=k+1)
        states = new
        active &= future[k+1]
    assert set(states) <= {0}
    poly = states.get(0, 0)
    raw = poly.to_bytes((poly.bit_length()+7)//8, 'little')
    result = {i//byte_width: int.from_bytes(raw[i:i+byte_width], 'little') for i in range(0, len(raw), byte_width)}
    result = {k: v for k, v in result.items() if v}
    budget.checkpoints.append(dict(component=label, rows=len(rows), columns=len(columns),
        histogram_entries=len(result), count=str(sum(result.values())), peak_packed_bytes=peak_bytes,
        peak_frontier_masks=peak_masks, coefficient_digit_bytes=byte_width, suffix_bound=suffix_bound))
    return result


def matching_histogram(family, weights, optimum, cutoff, budget, label, ordering='frequency', suffix_bound=True):
    s = family.solver
    layers = defaultdict(list)
    for i, c in enumerate(s.nodes): layers[c['fragment_index']].append(i)
    small, large = sorted(layers.values(), key=lambda x: (len(x), s.nodes[x[0]]['fragment_index']))
    large = set(large)
    rows = []
    for i in sorted(small, key=lambda i: (s.nodes[i]['frequency_hz'], s.nodes[i]['candidate_id'])):
        rows.append([(next(j for j in s.paths[k].nodes if j != i), weights[k])
            for k in s.by_candidate[i] if len(s.paths[k].nodes) == 2
            and next(j for j in s.paths[k].nodes if j != i) in large])
    primal, rows, penalties = previous.assignment_dual(rows)
    if primal != optimum: raise previous.CountUnresolved('Certified optimum mismatch')
    rows = [[(c, w) for c, w in row if w <= cutoff] for row in rows]
    columns = {c for row in rows for c, w in row}
    forced = sum(w for c, w in penalties.items() if c not in columns)
    cap = cutoff - forced
    if cap < 0: return {}
    unseen = set(range(len(rows)))
    histogram = {0: 1}
    number = 0
    while unseen:
        indices = {min(unseen)}
        while True:
            cols = {c for i in indices for c, w in rows[i]}
            expanded = indices | {i for i in unseen if any(c in cols for c, w in rows[i])}
            if expanded == indices: break
            indices = expanded
        unseen -= indices
        block = [rows[i] for i in sorted(indices)]
        divisor = math.gcd(*([penalties[c] for c in cols] + [w for row in block for c, w in row])) or 1
        order = sorted(cols, key=lambda c: (s.nodes[c]['frequency_hz'], s.nodes[c]['candidate_id']))
        if ordering == 'reverse_frequency': order.reverse()
        elif ordering != 'frequency': raise ValueError('Unknown ordering')
        partial = column_histogram([[(c,w//divisor) for c,w in row] for row in block], cap//divisor,
            budget, f'{label}/block{number}', {c:penalties[c]//divisor for c in cols}, order, suffix_bound)
        histogram = previous.convolve(histogram, {k*divisor:v for k,v in partial.items()}, cap, budget)
        number += 1
    return {k+forced:v for k,v in histogram.items()}


def count(family, budget=None, ordering='frequency', suffix_bound=True):
    budget = budget or previous.Budget()
    factors = family.factors if isinstance(family, previous.solver.EpisodeFamily) else [family]
    if not factors: return dict(count=1, method='fixed singletons', stats=budget.stats(), certificate=None)
    try:
        cert = previous.lattice_certificate(factors, family.margin, previous.cost_lattice(factors))
    except previous.CertificateUnavailable:
        return previous.count(family, budget, backend='ieee')
    histogram = {0:1}
    for i, (f,w,opt) in enumerate(zip(factors,cert['weights'],cert['optima'])):
        partial = matching_histogram(f,w,opt,cert['cutoff'],budget,f'factor{i}',ordering,suffix_bound)
        histogram = previous.convolve(histogram,partial,cert['cutoff'],budget)
    proof = {k:([v.numerator,v.denominator] if isinstance(v,Fraction) else v) for k,v in cert.items() if k!='weights'}
    return dict(count=sum(histogram.values()), method='certified column frontier exact generating function',
        ordering=ordering, suffix_bound=suffix_bound, certificate=proof, histogram_entries=len(histogram), stats=budget.stats())
