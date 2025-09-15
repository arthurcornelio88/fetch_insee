# Dossier de sortie

Ce dossier contient les fichiers enrichis générés par le processeur INSEE.

## Fichiers générés automatiquement

Les scripts génèrent automatiquement des fichiers avec la nomenclature suivante :

```
output/
├── companies_enriched.csv           # Fichier enrichi complet
├── demo_N_companies_enriched.csv    # Fichiers de démonstration 
└── [nom_original]_enriched.csv      # Basé sur le nom du fichier d'entrée
```

## Format des fichiers de sortie

Chaque fichier enrichi contient les colonnes suivantes :

- `Organisation_Original` : Nom d'entreprise original
- `Taille_Original` : Taille d'entreprise originale  
- `SIREN` : Numéro SIREN INSEE
- `Effectifs_Salesforce` : Effectifs au format numérique
- `Statut_Revision` : Statut de révision (CONFIRMED, TO_REVIEW, etc.)
- `Notes_Revision` : Notes explicatives pour la révision
- Plus de colonnes avec les données INSEE complètes

## Confidentialité

⚠️ **Important** : Ces fichiers peuvent contenir des données d'entreprises réelles.
Ne les commitez pas dans votre repository git - ils sont exclus par le .gitignore.