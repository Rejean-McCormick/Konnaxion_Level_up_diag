# Results and logs

## Objectif

Chaque niveau doit produire un résultat compréhensible sans devoir relire toute sa sortie console.

Le système conserve néanmoins les logs détaillés pour le diagnostic.

## Verdicts

Les verdicts LevelUpDiag sont :

```text
PASS
WARN
FAIL
SKIP
BLOCKED
PARTIAL
ERROR
INFRA_ERROR
CONFIG_ERROR
```

Leur signification détaillée est décrite dans [09-failure-and-blocking-model.md](09-failure-and-blocking-model.md).

## Rapport minimal d'un level

```json
{
  "schema": "levelupdiag.report.v1",
  "standard": "LevelUpDiag",
  "standard_version": "1.0",
  "level": "N04",
  "name": "Contracts",
  "verdict": "PASS",
  "findings": [],
  "artifacts": []
}
```

## Extension Koali recommandée

Sans rendre le schéma lourd, un résultat peut ajouter :

```json
{
  "started_at": "2026-08-07T10:00:00-04:00",
  "ended_at": "2026-08-07T10:00:12-04:00",
  "duration_seconds": 12.0,
  "exit_code": 0,
  "command": "python ci/scripts/run-contracts.py",
  "cwd": "C:/mycode/kOA-Linux/koa-linux",
  "output_tail": "..."
}
```

## Findings

Un finding est une observation structurée.

Exemple :

```json
{
  "severity": "FAIL",
  "code": "COMMAND_FAILED",
  "message": "Le runner de contrats a retourné un code non nul.",
  "path": "ci/scripts/run-contracts.py"
}
```

Un finding doit expliquer :

- ce qui s'est passé ;
- où ;
- pourquoi cela compte ;
- quoi vérifier ensuite lorsque c'est pertinent.

## Logs

Les logs doivent être regroupés par level et par run.

Exemple :

```text
.levelupdiag/
└── diagnostics/
    └── N04-contracts/
        └── 20260807_100000/
            ├── result.json
            ├── output.log
            └── notes.txt
```

## output.log

`output.log` contient la sortie complète ou suffisamment complète du processus externe.

Le rapport principal peut conserver seulement un `output_tail` pour rester lisible.

## latest

Une projection pratique peut pointer vers le dernier résultat de chaque level :

```text
.levelupdiag/latest/N04/result.json
```

Elle ne remplace pas l'historique des runs.

## Rapport de campagne

Une campagne peut écrire :

```text
.levelupdiag/runs/<run-id>/summary.json
.levelupdiag/runs/<run-id>/summary.txt
```

Le résumé contient :

- cible ;
- heure de début et de fin ;
- levels attendus ;
- verdict de chaque level ;
- nombre de PASS/WARN/FAIL/BLOCKED/etc. ;
- chemins vers les logs.

## Principe

Les logs racontent le détail.

Le résultat raconte la conclusion.
