from __future__ import annotations
import re
from pathlib import Path

FORBIDDEN = ("/api/home/", "/api/konsultations/", "/api/reseau/", "/api/profil/")
MUTATION = re.compile(r"\b(method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]|\.(?:post|put|patch|delete)\s*\()", re.I)
API_LITERAL = re.compile(r"['\"](/api/[A-Za-z0-9_./{}?&=:-]+)['\"]")
ROUTE_REG = re.compile(r"register_(?:required|optional)\(\s*router\s*,\s*['\"]([^'\"]+)['\"]")


def _files(root: Path):
    for ext in ('*.ts','*.tsx','*.js','*.jsx'):
        yield from root.rglob(ext)

def backend_prefixes(backend: Path) -> set[str]:
    prefixes=set()
    for p in backend.rglob('urls.py'):
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except OSError: continue
        prefixes.update('/api/'+x.strip('/') for x in ROUTE_REG.findall(text))
    return prefixes

def audit(frontend: Path, backend: Path) -> dict:
    double=[]; forbidden=[]; mutations=[]; endpoints=set()
    for p in _files(frontend):
        try: text=p.read_text(encoding='utf-8', errors='ignore')
        except OSError: continue
        rel=str(p.relative_to(frontend))
        for ep in API_LITERAL.findall(text):
            endpoints.add(ep.split('?')[0])
            if '/api/api/' in ep: double.append((rel,ep))
            if ep.startswith(FORBIDDEN): forbidden.append((rel,ep))
        if MUTATION.search(text) and ('credentials' in text or 'apiFetch' in text or 'fetch(' in text):
            if 'X-CSRFToken' not in text and 'X-XSRF-TOKEN' not in text and 'xsrfHeaderName' not in text:
                mutations.append(rel)
    prefixes=backend_prefixes(backend)
    unmapped=[]
    for ep in sorted(endpoints):
        if ep.startswith(FORBIDDEN): continue
        if prefixes and not any(ep==p or ep.startswith(p.rstrip('/')+'/') for p in prefixes):
            unmapped.append(ep)
    return {'double_api':double,'forbidden':forbidden,'csrf_risk_files':sorted(set(mutations)),'unmapped':unmapped,'backend_prefixes':sorted(prefixes),'frontend_endpoints':sorted(endpoints)}
