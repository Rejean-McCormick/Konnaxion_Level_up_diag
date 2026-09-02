from pathlib import Path
from konnaxion_diag.source_audit import audit, backend_prefixes

def test_register_helpers_and_contract_findings(tmp_path: Path):
    fe=tmp_path/'frontend'; be=tmp_path/'backend'; fe.mkdir(); be.mkdir()
    (be/'urls.py').write_text("register_required(router, 'users', V)\nregister_optional(router, 'admin/stats', V)\n")
    (fe/'x.ts').write_text("fetch('/api/home/x', {method:'POST', credentials:'include'}); const x='/api/api/admin/stats';")
    r=audit(fe,be)
    assert '/api/users' in r['backend_prefixes']
    assert r['double_api']
    assert r['forbidden']
    assert r['csrf_risk_files']
