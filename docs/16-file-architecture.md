# File Architecture

## Statut

Ce document fixe l'architecture de fichiers de la reconstruction propre de **LevelUpDiag-Koali**.

Il est normatif pour la structure du dépôt.

Il complète les autres documents sans redéfinir leur comportement fonctionnel. En cas de doute sur l'emplacement d'un fichier ou la création d'un nouveau fichier, ce document prévaut sur les exemples plus anciens.

L'architecture est verrouillée **documentairement** : aucun mécanisme de lockfile, de hash ou de validation par empreinte n'est utilisé.

## Règle principale

Un fichier source versionné ne doit être créé que s'il appartient à l'arborescence définie ici.

Un nouveau fichier, répertoire racine ou sous-système non prévu nécessite une décision explicite et une mise à jour de ce document avant composition.

Les fichiers runtime sous `.levelupdiag/` sont générés localement et ne font pas partie de l'architecture source versionnée.

## Arborescence finale

```text
LevelUpDiag-Koali/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
│
├── levelupdiag.config.example.json
├── levelupdiag_manifest.json
│
├── levelupdiag_wrapper.pyw
├── levelupdiag_wrapper_common.py
├── START_LEVELUPDIAG.bat
│
├── levelupdiag_core/
│   ├── __init__.py
│   ├── config.py
│   ├── manifest.py
│   ├── models.py
│   ├── planner.py
│   ├── commands.py
│   ├── runner.py
│   ├── verdicts.py
│   ├── reports.py
│   ├── logs.py
│   └── artifacts.py
│
├── levels/
│   ├── N00_control_panel.pyw
│   ├── N01_environment.pyw
│   ├── N02_repository.pyw
│   ├── N03_documentation.pyw
│   ├── N04_contracts.pyw
│   ├── N05_components.pyw
│   ├── N06_integrations.pyw
│   ├── N07_profiles.pyw
│   ├── N08_security.pyw
│   ├── N09_offline.pyw
│   ├── N10_system.pyw
│   └── N11_delivery.pyw
│
├── launchers/
│   ├── N00-control-panel.bat
│   ├── N01-environment.bat
│   ├── N02-repository.bat
│   ├── N03-documentation.bat
│   ├── N04-contracts.bat
│   ├── N05-components.bat
│   ├── N06-integrations.bat
│   ├── N07-profiles.bat
│   ├── N08-security.bat
│   ├── N09-offline.bat
│   ├── N10-system.bat
│   ├── N11-delivery.bat
│   └── run_level.bat
│
├── scripts/
│   ├── print_manifest.py
│   ├── run_level.py
│   └── verify_repo.py
│
├── schemas/
│   └── levelupdiag.result.schema.json
│
├── tests/
│   ├── test_config.py
│   ├── test_manifest.py
│   ├── test_planner.py
│   ├── test_commands.py
│   ├── test_runner.py
│   ├── test_reports.py
│   ├── test_logs.py
│   └── test_delivery_level.py
│
└── docs/
    ├── README.md
    ├── 01-overview.md
    ├── 02-architecture.md
    ├── 03-levels-and-checks.md
    ├── 04-configuration.md
    ├── 05-execution-and-ordering.md
    ├── 06-results-and-logs.md
    ├── 07-koa-linux-integration.md
    ├── 08-campaigns.md
    ├── 09-failure-and-blocking-model.md
    ├── 10-security.md
    ├── 11-cli-and-gui.md
    ├── 12-testing.md
    ├── 13-removal-before-delivery.md
    ├── 14-development.md
    ├── 15-reference.md
    ├── 16-file-architecture.md
    └── AI_COMPOSER_CONTRACT.json
```

## Racine du dépôt

### `.gitignore`

Contient uniquement les exclusions nécessaires au dépôt et aux sorties locales.

Doit au minimum exclure :

```text
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.levelupdiag/
*.log
*.tmp
```

### `README.md`

Point d'entrée humain.

Ne contient pas la spécification détaillée de l'architecture interne.

### `CHANGELOG.md`

Historique des changements fonctionnels, structurels et documentaires.

