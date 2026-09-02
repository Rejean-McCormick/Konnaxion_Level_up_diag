"""UTF-8 JSON/TXT serialization for LevelUpDiag-Koali results."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .models import Artifact, CampaignResult, Finding, LevelResult
from .verdicts import VERDICTS, normalize_verdict

_REQUIRED_LEVEL_FIELDS = {
    "schema",
    "standard",
    "standard_version",
    "level",
    "name",
    "verdict",
    "findings",
}


def _json_data(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _json_data(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _json_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_data(item) for item in value]
    return value


def _atomic_write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
        return path
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _json_text(value: Any) -> str:
    return json.dumps(_json_data(value), indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def write_level_result(result: LevelResult, path: str | Path) -> Path:
    """Atomically write one canonical level result as readable UTF-8 JSON."""

    if not isinstance(result, LevelResult):
        raise TypeError("result must be a LevelResult")
    return _atomic_write_text(Path(path), _json_text(result))


def _require_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _read_findings(raw: Any) -> list[Finding]:
    if not isinstance(raw, list):
        raise ValueError("findings must be an array")
    findings: list[Finding] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"findings[{index}] must be an object")
        try:
            findings.append(Finding(**item))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid finding at index {index}: {exc}") from exc
    return findings


def _read_artifacts(raw: Any) -> list[Artifact]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("artifacts must be an array")
    artifacts: list[Artifact] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"artifacts[{index}] must be an object")
        try:
            artifacts.append(Artifact(**item))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid artifact at index {index}: {exc}") from exc
    return artifacts


def _level_result_from_mapping(raw: Mapping[str, Any]) -> LevelResult:
    missing = sorted(_REQUIRED_LEVEL_FIELDS - raw.keys())
    if missing:
        raise ValueError(f"missing required level result field(s): {', '.join(missing)}")

    schema = _require_string(raw, "schema")
    standard = _require_string(raw, "standard")
    standard_version = _require_string(raw, "standard_version")
    level = _require_string(raw, "level")
    name = _require_string(raw, "name")
    verdict = normalize_verdict(_require_string(raw, "verdict"))
    if schema != "levelupdiag.report.v1":
        raise ValueError(f"unsupported schema: {schema!r}")
    if standard != "LevelUpDiag":
        raise ValueError(f"unsupported standard: {standard!r}")

    optional_list_fields = ("command",)
    for key in optional_list_fields:
        if key in raw and not isinstance(raw[key], list):
            raise ValueError(f"{key} must be an array")
    if "metadata" in raw and not isinstance(raw["metadata"], dict):
        raise ValueError("metadata must be an object")

    try:
        return LevelResult(
            schema=schema,
            standard=standard,
            standard_version=standard_version,
            level=level,
            name=name,
            verdict=verdict,
            findings=_read_findings(raw["findings"]),
            artifacts=_read_artifacts(raw.get("artifacts")),
            started_at=str(raw.get("started_at", "")),
            ended_at=str(raw.get("ended_at", "")),
            duration_seconds=float(raw.get("duration_seconds", 0.0)),
            exit_code=raw.get("exit_code"),
            command=[str(item) for item in raw.get("command", [])],
            cwd=str(raw.get("cwd", "")),
            output_tail=str(raw.get("output_tail", "")),
            metadata=dict(raw.get("metadata", {})),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid level result: {exc}") from exc


def read_level_result(path: str | Path) -> LevelResult:
    """Read and validate a canonical level result from UTF-8 JSON."""

    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {source}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("level result root must be an object")
    return _level_result_from_mapping(raw)


def _campaign_text(result: CampaignResult) -> str:
    lines = [
        f"LevelUpDiag campaign: {result.campaign}",
        f"Target: {result.target}",
        f"Verdict: {result.verdict}",
        f"Started: {result.started_at}",
        f"Ended: {result.ended_at}",
        "",
        "Levels:",
    ]
    lines.extend(f"- {item.level} {item.name}: {item.verdict}" for item in result.levels)
    if result.counts:
        lines.extend(["", "Counts:"])
        lines.extend(f"- {key}: {value}" for key, value in sorted(result.counts.items()))
    return "\n".join(lines) + "\n"


def write_campaign_summary(
    result: CampaignResult,
    json_path: str | Path,
    text_path: str | Path | None = None,
) -> tuple[Path, Path | None]:
    """Write a campaign summary as JSON and, optionally, a readable TXT file."""

    if not isinstance(result, CampaignResult):
        raise TypeError("result must be a CampaignResult")
    json_output = _atomic_write_text(Path(json_path), _json_text(result))
    text_output = None
    if text_path is not None:
        text_output = _atomic_write_text(Path(text_path), _campaign_text(result))
    return json_output, text_output
