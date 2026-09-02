# Contributing

Les contributions à LevelUpDiag-Koali doivent préserver la simplicité du système.

## Règles générales

Une modification doit avoir une responsabilité claire :

- ajout ou correction d'un niveau ;
- évolution du runner ;
- amélioration de la collecte de logs ;
- amélioration de la configuration ;
- amélioration du modèle de résultat ;
- amélioration de la GUI ou de la CLI ;
- adaptation à une commande publique de kOA-Linux.

Éviter d'introduire un nouveau concept lorsqu'un champ du manifeste, un helper partagé ou un nouveau niveau suffit.

## Ajouter un niveau

Un nouveau niveau doit :

1. avoir un identifiant stable ;
2. apparaître dans `levelupdiag_manifest.json` ;
3. avoir un fichier exécutable réel ;
4. utiliser la configuration partagée ;
5. écrire un résultat normalisé ;
6. retourner un code de sortie cohérent ;
7. ne pas modifier silencieusement la cible.

Voir [`docs/03-levels-and-checks.md`](docs/03-levels-and-checks.md).

## Modifier le core

Les helpers communs appartiennent à `levelupdiag_core/`.

Un helper partagé doit rester générique pour plusieurs niveaux. Une logique spécifique à un seul niveau reste dans ce niveau.

## Documentation

Toute évolution visible du manifeste, de la configuration, des verdicts, de l'ordre d'exécution ou des logs doit mettre à jour la documentation correspondante.

## Tests attendus

Avant fusion :

```text
configuration parsing
manifest parsing
level lookup
runner behavior
result serialization
log placement
failure mapping
CLI behavior
```

Les checks touchant kOA-Linux doivent aussi être testés contre un checkout de test ou des fixtures contrôlées.
