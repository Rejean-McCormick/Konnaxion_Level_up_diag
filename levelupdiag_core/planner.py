"""Deterministic level planning and dependency checks for LevelUpDiag-Koali."""

from __future__ import annotations

from collections.abc import Iterable

from .manifest import LevelInfo, normalize_level_id
from .models import LevelResult
from .verdicts import PASS, WARN


class PlanError(ValueError):
    """Raised when a requested level plan cannot be constructed safely."""


def _level_index(levels: Iterable[LevelInfo]) -> tuple[list[LevelInfo], dict[str, LevelInfo]]:
    ordered = list(levels)
    by_id: dict[str, LevelInfo] = {}
    for level in ordered:
        if level.id in by_id:
            raise PlanError(f"duplicate level id in planner input: {level.id}")
        by_id[level.id] = level
    return ordered, by_id


def build_plan(
    levels: list[LevelInfo],
    selected: list[str] | None = None,
) -> list[LevelInfo]:
    """Return a deterministic topological plan for enabled levels.

    ``selected=None`` plans every enabled level.  An explicit selection is
    normalized and expanded with all transitive dependencies.  Selecting a
    disabled level, or requiring a disabled dependency, is an explicit plan
    error rather than a silent skip.
    """

    ordered, by_id = _level_index(levels)
    order_index = {level.id: index for index, level in enumerate(ordered)}

    if selected is None:
        requested = [level.id for level in ordered if level.enabled]
    else:
        requested = []
        seen_requested: set[str] = set()
        for raw_id in selected:
            try:
                level_id = normalize_level_id(raw_id)
            except ValueError as exc:
                raise PlanError(str(exc)) from exc
            if level_id in seen_requested:
                continue
            seen_requested.add(level_id)
            requested.append(level_id)

    required_ids: set[str] = set()
    visiting: list[str] = []
    visited: set[str] = set()

    def include(level_id: str, *, dependency_of: str | None = None) -> None:
        level = by_id.get(level_id)
        if level is None:
            if dependency_of is None:
                raise PlanError(f"unknown selected level: {level_id}")
            raise PlanError(f"{dependency_of} depends on unknown level {level_id}")
        if not level.enabled:
            if dependency_of is None:
                raise PlanError(f"selected level is disabled: {level_id}")
            raise PlanError(f"{dependency_of} requires disabled dependency {level_id}")
        if level_id in visited:
            required_ids.add(level_id)
            return
        if level_id in visiting:
            start = visiting.index(level_id)
            cycle = [*visiting[start:], level_id]
            raise PlanError(f"dependency cycle detected: {' -> '.join(cycle)}")

        visiting.append(level_id)
        for dependency in level.depends_on:
            include(dependency, dependency_of=level_id)
        visiting.pop()
        visited.add(level_id)
        required_ids.add(level_id)

    for level_id in requested:
        include(level_id)

    # Stable Kahn topological sort.  Manifest/input order is the deterministic
    # tie-breaker for independent nodes.
    indegree: dict[str, int] = {level_id: 0 for level_id in required_ids}
    dependents: dict[str, list[str]] = {level_id: [] for level_id in required_ids}
    for level_id in required_ids:
        level = by_id[level_id]
        for dependency in level.depends_on:
            if dependency in required_ids:
                indegree[level_id] += 1
                dependents[dependency].append(level_id)

    ready = sorted(
        (level_id for level_id, degree in indegree.items() if degree == 0),
        key=order_index.__getitem__,
    )
    plan_ids: list[str] = []
    while ready:
        current = ready.pop(0)
        plan_ids.append(current)
        for dependent in sorted(dependents[current], key=order_index.__getitem__):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=order_index.__getitem__)

    if len(plan_ids) != len(required_ids):
        unresolved = sorted(required_ids - set(plan_ids), key=order_index.__getitem__)
        raise PlanError(f"dependency cycle detected among: {', '.join(unresolved)}")

    return [by_id[level_id] for level_id in plan_ids]


def dependency_blockers(
    level: LevelInfo,
    completed: dict[str, LevelResult],
) -> list[str]:
    """Return dependencies that are absent or not exploitable.

    A completed dependency is exploitable only when it is ``PASS`` or
    ``WARN``.  Every other canonical verdict blocks its dependent level.
    """

    blockers: list[str] = []
    for dependency in level.depends_on:
        result = completed.get(dependency)
        if result is None or result.verdict not in {PASS, WARN}:
            blockers.append(dependency)
    return blockers