### `CONTRIBUTING.md`

Règles de contribution et définition minimale d'une modification acceptable.

### `SECURITY.md`

Règles de sécurité propres à l'appendice.

### `pyproject.toml`

Déclare le projet Python, la version de Python supportée et les dépendances de développement éventuelles.

Le runtime du core doit rester basé sur la bibliothèque standard Python sauf décision explicite contraire.

### `levelupdiag.config.example.json`

Configuration exemple versionnée.

Aucune valeur propre à une machine ou secret réel.

### `levelupdiag_manifest.json`

Inventaire canonique des niveaux.

Il est l'unique source versionnée pour :

- identifiant du niveau ;
- nom ;
- fichier ;
- activation ;
- caractère requis ou optionnel ;
- dépendances ;
- timeout ;
- métadonnées nécessaires au runner.

Les niveaux ne doivent pas être découverts implicitement par scan du dossier.

### `levelupdiag_wrapper.pyw`

Application Tkinter principale.

Elle fournit la vue et délègue la logique au core.

### `levelupdiag_wrapper_common.py`

Helpers exclusivement liés au wrapper et au lancement graphique.

Toute logique réutilisable par la CLI appartient au core, pas à ce fichier.

### `START_LEVELUPDIAG.bat`

Point d'entrée Windows pratique vers le wrapper principal.

Il ne contient aucune logique de validation.

## `levelupdiag_core/`

Le core est fermé à **11 modules** dans la version cible.

Aucun sous-package supplémentaire n'est prévu.

### `__init__.py`

Exports publics stables du core.

### `config.py`

Propriétaire de :

- chargement de configuration ;
- fusion example/local ;
- résolution des chemins ;
- environnement explicitement ajouté.

Ne lance aucun check.

### `manifest.py`

Propriétaire de :

- lecture du manifeste ;
- `LevelInfo` ou construction équivalente ;
- normalisation d'identifiants ;
- lookup des niveaux.

Ne planifie pas l'exécution.

### `models.py`

Contient uniquement les structures de données partagées :

- `Finding` ;
- `Artifact` ;
- `StepResult` ;
- `LevelResult` ;
- `CampaignResult`.

Pas d'I/O, subprocess ou Tkinter.

### `planner.py`

Propriétaire de :

- sélection ;
- ordre ;
- dépendances ;
- détection de cycles ;
- blocage par dépendance.

Le plan reste déterministe et séquentiel par défaut.

### `commands.py`

Propriétaire de l'exécution de processus externes.

Il capture :

- commande ;
- cwd ;
- code de sortie ;
- timestamps ;
- durée ;
- sortie utile ;
- timeout ou erreur de lancement.

Le chemin normal d'exécution n'utilise pas `shell=True`.

### `runner.py`

Orchestrateur principal.

Il :

- utilise `planner.py` ;
- lance les levels ;
- transmet la configuration ;
- applique les dépendances ;
- agrège une campagne ;
- délègue les logs et rapports aux modules propriétaires.

Il ne contient aucune logique spécifique à N03, N04, N05, etc.

### `verdicts.py`

Source unique des verdicts :

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

Contient uniquement constantes et helpers d'agrégation/normalisation.

### `reports.py`

Lecture et écriture des résultats structurés.

Il n'exécute pas de commande.

### `logs.py`

Organisation et écriture des logs locaux.

Écrit uniquement dans les répertoires runtime configurés.

### `artifacts.py`

Helpers de chemins d'artefacts, noms sûrs et ouverture locale de dossiers/fichiers.

Il n'interprète pas le contenu d'un artefact comme code.

## `levels/`

Le dossier contient exactement les niveaux définis dans la taxonomie cible.

Chaque fichier est mince et spécifique à sa responsabilité.

Un level :

- charge la configuration ;
- vérifie ses prérequis locaux ;
- appelle les helpers du core ;
- lance au besoin une commande publique ;
- produit un `LevelResult` ;
- ne lance jamais directement un autre level.

### Taxonomie fixée

