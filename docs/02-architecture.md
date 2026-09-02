# Architecture

## Vue générale

```text
levelupdiag_wrapper.pyw
        │
        ├──────────────┐
        │              │
        ▼              ▼
configuration      manifest
        │              │
        └──────┬───────┘
               ▼
             runner
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
      N00    N01    N02 ...
        │      │      │
        └──────┼──────┘
               ▼
      results + logs + artifacts
```

## Composants

### Configuration

La configuration contient les éléments propres à la machine ou au checkout cible :

- racine de la cible ;
- outils disponibles ;
- commandes locales ;
- chemins de travail ;
- variables d'environnement nécessaires ;
- dossier de contrôle ;
- dossier de diagnostics.

### Manifest

Le manifeste est l'inventaire des niveaux.

Il décrit leur identité, leur fichier, leur ordre et les propriétés nécessaires au runner.

### Core

`levelupdiag_core/` contient les fonctions partagées :

```text
config
manifest
commands
runner
results
logs
artifacts
```

Le core doit rester suffisamment petit pour être compris sans framework supplémentaire.

### Levels

Les niveaux sont les unités réelles de travail.

Ils peuvent être écrits en `.pyw` lorsque l'expérience graphique est utile ou en `.py` lorsqu'une exécution console est préférable.

### Wrapper

Le wrapper fournit une interface visuelle pour :

- afficher les niveaux ;
- lancer un niveau ;
- suivre l'état ;
- ouvrir les rapports ou dossiers de diagnostics.

Le wrapper ne doit pas contenir la logique métier des niveaux.

## Direction des dépendances

```text
wrapper
   ↓
core
   ↓
manifest/config
   ↓
levels
   ↓
commandes publiques de la cible
```

Les levels peuvent utiliser le core partagé.

Le core ne doit pas dépendre d'un level particulier.

## Données runtime

Les sorties locales sont regroupées sous `.levelupdiag/`.

Exemple :

```text
.levelupdiag/
├── diagnostics/
│   ├── N01-environment/
│   ├── N02-services/
│   └── ...
├── runs/
└── latest/
```

L'organisation exacte peut évoluer, mais le chemin doit rester centralisé et configurable.
