# Upgrade notes from Konnaxion Mega Pack v2

## Retained Konnaxion logic

The `konnaxion_diag/` domain implementation and N00..N11 taxonomy are retained. The upgraded package changes the LevelUpDiag engine around them rather than replacing the Konnaxion tests with generic diagnostics.

## Evidence retention

Historical LevelUpDiag runtime evidence is not migrated. On each campaign start, current-only retention removes generated directories from earlier/legacy runs under the configured `.levelupdiag` control directory. This is intentional: the diagnostic sequence and current evidence are the source of truth.

## Correlation change

N11 previously treated all N01..N10 as expected even for focused campaigns. N00 now records the active campaign and ordered expected levels. N11 reports missing evidence only for levels actually expected in that campaign.

## Compatibility

`scripts/run_konnaxion.py <campaign>` still works. New direct CLI usage is `python levelupdiag.py run <campaign>`.