| ID | Fichier | Responsabilité |
|---|---|---|
| N00 | `N00_control_panel.pyw` | self-check léger / contrôle de l'appendice |
| N01 | `N01_environment.pyw` | environnement, Python, chemins et outils |
| N02 | `N02_repository.pyw` | checkout cible et état de dépôt observable |
| N03 | `N03_documentation.pyw` | validation documentaire publique |
| N04 | `N04_contracts.pyw` | validation des contrats |
| N05 | `N05_components.pyw` | validations des composants |
| N06 | `N06_integrations.pyw` | validations des intégrations disponibles |
| N07 | `N07_profiles.pyw` | validations des profils disponibles |
| N08 | `N08_security.pyw` | validations sécurité publiques |
| N09 | `N09_offline.pyw` | validations offline |
| N10 | `N10_system.pyw` | validations système |
| N11 | `N11_delivery.pyw` | absence de l'appendice dans la livraison |

Cette taxonomie ne doit pas être élargie, réduite ou renumérotée sans modification explicite de l'architecture.

## `launchers/`

Les launchers sont des wrappers Windows extrêmement minces.

Chaque launcher appelle `scripts/run_level.py` avec l'identifiant correspondant.

Exemple conceptuel :

```bat
@echo off
py "%~dp0..\scripts\run_level.py" N04 --windowed
```

Ils ne contiennent aucune logique de check, configuration ou verdict.

`run_level.bat` offre l'accès générique au lanceur CLI.

## `scripts/`

### `print_manifest.py`

Affiche le manifeste de manière lisible.

Pas de logique de validation.

### `run_level.py`

Entrée CLI canonique pour :

- lister les levels ;
- lancer un level ;
- lancer tous les levels activés ;
- lancer une campagne simple.

La GUI et les launchers doivent converger vers les mêmes fonctions core.

### `verify_repo.py`

Vérifie la cohérence structurelle de **LevelUpDiag-Koali lui-même** :

- fichiers obligatoires ;
- JSON lisible ;
- manifeste cohérent ;
- fichiers de levels présents ;
- imports/compilation Python ;
- dépendances de levels valides.

Il ne devient pas un validateur général de kOA-Linux.

## `schemas/`

La version cible contient un seul schéma :

```text
levelupdiag.result.schema.json
```

Il définit le rapport d'un level.

Aucun registre ou système complexe de schémas n'est prévu.

## `tests/`

La suite reste plate et directement mappée sur le core.

| Test | Couvre |
|---|---|
| `test_config.py` | configuration |
| `test_manifest.py` | manifeste et LevelInfo |
| `test_planner.py` | ordre et dépendances |
| `test_commands.py` | subprocess, timeout, erreurs |
| `test_runner.py` | orchestration et campagnes |
| `test_reports.py` | sérialisation |
| `test_logs.py` | layout et écriture des logs |
| `test_delivery_level.py` | N11 et détection des résidus |

Ne pas créer un arbre de tests par framework tant que ces huit fichiers restent suffisants.

## `docs/`

La documentation est adjacente au code et ne doit pas générer une seconde hiérarchie de gouvernance.

`AI_COMPOSER_CONTRACT.json` est le complément machine-readable destiné aux IA de composition.

`16-file-architecture.md` est la référence humaine canonique pour les chemins.

## Runtime local non versionné

Le runtime local est limité à :

```text
.levelupdiag/
├── diagnostics/
│   └── <level>/
│       └── <run>/
│           ├── result.json
│           └── output.log
├── runs/
│   └── <campaign>/
│       ├── summary.json
│       └── summary.txt
└── latest/
```

Des fichiers temporaires internes peuvent exister pendant une écriture, mais ils ne deviennent pas des formats publics.

`.levelupdiag/` :

- est ignoré par Git ;
- n'est pas une source d'autorité ;
- peut être supprimé sans affecter le code ;
- n'est jamais inclus dans une livraison kOA-Linux.

## Répertoires interdits sans décision explicite

Ne pas créer spontanément :

```text
src/
app/
api/
server/
services/
plugins/
workers/
agents/
database/
migrations/
state/
cache/
vendor/
generated/
dist/
build/
packages/
policies/
catalogs/
adapters/
workflows/
```

