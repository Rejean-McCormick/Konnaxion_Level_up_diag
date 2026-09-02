# Failure and blocking model

La distinction entre types d'échec est une fonction centrale de LevelUpDiag.

## PASS

Le niveau s'est exécuté correctement et sa condition attendue est satisfaite.

## WARN

Le niveau a trouvé une anomalie ou un risque non bloquant.

## FAIL

Le niveau a pu exécuter son diagnostic et la cible ne satisfait pas la condition attendue.

Exemple :

```text
les tests se lancent correctement
mais 3 tests échouent
→ FAIL
```

## SKIP

Le niveau n'a pas été exécuté volontairement.

Il doit avoir une raison explicite.

## BLOCKED

Le niveau devrait être exécuté, mais un prérequis empêche d'obtenir un résultat utile.

Exemples :

```text
outil requis absent
service requis indisponible
niveau dépendant bloqué
checkout cible non accessible
```

## PARTIAL

Le niveau a obtenu une partie des informations mais pas assez pour donner PASS ou FAIL de manière complète.

## ERROR

Le niveau ou son code interne a rencontré une erreur.

Exemple :

```text
exception Python dans le level
→ ERROR
```

## INFRA_ERROR

L'environnement d'exécution empêche le diagnostic.

Exemples :

```text
processus impossible à lancer
timeout d'infrastructure
interpréteur absent
erreur système
```

## CONFIG_ERROR

La configuration du diagnostic est incohérente ou invalide.

Exemples :

```text
target_repo_root invalide
level inconnu
commande obligatoire absente de la config
manifest mal formé
```

## Résumé

```text
FAIL
= la cible a été testée et le test n'est pas satisfait

BLOCKED
= la cible n'a pas pu être testée correctement

ERROR
= le check lui-même est cassé

INFRA_ERROR
= l'environnement d'exécution est cassé

CONFIG_ERROR
= la configuration de LevelUpDiag est cassée
```

## Agrégation

Par défaut :

- un `FAIL` requis rend la campagne en échec ;
- un `CONFIG_ERROR` requis rend la campagne en échec ;
- un `BLOCKED`, `PARTIAL` ou `INFRA_ERROR` requis rend la campagne bloquée ;
- un `SKIP` requis rend la campagne incomplète sauf règle explicite ;
- `WARN` n'est pas équivalent à `FAIL`.
