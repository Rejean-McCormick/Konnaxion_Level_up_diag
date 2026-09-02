"""Environment prerequisite level for LevelUpDiag-Koali."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.commands import find_executable
from levelupdiag_core.config import AppConfig, load_config
from levelupdiag_core.logs import run_directory, update_latest, write_output_log
from levelupdiag_core.manifest import get_level
from levelupdiag_core.models import Finding, LevelResult
from levelupdiag_core.reports import write_level_result
from levelupdiag_core.verdicts import BLOCKED, CONFIG_ERROR, PASS, WARN, exit_code

LEVEL_ID = "N01"
LEVEL_NAME = "Environment"

_PYTHON_NAMES = {"python", "python3", "py"}


def _now() -> datetime:
    return datetime.now().astimezone()


def _tool_available(name: str) -> tuple[bool, str | None]:
    normalized = name.strip()
    if normalized.casefold() in _PYTHON_NAMES:
        executable = Path(sys.executable).expanduser().resolve()
        return executable.is_file(), str(executable)
    found = find_executable(normalized)
    return found is not None, found


def run(config: AppConfig | None = None) -> LevelResult:
    """Validate the configured target path and required local toolchain."""

    started = _now()
    cfg = load_config() if config is None else config
    findings: list[Finding] = []
    config_error = False
    blocked = False
    warned = False

    diagnostics_root = cfg.diagnostics_root_path
    target_root = cfg.target_root_path

    if not diagnostics_root.is_dir():
        config_error = True
        findings.append(
            Finding(
                id="n01.diagnostics-root.invalid",
                severity=CONFIG_ERROR,
                message=f"LevelUpDiag-Koali diagnostics root is not a directory: {diagnostics_root}",
                category="configuration",
                path=str(diagnostics_root),
            )
        )

    if not cfg.target_repo_root.strip():
        config_error = True
        findings.append(
            Finding(
                id="n01.target.empty",
                severity=CONFIG_ERROR,
                message="target_repo_root is empty.",
                category="configuration",
                recommendation="Configure target_repo_root to the kOA-Linux checkout directory.",
            )
        )
    elif not target_root.exists() or not target_root.is_dir():
        config_error = True
        findings.append(
            Finding(
                id="n01.target.invalid",
                severity=CONFIG_ERROR,
                message=f"Configured target_repo_root is missing or not a directory: {target_root}",
                category="configuration",
                path=str(target_root),
                recommendation="Correct target_repo_root before running kOA-Linux validation levels.",
            )
        )

    required_tools = list(cfg.toolchain.get("required", []))
    optional_tools = list(cfg.toolchain.get("optional", []))
    observed_tools: dict[str, str] = {}

    for raw_name in required_tools:
        name = raw_name.strip()
        if not name:
            config_error = True
            findings.append(
                Finding(
                    id="n01.tool.required.invalid",
                    severity=CONFIG_ERROR,
                    message="toolchain.required contains an empty tool name.",
                    category="configuration",
                )
            )
            continue
        available, executable = _tool_available(name)
        if available:
            observed_tools[name] = executable or name
        else:
            blocked = True
            findings.append(
                Finding(
                    id=f"n01.tool.required.{name.casefold()}.missing",
                    severity=BLOCKED,
                    message=f"Required tool is not available: {name}",
                    category="toolchain",
                    recommendation=f"Install or expose '{name}' on PATH before running dependent levels.",
                )
            )

    for raw_name in optional_tools:
        name = raw_name.strip()
        if not name:
            warned = True
            findings.append(
                Finding(
                    id="n01.tool.optional.invalid",
                    severity=WARN,
                    message="toolchain.optional contains an empty tool name; it was ignored.",
                    category="configuration",
                )
            )
            continue
        available, executable = _tool_available(name)
        if available:
            observed_tools[name] = executable or name
        else:
            warned = True
            findings.append(
                Finding(
                    id=f"n01.tool.optional.{name.casefold()}.missing",
                    severity=WARN,
                    message=f"Optional tool is not available: {name}",
                    category="toolchain",
                )
            )

    if config_error:
        verdict = CONFIG_ERROR
    elif blocked:
        verdict = BLOCKED
    elif warned:
        verdict = WARN
    else:
        verdict = PASS

    ended = _now()
    summary_parts = [
        f"python={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        f"target={target_root}",
        f"required_tools={len(required_tools)}",
        f"optional_tools={len(optional_tools)}",
    ]
    return LevelResult(
        level=LEVEL_ID,
        name=LEVEL_NAME,
        verdict=verdict,
        findings=findings,
        started_at=started.isoformat(timespec="seconds"),
        ended_at=ended.isoformat(timespec="seconds"),
        duration_seconds=round((ended - started).total_seconds(), 6),
        cwd=str(target_root),
        output_tail="; ".join(summary_parts),
        metadata={
            "python_executable": str(Path(sys.executable).resolve()),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "diagnostics_root": str(diagnostics_root),
            "target_root": str(target_root),
            "control_root": str(cfg.control_root_path),
            "artifacts_root": str(cfg.artifacts_root_path),
            "observed_tools": observed_tools,
        },
    )


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
