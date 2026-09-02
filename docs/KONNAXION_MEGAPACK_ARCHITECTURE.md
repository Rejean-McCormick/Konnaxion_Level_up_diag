# Architecture — Konnaxion Mega Diagnostic Pack

## Taxonomie

| Niveau | Domaine | Rôle |
|---|---|---|
| N00 | Control & Discovery | session, cible, toolchain, surfaces |
| N01 | Repository & Static | forme repo, état Git |
| N02 | Backend / Django / DB | `manage.py check`, migrations, smoke backend |
| N03 | Frontend / Next | TypeScript, ESLint, Jest, build Next |
| N04 | API Contracts | scanners endpoints et OpenAPI |
| N05 | Runtime & Browser | HTTP local + Playwright smoke |
| N06 | Jobs / Redis / Celery | tests de tasks + probe runtime configurable |
| N07 | Security & Auth | Django deploy check + security gate Capsule Manager |
| N08 | Capsule Local | Manager, healthcheck engine, capsule hash |
| N09 | Deployed Runtime | DNS/HTTPS et deep diagnostic optionnel |
| N10 | Deep Scan | full-scan frontend + pytest complet backend |
| N11 | Correlation & Triage | corrélation uniquement sur la session courante |

## Dépendances

Tous les niveaux N01..N11 dépendent uniquement de N00. Cette forme est intentionnelle : une panne frontend ne doit pas empêcher la collecte backend, et inversement. N00 crée un `diagnostic_session_id`; N11 ignore les résultats `latest` qui n'appartiennent pas à cette session.

## Sécurité

- aucune opération de restart/deploy/restore ;
- aucun secret dans l'exemple ;
- redaction des tokens/mots de passe dans les sorties de commandes ;
- diagnostic distant désactivé par défaut ;
- deep remote diagnostic uniquement via une commande explicitement configurée ;
- exécution `shell=False` via le core LevelUpDiag.

## Pourquoi les outils restent dans leurs repos

Le pack ne recopie pas Jest, Playwright, Django, les tests métier ou les healthchecks Capsule Manager. Il appelle les surfaces natives et normalise leurs résultats en Findings LevelUpDiag. Les scripts purement diagnostiques existants peuvent rester là où ils sont ou migrer graduellement vers ce pack.
