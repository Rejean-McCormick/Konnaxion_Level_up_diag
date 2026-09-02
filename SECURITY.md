# Security

LevelUpDiag-Koali lance des processus externes et manipule des chemins locaux. Sa surface de sécurité principale est donc l'exécution de commandes et la collecte de sorties.

## Principes

- ne jamais placer de secret dans `levelupdiag.config.example.json` ;
- limiter les commandes à celles déclarées dans le manifeste ou la configuration ;
- préférer les commandes sous forme de liste d'arguments ;
- éviter l'interprétation shell lorsque ce n'est pas nécessaire ;
- valider les chemins avant lecture ou écriture ;
- ne jamais écrire en dehors des répertoires explicitement configurés ;
- traiter kOA-Linux comme une cible en lecture seule par défaut ;
- filtrer les valeurs sensibles avant écriture dans les logs ;
- ne pas transformer une erreur d'infrastructure en PASS.

## Données sensibles

Les logs peuvent contenir :

- chemins locaux ;
- sorties de processus ;
- noms d'utilisateur locaux ;
- variables d'environnement ;
- informations sur les outils installés.

Les niveaux ne doivent pas recopier l'environnement complet dans leurs rapports.

Les valeurs ressemblant à des secrets, tokens, mots de passe ou clés doivent être masquées avant persistance.

## Commandes

Les commandes provenant d'un fichier de configuration local sont considérées comme des entrées de confiance limitée.

Le runner doit :

1. connaître la commande réellement exécutée ;
2. enregistrer son répertoire de travail ;
3. appliquer un timeout ;
4. capturer le code de sortie ;
5. distinguer timeout, absence d'exécutable et échec de la cible.

## Signalement

Une vulnérabilité touchant l'exécution de commande, l'évasion de chemin, la fuite de secrets ou l'écriture non attendue dans la cible doit être traitée comme prioritaire.
