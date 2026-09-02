"""Canonical sequential orchestration for LevelUpDiag-Koali levels."""

from __future__ import annotations

from datetime import datetime
import importlib.machinery
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Callable

from .artifacts import safe_slug
from .config import AppConfig
from .logs import run_directory, update_latest, write_output_log
from .manifest import LevelInfo, list_levels
from .models import CampaignResult, Finding, LevelResult
from .planner import build_plan, dependency_blockers
from .reports import write_campaign_summary, write_level_result
from .verdicts import (
    BLOCKED,
    CONFIG_ERROR,
    ERROR,
    FAIL,
    INFRA_ERROR,
    PARTIAL,
    PASS,
    SKIP,
    VERDICTS,
    WARN,
    aggregate_verdicts,
)


def _now() -> datetime:
    return datetime.now().astimezone()


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _duration(started: datetime, ended: datetime) -> float:
    return round(max(0.0, (ended - started).total_seconds()), 6)


def _finding(
    finding_id: str,
    severity: str,
    message: str,
    *,
    path: str | None = None,
    evidence: str | None = None,
    recommendation: str | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        severity=severity,
        message=message,
        category="runner",
        path=path,
        evidence=evidence,
        recommendation=recommendation,
    )


def _synthetic_result(
    level: LevelInfo,
    verdict: str,
    finding: Finding,
    *,
    started: datetime,
    ended: datetime | None = None,
) -> LevelResult:
    finished = ended or _now()
    return LevelResult(
        level=level.id,
        name=level.name,
        verdict=verdict,
        findings=[finding],
        started_at=_iso(started),
        ended_at=_iso(finished),
        duration_seconds=_duration(started, finished),
    )


