from __future__ import annotations

import json
from pathlib import Path

import pytest

from levelupdiag_core.manifest import (
    CANONICAL_LEVEL_IDS,
    get_level,
    list_levels,
    load_manifest,
    normalize_level_id,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict:
    return json.loads((ROOT / "levelupdiag_manifest.json").read_text(encoding="utf-8"))


def test_normalize_level_number() -> None:
    assert normalize_level_id("4") == "N04"
    assert normalize_level_id("n4") == "N04"
    assert normalize_level_id("LUD-4") == "N04"


def test_normalize_invalid_level_fails() -> None:
    with pytest.raises(ValueError):
        normalize_level_id("contracts")


def test_konnaxion_manifest_has_exact_canonical_taxonomy() -> None:
    data = load_manifest(ROOT)
    assert validate_manifest(data) == []
    levels = list_levels(ROOT)
    assert tuple(level.id for level in levels) == CANONICAL_LEVEL_IDS
    assert get_level("N00", ROOT).name == "Control & Discovery"
    assert get_level("N11", ROOT).name == "Correlation & Triage"
    assert get_level("N11", ROOT).file == "levels/N11_n11_konnaxion.pyw"


def test_all_konnaxion_levels_are_campaign_blocking() -> None:
    levels = list_levels(ROOT)
    assert all(level.required for level in levels)
    assert levels[0].depends_on == ()
    assert all(level.depends_on == ("N00",) for level in levels[1:])


def test_duplicate_id_is_detected() -> None:
    data = _manifest()
    data["levels"][1]["id"] = "N00"
    errors = validate_manifest(data)
    assert any("duplicate level id: N00" in error for error in errors)


def test_unknown_dependency_is_detected() -> None:
    data = _manifest()
    data["levels"][5]["depends_on"] = ["N99"]
    errors = validate_manifest(data)
    assert any("depends on unknown level N99" in error for error in errors)


def test_invalid_structure_is_detected() -> None:
    data = _manifest()
    data["levels"][3]["enabled"] = "yes"
    data["levels"][3]["timeout_seconds"] = 0
    errors = validate_manifest(data)
    assert any("enabled must be a boolean" in error for error in errors)
    assert any("timeout_seconds must be a positive integer" in error for error in errors)


def test_cycle_is_detected() -> None:
    data = _manifest()
    data["levels"][0]["depends_on"] = ["N01"]
    errors = validate_manifest(data)
    assert any("dependency cycle detected" in error for error in errors)
