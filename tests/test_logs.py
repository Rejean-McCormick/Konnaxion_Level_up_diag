from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from levelupdiag_core.artifacts import level_artifacts_dir, safe_slug
from levelupdiag_core.config import AppConfig
from levelupdiag_core.logs import run_directory, update_latest, write_output_log
from levelupdiag_core.manifest import LevelInfo


def make_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        diagnostics_repo_root=str(tmp_path),
        target_repo_root=str(tmp_path / "target"),
        control_dir=".levelupdiag",
        artifacts_dir=".levelupdiag/diagnostics",
    )


def make_level() -> LevelInfo:
    return LevelInfo(id="N04", name="Contracts", file="levels/N04_contracts.pyw")


def test_safe_slug_is_conservative() -> None:
    assert safe_slug("N04 / Contracts") == "n04-contracts"
    assert safe_slug("../../Danger !!") == "danger"
    assert safe_slug("   ") == "artifact"


def test_level_artifacts_dir_stays_under_root(tmp_path: Path) -> None:
    directory = level_artifacts_dir(tmp_path, "N04", "../Contracts")
    assert directory == tmp_path.resolve() / "n04-contracts"
    assert directory.is_dir()


def test_run_directory_separates_two_runs_with_same_timestamp(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    level = make_level()
    when = datetime(2026, 8, 7, 10, 0, 0)

    first = run_directory(config, level, when)
    second = run_directory(config, level, when)

    assert first != second
    assert first.name == "20260807_100000"
    assert second.name == "20260807_100000-02"
    assert first.parent == config.artifacts_root_path / "n04-contracts"
    assert second.parent == first.parent


def test_write_output_log_utf8(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    path = write_output_log(run_dir, "résultat\nligne 2")
    assert path == run_dir.resolve() / "output.log"
    assert path.read_text(encoding="utf-8") == "résultat\nligne 2"


def test_update_latest_copies_result_atomically(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    level = make_level()
    run_dir = run_directory(config, level, datetime(2026, 8, 7, 10, 0, 0))
    result = run_dir / "result.json"
    result.write_text('{"verdict":"PASS"}\n', encoding="utf-8")

    latest = update_latest(config, level, result)

    assert latest == config.control_root_path / "latest" / "n04" / "result.json"
    assert latest.read_text(encoding="utf-8") == result.read_text(encoding="utf-8")
    assert not (latest.parent / ".result.json.tmp").exists()


def test_update_latest_rejects_source_outside_runtime_roots(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    level = make_level()
    outside = tmp_path / "outside-result.json"
    outside.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError):
        update_latest(config, level, outside)


def test_open_path_reveals_parent_without_executing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import levelupdiag_core.artifacts as artifacts

    artifact = tmp_path / "report.py"
    artifact.write_text("raise SystemExit('must not execute')\n", encoding="utf-8")
    launched: list[tuple[list[str], dict[str, object]]] = []

    def fake_popen(args, **kwargs):
        launched.append((list(args), dict(kwargs)))
        return object()

    monkeypatch.setattr(artifacts.subprocess, "Popen", fake_popen)
    if artifacts.os.name != "nt" and artifacts.sys.platform != "darwin":
        monkeypatch.setattr(artifacts, "shutil_which", lambda name: "/usr/bin/xdg-open")

    artifacts.open_path(artifact)

    assert launched
    args, kwargs = launched[0]
    assert kwargs.get("shell") is False
    if artifacts.os.name == "nt":
        assert "explorer.exe" in args[0].lower()
        assert "/select," in args
    else:
        assert str(artifact) not in args
        assert str(tmp_path.resolve()) in args
