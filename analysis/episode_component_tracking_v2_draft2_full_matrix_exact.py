#!/usr/bin/env python3
"""Versioned, opt-in frozen Draft 2 matrix execution; default is refusal.

Planning never calls scientific functions. Computation has no case-name dispatch.
All failures are terminal evidence within a batch; no automatic retries.
"""
import argparse
from collections import Counter
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import regress_episode_component_tracking_v2_draft2_six_capture_corrected as corrected

historical = corrected.staged.historical
staged = corrected.staged
sc = corrected.sc
ROOT = Path(__file__).resolve().parents[1]
STEM = 'episode-component-tracking-v2-draft2-full-matrix'
CANONICAL = ROOT / f'results/{STEM}-canonical-arms.json'
MANIFEST_SHA256 = 'd6b85599a9241f3267d91ded0b5145d208ec63f1507086e28fb14c3cd6b05b3a'
PLAN = ROOT / f'results/{STEM}-launch-plan.json'
OUTPUT = ROOT / 'results/episode-component-tracking-v2-draft2-full-matrix-exact-v1'
LAUNCH_INTEGRATION_BASE = '30904f3513d1c0c7354e4be02e77c35b3b28303f'
PLAN_SHA256 = 'b36749cd17804f70955be52b5c35d8e9d803bb643d72349a692ff1407a15b9c9'
BINDING = ROOT / f'results/{STEM}-launch-binding-v2.json'
RUNNER = 'analysis/episode_component_tracking_v2_draft2_full_matrix_exact.py'
REPRESENTATIONS = ('native', 'grid_sigma0', 'grid_sigma5', 'grid_sigma10', 'grid_sigma20')
WIDTHS = (200, 225, 250, 275, 300, 325, 350, None)
ASSOCIATIONS = ('connected', 'paths_margin0', 'paths_margin0.25', 'paths_margin1')
COUNT_LIMITS = dict(max_states=250000, max_transitions=5000000,
                    max_seconds=60, max_polynomial_bytes=33554432)
LIMITS = dict(count=COUNT_LIMITS, query=dict(max_calls=5000, max_seconds=120),
              family_construction_seconds=60, worker_timeout_seconds=400,
              worker_rss_kib=524288, workers=1)
# A deliberately stricter implementation of the review's conditional <=2 ceiling.
# There is no second-worker option until separate authorization/evidence is added.
MAX_WORKERS = 1
FIELDS = ('arm_id', 'representation', 'width_hz', 'association')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    """Exclusive artifact creation: a completed or failed artifact is never replaced."""
    with Path(path).open('xb') as stream:
        stream.write(corrected.exact.canonical_bytes(value))


def canonical(path=CANONICAL):
    if sc.sha(path) != MANIFEST_SHA256:
        raise ValueError('Canonical manifest changed')
    data = read(path)
    arms = [{k: row[k] for k in FIELDS} for row in data['arms']]
    combinations = [(a['representation'], a['width_hz'], a['association']) for a in arms]
    if (data['arm_count'] != 160 or len(arms) != 160
            or len({a['arm_id'] for a in arms}) != 160
            or len(set(combinations)) != 160
            or set(combinations) != set(itertools.product(REPRESENTATIONS, WIDTHS, ASSOCIATIONS))
            or arms != historical.arms()
            or [a['ordinal'] for a in data['arms']] != list(range(1, 161))):
        raise ValueError('Frozen Cartesian matrix/order mismatch')
    return arms


