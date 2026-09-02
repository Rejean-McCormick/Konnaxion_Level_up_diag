"""Shared data structures for LevelUpDiag-Koali.

This module deliberately contains no filesystem, subprocess, GUI, or network
I/O. It only defines the values exchanged between levels and the core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .verdicts import PASS, normalize_verdict

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(slots=True)
class Finding:
    """A structured observation emitted by a level."""

    id: str
    severity: str
    message: str
    category: str = "general"
    path: str | None = None
    evidence: str | None = None
    recommendation: str | None = None
    data: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("finding id must not be empty")
        if not self.message.strip():
            raise ValueError("finding message must not be empty")
        self.severity = normalize_verdict(self.severity)


@dataclass(slots=True)
class Artifact:
    """A local file or directory produced or referenced by a level."""

    kind: str
    path: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("artifact kind must not be empty")
        if not self.path.strip():
            raise ValueError("artifact path must not be empty")


@dataclass(slots=True)
class StepResult:
    """Normalized result of one external command or execution step."""

    verdict: str
    command: list[str] = field(default_factory=list)
    cwd: str = ""
    exit_code: int | None = None
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    output_tail: str = ""
    error: str | None = None

    def __post_init__(self) -> None:
        self.verdict = normalize_verdict(self.verdict)
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative")


@dataclass(slots=True)
class LevelResult:
    """Canonical result produced by one N00..N11 level."""

    level: str
    name: str
    verdict: str = PASS
    findings: list[Finding] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    schema: str = "levelupdiag.report.v1"
    standard: str = "LevelUpDiag"
    standard_version: str = "1.0"
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    exit_code: int | None = None
    command: list[str] = field(default_factory=list)
    cwd: str = ""
    output_tail: str = ""
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.verdict = normalize_verdict(self.verdict)
        if self.schema != "levelupdiag.report.v1":
            raise ValueError("unsupported level result schema")
        if self.standard != "LevelUpDiag":
            raise ValueError("unsupported report standard")
        if len(self.level) != 3 or self.level[0] != "N" or not self.level[1:].isdigit():
            raise ValueError("level must match N00..N99")
        if not self.name.strip():
            raise ValueError("level name must not be empty")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative")


@dataclass(slots=True)
class CampaignResult:
    """Simple grouping of level results executed against one target."""

    campaign: str
    target: str
    verdict: str
    levels: list[LevelResult] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.campaign.strip():
            raise ValueError("campaign name must not be empty")
        self.verdict = normalize_verdict(self.verdict)
        if any(value < 0 for value in self.counts.values()):
            raise ValueError("campaign counts must not be negative")
