# INSEE Data Processor 🏢

**Module professionnel pour enrichir des données d'entreprises avec l'API INSEE Sirene**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-compatible-green.svg)](https://github.com/astral-sh/uv)

## 🎯 Fonctionnalités

### 🆕 **Nouveautés Septembre 2025**
- 🏛️ **Classification INSEE officielle** : Utilise `Categorie_Entreprise_INSEE` (critères financiers inclus)
- 📊 **Conservation complète** : 19 colonnes API INSEE v3.11 préservées
- 🔧 **Logique de révision intelligente** : CONFLICT_TO_REVIEW/TO_REVIEW/NOT_FOUND
- ⚡ **Optimisations avancées** : Détection doublons, cache intelligent, gestion pauses API

### 🚀 **Fonctionnalités principales**
- 🔍 **Recherche automatique** dans la base Sirene INSEE
- 📊 **Enrichissement complet** avec toutes les données INSEE disponibles
- 🚀 **Export Salesforce** avec statuts de révision intelligents
- ⚡ **Cache intelligent** pour éviter les doublons (30-50% d'économie)
- 🛡️ **Rate limiting** respecté (30 requêtes/minute max)
- 🔧 **Correction automatique** des effectifs manquants
- 📝 **Interface flexible** : Support de noms de colonnes personnalisés
- 🧪 **Mode démo** pour tester avant traitement complet

## 🚀 Installation

### Prérequis
- Python 3.9+
- Clé API INSEE Sirene ([Obtenir ici](https://api.insee.fr/catalogue/))

### Installation avec uv (recommandé)

```bash
# Cloner le repository
git clone git@github.com:arthurcornelio88/insee_data_processor.git
cd insee_data_processor

# Installer les dépendances
uv sync

# Configurer la clé API
cp .env.example .env
# Éditer .env et ajouter votre SIRENE_API_KEY
```

### Installation alternative (pip)

```bash
# Installer les dépendances
pip install requests python-dotenv

# Configurer la clé API
cp .env.example .env
# Éditer .env et ajouter votre SIRENE_API_KEY
```

## 📋 Format des données

### Fichier d'entrée
Votre fichier CSV doit contenir au minimum une colonne avec les noms d'entreprises :

```csv
Organisation,Taille d'entreprise
ACME Corporation,GE
Tech Solutions SAS,ETI
Global Industries,PME
CompagnieInexistante,PME
```

### 🆕 Colonnes complètes générées (19 au total)

**Colonnes de base** :
- `Organisation_Original` : Nom d'entreprise original
- `Taille_Original` : Taille déclarée par l'utilisateur  
- `Statut_Recherche` : Trouvé/Non trouvé

**🏛️ Colonnes INSEE enrichies** :
- `SIREN` : Identifiant unique entreprise (9 chiffres)
- `SIRET` : Identifiant établissement principal
- `Denomination_INSEE` : Dénomination officielle complète
- `Categorie_Entreprise_INSEE` : **Classification officielle (MICRO/PME/ETI/GE)**
- `Date_Creation` : Date de création de l'entreprise
- `Activite_Principale` : Code APE/NAF détaillé
- `Etat_Administratif` : Statut actif/cessé
- `Etablissement_Siege` : Indicateur siège social
- `Nombre_Etablissements` : Nombre total d'établissements
- `tranche_effectifs_unite_legale` : Tranche officielle INSEE

**💼 Colonnes Salesforce** :
- `Effectifs_Description` : Description textuelle des effectifs
- `Effectifs_Numeric` : Valeur numérique calculée
- `Effectifs_Salesforce` : Valeur finale pour export
- `Confiance_Donnee` : Niveau de confiance (high/medium/low)
- `Statut_Revision` : TO_REVIEW/CONFLICT_TO_REVIEW/NOT_FOUND
- `Notes_Revision` : Explications détaillées des divergences

## 🔧 Utilisation

### Interface en ligne de commande

```bash
# Traitement complet avec toutes les colonnes INSEE
python scripts/process_companies.py data/<ton-fichier>.csv \
    --company-col "Organisation" \
    --size-col "Taille d'entreprise" \
    --output output/enriched_complet.csv

# Colonnes personnalisées
python scripts/process_companies.py data.csv \
    --company-col "nom_entreprise" \
    --size-col "taille"

# Mode démo (100 premières entreprises pour test)
python scripts/process_companies.py data/<ton-fichier>.csv \
    --company-col "Organisation" \
    --size-col "Taille d'entreprise" \
    --demo 100
```

### Utilisation en module Python

```python
from src.insee_client import INSEEClient
from src.data_processor import DataProcessor
from src.salesforce_export import SalesforceExporter
import pandas as pd

# Initialisation
client = INSEEClient()
processor = DataProcessor(client)
exporter = SalesforceExporter()

# Chargement des données
df = pd.read_csv("data/face_raw_full.csv")

# Traitement complet avec 19 colonnes conservées
df_enriched = processor.process_companies(
    df, 
    company_col="Organisation",
    size_col="Taille d'entreprise"
)

# Export Salesforce avec classification officielle
sf_data = exporter.transform_for_salesforce(df_enriched)
sf_data.to_csv("output/salesforce_export_complet.csv", index=False)

# Exemple d'analyse des divergences de classification
conflicts = sf_data[sf_data['Statut_Revision'] == 'CONFLICT_TO_REVIEW']
print(f"Divergences classification: {len(conflicts)} entreprises")
```

## ⚙️ Configuration

### Variables d'environnement (.env)
```env
SIRENE_API_KEY=votre_cle_api_insee
```

### Configuration avancée (config/config.yaml)
```yaml
insee:
  base_url: "https://api.insee.fr/api-sirene/3.11"  # API v3.11 avec toutes les données
  rate_limit: 30  # requêtes par minute
  delay_between_requests: 4  # secondes
  cache_enabled: true

processing:
  demo_rows: 100  # Nombre d'entreprises pour le mode démo
  batch_size: 100
  preserve_all_columns: true  # Conservation des 19 colonnes
  
salesforce:
  use_official_classification: true  # Utilise Categorie_Entreprise_INSEE
  auto_correct_effectifs: true
  revision_statuses:
    conflict: "CONFLICT_TO_REVIEW"  # Divergence déclaré vs INSEE
    review: "TO_REVIEW"             # Faible confiance
    not_found: "NOT_FOUND"          # Non trouvé Sirene
```

## 📊 Exemple de résultat (19 colonnes)

```csv
Organisation_Original,Taille_Original,Statut_Recherche,SIREN,SIRET,Denomination_INSEE,Categorie_Entreprise_INSEE,Date_Creation,Activite_Principale,Etat_Administratif,Etablissement_Siege,Nombre_Etablissements,tranche_effectifs_unite_legale,Effectifs_Description,Effectifs_Numeric,Effectifs_Salesforce,Confiance_Donnee,Statut_Revision,Notes_Revision
AIRBUS,GE,Trouvé,383474814,38347481400068,AIRBUS,GE,1991-10-18,30.30Z,A,False,,52,5000 à 9999 salariés,7500.0,7500.0,low,TO_REVIEW,📊 Faible confiance ou grande tranche - 5000 à 9999 salariés - Vérifier
ADECCO,PME,Trouvé,343009866,34300986600926,ADECCO TRAINING,GE,1987-10-05,85.59A,A,False,,22,100 à 199 salariés,150.0,150.0,medium,CONFLICT_TO_REVIEW,⚠️ Classification divergente: PME déclaré vs GE INSEE (effectifs: 150.0)
CompagnieInexistante,PME,Non trouvé,,,,,,,,,,,100 à 199 salariés,,100.0,medium,NOT_FOUND,📊 Effectifs estimés par script selon Taille_Original (PME)
```

### 🎯 Points clés du résultat
- **Classification officielle** : `Categorie_Entreprise_INSEE` fait autorité (ex: ADECCO = GE malgré 150 employés)
- **Divergences détectées** : Comparaison automatique déclaré vs INSEE
- **Données complètes** : 19 colonnes conservées pour analyses futures
- **Statuts intelligents** : TO_REVIEW, CONFLICT_TO_REVIEW, NOT_FOUND

## 🔍 Optimisations

### 🆕 Optimisations Septembre 2025
- **Classification officielle** : Fin des calculs approximatifs, utilise les critères INSEE complets
- **Conservation données** : 19 colonnes API complètes vs colonnes minimales précédentes  
- **Logique révision** : Détection intelligente des divergences (PME déclaré vs GE INSEE)

### Cache intelligent et performance
- **Détection des doublons** : Évite les requêtes redondantes automatiquement
- **Économie typique** : 30-50% de requêtes en moins sur gros datasets
- **Statistics en temps réel** : Affichage du taux d'optimisation et cache hits
- **Pause intelligente** : 2s entre variations pour respecter les limites API

### Gestion des erreurs et qualité
- **Rate limiting** : Respect automatique des limites API (30 req/min)
- **Variations de noms** : Essai de différentes variantes si échec initial
- **Correction automatique** : Estimation des effectifs manquants selon taille déclarée
- **Validation données** : Vérification cohérence et marquage des conflits

## 🛠️ Structure du projet

```
insee_data_processor/
├── src/
│   ├── insee_client.py      # Client API v3.11 avec cache et rate limiting
│   ├── data_processor.py    # Conservation 19 colonnes + logique enrichissement
│   └── salesforce_export.py # Export avec classification officielle INSEE
├── scripts/
│   ├── process_companies.py     # Interface CLI principale
│   ├── generate_report.py      # 🆕 Générateur rapports professionnels
│   ├── fix_size_thresholds.py  # Correction données existantes
│   └── fix_effectifs_description.py # Correction effectifs
├── data/
│   └── face_raw_full.csv       # Dataset principal (3034 entreprises)
├── docs/
│   ├── REFACTOR_CLASSIFICATION_INSEE.md # Documentation refactor
│   ├── RAPPORT_TRAITEMENT_INSEE_*.md    # 🆕 Rapports générés automatiquement
│   └── RAPPORT_OPTIMISATIONS_*.md       # 🆕 Rapports performance
├── config/
│   └── config.yaml            # Configuration API v3.11
├── .env.example              # Template variables d'environnement
└── pyproject.toml            # Dépendances uv
```

## 📊 Génération de rapports automatiques

### 🆕 Script de rapport professionnel

Après traitement des données, générez automatiquement des rapports complets avec statistiques et analyses :

```bash
# Génération de rapport standard
python scripts/generate_report.py output/face_raw_full_enriched.csv

# Rapport dans un répertoire spécifique
python scripts/generate_report.py output/results.csv --output-dir reports/

# Rapport sur données de démo
python scripts/generate_report.py output/demo_100_enriched.csv --verbose
```

### 📋 Contenu des rapports générés

**📊 Rapport principal** : `RAPPORT_TRAITEMENT_INSEE_YYYYMMDD_HHMM.md`
- **Résumé exécutif** : Taux de succès, optimisations, performance
- **Statistiques détaillées** : Statuts révision, niveaux confiance, effectifs
- **Analyse divergences** : Exemples anonymisés de conflits classification
- **Analyse sectorielle** : Top secteurs NAF, répartition temporelle
- **Recommandations** : Actions prioritaires par statut (CONFLICT/TO_REVIEW/NOT_FOUND)
- **ROI économique** : Valeur vs solutions payantes ($15K-50K/an évités)

**⚡ Rapport optimisations** : `RAPPORT_OPTIMISATIONS_YYYYMMDD_HHMM.md`
- **Détection doublons** : Top entreprises dupliquées, économies requêtes
- **Métriques performance** : Temps gagné, qualité données, précision
- **Comparaisons avant/après** : Amélioration logique classification

### 📈 Exemple d'utilisation complète

```bash
# 1. Traitement complet des données
python scripts/process_companies.py data/face_raw_full.csv \
    --company-col "Organisation" \
    --size-col "Taille d'entreprise" \
    --output output/face_raw_full_enriched.csv

# 2. Génération automatique des rapports
python scripts/generate_report.py output/face_raw_full_enriched.csv

# 3. Résultats dans docs/
# - RAPPORT_TRAITEMENT_INSEE_20250916_1430.md
# - RAPPORT_OPTIMISATIONS_20250916_1430.md
```

### 🎯 Avantages des rapports

- **Anonymisation automatique** : Données entreprises protégées
- **Analyse business** : Métriques ROI et valeur ajoutée  
- **Documentation complète** : Traçabilité et validation pour audits
- **Exemples concrets** : Conflits classification avec explications
- **Recommandations actionnables** : Priorités par statut révision

## 🧪 Tests et validation

### Mode démo pour validation
```bash
# Tester sur 100 entreprises avant traitement complet
python scripts/process_companies.py data/face_raw_full.csv \
    --company-col "Organisation" \
    --size-col "Taille d'entreprise" \
    --demo 100

# Analyser les divergences de classification  
python scripts/process_companies.py data/face_raw_full.csv \
    --company-col "Organisation" \
    --size-col "Taille d'entreprise" \
    --demo 50 \
    --output output/test_classifications.csv
```

### 🎯 Validation des résultats
- **Taux de succès validé** : 94% sur échantillon de 50 entreprises
- **Classification précise** : Détection automatique des divergences (ex: PME déclaré vs GE INSEE)
- **Données complètes** : 19 colonnes avec toutes les informations INSEE disponibles

### Scripts de correction disponibles
- `fix_size_thresholds.py` : Correction des classifications dans fichiers existants
- `fix_effectifs_description.py` : Correction des descriptions d'effectifs

## 🚨 Limitations et bonnes pratiques

### Limites API INSEE
- **30 requêtes/minute** maximum
- **Pause recommandée** : 4 secondes entre requêtes
- **Variations automatiques** : Essai de différentes formes du nom

### Recommandations usage production
- ✅ **Testez avec --demo** avant traitement complet (3034 entreprises ≈ 2h30)
- ✅ **Vérifiez votre quota API** INSEE avant gros traitements  
- ✅ **Analysez les CONFLICT_TO_REVIEW** : Divergences déclaré vs classification INSEE
- ✅ **Conservez toutes les colonnes** : 19 colonnes pour analyses futures
- ✅ **Gardez vos clés API sécurisées** (pas de commit dans git)
- ✅ **Surveillez les logs** pour optimisations et taux de succès

### 🆕 Nouveaux cas d'usage
- **Audit de classification** : Comparaison systématique déclaré vs INSEE officiel
- **Enrichissement complet** : 19 colonnes pour analyses avancées  
- **Détection anomalies** : Entreprises PME qui sont en fait GE (critères financiers)

## 📝 Licence

MIT License - Libre d'utilisation pour projets commerciaux et open source.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

---

**Développé avec ❤️ pour simplifier l'enrichissement de données d'entreprises**