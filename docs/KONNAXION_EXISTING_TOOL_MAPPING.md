# Existing Konnaxion diagnostic surfaces mapped by the Mega Pack

The pack is designed around the current snapshots supplied on 2026-09-02.

## Konnaxion repository

- `frontend/tools/full-scan.ps1` -> N10 Deep Scan
- TypeScript / `tsc` -> N03 Frontend / Next
- ESLint -> N03
- Jest -> N03
- Next production build -> N03
- Playwright smoke -> N05 Runtime & Browser
- `frontend/scripts/scan-endpoints.mjs` -> N04 API Contracts
- `backend/django_api_scanner.py` -> N04
- Django `manage.py check` -> N02
- migration drift (`makemigrations --check --dry-run`) -> N02
- `backend/tests/test_smoke_platform.py` -> N02
- OpenAPI tests -> N04
- Celery task tests -> N06

## Capsule Manager repository

- `kx_agent/runtime/healthchecks.py` presence -> N08 Capsule Local
- `tests/test_security_gate.py` -> N07 Security & Auth
- `tests/test_instance_states.py` -> N08
- capsule SHA-256 -> N08
- `KX_Diagnose_Online.ps1` can be configured as `konnaxion.commands.remote_deep_diagnostic` -> N09

The pack does not deploy, restart, restore, mutate instances, or expose secrets.
