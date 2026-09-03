from __future__ import annotations
import importlib.util, importlib.machinery, traceback
from pathlib import Path
from .config import load_config
from .manifest import get_level
from .models import Finding,LevelResult
from .reports import write_level_result
from .verdicts import ERROR
from datetime import datetime

def run_worker(root:Path,level_id:str,output:Path,target_override=None):
    spec=get_level(level_id,root); cfg=load_config(root,target_override)
    path=(root/spec.file).resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    mod_name=f'_levelupdiag_{spec.id.lower()}'
    loader=importlib.machinery.SourceFileLoader(mod_name,str(path))
    module_spec=importlib.util.spec_from_loader(mod_name,loader)
    if module_spec is None: raise RuntimeError(f'cannot load {path}')
    module=importlib.util.module_from_spec(module_spec); loader.exec_module(module)
    try:
        result=module.run(cfg)
        if not isinstance(result,LevelResult): raise TypeError(f'{spec.id} run() did not return LevelResult')
    except Exception as exc:
        now=datetime.now().astimezone().isoformat(timespec='seconds')
        result=LevelResult(spec.id,spec.name,ERROR,[Finding('diagnostics.level.exception',ERROR,'Unhandled diagnostic level exception.','diagnostics',evidence=f'{type(exc).__name__}: {exc}',recommendation='Inspect the traceback in console and fix the diagnostic code.')],started_at=now,ended_at=now,metadata={'traceback':traceback.format_exc()[-12000:]})
    write_level_result(output,result); return result
