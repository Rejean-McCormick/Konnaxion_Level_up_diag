# Security

Ce document complète le fichier racine [`SECURITY.md`](../SECURITY.md) avec les règles d'implémentation.

## Exécution de commandes

Le runner doit préférer :

```python
subprocess.run(
    ["python", "script.py"],
    shell=False,
)
```

à l'exécution d'une chaîne via shell.

Une commande sous forme de chaîne doit être réservée aux cas où un shell est réellement nécessaire et la source de la commande est maîtrisée.

## Répertoire de travail

Chaque Run doit connaître explicitement son `cwd`.

Un check kOA-Linux utilise normalement :

```text
cwd = target_repo_root
```

## Timeout

Toute commande externe doit avoir un timeout raisonnable.

Un timeout ne doit jamais produire PASS.

## Chemins

Les fonctions d'écriture doivent limiter leurs destinations à :

- `control_dir` ;
- `artifacts_dir` ;
- un autre répertoire explicitement autorisé.

Les valeurs contenant `..` ou résolvant en dehors de la racine attendue doivent être examinées avant écriture.

## Logs sensibles

Avant persistance, les niveaux doivent éviter ou masquer :

```text
password=
secret=
api_key=
token=
authorization:
```

Cette liste peut être adaptée dans la configuration.

## Variables d'environnement

Ne pas écrire l'environnement complet dans un log.

N'ajouter au sous-processus que les variables nécessaires en plus de l'environnement hérité.

## kOA-Linux

Le checkout de kOA-Linux est considéré en lecture seule pendant une campagne normale.

Les niveaux ne doivent pas :

- appliquer de patch ;
- modifier les manifests ;
- créer des commits ;
- nettoyer automatiquement le worktree.

## Artefacts externes

Lorsqu'un niveau inspecte une archive ou un dossier de livraison, il doit éviter d'exécuter son contenu.
