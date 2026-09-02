"""Local runtime log layout for LevelUpDiag-Koali."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .artifacts import level_artifacts_dir, safe_slug
from .config import AppConfig
from .manifest import LevelInfo


def _child(root: Path, *parts: str) -> Path:
    base = root.expanduser().resolve()
    candidate = base.joinpath(*parts).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("runtime path escapes its configured root")
    return candidate


def _allowed_runtime_source(config: AppConfig, source: Path) -> bool:
    resolved = source.expanduser().resolve()
    return resolved.is_relative_to(config.control_root_path) or resolved.is_relative_to(
        config.artifacts_root_path
    )


def run_directory(config: AppConfig, level: LevelInfo, started_at: datetime) -> Path:
    """Create a unique run directory under ``artifacts_dir``.

    The conventional path is ``<artifacts_dir>/<level>/<timestamp>/``.  If two
    runs share the same timestamp to the second, an incrementing suffix keeps
    both histories instead of overwriting the first.
    """

    level_root = level_artifacts_dir(config.artifacts_root_path, level.id, level.name)
    stamp = started_at.strftime("%Y%m%d_%H%M%S")
    directory = _child(level_root, stamp)
    suffix = 2
    while directory.exists():
        directory = _child(level_root, f"{stamp}-{suffix:02d}")
        suffix += 1
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def write_output_log(directory: str | Path, text: str) -> Path:
    """Write ``output.log`` in an existing or newly created run directory."""

    run_dir = Path(directory).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    path = (run_dir / "output.log").resolve()
    if not path.is_relative_to(run_dir):
        raise ValueError("output log path escapes the run directory")
    path.write_text(str(text), encoding="utf-8")
    return path


def update_latest(
    config: AppConfig,
    level: LevelInfo,
    result_path: str | Path,
) -> Path:
    """Atomically copy a level result into ``.levelupdiag/latest/<level>/``."""

    source = Path(result_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if not _allowed_runtime_source(config, source):
        raise ValueError("result_path must be under control_dir or artifacts_dir")

    latest_dir = _child(config.control_root_path, "latest", safe_slug(level.id))
    latest_dir.mkdir(parents=True, exist_ok=True)
    destination = _child(latest_dir, "result.json")
    temporary = _child(latest_dir, ".result.json.tmp")
    try:
        shutil.copyfile(source, temporary)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination
