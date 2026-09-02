"""Canonical manifest helpers for LevelUpDiag-Koali."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .config import detect_diag_root

MANIFEST_FILE = "levelupdiag_manifest.json"
MANIFEST_SCHEMA = "levelupdiag.koali.manifest.v1"
LEVEL_ID_RE = re.compile(r"^(?:N|LUD-?)?(\d{1,2})$", re.IGNORECASE)
CANONICAL_LEVEL_IDS = tuple(f"N{i:02d}" for i in range(12))


@dataclass(frozen=True, slots=True)
class LevelInfo:
    id: str
    name: str
    file: str
    enabled: bool = True
    required: bool = False
    depends_on: tuple[str, ...] = ()
    timeout_seconds: int = 180
    purpose: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def display_title(self) -> str:
        return f"{self.id} — {self.name}"

    def file_path(self, root: Path | None = None) -> Path:
        return (root or detect_diag_root()) / self.file


def normalize_level_id(value: str | int) -> str:
    raw = str(value).strip().upper().replace(" ", "")
    match = LEVEL_ID_RE.fullmatch(raw)
    if not match:
        raise ValueError(f"Invalid level identifier: {value!r}")
    number = int(match.group(1))
    if not 0 <= number <= 99:
        raise ValueError(f"Invalid level identifier: {value!r}")
    return f"N{number:02d}"


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid manifest JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    return data


def validate_manifest(data: Mapping[str, Any]) -> list[str]:
    """Return every structural error found in a manifest.

    The current Koali architecture is intentionally closed to N00..N11.
    """

    errors: list[str] = []
    if data.get("schema") != MANIFEST_SCHEMA:
        errors.append(f"schema must be {MANIFEST_SCHEMA!r}")

    levels = data.get("levels")
    if not isinstance(levels, list):
        return [*errors, "levels must be a list"]

    seen: set[str] = set()
    ids: list[str] = []
    dependencies: dict[str, tuple[str, ...]] = {}

    for index, item in enumerate(levels):
        prefix = f"levels[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        raw_id = item.get("id")
        if not isinstance(raw_id, str):
            errors.append(f"{prefix}.id must be a string")
            continue
        try:
            level_id = normalize_level_id(raw_id)
        except ValueError:
            errors.append(f"{prefix}.id is invalid: {raw_id!r}")
            continue
        if level_id != raw_id:
            errors.append(f"{prefix}.id must use canonical form {level_id}")
        if level_id not in CANONICAL_LEVEL_IDS:
            errors.append(f"{prefix}.id is outside the closed N00..N11 taxonomy")
        if level_id in seen:
            errors.append(f"duplicate level id: {level_id}")
        seen.add(level_id)
        ids.append(level_id)

        for field_name in ("name", "file"):
            value = item.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{field_name} must be a non-empty string")

        for field_name in ("enabled", "required"):
            if not isinstance(item.get(field_name), bool):
                errors.append(f"{prefix}.{field_name} must be a boolean")

        timeout = item.get("timeout_seconds")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            errors.append(f"{prefix}.timeout_seconds must be a positive integer")

        depends_on = item.get("depends_on")
        if not isinstance(depends_on, list) or not all(isinstance(x, str) for x in depends_on):
            errors.append(f"{prefix}.depends_on must be a list of level ids")
            dependencies[level_id] = ()
        else:
            normalized: list[str] = []
            for dep in depends_on:
                try:
                    canonical = normalize_level_id(dep)
                except ValueError:
                    errors.append(f"{prefix}.depends_on contains invalid id {dep!r}")
                    continue
                if canonical != dep:
                    errors.append(f"{prefix}.depends_on must use canonical id {canonical}")
                if canonical == level_id:
                    errors.append(f"{prefix}.depends_on cannot reference itself")
                normalized.append(canonical)
            if len(normalized) != len(set(normalized)):
                errors.append(f"{prefix}.depends_on contains duplicates")
            dependencies[level_id] = tuple(normalized)

        purpose = item.get("purpose", "")
        if not isinstance(purpose, str):
            errors.append(f"{prefix}.purpose must be a string")

        allowed = {
            "id",
            "name",
            "file",
            "enabled",
            "required",
            "depends_on",
            "timeout_seconds",
            "purpose",
        }
        unknown = set(item) - allowed
        if unknown:
            errors.append(
                f"{prefix} contains unsupported fields: {', '.join(sorted(unknown))}"
            )

    if ids != list(CANONICAL_LEVEL_IDS):
        errors.append("levels must contain exactly N00..N11 in canonical order")

    known = set(ids)
    for level_id, deps in dependencies.items():
        for dep in deps:
            if dep not in known:
                errors.append(f"{level_id} depends on unknown level {dep}")

    # Lightweight cycle detection so the manifest stays safe before planner.py exists.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(level_id: str, trail: tuple[str, ...]) -> None:
        if level_id in visited:
            return
        if level_id in visiting:
            errors.append(f"dependency cycle detected: {' -> '.join((*trail, level_id))}")
            return
        visiting.add(level_id)
        for dep in dependencies.get(level_id, ()):
            if dep in known:
                visit(dep, (*trail, level_id))
        visiting.remove(level_id)
        visited.add(level_id)

    for level_id in ids:
        visit(level_id, ())

    return errors


def load_manifest(root: Path | None = None) -> dict[str, Any]:
    diag_root = (root or detect_diag_root()).expanduser().resolve()
    path = diag_root / MANIFEST_FILE
    if not path.is_file():
        raise FileNotFoundError(f"Missing manifest: {path}")
    data = _read_manifest(path)
    errors = validate_manifest(data)
    if errors:
        raise ValueError("Invalid LevelUpDiag-Koali manifest:\n- " + "\n- ".join(errors))
    return data


def _level_from_item(item: Mapping[str, Any]) -> LevelInfo:
    return LevelInfo(
        id=str(item["id"]),
        name=str(item["name"]),
        file=str(item["file"]),
        enabled=bool(item["enabled"]),
        required=bool(item["required"]),
        depends_on=tuple(str(x) for x in item["depends_on"]),
        timeout_seconds=int(item["timeout_seconds"]),
        purpose=str(item.get("purpose", "")),
        raw=dict(item),
    )


def list_levels(root: Path | None = None) -> list[LevelInfo]:
    return [_level_from_item(item) for item in load_manifest(root)["levels"]]


def get_level(value: str | int, root: Path | None = None) -> LevelInfo:
    wanted = normalize_level_id(value)
    for level in list_levels(root):
        if level.id == wanted:
            return level
    raise KeyError(f"Unknown level: {wanted}")
