# Configuration

## Fichiers

LevelUpDiag utilise deux fichiers complémentaires :

```text
levelupdiag.config.example.json
levelupdiag.config.local.json
```

Le fichier `example` est versionné et sert de modèle.

Le fichier `local` contient les valeurs propres à la machine et ne doit pas contenir d'informations destinées au dépôt.

## Principes

- les chemins locaux appartiennent à la configuration locale ;
- les secrets ne doivent pas être versionnés ;
- tous les levels passent par le loader partagé ;
- les chemins sont résolus de manière cohérente ;
- un champ requis inconnu ou invalide doit produire une erreur claire.

## Configuration cible Koali

La configuration peut être simplifiée par rapport au modèle web générique :

```json
{
  "schema": "levelupdiag.koali.config.v1",
  "app_name": "kOA-Linux",
  "target_repo_root": "C:/mycode/kOA-Linux/koa-linux",
  "control_dir": ".levelupdiag",
  "artifacts_dir": ".levelupdiag/diagnostics",
  "toolchain": {
    "required": ["python"],
    "optional": ["git", "cargo"]
  },
  "commands": {
    "docs": "python docs/tools/validate_docs.py",
    "contracts": "python ci/scripts/run-contracts.py",
    "components": "python ci/scripts/run-components.py",
    "security": "python ci/scripts/run-security.py",
    "offline": "python ci/scripts/run-offline.py",
    "system": "python ci/scripts/run-system-tests.py"
  },
  "env": {}
}
```

Les commandes absentes du checkout cible ne doivent pas être inventées par la configuration.

## target_repo_root

La racine de kOA-Linux est une donnée centrale.

Le runner doit vérifier qu'elle existe avant de lancer des checks liés à la cible.

## control_dir

Le dossier de contrôle local contient l'état produit par LevelUpDiag-Koali.

Valeur recommandée :

```text
.levelupdiag
```

## artifacts_dir

Dossier des diagnostics et logs.

Valeur recommandée :

```text
.levelupdiag/diagnostics
```

## Toolchain

Les outils sont divisés en :

- `required` : absence bloquante pour les niveaux qui en dépendent ;
- `optional` : utilisés lorsqu'ils sont disponibles.

Un niveau doit signaler précisément quel outil lui manque.

## Commands

Les commandes sont des alias pratiques.

Un level peut utiliser un alias partagé au lieu de recopier une commande dans plusieurs fichiers.

## Environment

`env` contient seulement les variables explicitement nécessaires à l'exécution.

Éviter de recopier ou afficher l'environnement complet.
