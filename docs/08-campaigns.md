# Campaigns

## Définition

Une Campaign est simplement un groupe de levels exécutés ensemble.

Elle ne crée pas une nouvelle couche de règles.

Elle répond à :

```text
quelle cible ?
quels niveaux ?
dans quel ordre ?
quand ?
avec quel résultat final ?
```

## Exemple

```json
{
  "name": "merge-validation",
  "target": "kOA-Linux",
  "levels": ["N01", "N03", "N04", "N05"],
  "stop_on_config_error": true
}
```

## Types utiles

### developer-fast

Retour rapide pendant le développement.

Exécute seulement quelques niveaux courts.

### bundle-validation

Valide une zone ou un bundle de travail.

### merge-validation

Exécute les validations requises avant fusion.

### nightly

Exécute une série plus large lorsque le temps d'exécution est moins critique.

### release-preparation

Regroupe les validations pertinentes avant la préparation d'une livraison.

### delivery-check

Vérifie spécifiquement que l'appendice n'est pas présent dans le livrable.

## Résultat global

Une campagne ne devrait pas réduire toutes les situations à un booléen.

Résumé recommandé :

```json
{
  "campaign": "merge-validation",
  "status": "BLOCKED",
  "counts": {
    "PASS": 4,
    "WARN": 0,
    "FAIL": 0,
    "BLOCKED": 1
  }
}
```

## Complétude

La campagne doit connaître la liste des niveaux qu'elle devait exécuter.

Un niveau requis sans résultat final rend la campagne incomplète.

## Historique

Chaque campagne reçoit un identifiant de run ou un timestamp afin de séparer ses logs des campagnes précédentes.
