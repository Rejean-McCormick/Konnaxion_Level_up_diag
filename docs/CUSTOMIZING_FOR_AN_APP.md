# Customizing LevelUpDiag for an Application

This guide describes the recommended copy-and-customize workflow.

There is no profile system. The copied repository itself becomes the application-specific diagnostics suite.

## Step 1 — Duplicate the frame

Copy or clone the LevelUpDiag repository into a new dedicated repository.

Example:

```text
C:\mycode\MyApp\MyApp_LevelUpDiag
```

Recommended repository naming patterns include:

```text
MyApp-LevelUpDiag
MyApp-Diagnostics
levelupdiag-myapp
```

Choose one name and use it consistently in the manifest, reports, documentation, and launchers.

## Step 2 — Record the new suite identity

Update the manifest and documentation with:

- suite name;
- target application name;
- suite version;
- optional source frame version;
- report schema version;
- local control directory;
- level registry.

Example:

```json
{
  "schema": "levelupdiag.manifest.v1",
  "suite_name": "MyApp Diagnostics",
  "version": "1.0.0",
  "repository_mode": "standalone-diagnostics-suite",
  "config_file": "levelupdiag.config.local.json",
  "config_example_file": "levelupdiag.config.example.json",
  "control_dir_default": ".levelupdiag",
  "levels": []
}
```

## Step 3 — Define the application shape

Before editing levels, identify the target application's actual surfaces.

Possible surfaces include:

- Python package imports;
- command-line commands;
- desktop GUI workflows;
- background services;
- HTTP APIs;
- databases;
- files and generated artifacts;
- compiler or language toolchains;
- external executables;
- sandbox scenarios;
- deployment or packaging outputs.

Do not retain backend, frontend, browser, route, or OpenAPI assumptions unless the target application actually uses them.

## Step 4 — Replace the local configuration

Edit:

```text
levelupdiag.config.local.json
```

Also update the sanitized template:

```text
levelupdiag.config.example.json
```

At minimum, define:

- `app_name`;
- `target_repo_root`;
- `control_dir`;
- `artifacts_dir`;
- required tools;
- optional tools;
- application commands;
- environment overrides.

Add, remove, or rename configuration sections to match the suite.

Do not commit secrets, credentials, personal paths, or machine-specific tokens to the example file.

## Step 5 — Redesign the level map

Review every existing level and classify it as one of:

```text
KEEP
MODIFY
RENAME
MERGE
SPLIT
REMOVE
ADD
```

The number and meaning of the original levels are not mandatory.

A compact suite might use:

```text
N00  Control Panel
N01  Environment
N02  Repository Integrity
N03  Public Contracts
N04  Internal Test Suite
N05  Runtime and Resilience
N06  Real-World Sandbox
N07  Release Gate
```

A web application, desktop application, compiler, or data pipeline may require a completely different map.

## Step 6 — Update the manifest

For every level, define:

- stable level identifier;
- display name;
- level file;
- purpose;
- category;
- required capabilities;
- release-blocking status.

Example:

```json
{
  "id": "N03",
  "name": "Public Contracts",
  "file": "levels/03-public_contracts.pyw",
  "blocking_for_release": true,
  "purpose": "Validate public commands, schemas, imports, and stable interfaces.",
  "category": "contracts"
}
```

Remove obsolete fields and add application-specific metadata when needed.

## Step 7 — Implement the levels

Each required level should perform real checks.

A required level must not remain a placeholder that returns only `SKIP` or `PARTIAL`.

Use stable finding identifiers:

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

Keep evidence concise but reproducible.

## Step 8 — Update the shared core when appropriate

Application-specific customization is not limited to `levels/`.

Modify `levelupdiag_core/` when the suite needs different:

- configuration models;
- execution semantics;
- artifact handling;
- report models;
- verdict aggregation;
- process controls;
- campaign tracking;
- release policy support.

Keep generic helpers generic. Application-specific behavior can remain local to the customized copy without being forced into an abstraction.

## Step 9 — Update scripts and launchers

Review:

```text
scripts/run_level.py
scripts/verify_repo.py
launchers/
START_LEVELUPDIAG.bat
```

The repository verifier should check more than file existence. Recommended checks include:

- manifest parsing;
- unique and ordered level identifiers;
- existence of every level file;
- compilation of `.py` and `.pyw` files;
- manifest-to-level identifier consistency;
- launcher-to-level consistency;
- configuration parsing;
- report schema validity;
- detection of required placeholder levels;
- release-gate completeness rules.

## Step 10 — Define report and campaign behavior

Decide:

- where reports are written;
- how one execution campaign is identified;
- which metadata is required;
- how report freshness is established;
- how artifacts are referenced;
- how partial or interrupted executions are represented;
- which verdicts block release.

Reports from unrelated or historical campaigns should not be silently aggregated into the current release decision.

## Step 11 — Implement the release gate

The release gate should verify positive evidence of completeness.

Recommended minimum rules:

1. the expected campaign exists;
2. every required level produced a readable report;
3. every report belongs to that campaign;
4. report schemas are supported;
5. required artifacts exist;
6. no blocking verdict is present;
7. required `SKIP`, `BLOCKED`, or `PARTIAL` results are rejected;
8. application-specific release criteria pass.

Absence of a failure report is not sufficient evidence of success.

## Step 12 — Verify the customized repository

List the levels:

```bash
python scripts/run_level.py --list
```

Run repository verification:

```bash
python scripts/verify_repo.py
```

Run selected levels:

```bash
python scripts/run_level.py N01 --wait
python scripts/run_level.py N02 --wait
python scripts/run_level.py N03 --wait
```

Run the complete required campaign using the suite's own documented command or launcher.

## Step 13 — Document local decisions

Update:

```text
README.md
docs/FRAME_CUSTOMIZATION_MODEL.md
docs/CONFIG_REFERENCE.md
docs/LEVEL_CONTRACT.md
```

Also document:

- required tools;
- supported platforms;
- destructive operations;
- sandbox requirements;
- artifact locations;
- known limitations;
- release-blocking levels;
- expected execution order.

## Step 14 — Evolve independently

After duplication, the customized repository may diverge.

Later changes from the original frame may be copied selectively. There is no requirement to merge every upstream change or preserve cross-suite compatibility.
