"""Supplement the audit's inherited ru_maxrss with post-exec Linux VmHWM.

The validation parent imports test dependencies. Fork/exec can preserve its
ru_maxrss floor in children; /proc/self/status measures the current address space.
Only saved margin-1 families are read. Output must be new.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import episode_component_tracking_v2_draft2_exact_solver as exact
import episode_component_tracking_v2_draft2_cardinality_sidecar as sc
import benchmark_episode_component_tracking_v2_draft2_margin1_investigation as audit


def memory():
    return {key: int(value.split()[0]) for line in Path('/proc/self/status').read_text().splitlines()
            for key, value in [line.split(':',1)] if key in ('VmHWM','VmRSS')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--child')
    args=parser.parse_args()
    if args.child:
        before=memory()
        item=audit.child(json.loads(args.child))
        print(json.dumps(dict(before_kib=before,after_count_and_queries_kib=memory(),
                              result=item['result'])))
        return
    if args.output.exists():
        raise ValueError('Output must be NEW')
    cases={}
    for scope in ('group','episode'):
        for method in ('previous','column'):
            case=[scope,1.,method,'frequency',True]
            run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',json.dumps(case)],
                               check=True,capture_output=True,text=True,timeout=90)
            cases[f'{scope}-{method}']=json.loads(run.stdout)
    output=dict(cases=cases,computational_limits=audit.LIMITS,
        measurement='Linux /proc/self/status VmHWM KiB, current address space; includes model loading and sidecar queries',
        source_hashes={str(p.relative_to(audit.ROOT)):sc.sha(p)
                       for p in audit.sources()+[Path(__file__).resolve()]})
    args.output.write_bytes(exact.canonical_bytes(output))


if __name__=='__main__':
    main()
