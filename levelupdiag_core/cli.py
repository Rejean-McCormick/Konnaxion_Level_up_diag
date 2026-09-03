from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .config import ConfigError,load_config
from .manifest import ManifestError,load_manifest,get_campaign
from .runner import run_campaign,run_named_sequence
from .verdicts import exit_code,aggregate_verdicts
from .worker import run_worker

def main(argv=None):
    p=argparse.ArgumentParser(prog='levelupdiag',description='Konnaxion LevelUpDiag upgraded engine')
    p.add_argument('--target',help='Override target repository root')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor'); sub.add_parser('list')
    r=sub.add_parser('run'); r.add_argument('campaign',nargs='?',default='connection-debug')
    rs=sub.add_parser('run-sequence'); rs.add_argument('sequence',nargs='?',default='recommended-debug')
    w=sub.add_parser('_worker'); w.add_argument('--level',required=True); w.add_argument('--output',required=True); w.add_argument('--target',dest='worker_target')
    args=p.parse_args(argv); root=Path(__file__).resolve().parents[1]
    try:
        if args.cmd=='_worker':
            result=run_worker(root,args.level,Path(args.output),args.worker_target); return exit_code(result.verdict)
        cfg=load_config(root,args.target)
        if args.cmd=='doctor':
            m=load_manifest(root); print('LevelUpDiag Konnaxion doctor: PASS'); print(f'tool_root: {root}'); print(f'target_root: {cfg.target_root_path}'); print(f'control_root: {cfg.control_root_path}'); print(f'levels: {len(m["levels"])}'); return 0
        if args.cmd=='list':
            m=load_manifest(root)
            print('Campaigns:')
            for n,c in m['campaigns'].items(): print(f"  {n}: {' -> '.join(c['levels'])}")
            print('Sequences:')
            for n,s in m.get('sequences',{}).items(): print(f"  {n}: {' -> '.join(s['campaigns'])}")
            return 0
        if args.cmd=='run':
            result=run_campaign(args.campaign,config=cfg); print(f'campaign {result.campaign}: {result.verdict}'); return exit_code(result.verdict)
        if args.cmd=='run-sequence':
            outcomes=run_named_sequence(args.sequence,cfg); verdict=aggregate_verdicts([x.verdict for x in outcomes]); print(f'sequence {args.sequence}: {verdict}'); return exit_code(verdict)
    except (ConfigError,ManifestError,ValueError,OSError) as exc:
        print(f'LevelUpDiag error: {exc}',file=sys.stderr); return 30
    return 64
