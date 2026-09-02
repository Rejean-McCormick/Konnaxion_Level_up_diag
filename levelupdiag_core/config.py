"""Central configuration for LevelUpDiag-Koali.

The configuration module owns machine- and target-specific values.  It does
not execute checks or subprocesses.  A versioned example file provides the
base configuration and an optional local file overrides only the values that
need to differ on a developer machine.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

CONFIG_ENV = "LEVELUPDIAG_CONFIG"
ROOT_ENV = "LEVELUPDIAG_ROOT"
TARGET_ROOT_ENV = "LEVELUPDIAG_TARGET_REPO_ROOT"
APP_NAME_ENV = "LEVELUPDIAG_APP_NAME"

LOCAL_CONFIG = "levelupdiag.config.local.json"
EXAMPLE_CONFIG = "levelupdiag.config.example.json"
MANIFEST_FILE = "levelupdiag_manifest.json"
CONFIG_SCHEMA = "levelupdiag.koali.config.v1"

DEFAULT_COMMAND_KEYS = (
    "docs",
    "contracts",
    "components",
    "integrations",
    "profiles",
    "security",
    "offline",
    "system",
)


def detect_diag_root(start: Path | None = None) -> Path:
    """Return the LevelUpDiag-Koali repository root.

    Resolution is deterministic and intentionally does not require ``levels/``
    to exist because the clean reconstruction creates that directory in a
    later bundle.
    """

    explicit = os.environ.get(ROOT_ENV)
    if explicit:
        return Path(explicit).expanduser().resolve()

    current = (start or Path(__file__)).expanduser().resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / MANIFEST_FILE).is_file() or (
            candidate / EXAMPLE_CONFIG
        ).is_file():
            return candidate

    return Path(__file__).resolve().parents[1]


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Configuration must be a JSON object: {path}")
    return value


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        previous = result.get(key)
        if isinstance(previous, dict) and isinstance(value, Mapping):
            result[key] = _deep_merge(previous, value)
        else:
            result[key] = value
    return result


def _string_map(value: Any, *, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    out: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{field_name} keys and values must be strings")
        out[key] = item
    return out


def _toolchain(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ValueError("toolchain must be an object")
    result: dict[str, list[str]] = {}
    for key in ("required", "optional"):
        items = value.get(key, [])
        if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
            raise ValueError(f"toolchain.{key} must be a list of strings")
        result[key] = list(items)
    unknown = set(value) - {"required", "optional"}
    if unknown:
        names = ", ".join(sorted(str(x) for x in unknown))
        raise ValueError(f"Unsupported toolchain fields: {names}")
    return result


def _commands(value: Any) -> dict[str, str]:
    result = _string_map(value, field_name="commands")
    unknown = set(result) - set(DEFAULT_COMMAND_KEYS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Unsupported command keys: {names}")
    for key in DEFAULT_COMMAND_KEYS:
        result.setdefault(key, "")
    return result


@dataclass(slots=True)
class AppConfig:
    """Resolved configuration used by levels and runners."""

    diagnostics_repo_root: str
    schema: str = CONFIG_SCHEMA
    app_name: str = "kOA-Linux"
    target_repo_root: str = "."
    control_dir: str = ".levelupdiag"
    artifacts_dir: str = ".levelupdiag/diagnostics"
    toolchain: dict[str, list[str]] = field(
        default_factory=lambda: {"required": ["python"], "optional": ["git", "cargo"]}
    )
    commands: dict[str, str] = field(
        default_factory=lambda: {key: "" for key in DEFAULT_COMMAND_KEYS}
    )
    env_values: dict[str, str] = field(default_factory=dict)
    config_path: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def diagnostics_root_path(self) -> Path:
        return Path(self.diagnostics_repo_root).expanduser().resolve()

    @property
    def target_root_path(self) -> Path:
        path = Path(self.target_repo_root).expanduser()
        if not path.is_absolute():
            path = self.diagnostics_root_path / path
        return path.resolve()

    @property
    def control_root_path(self) -> Path:
        path = Path(self.control_dir).expanduser()
        if not path.is_absolute():
            path = self.diagnostics_root_path / path
        return path.resolve()

    @property
    def artifacts_root_path(self) -> Path:
        path = Path(self.artifacts_dir).expanduser()
        if not path.is_absolute():
            path = self.diagnostics_root_path / path
        return path.resolve()

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def command(self, name: str) -> str:
        if name not in DEFAULT_COMMAND_KEYS:
            raise KeyError(f"Unknown command key: {name}")
        return self.commands.get(name, "")

    def env(self) -> dict[str, str]:
        result = dict(os.environ)
        result.update(self.env_values)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "app_name": self.app_name,
            "target_repo_root": self.target_repo_root,
            "control_dir": self.control_dir,
            "artifacts_dir": self.artifacts_dir,
            "toolchain": {
                "required": list(self.toolchain.get("required", [])),
                "optional": list(self.toolchain.get("optional", [])),
            },
            "commands": {key: self.commands.get(key, "") for key in DEFAULT_COMMAND_KEYS},
            "env": dict(self.env_values),
        }


def _validate_config(raw: Mapping[str, Any]) -> None:
    schema = raw.get("schema")
    if schema != CONFIG_SCHEMA:
        raise ValueError(f"Unsupported configuration schema: {schema!r}")

    for field_name in (
        "app_name",
        "target_repo_root",
        "control_dir",
        "artifacts_dir",
    ):
        if not isinstance(raw.get(field_name), str) or not str(raw[field_name]).strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    _toolchain(raw.get("toolchain", {}))
    _commands(raw.get("commands", {}))
    _string_map(raw.get("env", {}), field_name="env")


def _config_path(diag_root: Path) -> Path:
    explicit = os.environ.get(CONFIG_ENV)
    if explicit:
        return Path(explicit).expanduser().resolve()
    local = diag_root / LOCAL_CONFIG
    return local if local.is_file() else diag_root / EXAMPLE_CONFIG


def load_config(path: Path | None = None, root: Path | None = None) -> AppConfig:
    """Load the example configuration and merge an optional local override."""

    diag_root = (root or detect_diag_root()).expanduser().resolve()
    example = diag_root / EXAMPLE_CONFIG
    if not example.is_file():
        raise FileNotFoundError(f"Missing versioned example configuration: {example}")

    base = _read_json_object(example)
    chosen = path.expanduser().resolve() if path is not None else _config_path(diag_root)
    override: dict[str, Any] = {}
    if chosen != example:
        if chosen.is_file():
            override = _read_json_object(chosen)
        elif path is not None or os.environ.get(CONFIG_ENV):
            raise FileNotFoundError(f"Configuration file does not exist: {chosen}")

    raw = _deep_merge(base, override)

    if os.environ.get(TARGET_ROOT_ENV):
        raw["target_repo_root"] = os.environ[TARGET_ROOT_ENV]
    if os.environ.get(APP_NAME_ENV):
        raw["app_name"] = os.environ[APP_NAME_ENV]

    _validate_config(raw)

    return AppConfig(
        diagnostics_repo_root=str(diag_root),
        schema=str(raw["schema"]),
        app_name=str(raw["app_name"]),
        target_repo_root=str(raw["target_repo_root"]),
        control_dir=str(raw["control_dir"]),
        artifacts_dir=str(raw["artifacts_dir"]),
        toolchain=_toolchain(raw["toolchain"]),
        commands=_commands(raw["commands"]),
        env_values=_string_map(raw["env"], field_name="env"),
        config_path=str(chosen),
        raw=dict(raw),
    )


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    """Write a local configuration explicitly requested by the caller."""

    chosen = (
        path.expanduser().resolve()
        if path is not None
        else config.diagnostics_root_path / LOCAL_CONFIG
    )
    chosen.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n"
    temporary = chosen.with_name(f".{chosen.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(chosen)
    config.config_path = str(chosen)
    return chosen