def _load_level_module(level: LevelInfo, source: Path) -> ModuleType:
    # SourceFileLoader is used deliberately because a .pyw suffix is not a
    # normal importlib source suffix on every platform.
    module_name = f"_levelupdiag_{level.id.lower()}_run"
    loader = importlib.machinery.SourceFileLoader(module_name, str(source))
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None:
        raise ImportError(f"cannot create import spec for {source}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _validate_level_module(level: LevelInfo, module: ModuleType) -> Callable[[AppConfig | None], LevelResult]:
    exported_id = getattr(module, "LEVEL_ID", None)
    exported_name = getattr(module, "LEVEL_NAME", None)
    run_function = getattr(module, "run", None)
    if exported_id != level.id:
        raise ValueError(
            f"{level.file} exports LEVEL_ID={exported_id!r}; expected {level.id!r}"
        )
    if exported_name != level.name:
        raise ValueError(
            f"{level.file} exports LEVEL_NAME={exported_name!r}; expected {level.name!r}"
        )
    if not callable(run_function):
        raise ValueError(f"{level.file} must export callable run(config)")
    return run_function


def _normalize_returned_result(level: LevelInfo, result: object) -> LevelResult:
    if not isinstance(result, LevelResult):
        raise TypeError(f"{level.file} run(config) must return LevelResult")
    if result.level != level.id:
        raise ValueError(
            f"{level.file} returned level={result.level!r}; expected {level.id!r}"
        )
    if result.name != level.name:
        raise ValueError(
            f"{level.file} returned name={result.name!r}; expected {level.name!r}"
        )
    return result


def _persist_level_result(
    level: LevelInfo,
    config: AppConfig,
    result: LevelResult,
    run_dir: Path,
) -> None:
    result_path = write_level_result(result, run_dir / "result.json")
    write_output_log(run_dir, result.output_tail)
    update_latest(config, level, result_path)


def run_level(
    level: LevelInfo,
    config: AppConfig,
    *,
    wait: bool = True,
) -> LevelResult:
    """Run one level in-process and persist its canonical result.

    ``wait`` is retained as a stable API compatibility flag.  Canonical runner
    execution is intentionally synchronous and deterministic.
    """

    del wait
    started = _now()
    run_dir = run_directory(config, level, started)
    source = level.file_path(config.diagnostics_root_path).resolve()

    if not source.is_file():
        result = _synthetic_result(
            level,
            CONFIG_ERROR,
            _finding(
                "runner.level-file-missing",
                CONFIG_ERROR,
                f"Level source file is missing: {source}",
                path=str(source),
                recommendation="Restore the level file declared by levelupdiag_manifest.json.",
            ),
            started=started,
        )
        _persist_level_result(level, config, result, run_dir)
        return result

    try:
        module = _load_level_module(level, source)
        run_function = _validate_level_module(level, module)
        result = _normalize_returned_result(level, run_function(config))
    except Exception as exc:  # Boundary: a broken level must become a result.
        ended = _now()
        result = _synthetic_result(
            level,
            ERROR,
            _finding(
                "runner.level-exception",
                ERROR,
                f"Unhandled exception while running {level.id}: {type(exc).__name__}: {exc}",
                path=str(source),
                evidence=f"{type(exc).__name__}: {exc}",
                recommendation="Fix the level implementation; do not convert the exception to PASS.",
            ),
            started=started,
            ended=ended,
        )
    else:
        ended = _now()
        if not result.started_at:
            result.started_at = _iso(started)
        if not result.ended_at:
            result.ended_at = _iso(ended)
        if result.duration_seconds == 0.0:
            result.duration_seconds = _duration(started, ended)

    _persist_level_result(level, config, result, run_dir)
    return result


def _blocked_dependency_result(
    level: LevelInfo,
    blockers: list[str],
) -> LevelResult:
    started = _now()
    ended = _now()
    joined = ", ".join(blockers)
    return _synthetic_result(
        level,
        BLOCKED,
        _finding(
            "runner.dependencies-blocked",
            BLOCKED,
            f"Level {level.id} was not executed because dependency results are not exploitable: {joined}",
            evidence=joined,
            recommendation="Resolve the blocking dependency results and rerun the campaign.",
        ),
        started=started,
        ended=ended,
    )


def _persist_without_execution(
    level: LevelInfo,
    config: AppConfig,
    result: LevelResult,
) -> None:
    started = _now()
    run_dir = run_directory(config, level, started)
    _persist_level_result(level, config, result, run_dir)


def _campaign_verdict(plan: list[LevelInfo], completed: dict[str, LevelResult]) -> str:
    required = [level for level in plan if level.required]
    if not required:
        return CONFIG_ERROR

    mapped: list[str] = []
    for level in required:
        result = completed.get(level.id)
        if result is None:
            mapped.append(BLOCKED)
            continue
        verdict = result.verdict
        if verdict in {SKIP, PARTIAL, BLOCKED, INFRA_ERROR}:
            mapped.append(BLOCKED)
        else:
            mapped.append(verdict)
    return aggregate_verdicts(mapped)


def _counts(results: list[LevelResult]) -> dict[str, int]:
    counts = {verdict: 0 for verdict in VERDICTS}
    for result in results:
        counts[result.verdict] += 1
    return counts


def _campaign_run_id(name: str, started: datetime) -> str:
    return f"{started.strftime('%Y%m%d_%H%M%S')}-{safe_slug(name)}"


def _run_campaign(
    name: str,
    level_ids: list[str] | None,
    config: AppConfig,
) -> CampaignResult:
    started = _now()
    levels = list_levels(config.diagnostics_root_path)
    plan = build_plan(levels, selected=level_ids)
    completed: dict[str, LevelResult] = {}
    ordered_results: list[LevelResult] = []

    for level in plan:
        blockers = dependency_blockers(level, completed)
        if blockers:
            result = _blocked_dependency_result(level, blockers)
            _persist_without_execution(level, config, result)
        else:
            result = run_level(level, config)
        completed[level.id] = result
        ordered_results.append(result)

    ended = _now()
    run_id = _campaign_run_id(name, started)
    campaign = CampaignResult(
        campaign=name,
        target=str(config.target_root_path),
        verdict=_campaign_verdict(plan, completed),
        levels=ordered_results,
        started_at=_iso(started),
        ended_at=_iso(ended),
        counts=_counts(ordered_results),
        metadata={
            "run_id": run_id,
            "selected_levels": [level.id for level in plan],
        },
    )
    summary_dir = config.control_root_path / "runs" / run_id
    write_campaign_summary(
        campaign,
        summary_dir / "summary.json",
        summary_dir / "summary.txt",
    )
    return campaign


def run_levels(
    level_ids: list[str] | None,
    config: AppConfig,
) -> CampaignResult:
    """Run selected levels, or every enabled level when ``level_ids`` is None."""

    return _run_campaign("run-levels", level_ids, config)


def run_campaign(
    name: str,
    level_ids: list[str],
    config: AppConfig,
) -> CampaignResult:
    """Run a named campaign with an explicit level selection."""

    if not isinstance(name, str) or not name.strip():
        raise ValueError("campaign name must be a non-empty string")
    return _run_campaign(name.strip(), level_ids, config)
