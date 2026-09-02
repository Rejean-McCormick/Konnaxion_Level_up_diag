from __future__ import annotations

import json
from pathlib import Path

import pytest

from levelupdiag_core.config import (
    APP_NAME_ENV,
    CONFIG_SCHEMA,
    TARGET_ROOT_ENV,
    AppConfig,
    load_config,
    save_config,
)


def _write_example(root: Path, **changes: object) -> Path:
    data = {
        "schema": CONFIG_SCHEMA,
        "app_name": "kOA-Linux",
        "target_repo_root": "../koa-linux",
        "control_dir": ".levelupdiag",
        "artifacts_dir": ".levelupdiag/diagnostics",
        "toolchain": {"required": ["python"], "optional": ["git", "cargo"]},
        "commands": {
            "docs": "python docs/tools/validate_docs.py",
            "contracts": "python ci/scripts/run-contracts.py",
            "components": "python ci/scripts/run-components.py",
            "integrations": "",
            "profiles": "",
            "security": "python ci/scripts/run-security.py",
            "offline": "python ci/scripts/run-offline.py",
            "system": "python ci/scripts/run-system-tests.py",
        },
        "env": {},
    }
    data.update(changes)
    path = root / "levelupdiag.config.example.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_example_without_local_config(tmp_path: Path) -> None:
    _write_example(tmp_path)
    config = load_config(root=tmp_path)
    assert config.app_name == "kOA-Linux"
    assert config.toolchain == {"required": ["python"], "optional": ["git", "cargo"]}
    assert config.command("integrations") == ""
    assert config.control_root_path == (tmp_path / ".levelupdiag").resolve()
    assert config.artifacts_root_path == (tmp_path / ".levelupdiag/diagnostics").resolve()


def test_local_config_deep_merges_commands_and_env(tmp_path: Path) -> None:
    _write_example(tmp_path)
    local = tmp_path / "levelupdiag.config.local.json"
    local.write_text(
        json.dumps(
            {
                "target_repo_root": "D:/work/koa-linux",
                "commands": {"integrations": "python tests/integration_runner.py"},
                "env": {"KOA_MODE": "test"},
            }
        ),
        encoding="utf-8",
    )
    config = load_config(root=tmp_path)
    assert config.target_repo_root == "D:/work/koa-linux"
    assert config.command("docs") == "python docs/tools/validate_docs.py"
    assert config.command("integrations") == "python tests/integration_runner.py"
    assert config.env()["KOA_MODE"] == "test"


def test_environment_overrides_target_and_app_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_example(tmp_path)
    monkeypatch.setenv(TARGET_ROOT_ENV, "./alternate-target")
    monkeypatch.setenv(APP_NAME_ENV, "Koali-Test")
    config = load_config(root=tmp_path)
    assert config.target_repo_root == "./alternate-target"
    assert config.app_name == "Koali-Test"


def test_save_config_writes_local_file_only_when_called(tmp_path: Path) -> None:
    _write_example(tmp_path)
    config = load_config(root=tmp_path)
    assert not (tmp_path / "levelupdiag.config.local.json").exists()
    path = save_config(config)
    assert path == tmp_path / "levelupdiag.config.local.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema"] == CONFIG_SCHEMA
    assert "diagnostics_repo_root" not in saved
    assert "config_path" not in saved


def test_invalid_unknown_command_key_is_rejected(tmp_path: Path) -> None:
    _write_example(tmp_path, commands={"surprise": "echo nope"})
    with pytest.raises(ValueError, match="Unsupported command keys"):
        load_config(root=tmp_path)
