"""LevelUpDiag-Koali self-check level.

N00 validates the appendix itself only. It does not inspect or validate the
kOA-Linux target repository.
"""

from __future__ import annotations

from datetime import datetime
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.config import AppConfig, load_config
from levelupdiag_core.logs import run_directory, update_latest, write_output_log
from levelupdiag_core.manifest import get_level, load_manifest
from levelupdiag_core.models import Finding, LevelResult
from levelupdiag_core.reports import write_level_result
from levelupdiag_core.verdicts import CONFIG_ERROR, PASS, exit_code

LEVEL_ID = "N00"
LEVEL_NAME = "Control Panel"

_BASE_CORE_MODULES = (
    "levelupdiag_core.config",
    "levelupdiag_core.manifest",
    "levelupdiag_core.models",
    "levelupdiag_core.commands",
    "levelupdiag_core.logs",
    "levelupdiag_core.artifacts",
    "levelupdiag_core.reports",
    "levelupdiag_core.verdicts",
)


def _now() -> datetime:
    return datetime.now().astimezone()


def _finish(
    started: datetime,
    verdict: str,
    findings: list[Finding],
    *,
    config: AppConfig | None = None,
) -> LevelResult:
    ended = _now()
    root = str(config.diagnostics_root_path) if config is not None else ""
    summary = (
        "LevelUpDiag-Koali base self-check passed."
        if verdict == PASS
        else "LevelUpDiag-Koali base self-check found configuration or core errors."
    )
    return LevelResult(
        level=LEVEL_ID,
        name=LEVEL_NAME,
        verdict=verdict,
        findings=findings,
        started_at=started.isoformat(timespec="seconds"),
        ended_at=ended.isoformat(timespec="seconds"),
        duration_seconds=round((ended - started).total_seconds(), 6),
        cwd=root,
        output_tail=summary,
        metadata={"diagnostics_root": root} if root else {},
    )


def run(config: AppConfig | None = None) -> LevelResult:
    """Check that configuration, manifest, and the frozen base core are usable."""

    started = _now()
    findings: list[Finding] = []

    if config is None:
        try:
            cfg = load_config()
        except (FileNotFoundError, OSError, ValueError) as exc:
            findings.append(
                Finding(
                    id="n00.configuration.unreadable",
                    severity=CONFIG_ERROR,
                    message="LevelUpDiag-Koali configuration could not be loaded.",
                    category="configuration",
                    evidence=f"{type(exc).__name__}: {exc}",
                    recommendation="Correct the local/example configuration before running other levels.",
                )
            )
            return _finish(started, CONFIG_ERROR, findings)
    else:
        cfg = config

    root = cfg.diagnostics_root_path
    if not root.is_dir():
        findings.append(
            Finding(
                id="n00.repository-root.invalid",
                severity=CONFIG_ERROR,
                message=f"LevelUpDiag-Koali diagnostics root is not a directory: {root}",
                category="configuration",
                path=str(root),
            )
        )

    if cfg.config_path:
        config_path = Path(cfg.config_path).expanduser().resolve()
        if not config_path.is_file():
            findings.append(
                Finding(
                    id="n00.configuration.source-missing",
                    severity=CONFIG_ERROR,
                    message=f"Resolved configuration source is missing: {config_path}",
                    category="configuration",
                    path=str(config_path),
                )
            )

    try:
        manifest = load_manifest(root=root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        findings.append(
            Finding(
                id="n00.manifest.unreadable",
                severity=CONFIG_ERROR,
                message="LevelUpDiag-Koali manifest could not be loaded or validated.",
                category="configuration",
                evidence=f"{type(exc).__name__}: {exc}",
                recommendation="Restore a valid levelupdiag_manifest.json before running campaigns.",
            )
        )
    else:
        if len(manifest.get("levels", [])) != 12:
            findings.append(
                Finding(
                    id="n00.manifest.level-count",
                    severity=CONFIG_ERROR,
                    message="The canonical manifest must contain exactly N00 through N11.",
                    category="configuration",
                )
            )

    for module_name in _BASE_CORE_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            findings.append(
                Finding(
                    id=f"n00.core.{module_name.rsplit('.', 1)[-1]}.unavailable",
                    severity=CONFIG_ERROR,
                    message=f"Required base core module is not importable: {module_name}",
                    category="internal-contract",
                    evidence=f"{type(exc).__name__}: {exc}",
                    recommendation="Restore the validated LDK-0001 through LDK-0004 baseline.",
                )
            )

    verdict = CONFIG_ERROR if findings else PASS
    return _finish(started, verdict, findings, config=cfg)


def main() -> int:
    """Standalone entry point with canonical persistence."""

    config = load_config()
    result = run(config)
    level = get_level(LEVEL_ID, root=config.diagnostics_root_path)
    try:
        started = datetime.fromisoformat(result.started_at) if result.started_at else _now()
    except ValueError:
        started = _now()
    directory = run_directory(config, level, started)
    result_path = write_level_result(result, directory / "result.json")
    write_output_log(directory, result.output_tail)
    update_latest(config, level, result_path)
    return exit_code(result.verdict)


if __name__ == "__main__":
    raise SystemExit(main())
