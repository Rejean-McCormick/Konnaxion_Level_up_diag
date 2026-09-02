# Development

## Objectif

Faire évoluer LevelUpDiag-Koali sans transformer l'outil en framework généraliste.

## Organisation du core

Structure cible compacte :

```text
levelupdiag_core/
├── __init__.py
├── config.py
├── manifest.py
├── models.py
├── planner.py
├── runner.py
├── commands.py
├── results.py
├── logs.py
└── artifacts.py
```

Tous ces fichiers ne doivent être créés que lorsqu'ils apportent une séparation réelle.

## Ajouter un nouveau level

1. choisir son identifiant ;
2. définir sa responsabilité ;
3. créer son fichier ;
4. ajouter l'entrée au manifeste ;
5. utiliser `load_config()` ;
6. utiliser les helpers communs ;
7. écrire un résultat ;
8. tester PASS, FAIL et prérequis manquant ;
9. documenter le niveau si son comportement n'est pas évident.

## Ajouter une dépendance

Ajouter `depends_on` dans le manifeste.

Éviter d'encoder des dépendances par des appels directs entre fichiers de levels.

## Ajouter une commande kOA

La commande doit :

- exister dans le checkout cible ;
- être utilisable depuis la racine cible ;
- avoir un comportement non interactif pour les campagnes automatisées ;
- produire un code de sortie exploitable.

## Modifier un verdict

Les verdicts sont une interface partagée.

Une nouvelle valeur doit avoir une signification réellement distincte et être comprise par :

```text
runner
reports
wrapper
tests
documentation
```

## Ajouter des champs au résultat

Préférer des champs simples et utiles.

Exemples raisonnables :

```text
started_at
ended_at
duration_seconds
exit_code
command
cwd
output_tail
```

Éviter les structures profondes si les levels n'en ont pas besoin.

## Compatibilité

Un changement de manifeste ou de rapport doit soit rester compatible avec les anciennes entrées, soit changer explicitement l'identifiant de schéma.

## Definition of done

Une évolution est terminée lorsque :

- elle fonctionne en CLI ;
- elle fonctionne via le wrapper si applicable ;
- les erreurs sont classées correctement ;
- les logs sont lisibles ;
- les tests associés passent ;
- la documentation correspond au comportement réel.
