from __future__ import annotations
import os
import re
from pathlib import Path

FORBIDDEN = ("/api/home/", "/api/konsultations/", "/api/reseau/", "/api/profil/")
MUTATION = re.compile(r"\b(method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]|\.(?:post|put|patch|delete)\s*\()", re.I)
API_LITERAL = re.compile(r"['\"](/api/[A-Za-z0-9_./{}?&=:-]+)['\"]")
ROUTE_REG = re.compile(r"register_(?:required|optional)\(\s*router\s*,\s*['\"]([^'\"]+)['\"]")


_EXCLUDED_DIRS={'.git','node_modules','.next','dist','build','coverage','artifacts','.venv','venv','__pycache__','.cache'}

def _walk_files(root: Path, names: set[str] | None = None, suffixes: tuple[str, ...] = ()):
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDED_DIRS]
        base=Path(dirpath)
        for name in filenames:
            if names is not None and name not in names: continue
            if suffixes and not name.endswith(suffixes): continue
            yield base/name

def _files(root: Path):
    yield from _walk_files(root, suffixes=('.ts','.tsx','.js','.jsx'))

def backend_prefixes(backend: Path) -> set[str]:
    prefixes=set()
    for p in _walk_files(backend, names={'urls.py'}):
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except OSError: continue
        prefixes.update('/api/'+x.strip('/') for x in ROUTE_REG.findall(text))
    return prefixes


def _strip_js_comments(text: str) -> str:
    """Remove // and /* */ comments while preserving string/template contents."""
    out: list[str] = []
    i = 0
    n = len(text)
    quote: str | None = None
    escaped = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if quote is not None:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"', '`'}:
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == '/' and nxt == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        if ch == '/' and nxt == '*':
            i += 2
            while i + 1 < n and not (text[i] == '*' and text[i + 1] == '/'):
                if text[i] == '\n':
                    out.append('\n')
                i += 1
            i = min(n, i + 2)
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _uses_csrf_safe_client(code: str) -> bool:
    if any(token in code for token in (
        'X-CSRFToken', 'X-XSRF-TOKEN', 'xsrfHeaderName',
        'apiFetch(', 'apiPost(', 'apiPut(', 'apiPatch(', 'apiDelete(',
    )):
        return True
    if "services/_request" in code or "@/services/_request" in code:
        return True
    return False

def audit(frontend: Path, backend: Path) -> dict:
    double=[]; forbidden=[]; mutations=[]; endpoints=set()
    for p in _files(frontend):
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except OSError: continue
        rel=str(p.relative_to(frontend))
        code=_strip_js_comments(text)
        for ep in API_LITERAL.findall(code):
            endpoints.add(ep.split('?')[0])
            if '/api/api/' in ep: double.append((rel,ep))
            if ep.startswith(FORBIDDEN): forbidden.append((rel,ep))
        if MUTATION.search(code) and ('credentials' in code or 'apiFetch' in code or 'fetch(' in code or '.post(' in code or '.put(' in code or '.patch(' in code or '.delete(' in code):
            if not _uses_csrf_safe_client(code):
                mutations.append(rel)
    prefixes=backend_prefixes(backend)
    unmapped=[]
    for ep in sorted(endpoints):
        if ep.startswith(FORBIDDEN): continue
        if prefixes and not any(ep==p or ep.startswith(p.rstrip('/')+'/') for p in prefixes):
            unmapped.append(ep)
    return {'double_api':double,'forbidden':forbidden,'csrf_risk_files':sorted(set(mutations)),'unmapped':unmapped,'backend_prefixes':sorted(prefixes),'frontend_endpoints':sorted(endpoints)}
