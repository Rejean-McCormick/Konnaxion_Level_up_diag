# LevelUpDiag Configuration Reference

Default local configuration file:

```text
levelupdiag.config.local.json
```

Default version-controlled template:

```text
levelupdiag.config.example.json
```

This document describes the starting configuration model. A customized suite may add, remove, rename, or replace fields.

## Configuration principles

- Local machine values belong in the local configuration.
- The example file should remain safe to commit.
- Secrets must not be stored in the example file.
- Levels should read configuration through the shared loader rather than parsing unrelated files independently.
- Application-specific configuration is expected and may differ between copies.
- Unknown or unsupported required fields should fail clearly.
- Paths should be resolved consistently and validated before use.

## Core fields

### `schema`

Configuration schema identifier.

```json
{
  "schema": "levelupdiag.config.v1"
}
```

### `app_name`

Name of the target application displayed in reports and the wrapper.

```json
{
  "app_name": "MyApp"
}
```

### `target_repo_root`

Root directory of the target application.

```json
{
  "target_repo_root": "C:/mycode/MyApp"
}
```

The path may be absolute or resolved according to the customized suite's policy.

### `control_dir`

Generated local control directory.

```json
{
  "control_dir": ".levelupdiag"
}
```

### `artifacts_dir`

Directory used for reports and diagnostic artifacts.

```json
{
  "artifacts_dir": ".levelupdiag/diagnostics"
}
```

The suite should define whether this path is resolved relative to the target repository, diagnostics repository, or another configured root.

## Toolchain

The `toolchain` section declares executables or capabilities used by levels.

```json
{
  "toolchain": {
    "required": [
      "python"
    ],
    "optional": [
      "git"
    ]
  }
}
```

A customized suite may use richer entries:

```json
{
  "toolchain": {
    "required": [
      {
        "id": "python",
        "command": "python",
        "version_args": ["--version"]
      }
    ]
  }
}
```

The exact format is suite-owned.

## Commands

The `commands` object stores local commands used by levels or the control panel.

Generic example:

```json
{
  "commands": {
    "install": "",
    "lint": "",
    "typecheck": "",
    "test": "python -m pytest",
    "build": "",
    "start": "",
    "stop": ""
  }
}
```

Desktop or CLI application example:

```json
{
  "commands": {
    "cli_help": "python -m myapp --help",
    "gui_start": "python -m myapp.gui",
    "test": "python -m pytest",
    "compile": "python -m compileall src tests"
  }
}
```

Web application example:

```json
{
  "commands": {
    "backend_start": "python -m myapp.api",
    "frontend_start": "pnpm -C frontend dev",
    "lint": "pnpm -C frontend lint",
    "typecheck": "pnpm -C frontend typecheck",
    "test": "python -m pytest",
    "build": "pnpm -C frontend build"
  }
}
```

Command names are not universal. Keep only those used by the customized suite.

## Application surfaces

A suite may define any application-specific sections it needs.

### HTTP example

```json
{
  "http": {
    "base_urls": {
      "backend": "http://127.0.0.1:8000",
      "frontend": "http://localhost:5173"
    },
    "health_paths": ["/health", "/readyz"],
    "openapi_paths": ["/openapi.json"],
    "critical_routes": ["/", "/dashboard"]
  }
}
```

### Desktop GUI example

```json
{
  "gui": {
    "enabled": true,
    "startup_command": "python -m myapp.gui",
    "startup_timeout_ms": 15000,
    "critical_flows": [
      "open_project",
      "run_validation",
      "inspect_report"
    ]
  }
}
```

### CLI example

```json
{
  "cli": {
    "entrypoint": "python -m myapp",
    "commands": [
      ["--help"],
      ["check"],
      ["validate", "--mode", "quick"]
    ]
  }
}
```

### External toolchain example

```json
{
  "external_tools": {
    "compiler": {
      "command": "mycompiler",
      "version_args": ["--version"]
    }
  }
}
```

These sections are examples only.

## Budgets

Optional execution or performance limits:

```json
{
  "budgets": {
    "command_timeout_ms": 30000,
    "startup_timeout_ms": 15000,
    "api_latency_ms": 1000,
    "page_load_ms": 3000
  }
}
```

Define units explicitly in field names or documentation.

## Security

Example security settings:

```json
{
  "security": {
    "forbidden_log_patterns": [
      "password=",
      "secret=",
      "api_key="
    ],
    "protected_paths": [],
    "allow_destructive_checks": false
  }
}
```

Security configuration must not itself contain real secrets.

## Environment values

Optional environment variables passed to commands:

```json
{
  "env": {
    "MYAPP_ENV": "diagnostic"
  }
}
```

The suite should define whether values replace or extend the inherited process environment.

## Complete starting example

```json
{
  "schema": "levelupdiag.config.v1",
  "app_name": "MyApp",
  "target_repo_root": "C:/mycode/MyApp",
  "control_dir": ".levelupdiag",
  "artifacts_dir": ".levelupdiag/diagnostics",
  "toolchain": {
    "required": ["python"],
    "optional": ["git"]
  },
  "commands": {
    "test": "python -m pytest",
    "compile": "python -m compileall src tests"
  },
  "budgets": {
    "command_timeout_ms": 30000
  },
  "security": {
    "forbidden_log_patterns": [
      "password=",
      "secret=",
      "api_key="
    ],
    "allow_destructive_checks": false
  },
  "env": {}
}
```

## Environment overrides

The starting frame supports or may support environment overrides such as:

```text
LEVELUPDIAG_CONFIG
LEVELUPDIAG_TARGET_REPO_ROOT
LEVELUPDIAG_APP_NAME
LEVELUPDIAG_BACKEND_URL
LEVELUPDIAG_FRONTEND_URL
```

A customized suite should document the exact overrides it actually implements.

Recommended rules:

- environment overrides take precedence over file values;
- unsupported overrides are ignored or rejected consistently;
- secret values are redacted from logs;
- effective configuration is recorded without exposing secrets;
- local overrides do not silently change release policy.

## Validation

Configuration validation should distinguish:

- missing local configuration;
- invalid JSON;
- unsupported schema version;
- missing required field;
- invalid path;
- unavailable required tool;
- invalid command definition;
- unsafe value;
- environment override conflict.

Configuration problems should normally produce `CONFIG_ERROR`, not a generic runtime failure.
