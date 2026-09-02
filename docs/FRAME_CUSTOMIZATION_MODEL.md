# LevelUpDiag Frame Customization Model

## Decision

LevelUpDiag is a general-purpose diagnostics frame intended to be copied into a dedicated repository and customized directly for one target application.

Each copy becomes an autonomous diagnostics suite.

The copy may change any part of the repository and may evolve independently. It is not required to load a profile, inherit from a central installation, preserve compatibility with other copies, or restrict application-specific logic to a single directory.

## What the frame provides

The initial repository provides reusable building blocks:

- an autonomous diagnostics repository;
- a central manifest;
- independently executable levels;
- a shared core for configuration, execution, reporting, and verdicts;
- a graphical wrapper;
- command-line scripts;
- optional per-level launchers;
- report and artifact schemas;
- a conventional local control directory.

These blocks are defaults, not permanent architectural constraints.

## What a customized copy may change

A customized suite may modify:

```text
levelupdiag_manifest.json
levelupdiag.config.local.json
levelupdiag.config.example.json
levelupdiag_wrapper.pyw
levelupdiag_wrapper_common.py
levelupdiag_core/
levels/
scripts/
launchers/
docs/
schemas/
```

It may also add or remove directories.

Typical changes include:

- renaming the suite and repository;
- replacing web-oriented assumptions with desktop, CLI, compiler, data, or service checks;
- reducing or increasing the number of levels;
- changing level identifiers and execution order;
- adding application-specific dependencies;
- changing configuration keys;
- replacing the release gate;
- changing report fields or schema versions;
- adding destructive maintenance operations behind explicit confirmation;
- replacing the wrapper or removing it entirely.

## Independence model

A customized copy:

- runs independently;
- owns its own versioning;
- owns its own release policy;
- owns its own compatibility decisions;
- may diverge permanently;
- may selectively import later generic fixes;
- does not depend on another LevelUpDiag repository at runtime.

## Stable concepts

Even when implementation details change, the following concepts are useful to preserve:

### Diagnostic level

A focused, independently executable unit of diagnosis.

### Finding

A structured result describing a condition, its severity, evidence, and recommended action.

### Artifact

A file or output produced or referenced by a diagnostic execution.

### Verdict

The summarized outcome of a check, level, or campaign.

### Campaign

A coherent execution of one or more levels whose reports are evaluated together.

### Release gate

A final decision process that verifies the completeness and acceptability of required evidence.

A copy may rename these concepts, but their separation helps prevent ambiguous reports and false release decisions.

## Process isolation

When practical, the wrapper should launch level files as separate processes instead of importing them directly.

Process isolation provides several advantages:

- one broken level does not necessarily break the wrapper;
- environment differences are easier to observe;
- exit codes remain meaningful;
- logs and reports can be isolated;
- levels remain independently executable.

A customized suite may replace this behavior when another execution model is more appropriate.

## Configuration rule

Machine-specific and target-specific values should normally come from configuration rather than hardcoded constants.

Examples include:

- target repository paths;
- executable paths;
- service URLs;
- start, build, test, and validation commands;
- critical routes or workflows;
- API endpoints;
- tool requirements;
- performance budgets;
- artifact directories;
- security patterns;
- environment variables.

Application invariants that are intentionally part of the suite may remain in code when that makes the contract clearer.

## Local control directory

The default generated directory is:

```text
.levelupdiag/
```

A customized suite may rename or relocate it.

Generated diagnostics should be separated from source-controlled files whenever practical.

## Recommended repository identity

A copied suite should clearly identify:

- the target application;
- the diagnostics suite name;
- the suite version;
- the source frame version, when useful;
- the report schema version;
- the release policy version, when independently versioned.

Example:

```json
{
  "suite_name": "MyApp LevelUpDiag",
  "target_application": "MyApp",
  "derived_from": "LevelUpDiag",
  "derived_from_version": "0.2.0",
  "suite_version": "1.0.0"
}
```

These fields document lineage only. They do not impose compatibility.

## Anti-patterns

Avoid treating the generic frame as though every target application must have:

- a backend;
- a frontend;
- an HTTP API;
- browser routes;
- Playwright;
- the same sixteen levels;
- the same release requirements;
- the same report schema forever.

Those are possible application choices, not universal requirements.

Also avoid:

- hiding application-specific assumptions in generic helpers;
- reporting release success from an incomplete campaign;
- treating `SKIP` as evidence that a required check passed;
- hardcoding local machine paths in committed levels;
- allowing destructive checks to run silently;
- coupling the diagnostics repository to the target application's importability.

## Result

The expected outcome is not one central framework serving many applications at runtime.

The expected outcome is a family of independent repositories that began from the same frame and were then customized for their own applications.
