# LevelUpDiag Level Contract

A level is an independently executable diagnostic unit, normally stored in:

```text
levels/
```

The starting frame uses `.pyw` files, but a customized suite may adopt another executable format when the runner and manifest support it.

## Required behavior

A level should:

1. identify itself with a stable level ID and display name;
2. load the central configuration through the shared configuration layer;
3. perform a focused set of checks;
4. produce structured findings;
5. generate a machine-readable report;
6. generate a human-readable report or equivalent summary;
7. preserve useful evidence;
8. avoid destructive behavior by default;
9. remain independently executable;
10. distinguish target failures from diagnostic-tool failures.

## Recommended module metadata

```python
LEVEL_ID = "N03"
LEVEL_NAME = "Public Contracts"
PURPOSE = "Validate public commands, schemas, imports, and interfaces."
```

The level ID and file registered in the manifest should agree with the module metadata.

## Standard entry point

The starting pattern is:

```python
from levelupdiag_core.level_runner import run_level_app

LEVEL_ID = "N03"
LEVEL_NAME = "Public Contracts"
PURPOSE = "Validate public commands, schemas, imports, and interfaces."


def run_checks(config, report, log):
    # Add focused checks here.
    ...


if __name__ == "__main__":
    run_level_app(
        LEVEL_ID,
        LEVEL_NAME,
        PURPOSE,
        run_checks,
    )
```

A customized suite may replace this entry point while preserving independently executable behavior.

## Finding contract

A finding should contain:

- a stable identifier;
- a verdict or severity;
- a category;
- a clear message;
- relevant evidence;
- an actionable recommendation when action is needed;
- optional file, command, route, endpoint, or artifact references;
- optional structured data.

Example:

```python
report.add(
    "repository.python.compile",
    PASS,
    "static_integrity",
    "Python sources compile successfully",
    evidence="python -m compileall completed with exit code 0",
    recommendation="No action required.",
)
```

Example failure:

```python
report.add(
    "cli.import.failed",
    FAIL,
    "contracts",
    "The canonical CLI module could not be imported",
    file="src/myapp/cli/main.py",
    evidence="ImportError: cannot import name 'EXIT_USAGE_OR_CONFIG'",
    recommendation="Restore consistency between the CLI entry point and exit-code module.",
)
```

## Finding identifiers

Finding IDs should be:

- stable across runs;
- lowercase;
- dot-separated;
- specific enough for filtering and regression comparison;
- independent from volatile wording.

Recommended pattern:

```text
<domain>.<subject>.<check>
```

Examples:

```text
environment.python.available
repository.manifest.valid
cli.help.exit_code
runtime.startup.smoke
release.required_levels.complete
```

Do not embed timestamps, temporary paths, or random IDs in the finding identifier.

## Verdict vocabulary

| Verdict | Meaning | Typical release effect |
|---|---|---|
| `PASS` | The check completed successfully | Accepted |
| `WARN` | A non-blocking issue or risk was found | Policy-dependent |
| `FAIL` | A required condition failed | Blocking |
| `SKIP` | The check was intentionally not executed | Policy-dependent; blocking when required |
| `BLOCKED` | A prerequisite prevented execution | Usually blocking when required |
| `PARTIAL` | The check produced incomplete but useful evidence | Policy-dependent; normally not equivalent to pass |
| `ERROR` | The level or check failed internally | Blocking |
| `INFRA_ERROR` | Required infrastructure was unavailable | Blocking or retryable |
| `CONFIG_ERROR` | The diagnostics configuration was invalid | Blocking |

The final release effect is owned by the customized suite's policy.

## Evidence

Evidence should be sufficient to reproduce or understand the result.

Useful evidence includes:

- command and arguments;
- exit code;
- bounded stdout and stderr excerpts;
- executable version;
- resolved file path;
- file hash;
- schema validation errors;
- elapsed time;
- artifact path;
- expected and observed values.

Avoid:

- unbounded logs in the finding message;
- secrets or credentials;
- unstable wording as the only evidence;
- claiming success without recording what was checked.

Large evidence should be written as an artifact and referenced by the finding.

## Reports

A level report should identify at least:

```text
schema
standard
standard_version
level
name
started_at
finished_at
app_name
target_repo_root
verdict
summary
findings
artifacts
metadata
```

The exact schema is owned by the customized suite.

Reports should be written atomically when practical. A partially written report must not be mistaken for a completed successful report.

## Artifacts

A level may create or reference artifacts such as:

- logs;
- screenshots;
- command transcripts;
- schema validation output;
- test reports;
- coverage files;
- manifests;
- generated packages;
- sandbox results.

Each artifact should have:

- a type or kind;
- a path;
- an optional description;
- clear ownership;
- a relationship to the current execution campaign.

## Configuration access

Use the shared configuration layer:

```python
from levelupdiag_core.config import load_config

config = load_config()
```

or use the configuration object supplied by the level runner.

Do not hardcode machine-specific values such as:

- local repository paths;
- executable locations;
- ports or URLs;
- credentials;
- personal directories;
- artifact roots.

Intentional application invariants may remain in code when they are part of the diagnostic contract.

## Process execution

Commands should be executed through the shared command or process layer when available.

A level should record:

- executable and arguments;
- working directory;
- relevant environment changes;
- timeout;
- exit code;
- termination reason;
- bounded stdout and stderr;
- produced artifacts.

Avoid shell execution unless it is required and explicitly controlled.

## Timeouts and cancellation

Potentially blocking operations should have a timeout.

A cancelled or timed-out operation should not be reported as `PASS`.

Use:

- `BLOCKED` when a prerequisite prevents the check;
- `INFRA_ERROR` when infrastructure is unavailable;
- `ERROR` when the level implementation fails;
- the suite's cancellation result when explicitly supported.

## Destructive operations

Destructive behavior includes:

- deleting target files;
- rewriting configuration;
- updating reviewed baselines;
- modifying databases;
- installing or uninstalling dependencies;
- terminating unrelated processes;
- publishing artifacts;
- changing source-controlled files.

Such operations should require:

1. explicit documentation;
2. an explicit configuration capability;
3. clear user confirmation or a dedicated non-interactive authorization flag;
4. evidence of what changed;
5. a safe rollback or recovery strategy when practical.

## Placeholder levels

A placeholder level may be useful during initial customization, but it must be visible.

A placeholder should produce `SKIP` or `PARTIAL` with a clear recommendation.

A level marked as required or release-blocking must not be accepted as complete while it remains a placeholder.

## Independent execution

A level should be runnable:

```bash
python scripts/run_level.py N03 --wait
```

and, when supported, directly:

```bash
python levels/03-public_contracts.pyw
```

Independent execution should produce the same diagnostic meaning as execution through the wrapper.

## Test requirements

Recommended tests for each level include:

- module compilation;
- manifest-to-module ID consistency;
- valid configuration path;
- missing prerequisite behavior;
- success finding;
- failure finding;
- exception handling;
- timeout handling;
- report serialization;
- artifact creation;
- no destructive effect by default.

## Release-gate interaction

A level should declare whether it is required for release.

The release gate should not infer completion from file existence alone. It should verify:

- the expected level report exists;
- the report is valid;
- it belongs to the intended campaign;
- the level completed;
- its verdict is acceptable under the release policy;
- required artifacts exist.

`SKIP`, `BLOCKED`, or `PARTIAL` must not be treated as `PASS` unless the local release policy explicitly allows that exact condition.