def verify_plan(plan_path=PLAN, expected_hash=None):
    if expected_hash is not None and sc.sha(plan_path) != expected_hash:
        raise ValueError('Wrong frozen plan hash')
    plan = read(plan_path)
    if (plan['arms'] != canonical() or plan['manifest_sha256'] != MANIFEST_SHA256
            or plan['limits'] != LIMITS or plan['output_root'] != str(OUTPUT.relative_to(ROOT))
            or plan['format'] != 'KRAKEN_DRAFT2_FULL_MATRIX_EXACT_PLAN_V1'):
        raise ValueError('Frozen plan/configuration mismatch')
    if staged.QUERY_LIMITS != LIMITS['query']:
        raise ValueError('Query limit drift')
    if sc.sha(plan_path) != PLAN_SHA256:
        raise ValueError('Frozen launch plan hash drift')
    binding = read(BINDING)
    # Only the launch-control adapter is superseded. The original plan and its
    # original runner digest remain historical evidence, not rewritten provenance.
    expected_binding = dict(
        format='KRAKEN_DRAFT2_FULL_MATRIX_LAUNCH_BINDING_V2',
        launch_integration_base=LAUNCH_INTEGRATION_BASE,
        plan_sha256=PLAN_SHA256, manifest_sha256=MANIFEST_SHA256,
        runner_path=RUNNER, original_runner_sha256=plan['sources'][RUNNER],
        runner_sha256=sc.sha(ROOT / RUNNER))
    if binding != expected_binding:
        raise ValueError('Launch binding / exact runner source hash drift')
    if plan['checkpoint'] != LAUNCH_INTEGRATION_BASE:
        raise ValueError('Launch integration base mismatch')
    current_head = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.run(['git', 'merge-base', '--is-ancestor',
                       LAUNCH_INTEGRATION_BASE, current_head], cwd=ROOT,
                      capture_output=True).returncode != 0:
        raise ValueError('HEAD is not a descendant of launch integration base')
    if OUTPUT.resolve() != OUTPUT or any(
            (ROOT / path).is_relative_to(OUTPUT) for path in plan['sources']):
        raise ValueError('Historical output namespace collision or symlink')
    for path, digest in plan['sources'].items():
        if path == RUNNER:
            digest = binding['runner_sha256']
        if sc.sha(ROOT / path) != digest:
            raise ValueError('Provenance source hash drift: ' + path)
    required = {str(p.relative_to(ROOT)) for p in (ROOT / 'analysis').glob('*.py')}
    if not required <= set(plan['sources']):
        raise ValueError('Incomplete source provenance')
    for suffix, decision in [('definition', 'MATRIX_DEFINITION_FROZEN_AND_RECONSTRUCTED'),
                             ('feasibility', 'COMPUTATIONAL_BLOCKERS_REMAIN')]:
        if read(ROOT / f'results/{STEM}-{suffix}-review.json')['decision'] != decision:
            raise ValueError('Historical review changed')
    return plan


def select(arms, identifiers):
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ValueError('Explicit nonempty unique arm selection required')
    if not set(identifiers) <= {a['arm_id'] for a in arms}:
        raise ValueError('Unknown arm')
    return [a for a in arms if a['arm_id'] in identifiers]


def checkpoint(plan_hash, selected, context):
    return dict(format='KRAKEN_DRAFT2_FULL_MATRIX_EXACT_BATCH_V1', plan_sha256=plan_hash,
                manifest_sha256=MANIFEST_SHA256, limits=LIMITS,
                selected=[a['arm_id'] for a in selected], git_context=context)


