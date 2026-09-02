# CLI and GUI

LevelUpDiag-Koali possède deux surfaces : scripts CLI et wrapper graphique.

## CLI

Le script historique principal est :

```text
scripts/run_level.py
```

Il permet de lister ou lancer un niveau.

Exemples :

```text
py scripts/run_level.py --list
py scripts/run_level.py N04
py scripts/run_level.py 4 --wait
py scripts/run_level.py N04 --windowed
```

## Évolution Koali recommandée

Conserver ces usages et ajouter progressivement :

```text
py scripts/run_level.py --all
py scripts/run_level.py --campaign merge-validation
py scripts/run_level.py --from N03 --to N06
```

Il n'est pas nécessaire de construire une grosse CLI tant que ces commandes couvrent le besoin.

## print_manifest.py

Ce script fournit une vue rapide du manifeste.

Il doit rester un outil simple de diagnostic.

## verify_repo.py

Ce script vérifie la structure du dépôt LevelUpDiag-Koali :

- fichiers principaux présents ;
- manifeste lisible ;
- levels référencés présents ;
- modules Python compilables ;
- configuration exemple lisible.

Il vérifie la cohérence fonctionnelle du dépôt, pas le contenu de kOA-Linux.

## GUI

Le wrapper `.pyw` doit permettre :

- voir la liste ordonnée ;
- voir l'état de chaque level ;
- lancer un level ;
- lancer une campagne ;
- ouvrir les logs ;
- afficher le dernier résultat.

## Autorité

La GUI ne possède pas de logique de verdict différente de la CLI.

Les deux passent par les mêmes fonctions partagées.

## Mode windowed

Un fichier `.pyw` peut être lancé via Python windowed.

Un niveau destiné à l'automatisation devrait éviter de dépendre d'une interaction GUI obligatoire.
