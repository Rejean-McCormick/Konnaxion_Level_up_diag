# Konnaxion LevelUpDiag — Upgraded v3

This package upgrades the Konnaxion LevelUpDiag Mega Pack onto the evolved LevelUpDiag engine while preserving the Konnaxion-specific diagnostic domains and test order.

## What is preserved

- Exact Konnaxion taxonomy N00..N11.
- Existing Django, Next, TypeScript, ESLint, Jest, OpenAPI, Playwright, Celery/Redis, Capsule Manager and deployed-runtime diagnostics.
- Static source audit: double `/api/api`, forbidden legacy namespaces, CSRF-risk and unmapped endpoint checks.
- `.venv` Python autodetection and `corepack pnpm` fallback.
- Remote diagnostics disabled by default and no destructive deployment/restart/restore operations.
- Original ordered campaigns.

## What is upgraded

- Process isolation: every level runs in its own Python process.
- Explicit sequential campaign execution. Konnaxion test order is never lost to parallel scheduling.
- Campaign/expected-level metadata propagated into N00 session state.
- N11 correlates only the levels expected by the active campaign.
- Current-only evidence retention: old LevelUpDiag `runs`, `logs`, `diagnostics`, `latest`, `current` and stale Konnaxion session evidence are purged at the start of a campaign.
- Bounded/redacted command output, `shell=False`, timeouts and progress heartbeat.
- Modern manifest/config schemas while accepting the previous local Konnaxion config schema during migration.

## Primary campaign

```powershell
python levelupdiag.py run connection-debug
```

Its exact sequence is:

```text
N00 -> N01 -> N02 -> N03 -> N04 -> N05 -> N06 -> N11
```

## Recommended escalation sequence

The existing Konnaxion workflow is preserved:

```text
source-audit -> auth-debug -> connection-debug -> full-local
```

Run it automatically with:

```powershell
python levelupdiag.py run-sequence recommended-debug
```

Each campaign still has its own N00 session and N11 final correlation.

## Configuration

If the `levelupdiag/` directory is copied directly into the Konnaxion repo, the default `target_repo_root: "auto"` diagnoses its parent. For a standalone LevelUpDiag checkout, run the configuration script or set `target_repo_root` in `levelupdiag.config.local.json`.

No application command is guessed outside the Konnaxion command defaults already encoded by this pack.

## Runtime evidence

Only current evidence is retained:

```text
<Konnaxion>/.levelupdiag/current/
<Konnaxion>/.levelupdiag/latest/
```

No historical run archive is maintained by default.
