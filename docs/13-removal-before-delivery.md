# Removal before delivery

## Règle

LevelUpDiag-Koali est un outil de développement et de validation.

Il doit être retiré avant toute livraison de kOA-Linux.

## Ce qui doit être absent

Le livrable final ne doit pas contenir notamment :

```text
LevelUpDiag-Koali/
levelupdiag_core/
.levelupdiag/
levelupdiag_manifest.json
levelupdiag.config.example.json
levelupdiag.config.local.json
levelupdiag_wrapper.pyw
levelupdiag_wrapper_common.py
START_LEVELUPDIAG.bat
launchers/
```

La liste réelle du check doit correspondre aux noms utilisés par le dépôt final.

## Niveau dédié

Le manifeste Koali devrait contenir un niveau final :

```text
delivery.appendix.absent
```

ou un identifiant Nxx équivalent.

Son rôle est uniquement de vérifier l'absence de l'appendice dans les artefacts inspectés.

## Ce que le check inspecte

Selon le type de livraison :

- répertoire de staging ;
- archive ;
- contenu de package ;
- image montée ou extraite ;
- inventaire des fichiers du livrable.

## Ce qui peut être conservé hors livraison

Les rapports LevelUpDiag peuvent être conservés séparément comme diagnostics de développement.

Ils ne doivent pas être copiés dans le produit uniquement parce qu'ils ont servi à sa validation.

## Procédure recommandée

1. terminer les campagnes utiles ;
2. exporter les rapports nécessaires hors du staging ;
3. supprimer l'appendice et `.levelupdiag/` du périmètre de build ;
4. reconstruire ou nettoyer le staging ;
5. exécuter le check d'absence ;
6. seulement ensuite poursuivre le processus de livraison.

## Échec

Toute présence résiduelle produit :

```text
FAIL
```

Le remède est de corriger le staging ou la procédure de packaging, puis relancer le check.
