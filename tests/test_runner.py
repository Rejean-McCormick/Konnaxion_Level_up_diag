from __future__ import annotations

import json
from pathlib import Path

import pytest

from levelupdiag_core.config import AppConfig
from levelupdiag_core.manifest import LevelInfo
from levelupdiag_core.runner import run_campaign, run_level
from levelupdiag_core import runner
from levelupdiag_core.verdicts import (
    BLOCKED,
    CONFIG_ERROR,
    ERROR,
    FAIL,
    INFRA_ERROR,
    PARTIAL,
    PASS,
    SKIP,
    WARN,
)


def config_for(tmp_path: Path) -> AppConfig:
    target = tmp_path / "target"
    target.mkdir(exist_ok=True)
    return AppConfig(
        diagnostics_repo_root=str(tmp_path),
        target_repo_root=str(target),
        control_dir=".levelupdiag",
        artifacts_dir=".levelupdiag/diagnostics",
    )


def make_level(
    level_id: str,
    *,
    name: str | None = None,
    required: bool = True,
    enabled: bool = True,
    depends_on: tuple[str, ...] = (),
) -> LevelInfo:
    return LevelInfo(
        id=level_id,
        name=name or level_id,
        file=f"levels/{level_id}.pyw",
        required=required,
        enabled=enabled,
        depends_on=depends_on,
    )


def write_fake_level(
    root: Path,
    level: LevelInfo,
    *,
    verdict: str = PASS,
    output: str = "",
    raises: str | None = None,
    marker: Path | None = None,
) -> Path:
    path = root / level.file
    path.parent.mkdir(parents=True, exist_ok=True)
    body: list[str] = [
        "from levelupdiag_core.models import LevelResult",
        f"LEVEL_ID = {level.id!r}",
        f"LEVEL_NAME = {level.name!r}",
        "def run(config=None):",
    ]
    if marker is not None:
        body.append(f"    open({str(marker)!r}, 'w', encoding='utf-8').write('executed')")
    if raises is not None:
        body.append(f"    raise RuntimeError({raises!r})")
    else:
        body.append(
            f"    return LevelResult(level=LEVEL_ID, name=LEVEL_NAME, verdict={verdict!r}, output_tail={output!r})"
        )
    body.extend(["def main():", "    return 0", ""])
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def latest_result(config: AppConfig, level_id: str) -> dict[str, object]:
    path = config.control_root_path / "latest" / level_id.lower() / "result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_run_level_loads_pyw_in_process_and_persists_result(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    subject = make_level("N01", name="Environment")
    write_fake_level(tmp_path, subject, verdict=PASS, output="hello from level")

    result = run_level(subject, config)

    assert result.verdict == PASS
    assert result.output_tail == "hello from level"
    assert latest_result(config, "N01")["verdict"] == PASS
    run_dirs = list((config.artifacts_root_path / "n01-environment").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "result.json").is_file()
    assert (run_dirs[0] / "output.log").read_text(encoding="utf-8") == "hello from level"


def test_run_level_missing_source_is_config_error_and_persisted(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    subject = make_level("N01")

    result = run_level(subject, config)

    assert result.verdict == CONFIG_ERROR
    assert result.findings[0].id == "runner.level-file-missing"
    assert latest_result(config, "N01")["verdict"] == CONFIG_ERROR


def test_run_level_unhandled_exception_becomes_error(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    subject = make_level("N01")
    write_fake_level(tmp_path, subject, raises="boom")

    result = run_level(subject, config)

    assert result.verdict == ERROR
    assert result.findings[0].id == "runner.level-exception"
    assert "RuntimeError: boom" in result.findings[0].message


def test_campaign_blocks_dependent_without_executing_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = config_for(tmp_path)
    first = make_level("N01")
    second = make_level("N02", depends_on=("N01",))
    write_fake_level(tmp_path, first, verdict=FAIL, output="first failed")
    marker = tmp_path / "n02-executed.txt"
    write_fake_level(tmp_path, second, verdict=PASS, marker=marker)
    monkeypatch.setattr(runner, "list_levels", lambda root=None: [first, second])

    campaign = run_campaign("dependency-check", ["N02"], config)

    assert [item.verdict for item in campaign.levels] == [FAIL, BLOCKED]
    assert campaign.levels[1].findings[0].id == "runner.dependencies-blocked"
    assert not marker.exists()
    assert campaign.verdict == BLOCKED


def test_optional_fail_does_not_degrade_required_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = config_for(tmp_path)
    required = make_level("N01", required=True)
    optional = make_level("N08", required=False, depends_on=("N01",))
    write_fake_level(tmp_path, required, verdict=PASS)
    write_fake_level(tmp_path, optional, verdict=FAIL)
    monkeypatch.setattr(runner, "list_levels", lambda root=None: [required, optional])

    campaign = run_campaign("optional-fail", ["N08"], config)

    assert [item.verdict for item in campaign.levels] == [PASS, FAIL]
    assert campaign.verdict == PASS
    assert campaign.counts[PASS] == 1
    assert campaign.counts[FAIL] == 1


def test_required_warn_makes_campaign_warn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = config_for(tmp_path)
    subject = make_level("N01", required=True)
    write_fake_level(tmp_path, subject, verdict=WARN)
    monkeypatch.setattr(runner, "list_levels", lambda root=None: [subject])

    campaign = run_campaign("warning", ["N01"], config)

    assert campaign.verdict == WARN


@pytest.mark.parametrize(
    ("level_verdict", "campaign_verdict"),
    [
        (PASS, PASS),
        (WARN, WARN),
        (FAIL, FAIL),
        (SKIP, BLOCKED),
        (PARTIAL, BLOCKED),
        (BLOCKED, BLOCKED),
        (INFRA_ERROR, BLOCKED),
        (CONFIG_ERROR, CONFIG_ERROR),
        (ERROR, ERROR),
    ],
)
def test_required_verdict_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    level_verdict: str,
    campaign_verdict: str,
) -> None:
    config = config_for(tmp_path)
    subject = make_level("N01", required=True)
    write_fake_level(tmp_path, subject, verdict=level_verdict)
    monkeypatch.setattr(runner, "list_levels", lambda root=None: [subject])

    campaign = run_campaign(f"required-{level_verdict.lower()}", ["N01"], config)

    assert campaign.verdict == campaign_verdict


def test_campaign_with_no_required_level_is_config_error_and_writes_summaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = config_for(tmp_path)
    optional = make_level("N00", name="Control Panel", required=False)
    write_fake_level(tmp_path, optional, verdict=PASS)
    monkeypatch.setattr(runner, "list_levels", lambda root=None: [optional])

    campaign = run_campaign("delivery preview", ["N00"], config)

    assert campaign.verdict == CONFIG_ERROR
    run_id = campaign.metadata["run_id"]
    assert isinstance(run_id, str)
    assert run_id.endswith("-delivery-preview")
    summary_dir = config.control_root_path / "runs" / run_id
    assert (summary_dir / "summary.json").is_file()
    assert (summary_dir / "summary.txt").is_file()
    payload = json.loads((summary_dir / "summary.json").read_text(encoding="utf-8"))
    assert payload["metadata"]["run_id"] == run_id
    assert payload["verdict"] == CONFIG_ERROR
