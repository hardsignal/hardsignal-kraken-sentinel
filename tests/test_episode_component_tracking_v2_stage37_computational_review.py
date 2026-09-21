"""Read-only Stage 37 evidence reconstruction; never launches scientific work.

Run with PYTHONPATH=analysis python -m unittest discover -s tests -p '*stage37*'.
The raw-tree test is explicitly skipped when the external archive is unavailable.
"""
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import statistics
import subprocess
from unittest.mock import patch
import unittest
from provenance.stage37_gitignore_v1 import effective_historical_digest

ROOT = Path(__file__).resolve().parents[1]
RAW = Path('/home/maciejduranczyk/hardsignal-kraken-sentinel/results/episode-component-tracking-v2-draft2-full-matrix-exact-v1')
AUDIT = 'results/episode-component-tracking-v2-draft2-stage36-final-audit.json'
INVENTORY = 'results/episode-component-tracking-v2-draft2-stage36-files.sha256'
PLAN = 'results/episode-component-tracking-v2-draft2-full-matrix-launch-plan.json'
REVIEW = 'results/episode-component-tracking-v2-stage37-computational-review.json'
LIMITS = dict(count=dict(max_states=250000, max_transitions=5000000, max_seconds=60,
                        max_polynomial_bytes=33554432),
              family_construction_seconds=60, query=dict(max_calls=5000, max_seconds=120),
              worker_timeout_seconds=400, worker_rss_kib=524288, workers=1)
DECISION = 'STAGE37_COMPUTATIONAL_EVIDENCE_REVIEW_COMPLETE'
PINS = {'results/episode-component-tracking-v2-draft2-stage36-final-audit.json': 'bc2243896e6db220733ebe7cf917e6c1f08185bc935b54dd55c9f8e39d8eabcb', 'results/episode-component-tracking-v2-draft2-stage36-files.sha256': '3f2794459be61714e7d5b1859ca919e16882f71fe1794db8b2905089006d92ba', 'results/episode-component-tracking-v2-draft2-full-matrix-launch-plan.json': 'b36749cd17804f70955be52b5c35d8e9d803bb643d72349a692ff1407a15b9c9', 'results/episode-component-tracking-v2-draft2-full-matrix-canonical-arms.json': 'd6b85599a9241f3267d91ded0b5145d208ec63f1507086e28fb14c3cd6b05b3a', '.gitignore': '3bea5d21bee9a0982907fab3c62f8a873010c8e5d8e4722722a967ba103439ba', 'results/episode-component-tracking-v2-draft2-full-matrix-launch-binding-v2.json': '800dfcb6578b800d001632ef02b0570bd9b487689daa90c4acbf11368e74d5b6'}
REVIEW_SHA256 = 'bbaa1560539e54e98bb49cc0665e0c010641f7d81a7d9a7822ee01b6f9e83ceb'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    # Explicit linear interpolation at (n - 1) * p.
    def percentile(p):
        x = (len(values) - 1) * p
        lo = int(x)
        return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (x - lo)
    return dict(n=len(values), min=values[0], median=statistics.median(values),
                p95=percentile(.95), max=values[-1], mean=statistics.mean(values), sum=sum(values))


def polynomial_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('peak_packed_bytes', 'polynomial_bytes', 'packed_polynomial_bytes', 'bytes_required') and isinstance(item, int):
                yield item
            yield from polynomial_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from polynomial_values(item)


def resource_summary(rows):
    return dict(arms=len(rows), states=dict(sorted(Counter(a['state'] for a in rows).items())),
                elapsed_seconds=distribution([a['elapsed_seconds'] for a in rows]),
                observed_peak_rss_kib=distribution([a['observed_peak_rss_kib'] for a in rows]))


def validate_review(payload):
    require(payload['decision'] == DECISION, 'decision drift')
    require(payload['limits'] == LIMITS, 'limit drift')
    require(payload['evidence_sha256'] == PINS, 'evidence binding drift')
    audit = read(ROOT / AUDIT)
    require([{k: row[k] for k in original} for row, original in zip(payload['arms'], audit['arms'])] == audit['arms'], 'arm payload drift')
    require(len(payload['arms']) == 160, 'arm count drift')
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + '\n').encode()
    require(hashlib.sha256(encoded).hexdigest() == REVIEW_SHA256, 'review payload drift')


