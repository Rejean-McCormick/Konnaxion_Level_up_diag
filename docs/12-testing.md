# Testing

## Objectif

Les tests de LevelUpDiag-Koali doivent vérifier principalement l'orchestration.

Le système testé n'est pas kOA-Linux lui-même : les checks kOA appellent les validateurs de kOA-Linux.

## Tests unitaires

Couvrir au minimum :

```text
load_config
path resolution
load_manifest
normalize_level_id
get_level
level ordering
dependency resolution
verdict normalization
result serialization
artifact path helpers
```

## Tests runner

Cas essentiels :

1. level PASS ;
2. level FAIL ;
3. exécutable absent ;
4. fichier level absent ;
5. timeout ;
6. exception du level ;
7. dépendance BLOCKED ;
8. config invalide ;
9. output volumineux ;
10. plusieurs levels exécutés dans l'ordre.

## Tests de logs

Vérifier :

- création du dossier ;
- séparation entre deux runs ;
- écriture de `result.json` ;
- écriture de la sortie ;
- comportement du dossier `latest`.

## Tests de manifeste

Vérifier :

- identifiants uniques ;
- fichiers existants ;
- dépendances existantes ;
- absence de cycle simple ;
- ordre stable.

## Tests GUI

La GUI doit être testée surtout pour :

- chargement du manifeste ;
- affichage des niveaux ;
- lancement correct ;
- ouverture du bon dossier ;
- remontée du bon verdict.

La logique d'exécution doit rester testable sans interface graphique.

## Tests d'intégration kOA

Utiliser un checkout ou une fixture connue.

Tester au minimum :

- cible absente ;
- commande absente ;
- commande PASS ;
- commande FAIL ;
- commande BLOCKED par outil manquant.

## Test de retrait

Construire une fausse livraison contenant un fichier LevelUpDiag et vérifier que le level de contrôle le détecte.

Construire ensuite une livraison propre et vérifier qu'elle passe.
