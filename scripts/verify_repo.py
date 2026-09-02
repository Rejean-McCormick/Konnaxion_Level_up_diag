from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.manifest import MANIFEST_FILE, list_levels, load_manifest, validate_manifest

AI_CONTRACT = "docs/AI_COMPOSER_CONTRACT.json"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_paths() -> list[str]:
    contract_path = ROOT / AI_CONTRACT
    data = _read_json(contract_path)
    if not isinstance(data, dict):
        raise ValueError(f"{AI_CONTRACT} must contain a JSON object")
    layout = data.get("final_repository_layout")
    if not isinstance(layout, dict):
        raise ValueError(f"{AI_CONTRACT} has no final_repository_layout object")

    paths: list[str] = []
    for key in (
        "root_files",
        "core_files",
        "script_files",
        "schema_files",
        "level_files",
        "launcher_files",
        "test_files",
    ):
        values = layout.get(key)
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError(f"final_repository_layout.{key} must be a list of strings")
        paths.extend(values)

    documentation = [
        "docs/README.md",
        "docs/01-overview.md",
        "docs/02-architecture.md",
        "docs/03-levels-and-checks.md",
        "docs/04-configuration.md",
        "docs/05-execution-and-ordering.md",
        "docs/06-results-and-logs.md",
        "docs/07-koa-linux-integration.md",
        "docs/08-campaigns.md",
        "docs/09-failure-and-blocking-model.md",
        "docs/10-security.md",
        "docs/11-cli-and-gui.md",
        "docs/12-testing.md",
        "docs/13-removal-before-delivery.md",
        "docs/14-development.md",
        "docs/15-reference.md",
        "docs/16-file-architecture.md",
        AI_CONTRACT,
    ]
    paths.extend(documentation)
    return list(dict.fromkeys(paths))


def _check_required_paths(expected: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for relative in expected:
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")
    return errors


def _check_json_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.json")):
        if ".levelupdiag" in path.parts:
            continue
        try:
            _read_json(path)
        except (OSError, json.JSONDecodeError, UnicodeError) as exc:
            errors.append(f"invalid JSON: {path.relative_to(ROOT)}: {exc}")
    return errors


def _check_manifest() -> list[str]:
    errors: list[str] = []
    try:
        raw = _read_json(ROOT / MANIFEST_FILE)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        return [f"unable to read manifest: {exc}"]
    if not isinstance(raw, dict):
        return ["manifest must be a JSON object"]

    errors.extend(f"manifest: {message}" for message in validate_manifest(raw))
    if errors:
        return errors

    try:
        levels = list_levels(ROOT)
    except (OSError, ValueError) as exc:
        return [f"manifest load failed: {exc}"]

    files_seen: set[str] = set()
    for level in levels:
        if level.file in files_seen:
            errors.append(f"duplicate level file in manifest: {level.file}")
        files_seen.add(level.file)
        if not level.file_path(ROOT).is_file():
            errors.append(f"manifest level file missing: {level.id} -> {level.file}")
    return errors


def _check_python_compilation() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".py", ".pyw"}:
            continue
        if ".levelupdiag" in path.parts:
            continue
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"python compile failed: {path.relative_to(ROOT)}: {exc}")
    return errors


def verify_repo() -> list[str]:
    errors: list[str] = []
    try:
        expected = _expected_paths()
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError) as exc:
        return [f"architecture contract unreadable: {exc}"]

    errors.extend(_check_required_paths(expected))
    errors.extend(_check_json_files())
    errors.extend(_check_manifest())
    errors.extend(_check_python_compilation())
    return errors


def main() -> int:
    errors = verify_repo()
    if errors:
        print(f"LevelUpDiag-Koali repository verification: FAIL ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1

    print("LevelUpDiag-Koali repository verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
