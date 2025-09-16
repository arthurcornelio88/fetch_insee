# 📊 Guide d'utilisation du générateur de rapports INSEE

## Utilisation rapide

```bash
# Après traitement de vos données avec process_companies.py
python scripts/generate_report.py output/votre_fichier_enrichi.csv
```

## Exemples concrets

### 1. Rapport sur dataset complet
```bash
python scripts/generate_report.py "output/face_raw_full_FINAL_corrections_appliquées.csv"
```

### 2. Rapport de démo avec répertoire personnalisé
```bash
python scripts/generate_report.py output/demo_100_enriched.csv --output-dir reports/
```

### 3. Mode verbose pour débogage
```bash
python scripts/generate_report.py output/results.csv --verbose
```

## Fichiers générés

Le script génère automatiquement 2 rapports :
- `RAPPORT_TRAITEMENT_INSEE_YYYYMMDD_HHMM.md` : Rapport principal avec statistiques complètes
- `RAPPORT_OPTIMISATIONS_YYYYMMDD_HHMM.md` : Rapport des optimisations et performance

## Prérequis

Le fichier CSV doit contenir les colonnes suivantes (générées par `process_companies.py`) :
- `Organisation_Original` : Nom d'entreprise 
- `Statut_Recherche` : Trouvé/Non trouvé
- `Statut_Revision` : CONFLICT_TO_REVIEW/CONFIRMED/TO_REVIEW/NOT_FOUND
- `Confiance_Donnee` : high/medium/low/none

## Protection des données

Les rapports anonymisent automatiquement tous les noms d'entreprises pour protéger les données sensibles.