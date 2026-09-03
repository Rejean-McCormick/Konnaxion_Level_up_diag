import json,os,tempfile,unittest
from pathlib import Path
from levelupdiag_core.config import AppConfig
from konnaxion_diag.common import start_session,active_session
class SessionTests(unittest.TestCase):
    def test_expected_levels_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=root/'target'; target.mkdir(); cfg=AppConfig({'schema':'levelupdiag.config.v2','target_repo_root':str(target),'control_dir':'.levelupdiag'},root)
            old=dict(os.environ)
            try:
                os.environ['LEVELUPDIAG_CAMPAIGN']='connection-debug'; os.environ['LEVELUPDIAG_EXPECTED_LEVELS']='N00,N01,N02,N11'; os.environ['LEVELUPDIAG_RUN_ID']='x'
                start_session(cfg); s=active_session(cfg); self.assertEqual(s['campaign'],'connection-debug'); self.assertEqual(s['expected_levels'],['N00','N01','N02','N11'])
            finally:
                os.environ.clear(); os.environ.update(old)