def build_review(raw=RAW):
    """Recompute aggregates from archived bytes, with no solver execution or writes."""
    for name, digest in PINS.items():
        require(sha(ROOT / name) == digest, 'frozen evidence drift: ' + name)
    audit, plan = read(ROOT / AUDIT), read(ROOT / PLAN)
    require(plan['limits'] == LIMITS, 'plan limit drift')
    binding = read(ROOT / 'results/episode-component-tracking-v2-draft2-full-matrix-launch-binding-v2.json')
    for name, digest in plan['sources'].items():
        if name == binding['runner_path']:
            digest = binding['runner_sha256']
        if name == '.gitignore':
            historical = subprocess.check_output(['git','show','e559d63:' + name], cwd=ROOT)
            require(hashlib.sha256(historical).hexdigest() == digest, 'historical gitignore drift')
        else:
            require(effective_historical_digest(ROOT, name, sha(ROOT / name)) == digest,
                    'source drift: ' + name)
    inventory = {}
    for line in (ROOT / INVENTORY).read_text().splitlines():
        digest, name = line.split('  ', 1)
        name = name.removeprefix('./')
        require(name not in inventory, 'duplicate inventory path')
        inventory[name] = digest
    actual_paths = {str(p.relative_to(raw)) for p in raw.rglob('*') if p.is_file()}
    require(actual_paths == set(inventory), 'raw inventory additions or omissions')
    for name, digest in inventory.items():
        require(sha(raw / name) == digest, 'raw hash drift: ' + name)
    canonical = [a['arm_id'] for a in plan['arms']]
    require(len(canonical) == len(set(canonical)) == 160, 'canonical duplicates')
    require(set(canonical) == {a['arm'] for a in audit['arms']} and len(audit['arms']) == 160, 'audit arm drift')
    seen, batches, receipts = set(), [], {}
    for batch in sorted(raw.glob('stage36-full*')):
        checkpoint = read(batch / 'batch.json')
        require(checkpoint['limits'] == LIMITS, 'batch limit drift')
        require(checkpoint['plan_sha256'] == sha(ROOT / PLAN), 'batch plan drift')
        require(checkpoint['manifest_sha256'] == audit['manifest_sha256'], 'batch manifest drift')
        selected = checkpoint['selected']
        require(selected == [a for a in canonical if a not in seen], 'selection is not previously unaccounted suffix')
        executed = [a for a in selected if (batch / a / 'receipt.json').exists()]
        require(executed == selected[:len(executed)], 'non-prefix execution')
        require(not seen.intersection(executed), 'retry or duplicate')
        require({p.parent.name for p in batch.glob('*/receipt.json')} == set(executed), 'unselected execution')
        for arm in executed:
            receipts[arm] = batch / arm
        seen.update(executed)
        batches.append(dict(batch=batch.name, selected_count=len(selected), executed_count=len(executed),
                            executed_arms=executed, selected_only_previously_unaccounted=True))
    require(seen == set(canonical), 'missing execution')
    rows, episode_metrics = [], []
    for original in audit['arms']:
        row = dict(original)
        directory = receipts[row['arm']]
        require(directory.parent.name == row['batch'], 'batch attribution drift')
        receipt = read(directory / 'receipt.json')
        require(sha(directory / 'receipt.json') == row['receipt_sha256'], 'terminal receipt drift')
        require(receipt['state'] == row['state'], 'terminal state drift')
        require(receipt['plan_sha256'] == sha(ROOT / PLAN) and receipt['manifest_sha256'] == audit['manifest_sha256'], 'receipt binding drift')
        files = {str(p.relative_to(directory)): inventory[str(p.relative_to(raw))]
                 for p in directory.rglob('*') if p.is_file() and p.name != 'receipt.json'}
        require(files == receipt['files'], 'receipt file set drift')
        worker = read(directory / 'worker-audit.json')
        require(worker['limits'] == LIMITS and worker['reason'] is None, 'worker limit or termination drift')
        for key in ('elapsed_seconds', 'observed_peak_rss_kib', 'exit_code'):
            require(worker[key] == row[key], 'worker audit mismatch')
        require(0 < row['elapsed_seconds'] < 400 and 0 < row['observed_peak_rss_kib'] < 524288, 'worker ceiling exceeded')
        rep, width, assoc = row['arm'].split('__')
        row.update(representation=rep, width=width[1:], association=assoc,
                   classification='A' if row['state'] == 'COMPLETE' else 'B',
                   timeout_fraction=row['elapsed_seconds'] / 400,
                   rss_fraction=row['observed_peak_rss_kib'] / 524288,
                   timeout_headroom_seconds=400-row['elapsed_seconds'],
                   rss_headroom_kib=524288-row['observed_peak_rss_kib'])
        if row['state'] == 'COMPLETE':
            require(row['exit_code'] == 0 and (directory / 'worker-complete.json').exists(), 'missing completion')
            require(read(directory / 'worker-complete.json')['peak_rss_kib'] <= row['observed_peak_rss_kib'], 'RSS mismatch')
        else:
            failure = read(directory / 'failure.json')
            require(failure == dict(state='COMPUTATION_UNRESOLVED', reason='Unresolved: Exact-cover search limit reached; result is unresolved'), 'failure drift')
            require(row['exit_code'] == 1 and not (directory / 'worker-complete.json').exists(), 'invalid failure evidence')
        metrics, incomplete = [], []
        for episode in sorted(directory.glob('episode-*')):
            if not (episode / 'result.json').exists():
                incomplete.append(dict(episode=episode.name, retained_files=sorted(p.name for p in episode.iterdir())))
                continue
            result = read(episode / 'result.json')
            require(result['states']['provenance_validation']['state'] == 'VERIFIED' and
                    result['states']['metric_projection']['state'] == 'COMPLETE', 'result stage drift')
            require(result['computational_limits'] == LIMITS['query'], 'query limit drift')
            require(result['query_engine']['query_limits'] == LIMITS['query'] and result['query_engine']['search_limit'] == 200000, 'query engine drift')
            metric = dict(arm=row['arm'], episode=episode.name, arm_state=row['state'],
                          query_calls=result.get('query_calls'), count=None, query_statistics=read(episode / 'query-statistics.json'))
            require((episode / 'reload.json').exists(), 'missing reload evidence')
            if assoc == 'connected':
                require(result['cardinality'] is None and metric['query_calls'] is None and metric['query_statistics'] is None, 'connected applicability drift')
                require(not (episode / 'count-outcome.json').exists(), 'unexpected connected count')
            else:
                count = read(episode / 'count-outcome.json')
                card = read(episode / 'cardinality.json')
                require(count['count_state'] == card['cardinality']['state'] == 'EXACT', 'inexact cardinality')
                require(count['exact_count_decimal'] == card['cardinality']['value_decimal'] == result['cardinality']['value_decimal'], 'cardinality mismatch')
                require(card['computational_limits'] == LIMITS['count'], 'count limit drift')
                require(card['runtime_state_statistics'] == count['statistics'], 'count statistics mismatch')
                for k, limit in [('peak_states',250000),('transitions',5000000),('elapsed_seconds',60)]:
                    require(0 <= count['statistics'][k] <= limit, 'count resource exceeded')
                poly = list(polynomial_values(count))
                require(poly and max(poly) <= 33554432, 'polynomial metric missing or exceeded')
                require(0 <= metric['query_calls'] <= 5000, 'query calls exceeded')
                require(result['states']['exact_queries']['state'] == 'EXACT', 'query incomplete')
                metric['count'] = dict(value_decimal=count['exact_count_decimal'], method=count['method'],
                                       dispatch=count['details']['dispatch'], statistics=count['statistics'], polynomial_bytes=max(poly))
            metrics.append(metric)
        require(len(metrics) == 41 if row['state'] == 'COMPLETE' else len(metrics) == 1, 'episode coverage drift')
        if row['state'] != 'COMPLETE':
            require(incomplete == [dict(episode='episode-002', retained_files=['candidates.json','family.json'])], 'unresolved terminal boundary drift')
        row['completed_episode_count'] = len(metrics)
        row['incomplete_episodes'] = incomplete
        row['query_calls'] = distribution([m['query_calls'] for m in metrics if m['query_calls'] is not None])
        counts = [m['count'] for m in metrics if m['count']]
        row['count_metrics'] = {k: distribution([c['statistics'][k] for c in counts]) for k in ['peak_states','transitions','elapsed_seconds']}
        row['count_metrics']['polynomial_bytes'] = distribution([c['polynomial_bytes'] for c in counts])
        row['count_methods'] = dict(sorted(Counter(c['method'] for c in counts).items()))
        row['cardinality_range_decimal'] = dict(min=str(min(int(c['value_decimal']) for c in counts)), max=str(max(int(c['value_decimal']) for c in counts))) if counts else None
        rows.append(row)
        episode_metrics.extend(metrics)
    states = dict(Counter(r['state'] for r in rows))
    require(states == {'COMPLETE':152,'COMPUTATION_UNRESOLVED':8}, 'accounting drift')
    unresolved = [r['arm'] for r in rows if r['classification'] == 'B']
    require(set(unresolved) == {f'native__w{w}__paths_margin{m}' for w in ['300','325','350','unlimited'] for m in ['0.25','1']}, 'unresolved pattern drift')
    groups = {}
    for fields in [('state',),('representation','state'),('representation','width','state'),('representation','association','state'),('width','state'),('association','state'),('representation','width','association','state')]:
        buckets = defaultdict(list)
        for row in rows:
            buckets[' / '.join(str(row[f]) for f in fields)].append(row)
        groups['_'.join(fields)] = {key:resource_summary(value) for key,value in sorted(buckets.items())}
    counted = [m for m in episode_metrics if m['count']]
    def extrema(key):
        vals = [(m['count']['statistics'][key],m['arm'],m['episode']) for m in counted]
        peak = max(vals)
        return dict(distribution=distribution([v[0] for v in vals]), maximum=dict(value=peak[0],arm=peak[1],episode=peak[2]))
    queries = [m for m in episode_metrics if m['query_calls'] is not None]
    qmax = max(queries,key=lambda m:m['query_calls'])
    polymax = max(counted,key=lambda m:m['count']['polynomial_bytes'])
    maxcard = max(counted,key=lambda m:int(m['count']['value_decimal']))
    smoke = [dict(batch=p.parent.parent.name, arm=p.parent.name, state=read(p)['state']) for p in sorted(raw.glob('stage36-smoke*/*/receipt.json'))]
    require(len(smoke) == 2 and all(s['state']=='COMPLETE' and s['arm'] not in unresolved for s in smoke), 'smoke accounting drift')
    return dict(decision=DECISION, stage='37B-preselection', frozen_checkpoint='0df44abb54231d5e8bfe84fe316ebbcf10d3130c',
                evidence_sha256=PINS, limits=LIMITS, raw_root=str(raw),
                classification=dict(A='COMPLETE within observed frozen worker and recorded inner budgets',B='COMPUTATION_UNRESOLVED: exact-cover search bound reached',C='Not applicable or unavailable; null is never zero usage'),
                integrity=dict(inventory_files_verified=len(inventory), source_files_verified=len(plan['sources']), canonical_arms=160,
                               states=states, duplicate_full_matrix_executions=0, unresolved_retries=0, grid_complete=128,
                               limit_drift=False, all_terminal_receipts_verified=True,
                               source_binding_exceptions=['Runner uses committed launch-binding-v2 digest', '.gitignore changed only at evidence-freeze checkpoint; historical launch bytes verified; unmodified verify_plan now rejects it'], executed_batches_disjoint=True,
                               planned_selections_pairwise_disjoint=False, selection_rule='Each selected list equals the canonical suffix not yet accounted at batch start',
                               batches=batches, smoke_runs_excluded=smoke),
                arms=rows, groups=groups, unresolved_arms=unresolved,
                episode_aggregates=dict(completed_episode_results=len(episode_metrics), exact_count_episodes=len(counted),
                    connected_not_applicable=len(episode_metrics)-len(counted), partial_unresolved_completed_episodes=8,
                    count_statistics={k:extrema(k) for k in ['peak_states','transitions','elapsed_seconds']},
                    polynomial_bytes_maximum=dict(value=polymax['count']['polynomial_bytes'],arm=polymax['arm'],episode=polymax['episode']),
                    polynomial_bytes=distribution([m['count']['polynomial_bytes'] for m in counted]),
                    count_methods=dict(sorted(Counter(m['count']['method'] for m in counted).items())),
                    dispatches=[json.loads(s) for s in sorted({json.dumps(m['count']['dispatch'],sort_keys=True) for m in counted})],
                    cardinality_min_decimal=str(min(int(m['count']['value_decimal']) for m in counted)),
                    cardinality_max=dict(value_decimal=maxcard['count']['value_decimal'],arm=maxcard['arm'],episode=maxcard['episode']),
                    query_calls=distribution([m['query_calls'] for m in queries]),
                    query_calls_maximum=dict(value=qmax['query_calls'],arm=qmax['arm'],episode=qmax['episode']),
                    query_find_calls=distribution([m['query_statistics']['engine']['find_calls'] for m in queries]),
                    factor_search_nodes=distribution([f['search_nodes'] for m in queries for f in m['query_statistics']['factors']])),
                validation=dict(new_review_tests=4, exact_solver_and_count_tests=39,
                                existing_full_matrix_tests=dict(run=43,passed=34,errors=9,
                                    reason='Pre-existing .gitignore hash mismatch introduced by frozen checkpoint 0df44ab'),
                                scientific_arm_executions_during_review=0),
                unavailable_metrics=['Per-episode query elapsed seconds','Family construction elapsed seconds',
                                     'Counters at the failing exact-cover search boundary','Count/query metrics for unexecuted later episodes',
                                     'Continuous RSS trace; worker audit retains sampled RSS/high-water maximum'],
                assessment='Computational evidence only; no final configuration selection. Completion does not establish scientific quality; unresolved does not establish scientific inferiority. All recorded completed metrics fit frozen ceilings; missing timings prevent independent numeric confirmation of every inner time ceiling.')


