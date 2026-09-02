from __future__ import annotations

import json
from pathlib import Path

import pytest

from levelupdiag_core.models import Artifact, CampaignResult, Finding, LevelResult, StepResult
from levelupdiag_core.reports import read_level_result, write_campaign_summary, write_level_result
from levelupdiag_core.verdicts import (
    BLOCKED,
    CONFIG_ERROR,
    ERROR,
    FAIL,
    INFRA_ERROR,
    PARTIAL,
    PASS,
    SKIP,
    WARN,
    VERDICTS,
    aggregate_verdicts,
    normalize_verdict,
)


def test_schema_is_parseable_and_contains_exact_verdicts() -> None:
    schema = json.loads(Path("schemas/levelupdiag.result.schema.json").read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema"]["const"] == "levelupdiag.report.v1"
    assert tuple(schema["properties"]["verdict"]["enum"]) == VERDICTS
    assert set(schema["required"]) == {
        "schema",
        "standard",
        "standard_version",
        "level",
        "name",
        "verdict",
        "findings",
    }


def test_normalize_verdict_is_explicit_and_strict() -> None:
    assert normalize_verdict(" pass ") == PASS
    assert normalize_verdict("infra_error") == INFRA_ERROR

    with pytest.raises(ValueError, match="unsupported verdict"):
        normalize_verdict("MAYBE")
    with pytest.raises(ValueError, match="must be a string"):
        normalize_verdict(None)  # type: ignore[arg-type]


def test_aggregate_verdicts_uses_documented_precedence() -> None:
    assert aggregate_verdicts([PASS, SKIP]) == SKIP
    assert aggregate_verdicts([PASS, WARN]) == WARN
    assert aggregate_verdicts([WARN, PARTIAL]) == PARTIAL
    assert aggregate_verdicts([FAIL, BLOCKED]) == BLOCKED
    assert aggregate_verdicts([BLOCKED, INFRA_ERROR]) == INFRA_ERROR
    assert aggregate_verdicts([INFRA_ERROR, CONFIG_ERROR]) == CONFIG_ERROR
    assert aggregate_verdicts([CONFIG_ERROR, ERROR]) == ERROR

    with pytest.raises(ValueError, match="empty verdict"):
        aggregate_verdicts([])


def test_level_result_round_trip_utf8(tmp_path: Path) -> None:
    original = LevelResult(
        level="N04",
        name="Contrats – intégrité",
        verdict=FAIL,
        findings=[
            Finding(
                id="contracts.failure",
                severity=FAIL,
                category="contracts",
                message="Échec déterministe de validation.",
                path="ci/scripts/run-contracts.py",
                recommendation="Corriger le contrat concerné.",
                data={"count": 1},
            )
        ],
        artifacts=[Artifact(kind="log", path="output.log", description="Sortie complète")],
        started_at="2026-08-07T12:00:00-04:00",
        ended_at="2026-08-07T12:00:01-04:00",
        duration_seconds=1.0,
        exit_code=2,
        command=["python", "ci/scripts/run-contracts.py"],
        cwd="C:/work/koa-linux",
        output_tail="contrat invalide",
        metadata={"target": "kOA-Linux"},
    )
    path = tmp_path / "result.json"

    written = write_level_result(original, path)
    loaded = read_level_result(path)

    assert written == path
    assert loaded == original
    text = path.read_text(encoding="utf-8")
    assert "Contrats – intégrité" in text
    assert text.endswith("\n")
    assert not list(tmp_path.glob(".result.json.*.tmp"))


def test_read_level_result_rejects_invalid_forms(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"

    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be an object"):
        read_level_result(path)

    path.write_text(json.dumps({"schema": "levelupdiag.report.v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required"):
        read_level_result(path)

    invalid = {
        "schema": "levelupdiag.report.v1",
        "standard": "LevelUpDiag",
        "standard_version": "1.0",
        "level": "N04",
        "name": "Contracts",
        "verdict": "SUCCESS",
        "findings": [],
    }
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported verdict"):
        read_level_result(path)


def test_campaign_summary_writes_readable_json_and_optional_text(tmp_path: Path) -> None:
    level = LevelResult(level="N01", name="Environment", verdict=PASS)
    campaign = CampaignResult(
        campaign="developer-fast",
        target="kOA-Linux",
        verdict=WARN,
        levels=[level],
        started_at="2026-08-07T12:00:00-04:00",
        ended_at="2026-08-07T12:00:02-04:00",
        counts={PASS: 1, WARN: 1},
    )
    json_path = tmp_path / "summary.json"
    text_path = tmp_path / "summary.txt"

    outputs = write_campaign_summary(campaign, json_path, text_path)

    assert outputs == (json_path, text_path)
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["campaign"] == "developer-fast"
    assert parsed["verdict"] == WARN
    assert parsed["levels"][0]["level"] == "N01"
    assert "Verdict: WARN" in text_path.read_text(encoding="utf-8")


def test_models_reject_invalid_invariants() -> None:
    with pytest.raises(ValueError, match="level must match"):
        LevelResult(level="4", name="Contracts", verdict=PASS)
    with pytest.raises(ValueError, match="duration_seconds"):
        StepResult(verdict=PASS, duration_seconds=-0.1)
    with pytest.raises(ValueError, match="artifact path"):
        Artifact(kind="log", path="")
