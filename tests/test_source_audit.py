import tempfile, unittest
from pathlib import Path
from konnaxion_diag.source_audit import audit

class SourceAuditTests(unittest.TestCase):
    def test_register_helpers_and_contract_findings(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path=Path(d); fe=tmp_path/"frontend"; be=tmp_path/"backend"; fe.mkdir(); be.mkdir()
            (be/"urls.py").write_text("register_required(router, 'users', V)\nregister_optional(router, 'admin/stats', V)\n",encoding="utf-8")
            (fe/"x.ts").write_text("fetch('/api/home/x', {method:'POST', credentials:'include'}); const x='/api/api/admin/stats';",encoding="utf-8")
            r=audit(fe,be)
            self.assertIn('/api/users',r['backend_prefixes']); self.assertTrue(r['double_api']); self.assertTrue(r['forbidden']); self.assertTrue(r['csrf_risk_files'])