class ComputationalReviewTests(unittest.TestCase):
    def test_frozen_bindings_and_payload(self):
        for name, digest in PINS.items():
            self.assertEqual(sha(ROOT / name), digest, name)
        validate_review(read(ROOT / REVIEW))

    def test_payload_and_limit_drift_rejected(self):
        baseline = read(ROOT / REVIEW)
        for mutate in [lambda p:p['limits'].__setitem__('workers',2),
                       lambda p:p['limits']['count'].__setitem__('max_states',250001),
                       lambda p:p['arms'][0].__setitem__('elapsed_seconds',0),
                       lambda p:p['episode_aggregates']['query_calls'].__setitem__('max',0),
                       lambda p:p['integrity'].__setitem__('unresolved_retries',1)]:
            payload = copy.deepcopy(baseline)
            mutate(payload)
            with self.assertRaises(ValueError):
                validate_review(payload)

    def test_frozen_launch_sources_and_limits(self):
        import episode_component_tracking_v2_draft2_full_matrix_exact as launch
        self.assertEqual(launch.LIMITS, LIMITS)
        # The saved review records the pre-repair failure; its bytes stay frozen.
        self.assertEqual(len(launch.verify_plan()['arms']), 160)

    @unittest.skipUnless(RAW.is_dir(), 'External read-only Stage 36 archive unavailable')
    def test_raw_inventory_receipts_and_recomputed_aggregates(self):
        self.assertEqual(build_review(), read(ROOT / REVIEW))


if __name__ == '__main__':
    unittest.main()
