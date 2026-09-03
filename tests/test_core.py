import tempfile,unittest
from pathlib import Path
from levelupdiag_core.commands import run_cmd
from levelupdiag_core.verdicts import PASS,INFRA_ERROR
class CoreTests(unittest.TestCase):
    def test_shell_false_command(self):
        import sys
        with tempfile.TemporaryDirectory() as d:
            r=run_cmd([sys.executable,'-c','print("ok")'],cwd=Path(d),timeout=10,name='test',tail_chars=1000)
            self.assertEqual(r.verdict,PASS); self.assertIn('ok',r.output_tail)
    def test_timeout_is_infra_error(self):
        import sys
        with tempfile.TemporaryDirectory() as d:
            r=run_cmd([sys.executable,'-c','import time; time.sleep(2)'],cwd=Path(d),timeout=1,name='timeout',tail_chars=1000)
            self.assertEqual(r.verdict,INFRA_ERROR); self.assertTrue(r.timed_out)
