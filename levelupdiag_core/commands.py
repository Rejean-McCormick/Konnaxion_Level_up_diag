from __future__ import annotations
import os, shutil, subprocess, threading, time
from collections import deque
from pathlib import Path
from .models import StepResult
from .verdicts import PASS, FAIL, INFRA_ERROR

def find_executable(name): return shutil.which(name)

def _redact(text):
    import re
    if not text: return ''
    text=re.sub(r'(?i)(password|secret|token|private[_-]?key|api[_-]?key|authorization|cookie)(\s*[:=]\s*)([^\s"\';]+)',r'\1\2[REDACTED]',text)
    text=re.sub(r'(?i)((?:postgres|postgresql|redis)://[^:/\s]+:)[^@\s]+@',r'\1[REDACTED]@',text)
    return text

def run_cmd(command,*,cwd:Path,timeout:int,name:str='',env=None,tail_chars:int=12000)->StepResult:
    args=[str(x) for x in command]
    if not args: raise ValueError('empty command')
    started=time.monotonic(); lines=deque(); total=[0]; lock=threading.Lock()
    try:
        proc=subprocess.Popen(args,cwd=str(cwd),env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,encoding='utf-8',errors='replace',shell=False,bufsize=1)
    except (OSError,PermissionError) as exc:
        return StepResult(name or args[0],tuple(args),str(cwd),INFRA_ERROR,None,round(time.monotonic()-started,3),'',f'{type(exc).__name__}: {exc}',False)
    def reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            with lock:
                lines.append(line); total[0]+=len(line)
                while lines and total[0]>max(tail_chars*2,24000): total[0]-=len(lines.popleft())
    t=threading.Thread(target=reader,daemon=True); t.start()
    heartbeat=int(os.environ.get('LEVELUPDIAG_HEARTBEAT_SECONDS','15') or '15'); next_hb=time.monotonic()+max(heartbeat,5)
    timed_out=False
    while proc.poll() is None:
        elapsed=time.monotonic()-started
        if elapsed>=timeout:
            timed_out=True
            try: proc.kill()
            except OSError: pass
            break
        if heartbeat>0 and time.monotonic()>=next_hb:
            print(f"    … {name or args[0]} still running ({int(elapsed)}s)",flush=True)
            next_hb=time.monotonic()+heartbeat
        time.sleep(0.1)
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try: proc.kill()
        except OSError: pass
    t.join(timeout=2)
    if proc.stdout is not None:
        try: proc.stdout.close()
        except OSError: pass
    with lock: output=''.join(lines)
    output=_redact(output)[-tail_chars:]
    duration=round(time.monotonic()-started,3)
    if timed_out:
        return StepResult(name or args[0],tuple(args),str(cwd),INFRA_ERROR,None,duration,output,f'timeout after {timeout}s',True)
    code=proc.returncode
    return StepResult(name or args[0],tuple(args),str(cwd),PASS if code==0 else FAIL,code,duration,output,'',False)
