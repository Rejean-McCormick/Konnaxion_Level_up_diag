# kOA-Linux integration

## Principe

LevelUpDiag-Koali est externe à kOA-Linux.

Il connaît le chemin du checkout cible grâce à :

```text
target_repo_root
```

Il appelle ensuite uniquement des scripts ou commandes publiques disponibles dans ce checkout.

## Dépendance à sens unique

```text
LevelUpDiag-Koali
        ↓
commandes publiques
        ↓
kOA-Linux
```

kOA-Linux ne dépend pas de LevelUpDiag-Koali.

## Exemples de commandes

Selon ce qui existe dans la version de kOA-Linux ciblée :

```text
python docs/tools/validate_docs.py
python ci/scripts/run-contracts.py
python ci/scripts/run-components.py
python ci/scripts/run-security.py
python ci/scripts/run-offline.py
python ci/scripts/run-system-tests.py
```

Le manifeste ou la configuration doivent refléter les commandes réellement disponibles dans le checkout utilisé.

## Lecture seule par défaut

Les niveaux Koali doivent considérer le checkout comme une cible en lecture seule.

Une opération qui modifie le checkout doit être séparée des campagnes ordinaires et clairement signalée.

## Révision

Lorsqu'un checkout Git est disponible, les rapports peuvent enregistrer :

```text
branch
HEAD
working tree clean/dirty
```

Ces informations servent au diagnostic et à l'identification du contexte d'exécution.

## Autorité

Si LevelUpDiag-Koali et kOA-Linux divergent sur une règle, la règle de kOA-Linux prévaut.

LevelUpDiag-Koali n'a pas pour rôle de corriger automatiquement cette divergence.

## Absence d'interface publique

Lorsqu'un niveau attend une commande qui n'existe pas dans la cible :

```text
BLOCKED
```

ou :

```text
CONFIG_ERROR
```

selon que le problème vient de la cible ou de la configuration.

Il ne faut pas contourner le problème par un import interne non documenté.