def association(fragments, setting, directory, context, sources):
    """Only scientific setting + candidate structure enter computational dispatch.

    No capture, episode, device, arm identifier, expected count or outcome argument.
    The same corrected count_exact function is used by the committed regression.
    """
    family_path = sidecar_path = None
    write(directory / 'candidates.json', fragments)
    if setting not in ASSOCIATIONS:
        raise ValueError('Unknown association setting')
    if setting != 'connected':
        family = corrected.limited.construct(fragments, float(setting.removeprefix('paths_margin')), 60)
        family_path = directory / 'family.json'
        write(family_path, family.artifact())
        budget = corrected.previous.Budget(**COUNT_LIMITS)
        with staged.deadline(60):
            counted = corrected.count_exact(family, budget)
        outcome = dict(count_state='EXACT', exact_count_decimal=str(counted.pop('count')),
                       method=counted['method'], certificate=counted.get('certificate'),
                       details=counted, statistics=dict(budget.stats(),
                           process_peak_rss_kib=corrected.memory()['VmHWM']))
        for statistic, limit in [('peak_states', 'max_states'), ('transitions', 'max_transitions'),
                                 ('elapsed_seconds', 'max_seconds')]:
            if outcome['statistics'][statistic] > COUNT_LIMITS[limit]:
                raise ValueError('Counting resource limit exceeded: ' + statistic)
        if corrected.polynomial_bytes(outcome) > COUNT_LIMITS['max_polynomial_bytes']:
            raise ValueError('Packed polynomial limit exceeded')
        write(directory / 'count-outcome.json', outcome)
        with staged.deadline(60):
            card = sc.create(ROOT, family_path, outcome, [ROOT / p for p in sources if p.startswith('analysis/')], COUNT_LIMITS)
        sidecar_path = directory / 'cardinality.json'
        write(sidecar_path, card)
    request = staged.request(ROOT, fragments, staged.CONNECTED if setting == 'connected' else staged.COMPACT,
                             family_path, sidecar_path, staged.reference(ROOT, directory / 'candidates.json'))
    write(directory / 'request.json', request)
    with corrected.construction_limits(60):
        result, statistics = corrected.queries.integrate(
            ROOT, request, fragments, context, corrected.queries.engine_reference(ROOT, 'forward'))
    write(directory / 'result.json', result)
    write(directory / 'query-statistics.json', statistics)
    required = dict(provenance_validation='VERIFIED', metric_projection='COMPLETE')
    if setting != 'connected':
        required.update(family_construction='COMPLETE', cardinality_counting='EXACT', exact_queries='EXACT')
    if any(result['states'][k]['state'] != v for k, v in required.items()):
        raise ValueError('Incomplete exact stages; see preserved result')
    if result['association']['structural_constraint_violations']:
        raise ValueError('Scientific structural constraint violation')
    # Reload revalidates hashes, family, public queries, and deterministic bytes.
    with corrected.construction_limits(60):
        corrected.queries.reproduce(ROOT, read(directory / 'result.json'), fragments)
    write(directory / 'reload.json', dict(state='BYTE_IDENTICAL'))
    return result


def execute_arm(arm, directory, batch, plan):
    """Future worker body. This function is never called by plan-only mode."""
    episodes, inputs = historical.load_inputs()
    write(directory / 'inputs.json', inputs)
    records = []
    for index, ep in enumerate(episodes):
        fs, fm = [], []
        for source in ep['fragments']:
            meta = source['metadata']
            components = historical.detect(source['frequency'], source['power'], arm['representation'])
            cs = historical.apply_width(components, arm['width_hz'], ep['episode'], meta['fragment_index'])
            fs.append(dict(usable_spectrum=meta['usable_spectrum'], components=cs))
            fm.append(historical.fragment_metrics(source['frequency'], source['power'], cs,
                                                   meta['v1_strongest_component_offset_hz']))
        case = directory / f'episode-{index + 1:03d}'
        case.mkdir()
        result = association(fs, arm['association'], case, batch['git_context'], plan['sources'])
        records.append(dict(capture=ep['capture'], episode=ep['episode'], fragments=fm,
                            components=fs, association=result['association'], metrics=result['metrics'],
                            prior_status=ep['prior']['status'],
                            primary_after_connected_veto=(result['association']['primary'] is not None
                                and historical.d1.track_episode(fs)['primary_track_id'] is None)))
    # This entrypoint executes the real-data matrix only. Shared historical
    # association/synthetic fixtures remain separately pinned evidence; no new
    # acceptance decision or reinterpretation of their failures is made here.
    allfm = [f for e in records for f in e['fragments']]
    metrics = dict(detection_count=sum(f['detection_count'] for f in allfm),
        width_rejection=sum(f['width_rejection'] for f in allfm),
        primary_tracks=sum(e['association']['primary'] is not None for e in records),
        null_primary_episodes=sum(e['association']['primary'] is None for e in records),
        persistent_tracks=sum(len(e['association']['persistent_tracks']) for e in records),
        statuses=dict(Counter(e['association']['status'] for e in records)),
        diagnostic_dominant_denominator=sum(f['dominant_in_diagnostic_region'] for f in allfm),
        diagnostic_dominant_retained=sum(f['dominant_in_diagnostic_region'] and f['dominant_retained'] for f in allfm),
        resolution_dependence={str(n): dict(fragments=sum(f['samples'] == n for f in allfm),
            detections=sum(f['detection_count'] for f in allfm if f['samples'] == n))
            for n in sorted({f['samples'] for f in allfm})},
        status_transitions=dict(Counter(e['prior_status'] + ' -> ' + e['association']['status'] for e in records)),
        structural_constraint_violations=sum(e['association']['structural_constraint_violations'] for e in records))
    write(directory / 'arm.json', dict(arm=arm, episodes=records, metrics=metrics))


