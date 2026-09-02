"""Public LevelUpDiag-Koali core API."""

from .config import AppConfig, load_config, save_config
from .manifest import LevelInfo, get_level, list_levels, normalize_level_id
from .models import Artifact, CampaignResult, Finding, LevelResult, StepResult
from .planner import PlanError, build_plan, dependency_blockers
from .runner import run_campaign, run_level, run_levels
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
    exit_code,
    normalize_verdict,
)

__all__ = [
    "AppConfig",
    "Artifact",
    "BLOCKED",
    "CONFIG_ERROR",
    "CampaignResult",
    "ERROR",
    "FAIL",
    "Finding",
    "INFRA_ERROR",
    "LevelInfo",
    "LevelResult",
    "PARTIAL",
    "PASS",
    "PlanError",
    "SKIP",
    "StepResult",
    "VERDICTS",
    "WARN",
    "aggregate_verdicts",
    "build_plan",
    "dependency_blockers",
    "exit_code",
    "get_level",
    "list_levels",
    "load_config",
    "normalize_level_id",
    "normalize_verdict",
    "run_campaign",
    "run_level",
    "run_levels",
    "save_config",
]
