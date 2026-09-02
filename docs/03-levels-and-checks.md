# Levels and checks

## Définition

Un Level est une unité de diagnostic ou de validation autonome.

Un bon niveau répond à une question précise, par exemple :

```text
L'environnement minimum est-il disponible ?
Les scripts de validation documentaire passent-ils ?
Les composants peuvent-ils lancer leurs tests ?
Les intégrations obligatoires sont-elles accessibles ?
Le livrable contient-il encore l'appendice ?
```

## Identité

Les identifiants historiques LevelUpDiag utilisent la forme :

```text
N00
N01
N02
...
```

Cette convention peut être conservée pour rester simple et compatible avec les launchers.

Le numéro représente l'ordre principal, pas une hiérarchie d'autorité.

## Contrat minimal

Chaque entrée du manifeste devrait contenir au minimum :

```json
{
  "id": "N03",
  "name": "Static Integrity",
  "file": "levels/N03_static_integrity.pyw",
  "enabled": true,
  "required": true,
  "depends_on": ["N01"],
  "timeout_seconds": 180
}
```

Les champs optionnels doivent rester justifiés par un besoin réel.

## Responsabilités d'un niveau

Un niveau doit :

1. charger la configuration partagée ;
2. valider ses prérequis propres ;
3. exécuter son diagnostic ;
4. produire des findings utiles ;
5. écrire un résultat normalisé ;
6. retourner un code de sortie cohérent.

## Niveau autonome

Un level doit pouvoir être lancé directement lorsque cela facilite le diagnostic :

```text
python levels/N03_static_integrity.py
```

ou, pour un niveau graphique :

```text
pythonw levels/N03_static_integrity.pyw
```

Le runner reste néanmoins le chemin normal pour une exécution alignée.

## Dépendances simples

Utiliser `depends_on` lorsqu'un niveau ne peut pas fournir un résultat utile sans un autre niveau.

Exemple :

```text
N01 Environment
   ↓
N03 Static Integrity
   ↓
N04 Contracts
```

Ne pas créer de dépendance seulement pour exprimer une préférence d'affichage.

## Required vs optional

`required: true` signifie que le niveau fait partie du résultat attendu de la campagne.

`required: false` signifie qu'il peut être absent ou non applicable sans empêcher la campagne de terminer.

## Placeholders

Une entrée de manifeste sans fichier réel est considérée incomplète.

Le runner doit la signaler clairement et ne pas la présenter comme un test réussi.
