from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass(slots=True)
class Finding:
    id: str
    severity: str
    message: str
    category: str
    path: str | None = None
    evidence: Any = None
    recommendation: str | None = None
    data: dict[str, Any] | None = None
    def to_dict(self):
        d=asdict(self)
        return {k:v for k,v in d.items() if v is not None}

@dataclass(slots=True)
class Artifact:
    kind: str
    path: str
    description: str | None = None
    data: dict[str, Any] | None = None
    def to_dict(self):
        d=asdict(self); return {k:v for k,v in d.items() if v is not None}

@dataclass(slots=True)
class StepResult:
    name: str
    command: tuple[str, ...]
    cwd: str
    verdict: str
    exit_code: int | None
    duration_seconds: float
    output_tail: str = ""
    error: str = ""
    timed_out: bool = False
    def to_dict(self): return asdict(self)

@dataclass(slots=True)
class LevelResult:
    level: str
    name: str
    verdict: str
    findings: list[Finding] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    cwd: str = ""
    output_tail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        return {
            "schema":"levelupdiag.report.v2","level":self.level,"level_id":self.level,"name":self.name,
            "level_name":self.name,"verdict":self.verdict,"findings":[f.to_dict() for f in self.findings],
            "artifacts":[a.to_dict() for a in self.artifacts],"started_at":self.started_at,"ended_at":self.ended_at,
            "duration_seconds":self.duration_seconds,"cwd":self.cwd,"output_tail":self.output_tail,"metadata":self.metadata,
        }

@dataclass(slots=True)
class CampaignResult:
    campaign: str
    verdict: str
    levels: list[LevelResult]
    run_id: str
    started_at: str
    ended_at: str
    expected_levels: list[str]
    def to_dict(self):
        return {
            "schema":"levelupdiag.campaign-summary.v2","campaign":self.campaign,"selection":self.campaign,
            "verdict":self.verdict,"run_id":self.run_id,"started_at":self.started_at,"ended_at":self.ended_at,
            "expected_levels":self.expected_levels,
            "levels":[{"id":r.level,"name":r.name,"verdict":r.verdict} for r in self.levels],
        }
