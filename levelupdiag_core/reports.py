from __future__ import annotations
import json, os
from pathlib import Path
from .models import Artifact,Finding,LevelResult

def write_json(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,path)

def write_level_result(path:Path,result:LevelResult): write_json(path,result.to_dict())

def read_level_result(path:Path)->LevelResult:
    d=json.loads(path.read_text(encoding='utf-8'))
    return LevelResult(
        level=d.get('level') or d.get('level_id'), name=d.get('name') or d.get('level_name',''), verdict=d.get('verdict','ERROR'),
        findings=[Finding(id=f['id'],severity=f.get('severity') or f.get('verdict','ERROR'),message=f.get('message',''),category=f.get('category',''),path=f.get('path'),evidence=f.get('evidence'),recommendation=f.get('recommendation'),data=f.get('data')) for f in d.get('findings',[])],
        artifacts=[Artifact(kind=a.get('kind','artifact'),path=a.get('path',''),description=a.get('description'),data=a.get('data')) for a in d.get('artifacts',[])],
        started_at=d.get('started_at',''),ended_at=d.get('ended_at',''),duration_seconds=float(d.get('duration_seconds',0) or 0),cwd=d.get('cwd',''),output_tail=d.get('output_tail',''),metadata=dict(d.get('metadata',{}))
    )
