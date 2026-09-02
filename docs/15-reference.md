# Reference

## Fichiers principaux

| Fichier | Rôle |
|---|---|
| `levelupdiag_manifest.json` | Inventaire et ordre des levels |
| `levelupdiag.config.example.json` | Modèle versionné de configuration |
| `levelupdiag.config.local.json` | Configuration locale |
| `levelupdiag_wrapper.pyw` | Interface graphique |
| `levelupdiag_wrapper_common.py` | Helpers du wrapper |
| `scripts/run_level.py` | Lanceur CLI |
| `scripts/print_manifest.py` | Affichage du manifeste |
| `scripts/verify_repo.py` | Vérification structurelle du dépôt |
| `levelupdiag_core/` | Helpers partagés |
| `.levelupdiag/` | État et diagnostics locaux |

## Verdicts

| Verdict | Signification |
|---|---|
| `PASS` | condition satisfaite |
| `WARN` | anomalie non bloquante |
| `FAIL` | cible testée, condition non satisfaite |
| `SKIP` | exécution volontairement omise |
| `BLOCKED` | prérequis manquant |
| `PARTIAL` | résultat incomplet |
| `ERROR` | erreur du level |
| `INFRA_ERROR` | problème d'environnement |
| `CONFIG_ERROR` | configuration invalide |

## Champs de configuration principaux

| Champ | Rôle |
|---|---|
| `schema` | version du format |
| `app_name` | nom de la cible |
| `target_repo_root` | racine du checkout cible |
| `control_dir` | état runtime LevelUpDiag |
| `artifacts_dir` | logs et diagnostics |
| `toolchain` | outils requis ou optionnels |
| `commands` | commandes partagées |
| `env` | variables explicitement ajoutées |

## Champs d'un level

Base recommandée :

```text
id
name
file
enabled
required
depends_on
timeout_seconds
```

## Résultat minimal

```text
schema
standard
standard_version
level
name
verdict
findings
artifacts
```

## Codes de sortie recommandés

Pour le runner :

| Code | Sens |
|---|---|
| `0` | lancement ou résultat réussi |
| `1` | résultat négatif du level |
| `2` | argument ou level inconnu |
| `3` | fichier ou prérequis principal manquant |
| `4` | configuration invalide |
| `5` | erreur interne du runner |

Les levels individuels peuvent avoir des codes internes différents si leur rapport JSON donne le verdict canonique.

## Layout des diagnostics

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

## Conventions de nommage

Levels :

```text
N00
N01
N02
```

Fichiers :

```text
N01_environment.pyw
N04_contracts.py
```

Dossiers diagnostics :

```text
N01-environment/
N04-contracts/
```
