# Execution and ordering

Ce document décrit le cœur de LevelUpDiag-Koali : aligner une série de niveaux et produire une exécution lisible.

## Ordre principal

Les niveaux restent ordonnés par leur identifiant ou par un champ `order` explicite.

Exemple :

```text
N00 Control Panel
N01 Environment
N02 Repository
N03 Documentation
N04 Contracts
N05 Components
N06 Integrations
N07 Profiles
N08 Security
N09 Offline
N10 System
N11 Delivery
```

La liste exacte appartient au manifeste.

## Dépendances

L'ordre numérique indique la progression générale.

`depends_on` exprime les dépendances obligatoires.

Exemple :

```text
N01 Environment
 ├─→ N03 Documentation
 ├─→ N04 Contracts
 └─→ N05 Components

N04 Contracts
 └─→ N06 Integrations
```

## Plan d'exécution

Avant lancement, le runner construit une liste de niveaux :

1. filtrer les niveaux désactivés ;
2. vérifier les fichiers ;
3. vérifier les dépendances ;
4. classer les niveaux ;
5. déterminer ceux qui sont immédiatement exécutables ;
6. lancer les niveaux ;
7. enregistrer chaque résultat ;
8. continuer ou bloquer selon la politique de campagne.

## Exécution séquentielle

C'est le mode par défaut.

```text
N01 → N02 → N03 → N04
```

Il est le plus facile à diagnostiquer.

## Exécution parallèle

Le parallélisme peut être utilisé uniquement pour des niveaux indépendants.

```text
       ┌→ N03
N01 ───┼→ N04
       └→ N05
```

Le runner ne doit jamais paralléliser deux niveaux lorsqu'une dépendance explicite existe.

## Précondition échouée

Si N04 dépend de N03 et que N03 est `BLOCKED`, N04 devient normalement `BLOCKED` avec une raison liée à la dépendance.

Un échec fonctionnel (`FAIL`) peut soit arrêter les dépendants, soit les laisser tourner si leur résultat reste utile. Ce comportement doit être déclaré au niveau de la campagne ou du level, pas implicite.

## Timeout

Chaque niveau peut définir un timeout.

Lorsqu'il est dépassé :

- le processus est arrêté ;
- le résultat indique le timeout ;
- les sorties disponibles sont conservées ;
- le runner continue selon la politique de la campagne.

## Fenêtres `.pyw`

Les niveaux `.pyw` peuvent être lancés avec Python windowed.

Pour une campagne automatisée, préférer une variante non interactive si le niveau en possède une.

## Fin de campagne

Une campagne est terminée lorsque tous les niveaux attendus ont reçu un état final :

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

L'absence de résultat n'est pas un résultat final.
