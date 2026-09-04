# Konnaxion LevelUpDiag — Upgraded v3

This package upgrades the Konnaxion LevelUpDiag Mega Pack onto the evolved LevelUpDiag engine while preserving the Konnaxion-specific diagnostic domains and test order.

## Konnaxion target auto-detection

When `target_repo_root` is `auto`, LevelUpDiag supports both common layouts:

```text
<Konnaxion repo>/LevelUpDiag/
```

and the historical workspace layout:

```text
<workspace>/
├── LevelUpDiag/
└── Konnaxion/
    ├── frontend/
    └── backend/
```

It scores Konnaxion markers (`frontend`, `backend`, `package.json`, `manage.py`) and selects the correct target automatically.

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

## Console graphique de sélection

Le root inclut maintenant `LEVELUPDIAG_CONSOLE.pyw`. Sous Windows, un double-clic ouvre une console graphique inspirée du modèle fourni :

- sélection d'une campagne depuis le manifest ;
- sélection manuelle de niveaux N00..N11 ;
- presets Source audit, Auth debug, Connection debug et Full local ;
- sortie du diagnostic en direct ;
- arrêt du processus ;
- ouverture directe du dossier de preuves `.levelupdiag/current`.

La console lance le même moteur `levelupdiag.py`; elle ne duplique pas les tests.

## Nettoyage des alias historiques

Les anciens alias `MegaPack` ont été retirés du root et sont supprimés lors d'un upgrade après sauvegarde :

- `INSTALL_AND_CONFIGURE_KONNAXION_MEGAPACK.pyw`
- `CONFIGURE_KONNAXION_MEGAPACK.ps1`
- `INSTALL_MEGAPACK.ps1`

Les noms LevelUpDiag v3 sont désormais les seules entrées d'installation/configuration conservées.
