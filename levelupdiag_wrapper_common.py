"""GUI-only helpers for the LevelUpDiag-Koali Tkinter wrapper.

This module deliberately does not create a ``Tk`` instance at import time.  It
also imports the Wave-A runner lazily so the GUI code can be compiled and
inspected against the frozen public interface before ``runner.py`` is merged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, SimpleQueue
import threading
from typing import Callable, Generic, TypeVar

from levelupdiag_core.artifacts import level_artifacts_dir, open_path, safe_slug
from levelupdiag_core.config import AppConfig, load_config
from levelupdiag_core.manifest import LevelInfo, list_levels
from levelupdiag_core.models import CampaignResult, LevelResult
from levelupdiag_core.reports import read_level_result

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class LevelRow:
    """Presentation-only snapshot used by the Treeview."""

    level: LevelInfo
    last_verdict: str

    @property
    def enabled_text(self) -> str:
        return "yes" if self.level.enabled else "no"

    @property
    def required_text(self) -> str:
        return "yes" if self.level.required else "no"


@dataclass(frozen=True, slots=True)
class TaskMessage(Generic[T]):
    """One background-task completion message consumed by the Tk thread."""

    kind: str
    payload: T | BaseException


class BackgroundTask(Generic[T]):
    """Run one callable on a daemon thread and expose completion via polling.

    The worker thread never calls Tk methods.  The GUI polls :meth:`poll` from
    the Tk event loop, which keeps all widget interaction on the main thread.
    """

    def __init__(self, target: Callable[[], T]) -> None:
        self._target = target
        self._messages: SimpleQueue[TaskMessage[T]] = SimpleQueue()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            raise RuntimeError("background task is already running")

        def worker() -> None:
            try:
                self._messages.put(TaskMessage("result", self._target()))
            except Exception as exc:  # surfaced to the GUI; never hidden
                self._messages.put(TaskMessage("error", exc))

        self._thread = threading.Thread(
            target=worker,
            name="LevelUpDiag-Koali-GUI-runner",
            daemon=True,
        )
        self._thread.start()

    def poll(self) -> TaskMessage[T] | None:
        try:
            return self._messages.get_nowait()
        except Empty:
            return None


def load_gui_state() -> tuple[AppConfig, list[LevelInfo]]:
    """Load current configuration and manifest for the wrapper."""

    config = load_config()
    levels = list_levels(config.diagnostics_root_path)
    return config, levels


def latest_result_path(config: AppConfig, level: LevelInfo) -> Path:
    """Return the stable latest-result path owned by ``logs.update_latest``."""

    return config.control_root_path / "latest" / safe_slug(level.id) / "result.json"


def latest_verdict(config: AppConfig, level: LevelInfo) -> str:
    """Read the last persisted verdict, or an em dash when none is available.

    A malformed result is displayed as ``UNREADABLE`` rather than being mapped
    to a canonical verdict.  The GUI is not allowed to invent result semantics.
    """

    path = latest_result_path(config, level)
    if not path.is_file():
        return "—"
    try:
        return read_level_result(path).verdict
    except (OSError, TypeError, ValueError):
        return "UNREADABLE"


def level_rows(config: AppConfig, levels: list[LevelInfo]) -> list[LevelRow]:
    """Build presentation rows while preserving manifest order."""

    return [LevelRow(level=level, last_verdict=latest_verdict(config, level)) for level in levels]


def enabled_level_ids(levels: list[LevelInfo]) -> list[str]:
    """Return enabled level ids in manifest order."""

    return [level.id for level in levels if level.enabled]


def run_one(level: LevelInfo, config: AppConfig) -> LevelResult:
    """Invoke the frozen Wave-A runner interface lazily."""

    try:
        from levelupdiag_core.runner import run_level
    except ImportError as exc:
        raise RuntimeError(
            "levelupdiag_core.runner is unavailable; merge LDK-0005 before running levels"
        ) from exc
    return run_level(level, config, wait=True)


def run_enabled(levels: list[LevelInfo], config: AppConfig) -> CampaignResult:
    """Run all enabled levels via the frozen Wave-A runner interface."""

    try:
        from levelupdiag_core.runner import run_levels
    except ImportError as exc:
        raise RuntimeError(
            "levelupdiag_core.runner is unavailable; merge LDK-0005 before running campaigns"
        ) from exc
    return run_levels(enabled_level_ids(levels), config)


def open_logs(config: AppConfig, level: LevelInfo | None = None) -> Path:
    """Open the relevant local log folder using ``artifacts.open_path``.

    Selecting a level opens/creates its artifact root.  With no selection, the
    global diagnostics root is opened.  This affects only local runtime output.
    """

    if level is None:
        path = config.artifacts_root_path
        path.mkdir(parents=True, exist_ok=True)
    else:
        path = level_artifacts_dir(config.artifacts_root_path, level.id, level.name)
    open_path(path)
    return path


def format_level_result(result: LevelResult) -> str:
    """Small human-readable result summary for the GUI log pane."""

    lines = [f"{result.level} — {result.name}: {result.verdict}"]
    if result.duration_seconds:
        lines.append(f"duration: {result.duration_seconds:.3f}s")
    if result.exit_code is not None:
        lines.append(f"exit code: {result.exit_code}")
    for finding in result.findings:
        lines.append(f"[{finding.severity}] {finding.id}: {finding.message}")
    if result.output_tail:
        lines.extend(["", result.output_tail])
    return "\n".join(lines)


def format_campaign_result(result: CampaignResult) -> str:
    """Small human-readable campaign summary without re-aggregating it."""

    lines = [f"Campaign {result.campaign}: {result.verdict}"]
    if result.target:
        lines.append(f"target: {result.target}")
    if result.counts:
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(result.counts.items()))
        lines.append(f"counts: {rendered}")
    lines.append("")
    lines.extend(f"{item.level} — {item.name}: {item.verdict}" for item in result.levels)
    return "\n".join(lines).rstrip()
