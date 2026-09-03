import json
import tempfile
import unittest
from pathlib import Path

from levelupdiag_core.config import AppConfig


class AutoTargetTests(unittest.TestCase):
    def _data(self):
        return {
            "schema":"levelupdiag.config.v2",
            "target_repo_root":"auto",
            "control_dir":".levelupdiag",
            "konnaxion":{"frontend_dir":"frontend","backend_dir":"backend"},
        }

    def _markers(self, target: Path):
        (target/"frontend").mkdir(parents=True)
        (target/"backend").mkdir(parents=True)
        (target/"frontend"/"package.json").write_text("{}", encoding="utf-8")
        (target/"backend"/"manage.py").write_text("# manage", encoding="utf-8")

    def test_copy_inside_repo(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"Konnaxion"; tool=target/"LevelUpDiag"; tool.mkdir(parents=True)
            self._markers(target)
            cfg=AppConfig(self._data(),tool)
            self.assertEqual(cfg.target_root_path,target.resolve())

    def test_historical_sibling_layout(self):
        with tempfile.TemporaryDirectory() as td:
            workspace=Path(td); tool=workspace/"LevelUpDiag"; tool.mkdir()
            target=workspace/"Konnaxion"; self._markers(target)
            cfg=AppConfig(self._data(),tool)
            self.assertEqual(cfg.target_root_path,target.resolve())