def batch_directory(name):
    if not name or Path(name).name != name or name in ('.', '..'):
        raise ValueError('Batch must be a simple directory name')
    path = OUTPUT / name
    if OUTPUT.is_symlink() or path.is_symlink() or path.resolve() != path:
        raise ValueError('Output symlink/escape prohibited')
    return path


def verify_receipt(directory):
    receipt = read(directory / 'receipt.json')
    actual = {str(p.relative_to(directory)): sc.sha(p) for p in sorted(directory.rglob('*'))
              if p.is_file() and p.name != 'receipt.json'}
    if actual != receipt['files']:
        raise ValueError('Result hash drift')
    if receipt['state'] != 'COMPLETE':
        raise ValueError('Failed arm preserved; automatic retry prohibited')


def worker(batch_path, arm_id, plan_hash):
    plan = verify_plan(expected_hash=plan_hash)
    batch = read(batch_path)
    if batch['plan_sha256'] != plan_hash or arm_id not in batch['selected']:
        raise ValueError('Worker authorization mismatch')
    arm = select(plan['arms'], [arm_id])[0]
    directory = batch_path.parent / arm_id
    try:
        execute_arm(arm, directory, batch, plan)
        write(directory / 'worker-complete.json', dict(state='COMPLETE',
              peak_rss_kib=corrected.memory()['VmHWM']))
    except Exception as exc:
        write(directory / 'failure.json', dict(state='COMPUTATION_UNRESOLVED',
                                               reason=f'{type(exc).__name__}: {exc}'))
        return 1
    return 0


def launch_arm(batch_path, arm, plan_hash):
    directory = batch_path.parent / arm['arm_id']
    directory.mkdir()  # Atomic exclusive reservation, before creating any result.
    command = [sys.executable, str(Path(__file__).resolve()), '--internal-worker', str(batch_path),
               '--arm', arm['arm_id'], '--confirm-frozen-plan', plan_hash]
    start = time.monotonic()
    peak, reason = 0, None
    with (directory / 'worker.log').open('x') as log:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                usage = corrected.memory(proc.pid)
                peak = max(peak, usage.get('VmRSS', 0), usage.get('VmHWM', 0))
                if peak > LIMITS['worker_rss_kib']:
                    reason = 'Observed worker RSS ceiling exceeded'
                elif time.monotonic() - start > LIMITS['worker_timeout_seconds']:
                    reason = 'Worker timeout exceeded'
                if reason:
                    proc.kill()
                    break
                time.sleep(.05)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
    if (directory / 'worker-complete.json').exists():
        peak = max(peak, read(directory / 'worker-complete.json')['peak_rss_kib'])
        if peak > LIMITS['worker_rss_kib']:
            reason = 'Worker high-water RSS ceiling exceeded'
    write(directory / 'worker-audit.json', dict(exit_code=proc.returncode, reason=reason,
          observed_peak_rss_kib=peak, elapsed_seconds=time.monotonic() - start, limits=LIMITS))
    complete = proc.returncode == 0 and reason is None and (directory / 'worker-complete.json').exists()
    files = {str(p.relative_to(directory)): sc.sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}
    write(directory / 'receipt.json', dict(state='COMPLETE' if complete else 'COMPUTATION_UNRESOLVED',
          plan_sha256=plan_hash, manifest_sha256=MANIFEST_SHA256, files=files))
    return complete