Cette interdiction concerne l'architecture source LevelUpDiag-Koali. Un outil externe peut évidemment produire temporairement `build/` ou `dist/`, mais ces répertoires ne deviennent pas des composants du design sans décision explicite.

## Fichiers et concepts explicitement hors architecture cible

La reconstruction propre n'emporte pas les éléments historiques suivants :

```text
.smartignore
GitSink.bat
levelupdiag_core/http.py
```

Les anciennes taxonomies orientées frontend/backend/Playwright/UX ne sont pas reconduites.

Aucun fichier de validation par hash, inventaire d'empreintes ou lockfile d'architecture ne doit être ajouté.

## Propriété des responsabilités

Chaque responsabilité a un propriétaire unique :

| Responsabilité | Propriétaire |
|---|---|
| configuration | `levelupdiag_core/config.py` |
| inventaire des levels | `levelupdiag_manifest.json` + `manifest.py` |
| modèles | `models.py` |
| ordre/dépendances | `planner.py` |
| subprocess | `commands.py` |
| orchestration | `runner.py` |
| verdicts | `verdicts.py` |
| sérialisation | `reports.py` |
| logs | `logs.py` |
| artefacts | `artifacts.py` |
| interface graphique | `levelupdiag_wrapper*.py*` |
| CLI | `scripts/run_level.py` |
| vérification du dépôt appendice | `scripts/verify_repo.py` |
| logique spécifique d'un check | `levels/Nxx_*.pyw` |

Dupliquer une responsabilité entre deux propriétaires est une dérive architecturale.

## Règles de dépendances internes

Dépendances admises :

```text
wrapper ───────→ core
scripts ───────→ core
levels ────────→ core
runner ────────→ planner
runner ────────→ commands
runner ────────→ reports
runner ────────→ logs
core modules ──→ models/verdicts/config selon besoin
```

Dépendances interdites :

```text
core → wrapper
core → level spécifique
level → autre level
kOA-Linux → LevelUpDiag-Koali
reports → subprocess
models → I/O
verdicts → I/O
```

## Règle de création de fichier

Une IA ou un développeur ne doit pas résoudre un problème en créant un nouveau module par défaut.

Ordre de décision :

1. la responsabilité appartient-elle à un fichier existant ?
2. peut-elle être ajoutée sans casser sa cohésion ?
3. est-ce une logique spécifique à un level ?
4. est-ce réellement une nouvelle responsabilité durable ?

Seulement le quatrième cas peut justifier une évolution de l'architecture.

Avant création, le changement doit mettre à jour :

```text
docs/16-file-architecture.md
docs/AI_COMPOSER_CONTRACT.json
docs/README.md si la navigation documentaire change
```

## Règle de renommage

Les chemins suivants sont des interfaces stables du dépôt :

```text
levelupdiag_manifest.json
levelupdiag.config.example.json
levelupdiag_wrapper.pyw
levelupdiag_wrapper_common.py
START_LEVELUPDIAG.bat
levelupdiag_core/
levels/
launchers/
scripts/
schemas/
tests/
docs/
```

Ils ne doivent pas être renommés dans une reconstruction ou un refactor ordinaire.

## Règle de suppression

Un fichier de l'arborescence finale peut être supprimé uniquement si :

1. sa responsabilité disparaît réellement ;
2. aucune autre documentation ne l'exige ;
3. le manifeste et les imports sont adaptés ;
4. ce document est modifié dans la même évolution.

## Critère de conformité structurelle

Une reconstruction propre est structurellement conforme lorsque :

- tous les fichiers obligatoires de l'arborescence finale existent ;
- aucun fichier historique explicitement retiré n'est repris ;
- aucun nouveau sous-système non prévu n'a été ajouté ;
- chaque level déclaré possède exactement son fichier attendu ;
- les responsabilités restent dans leurs modules propriétaires ;
- `.levelupdiag/` reste local et non versionné ;
- LevelUpDiag-Koali reste indépendant du code runtime de kOA-Linux.

La conformité structurelle repose sur les chemins et contrats documentés, pas sur des empreintes de fichiers.
