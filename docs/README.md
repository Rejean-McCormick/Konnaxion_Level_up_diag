# Documentation LevelUpDiag-Koali

Cette documentation décrit le fonctionnement du dépôt LevelUpDiag-Koali.

Le système reste volontairement compact : il orchestre des niveaux indépendants, aligne leur exécution et centralise leurs résultats.

## Lire d'abord

1. [Overview](01-overview.md)
2. [Architecture](02-architecture.md)
3. [Levels and checks](03-levels-and-checks.md)
4. [Configuration](04-configuration.md)
5. [Execution and ordering](05-execution-and-ordering.md)
6. [Results and logs](06-results-and-logs.md)

## kOA-Linux

- [Integration with kOA-Linux](07-koa-linux-integration.md)
- [Campaigns](08-campaigns.md)
- [Failure and blocking model](09-failure-and-blocking-model.md)
- [Removal before delivery](13-removal-before-delivery.md)

## Développement et exploitation

- [Security](10-security.md)
- [CLI and GUI](11-cli-and-gui.md)
- [Testing](12-testing.md)
- [Development](14-development.md)
- [Reference](15-reference.md)

## Architecture en une phrase

> Le manifeste indique quoi lancer, le runner décide quand le lancer, chaque niveau produit un résultat, et LevelUpDiag-Koali rassemble les logs.