def run_batch(name, selected, plan_hash, resume=False):
    verify_plan(expected_hash=plan_hash)
    directory = batch_directory(name)
    if resume:
        batch = read(directory / 'batch.json')
        if (batch['selected'] != [a['arm_id'] for a in selected]
                or batch != checkpoint(plan_hash, selected, batch['git_context'])):
            raise ValueError('Resume checkpoint mismatch')
    else:
        OUTPUT.mkdir(exist_ok=True)
        directory.mkdir()
        batch = checkpoint(plan_hash, selected, staged.git_context(ROOT))
        write(directory / 'batch.json', batch)
    # Exclusive controller lock; crashes leave a lock and require explicit review.
    lock = directory / 'controller.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        for arm in selected:
            target = directory / arm['arm_id']
            if target.exists():
                verify_receipt(target)
                continue
            if not launch_arm(directory / 'batch.json', arm, plan_hash):
                return 1
    finally:
        os.close(fd)
        lock.unlink()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan-only', action='store_true')
    mode.add_argument('--arm')
    mode.add_argument('--arm-list', type=Path, help='JSON list of unique canonical arm IDs')
    mode.add_argument('--execute-full-matrix', action='store_true')
    mode.add_argument('--resume', help='Existing batch name; selection comes from checkpoint')
    parser.add_argument('--confirm-frozen-plan')
    parser.add_argument('--batch')
    parser.add_argument('--internal-worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    plan = verify_plan(expected_hash=args.confirm_frozen_plan)
    if args.plan_only:
        if args.internal_worker or args.batch:
            parser.error('Plan mode cannot launch a worker or create a batch')
        print(json.dumps(dict(plan_sha256=sc.sha(PLAN), manifest_sha256=MANIFEST_SHA256,
                             arm_count=len(plan['arms']), limits=LIMITS,
                             output_paths=[str(OUTPUT / '<batch>' / a['arm_id']) for a in plan['arms']],
                             scientific_execution=False), sort_keys=True))
        return 0
    if not args.confirm_frozen_plan:
        parser.error('Execution requires --confirm-frozen-plan HASH')
    if args.internal_worker:
        # A worker can only be entered by its live controller, with exclusive reservation.
        path = args.internal_worker.resolve()
        if (path.name != 'batch.json' or path.parent.parent != OUTPUT
                or not (path.parent / 'controller.lock').is_file() or not args.arm
                or not (path.parent / args.arm).is_dir()):
            parser.error('Invalid internal worker reservation')
        return worker(path, args.arm, args.confirm_frozen_plan)
    if args.resume:
        if args.batch:
            parser.error('--resume specifies its own batch')
        ids = read(batch_directory(args.resume) / 'batch.json')['selected']
    elif args.execute_full_matrix:
        ids = [a['arm_id'] for a in plan['arms']]
    else:
        ids = [args.arm] if args.arm else read(args.arm_list)
        if len(ids) >= 160:
            parser.error('All arms require --execute-full-matrix')
    selected = select(plan['arms'], ids)
    if not (args.batch or args.resume):
        parser.error('Execution requires --batch NAME')
    return run_batch(args.batch or args.resume, selected, args.confirm_frozen_plan, bool(args.resume))


if __name__ == '__main__':
    sys.exit(main())
