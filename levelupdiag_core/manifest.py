from __future__ import annotations
import json,re
from dataclasses import dataclass
from pathlib import Path

CANONICAL_LEVEL_IDS=tuple(f'N{i:02d}' for i in range(100))
class ManifestError(RuntimeError): pass
@dataclass(frozen=True,slots=True)
class LevelSpec:
    id:str; name:str; file:str; required:bool; depends_on:tuple[str,...]; timeout_seconds:int; order:int; purpose:str=''; parallel_safe:bool=False

def normalize_level_id(value):
    s=str(value).strip().upper(); m=re.fullmatch(r'(?:LUD[-_ ]?)?(?:N)?(\d{1,2})',s)
    if not m: raise ValueError(f'invalid level id: {value}')
    return f'N{int(m.group(1)):02d}'

def load_manifest(root:Path|None=None):
    root=(root or Path(__file__).resolve().parents[1]).resolve(); p=root/'levelupdiag_manifest.json'
    with p.open('r',encoding='utf-8') as f: data=json.load(f)
    errors=validate_manifest(data)
    if errors: raise ManifestError('; '.join(errors))
    return data

def validate_manifest(data):
    errors=[]
    if data.get('schema')!='levelupdiag.manifest.v2': errors.append('unsupported manifest schema')
    levels=data.get('levels',[])
    ids=[x.get('id') for x in levels]
    seen=set()
    for lid in ids:
        if lid in seen: errors.append(f'duplicate level id: {lid}')
        seen.add(lid)
    known=set(ids)
    for x in levels:
        for dep in x.get('depends_on',[]):
            if dep not in known: errors.append(f"{x.get('id')} depends on unknown level {dep}")
    for name,c in data.get('campaigns',{}).items():
        seq=c.get('levels',[])
        for lid in seq:
            if lid not in known: errors.append(f'campaign {name} contains unknown level {lid}')
        if c.get('execution','sequential') not in {'sequential','dependency'}: errors.append(f'campaign {name} has invalid execution mode')
    return errors

def list_levels(root:Path|None=None):
    return [LevelSpec(x['id'],x['name'],x['file'],bool(x.get('required',False)),tuple(x.get('depends_on',[])),int(x.get('timeout_seconds',120)),int(x.get('order',0)),x.get('purpose',''),bool(x.get('parallel_safe',False))) for x in load_manifest(root)['levels']]

def get_level(level_id,root:Path|None=None):
    lid=normalize_level_id(level_id)
    for x in list_levels(root):
        if x.id==lid: return x
    raise ManifestError(f'unknown level: {lid}')

def get_campaign(name,root:Path|None=None):
    m=load_manifest(root); c=m.get('campaigns',{}).get(name)
    if c is None: raise ManifestError(f'unknown campaign: {name}')
    return dict(c)
