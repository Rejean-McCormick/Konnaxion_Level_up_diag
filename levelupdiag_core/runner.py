from __future__ import annotations
import os, shutil, subprocess, sys, time, uuid
from datetime import datetime
from pathlib import Path
from .config import AppConfig
from .manifest import get_campaign,get_level,load_manifest
from .models import CampaignResult,Finding,LevelResult
from .reports import read_level_result,write_json,write_level_result
from .verdicts import aggregate_verdicts,BLOCKED,CONFIG_ERROR,ERROR,INFRA_ERROR,PASS,WARN

_HARD_DEP={BLOCKED,CONFIG_ERROR,ERROR,INFRA_ERROR}

def _now(): return datetime.now().astimezone().isoformat(timespec='seconds')
def _run_id(): return datetime.now().astimezone().strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]

def _tracked_status(target:Path, ignored_roots=()):
    if not (target/'.git').exists() or shutil.which('git') is None: return None
    try:
        cmd=['git','status','--porcelain=v1','--untracked-files=no']
        exclusions=[]
        target_resolved=target.resolve(strict=False)
        for ignored in ignored_roots:
            try:
                rel=Path(ignored).resolve(strict=False).relative_to(target_resolved)
            except ValueError:
                continue
            rel_posix=rel.as_posix().strip('/')
            if rel_posix and rel_posix != '.':
                exclusions.extend([
                    f':(top,exclude){rel_posix}',
                    f':(top,exclude){rel_posix}/**',
                ])
        if exclusions:
            cmd.extend(['--','.',*exclusions])
        cp=subprocess.run(cmd,cwd=str(target),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',timeout=15,shell=False,check=False)
        return cp.stdout if cp.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): return None

def _cleanup_runtime(control:Path,purge_legacy=True):
    control.mkdir(parents=True,exist_ok=True)
    names=['current','latest','konnaxion']
    if purge_legacy: names += ['runs','logs','diagnostics']
    for name in names:
        p=control/name
        if p.exists(): shutil.rmtree(p,ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)

def _blocked(spec,reason):
    now=_now(); return LevelResult(spec.id,spec.name,BLOCKED,[Finding('diagnostics.dependency.blocked',BLOCKED,'Level blocked by an unavailable required dependency.','dependency',evidence=reason)],started_at=now,ended_at=now)

def run_campaign(campaign,levels=None,config:AppConfig|None=None):
    root=(config.diagnostics_root_path if config else Path(__file__).resolve().parents[1])
    if config is None:
        from .config import load_config
        config=load_config(root)
    m=load_manifest(root)
    if levels is None:
        c=get_campaign(campaign,root); levels=list(c['levels']); mode=c.get('execution','sequential')
    else:
        # Compatibility path: a caller may still pass an ordered level list.
        levels=list(levels); mode='sequential'
    expected=[str(x) for x in levels]
    control=config.control_root_path; exec_cfg=config.get('execution',{}) if isinstance(config.get('execution',{}),dict) else {}
    before_tracked=_tracked_status(config.target_root_path,(control,)) if exec_cfg.get('protect_tracked_files',True) else None
    _cleanup_runtime(control,bool(exec_cfg.get('purge_legacy_evidence',True)))
    current=control/'current'; latest=control/'latest'; current.mkdir(parents=True,exist_ok=True); latest.mkdir(parents=True,exist_ok=True)
    run_id=_run_id(); started=_now(); results=[]; by_id={}
    heartbeat=int(exec_cfg.get('command_heartbeat_seconds',15) or 0)
    env_base=dict(os.environ); env_base.update({'LEVELUPDIAG_CAMPAIGN':campaign,'LEVELUPDIAG_EXPECTED_LEVELS':','.join(expected),'LEVELUPDIAG_RUN_ID':run_id,'LEVELUPDIAG_HEARTBEAT_SECONDS':str(heartbeat)})
    print(f'LevelUpDiag Konnaxion — {campaign} [{mode}]',flush=True)
    print('Sequence: '+' -> '.join(expected),flush=True)
    for index,lid in enumerate(expected,1):
        spec=get_level(lid,root)
        bad={dep:by_id[dep].verdict for dep in spec.depends_on if dep in by_id and by_id[dep].verdict in _HARD_DEP}
        output=current/'levels'/spec.id.lower()/'result.json'; output.parent.mkdir(parents=True,exist_ok=True)
        if bad:
            result=_blocked(spec,bad); write_level_result(output,result)
        else:
            print(f'[{index:02d}/{len(expected):02d}] {spec.id} {spec.name} — START',flush=True)
            cmd=[sys.executable,str(root/'levelupdiag.py'),'_worker','--level',spec.id,'--output',str(output),'--target',str(config.target_root_path)]
            started_level=time.monotonic()
            try:
                cp=subprocess.run(cmd,cwd=str(config.target_root_path),env=env_base,stdin=subprocess.DEVNULL,timeout=spec.timeout_seconds,shell=False,check=False)
                if output.is_file(): result=read_level_result(output)
                else:
                    now=_now(); result=LevelResult(spec.id,spec.name,INFRA_ERROR,[Finding('diagnostics.worker.missing-result',INFRA_ERROR,'Level worker produced no result.','diagnostics',evidence={'return_code':cp.returncode})],started_at=now,ended_at=now)
                    write_level_result(output,result)
            except subprocess.TimeoutExpired:
                now=_now(); result=LevelResult(spec.id,spec.name,INFRA_ERROR,[Finding('diagnostics.worker.timeout',INFRA_ERROR,f'Level exceeded its {spec.timeout_seconds}s timeout.','diagnostics')],started_at=now,ended_at=now)
                write_level_result(output,result)
            print(f'[{index:02d}/{len(expected):02d}] {spec.id} {spec.name} — {result.verdict} ({time.monotonic()-started_level:.1f}s)',flush=True)
        by_id[spec.id]=result; results.append(result)
        latest_file=latest/spec.id.lower()/'result.json'; latest_file.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(output,latest_file)
    verdict=aggregate_verdicts([r.verdict for r in results])
    after_tracked=_tracked_status(config.target_root_path,(control,)) if before_tracked is not None else None
    protection=None
    if before_tracked is not None and after_tracked is not None and before_tracked != after_tracked:
        protection={'verdict':'ERROR','message':'Tracked Git state changed during diagnostics.','before':before_tracked,'after':after_tracked}
        verdict=ERROR
    ended=_now(); summary=CampaignResult(campaign,verdict,results,run_id,started,ended,expected)
    payload=summary.to_dict(); payload['target_repo_root']=str(config.target_root_path); payload['retention']='current_only'; payload['sequence']=expected; payload['target_protection']=protection
    write_json(current/'summary.json',payload); (current/'summary.txt').write_text(f'{campaign}: {verdict}\n'+' -> '.join(expected)+'\n'+"\n".join(f'{r.level} {r.verdict} {r.name}' for r in results)+'\n',encoding='utf-8')
    return summary

def run_named_sequence(name,config:AppConfig):
    root=config.diagnostics_root_path; m=load_manifest(root); seq=m.get('sequences',{}).get(name)
    if seq is None: raise ValueError(f'unknown sequence: {name}')
    outcomes=[]
    for campaign in seq.get('campaigns',[]):
        outcomes.append(run_campaign(campaign,config=config))
        if outcomes[-1].verdict not in {PASS,WARN} and not seq.get('continue_on_failure',True): break
    return outcomes
