from __future__ import annotations

import pytest

from levelupdiag_core.manifest import LevelInfo
from levelupdiag_core.models import LevelResult
from levelupdiag_core.planner import PlanError, build_plan, dependency_blockers
from levelupdiag_core.verdicts import BLOCKED, FAIL, PASS, WARN


def level(
    level_id: str,
    *,
    enabled: bool = True,
    required: bool = False,
    depends_on: tuple[str, ...] = (),
) -> LevelInfo:
    return LevelInfo(
        id=level_id,
        name=level_id,
        file=f"levels/{level_id}.pyw",
        enabled=enabled,
        required=required,
        depends_on=depends_on,
    )


def test_build_plan_all_enabled_is_deterministic_topological_order() -> None:
    levels = [
        level("N00"),
        level("N01"),
        level("N02", depends_on=("N01",)),
        level("N03", depends_on=("N01", "N02")),
        level("N04", depends_on=("N01",)),
    ]

    assert [item.id for item in build_plan(levels)] == ["N00", "N01", "N02", "N03", "N04"]


def test_explicit_selection_adds_transitive_dependencies() -> None:
    levels = [
        level("N00"),
        level("N01"),
        level("N02", depends_on=("N01",)),
        level("N03", depends_on=("N02",)),
    ]

    assert [item.id for item in build_plan(levels, ["3"])] == ["N01", "N02", "N03"]


def test_disabled_selected_level_is_explicit_error() -> None:
    with pytest.raises(PlanError, match="selected level is disabled: N02"):
        build_plan([level("N01"), level("N02", enabled=False)], ["N02"])


def test_disabled_transitive_dependency_is_explicit_error() -> None:
    levels = [
        level("N01", enabled=False),
        level("N02", depends_on=("N01",)),
    ]
    with pytest.raises(PlanError, match="N02 requires disabled dependency N01"):
        build_plan(levels, ["N02"])


def test_unknown_dependency_is_explicit_error() -> None:
    levels = [level("N02", depends_on=("N01",))]
    with pytest.raises(PlanError, match="N02 depends on unknown level N01"):
        build_plan(levels, ["N02"])


def test_cycle_is_detected() -> None:
    levels = [
        level("N01", depends_on=("N02",)),
        level("N02", depends_on=("N01",)),
    ]
    with pytest.raises(PlanError, match="dependency cycle detected"):
        build_plan(levels, ["N01"])


def test_dependency_blockers_accepts_only_pass_or_warn() -> None:
    subject = level("N03", depends_on=("N01", "N02"))
    completed = {
        "N01": LevelResult(level="N01", name="N01", verdict=PASS),
        "N02": LevelResult(level="N02", name="N02", verdict=WARN),
    }
    assert dependency_blockers(subject, completed) == []

    completed["N02"] = LevelResult(level="N02", name="N02", verdict=FAIL)
    assert dependency_blockers(subject, completed) == ["N02"]

    completed["N02"] = LevelResult(level="N02", name="N02", verdict=BLOCKED)
    assert dependency_blockers(subject, completed) == ["N02"]

    del completed["N01"]
    assert dependency_blockers(subject, completed) == ["N01", "N02"]
