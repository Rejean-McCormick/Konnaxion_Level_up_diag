"""Read-only target repository observation level for LevelUpDiag-Koali."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.commands import find_executable, run_cmd
from levelupdiag_core.config import AppConfig, load_config
from levelupdiag_core.logs import run_directory, update_latest, write_output_log
from levelupdiag_core.manifest import get_level
from levelupdiag_core.models import Finding, LevelResult, StepResult
from levelupdiag_core.reports import write_level_result
from levelupdiag_core.verdicts import CONFIG_ERROR, INFRA_ERROR, PASS, WARN, exit_code

LEVEL_ID = "N02"
LEVEL_NAME = "Repository"


def _now() -> datetime:
    return datetime.now().astimezone()


def _run_git(
    git: str,
    target: Path,
    args: list[str],
    *,
    timeout: int,
    name: str,
    env: dict[str, str],
) -> StepResult:
    return run_cmd(
        [git, "-C", str(target), *args],
        cwd=target,
        timeout=timeout,
        name=name,
        env=env,
    )


def run(config: AppConfig | None = None) -> LevelResult:
    """Observe target repository metadata without modifying the checkout."""

    started = _now()
    cfg = load_config() if config is None else config
    target = cfg.target_root_path
    findings: list[Finding] = []
    metadata: dict[str, object] = {"target_root": str(target)}

    if not cfg.target_repo_root.strip() or not target.exists() or not target.is_dir():
        ended = _now()
        return LevelResult(
            level=LEVEL_ID,
            name=LEVEL_NAME,
            verdict=CONFIG_ERROR,
            findings=[
                Finding(
                    id="n02.target.invalid",
                    severity=CONFIG_ERROR,
                    message=f"Configured target repository is missing or not a directory: {target}",
                    category="configuration",
                    path=str(target),
                    recommendation="Correct target_repo_root before repository observation.",
                )
            ],
            started_at=started.isoformat(timespec="seconds"),
            ended_at=ended.isoformat(timespec="seconds"),
            duration_seconds=round((ended - started).total_seconds(), 6),
            cwd=str(target),
            output_tail="Target repository path is invalid.",
            metadata=metadata,
        )

    level = get_level(LEVEL_ID, root=cfg.diagnostics_root_path)
    timeout = level.timeout_seconds
    git = find_executable("git")
    if git is None:
        findings.append(
            Finding(
                id="n02.git.unavailable",
                severity=WARN,
                message="Git is not available; the target directory is usable but repository metadata cannot be observed.",
                category="toolchain",
                path=str(target),
            )
        )
        ended = _now()
        return LevelResult(
            level=LEVEL_ID,
            name=LEVEL_NAME,
            verdict=WARN,
            findings=findings,
            started_at=started.isoformat(timespec="seconds"),
            ended_at=ended.isoformat(timespec="seconds"),
            duration_seconds=round((ended - started).total_seconds(), 6),
            cwd=str(target),
            output_tail="Target directory exists; Git metadata unavailable.",
            metadata=metadata,
        )

    env = cfg.env()
    probe = _run_git(
        git,
        target,
        ["rev-parse", "--is-inside-work-tree"],
        timeout=timeout,
        name="N02 git repository probe",
        env=env,
    )
    if probe.verdict == INFRA_ERROR:
        ended = _now()
        return LevelResult(
            level=LEVEL_ID,
            name=LEVEL_NAME,
            verdict=INFRA_ERROR,
            findings=[
                Finding(
                    id="n02.git.probe-infra-error",
                    severity=INFRA_ERROR,
                    message="Git repository observation could not be executed.",
                    category="execution",
                    evidence=probe.error or probe.output_tail or None,
                )
            ],
            started_at=started.isoformat(timespec="seconds"),
            ended_at=ended.isoformat(timespec="seconds"),
            duration_seconds=round((ended - started).total_seconds(), 6),
            exit_code=probe.exit_code,
            command=list(probe.command),
            cwd=str(target),
            output_tail=probe.output_tail,
            metadata=metadata,
        )

    if probe.verdict != PASS or probe.output_tail.strip().casefold() != "true":
        findings.append(
            Finding(
                id="n02.git.not-repository",
                severity=WARN,
                message="Target directory exists but is not an observable Git worktree.",
                category="repository",
                path=str(target),
                evidence=probe.output_tail or None,
            )
        )
        ended = _now()
        metadata["is_git_repository"] = False
        return LevelResult(
            level=LEVEL_ID,
            name=LEVEL_NAME,
            verdict=WARN,
            findings=findings,
            started_at=started.isoformat(timespec="seconds"),
            ended_at=ended.isoformat(timespec="seconds"),
            duration_seconds=round((ended - started).total_seconds(), 6),
            cwd=str(target),
            output_tail="Target directory exists but is not a Git worktree.",
            metadata=metadata,
        )

    metadata["is_git_repository"] = True
    observations: list[str] = []
    execution_infra_error = False

    branch_step = _run_git(
        git,
        target,
        ["branch", "--show-current"],
        timeout=timeout,
        name="N02 git branch",
        env=env,
    )
    if branch_step.verdict == PASS:
        branch = branch_step.output_tail.strip() or "(detached)"
        metadata["branch"] = branch
        observations.append(f"branch={branch}")
    elif branch_step.verdict == INFRA_ERROR:
        execution_infra_error = True
        findings.append(
            Finding(
                id="n02.git.branch-infra-error",
                severity=INFRA_ERROR,
                message="Unable to observe the current Git branch.",
                category="execution",
                evidence=branch_step.error or branch_step.output_tail or None,
            )
        )
    else:
        findings.append(
            Finding(
                id="n02.git.branch-unavailable",
                severity=WARN,
                message="Git worktree detected but current branch could not be determined.",
                category="repository",
                evidence=branch_step.output_tail or None,
            )
        )

    head_step = _run_git(
        git,
        target,
        ["rev-parse", "HEAD"],
        timeout=timeout,
        name="N02 git HEAD",
        env=env,
    )
    if head_step.verdict == PASS:
        head = head_step.output_tail.strip()
        metadata["head"] = head
        observations.append(f"HEAD={head}")
    elif head_step.verdict == INFRA_ERROR:
        execution_infra_error = True
        findings.append(
            Finding(
                id="n02.git.head-infra-error",
                severity=INFRA_ERROR,
                message="Unable to observe Git HEAD.",
                category="execution",
                evidence=head_step.error or head_step.output_tail or None,
            )
        )
    else:
        findings.append(
            Finding(
                id="n02.git.head-unavailable",
                severity=WARN,
                message="Git worktree has no observable HEAD commit.",
                category="repository",
                evidence=head_step.output_tail or None,
            )
        )

    status_step = _run_git(
        git,
        target,
        ["status", "--porcelain", "--untracked-files=normal"],
        timeout=timeout,
        name="N02 git status",
        env=env,
    )
    if status_step.verdict == PASS:
        status_text = status_step.output_tail.strip()
        dirty = bool(status_text)
        metadata["dirty"] = dirty
        observations.append(f"dirty={'true' if dirty else 'false'}")
        if dirty:
            findings.append(
                Finding(
                    id="n02.git.worktree-dirty",
                    severity=WARN,
                    message="Git worktree contains tracked or untracked changes.",
                    category="repository",
                    path=str(target),
                    evidence=status_text[-4000:] or None,
                    recommendation="Review the working tree state before interpreting validation evidence.",
                )
            )
    elif status_step.verdict == INFRA_ERROR:
        execution_infra_error = True
        findings.append(
            Finding(
                id="n02.git.status-infra-error",
                severity=INFRA_ERROR,
                message="Unable to observe Git working tree status.",
                category="execution",
                evidence=status_step.error or status_step.output_tail or None,
            )
        )
    else:
        findings.append(
            Finding(
                id="n02.git.status-unavailable",
                severity=WARN,
                message="Git worktree detected but status could not be determined.",
                category="repository",
                evidence=status_step.output_tail or None,
            )
        )

    if execution_infra_error:
        verdict = INFRA_ERROR
    elif findings:
        verdict = WARN
    else:
        verdict = PASS

    ended = _now()
    return LevelResult(
        level=LEVEL_ID,
        name=LEVEL_NAME,
        verdict=verdict,
        findings=findings,
        started_at=started.isoformat(timespec="seconds"),
        ended_at=ended.isoformat(timespec="seconds"),
        duration_seconds=round((ended - started).total_seconds(), 6),
        cwd=str(target),
        output_tail="; ".join(observations) or "Git worktree observed.",
        metadata=metadata,
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
