# Overview

## But

LevelUpDiag-Koali sert à exécuter de manière cohérente une série de diagnostics et validations autour d'un checkout de kOA-Linux.

Il répond principalement à quatre questions :

1. quels niveaux existent ;
2. dans quel ordre doivent-ils être exécutés ;
3. quel est le résultat de chacun ;
4. où retrouver les logs et artefacts produits.

## Nature du système

LevelUpDiag-Koali est un appendice de développement.

Il peut vivre :

```text
workspace/
├── koa-linux/
└── LevelUpDiag-Koali/
```

Il reste autonome et peut être supprimé sans empêcher kOA-Linux de fonctionner.

## Ce qu'il fait

- charge une configuration ;
- découvre les niveaux via un manifeste ;
- lance un niveau précis ou une série ;
- gère les prérequis simples ;
- applique des timeouts ;
- capture les sorties ;
- attribue un verdict ;
- produit des rapports ;
- affiche l'état via CLI ou GUI.

## Ce qu'il ne fait pas

- il ne remplace pas les tests de kOA-Linux ;
- il ne définit pas les règles de kOA-Linux ;
- il ne construit pas une nouvelle couche d'autorité ;
- il ne doit pas devenir une dépendance du produit ;
- il ne doit pas être nécessaire au runtime.

## Concepts principaux

### Level

Une unité de diagnostic ou validation exécutable.

### Run

Une exécution réelle d'un Level à un instant donné.

### Result

Le résultat normalisé du Run.

### Finding

Une observation utile produite par un niveau.

### Artifact

Un fichier auxiliaire produit par un niveau : log, rapport, capture ou sortie de commande.

### Campaign

Un ensemble de Runs exécutés ensemble avec une même cible et un même contexte.

## Philosophie

Le système privilégie :

- des niveaux petits ;
- des responsabilités lisibles ;
- des résultats explicites ;
- des logs faciles à retrouver ;
- une orchestration compréhensible ;
- peu de magie.
