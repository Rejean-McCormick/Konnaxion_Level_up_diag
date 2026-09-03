import unittest
from pathlib import Path
from levelupdiag_core.manifest import load_manifest,validate_manifest,get_level
ROOT=Path(__file__).resolve().parents[1]
class ManifestTests(unittest.TestCase):
    def test_taxonomy(self):
        m=load_manifest(ROOT); self.assertEqual(validate_manifest(m),[]); self.assertEqual([x['id'] for x in m['levels']],[f'N{i:02d}' for i in range(12)])
    def test_dependencies(self):
        m=load_manifest(ROOT); self.assertEqual(m['levels'][0]['depends_on'],[]); self.assertTrue(all(x['depends_on']==['N00'] for x in m['levels'][1:]))
    def test_connection_sequence(self):
        m=load_manifest(ROOT); self.assertEqual(m['campaigns']['connection-debug']['levels'],['N00','N01','N02','N03','N04','N05','N06','N11']); self.assertEqual(m['campaigns']['connection-debug']['execution'],'sequential')
    def test_recommended_sequence(self):
        m=load_manifest(ROOT); self.assertEqual(m['sequences']['recommended-debug']['campaigns'],['source-audit','auth-debug','connection-debug','full-local'])
