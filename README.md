# INSEE Data Processor 🏢

**Module professionnel pour enrichir des données d'entreprises avec l'API INSEE Sirene**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-compatible-green.svg)](https://github.com/astral-sh/uv)

## 🎯 Fonctionnalités

- 🔍 **Recherche automatique** dans la base Sirene INSEE
- 📊 **Enrichissement** avec effectifs, SIREN, catégories d'entreprise
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
company_name,size_category
ACME Corporation,Grande entreprise
Tech Solutions SAS,ETI
Global Industries,PME
```

### Colonnes générées
- `siren` : Numéro SIREN (9 chiffres)
- `denomination` : Nom officiel
- `categorie_entreprise` : GE/ETI/PME/TPE
- `tranche_effectifs` : Tranche d'effectifs détaillée
- `date_creation` : Date de création
- `code_postal` : Code postal du siège
- `ville` : Ville du siège

## 🔧 Utilisation

### Interface en ligne de commande

```bash
# Traitement basique
python scripts/process_companies.py data/companies_sample.csv

# Colonnes personnalisées
python scripts/process_companies.py data.csv --company-col "nom_entreprise" --size-col "taille"

# Mode démo (3 premières lignes)
python scripts/process_companies.py data/companies_sample.csv --demo
```

### Utilisation en module Python

```python
from src.insee_client import INSEEClient
from src.data_processor import DataProcessor
from src.salesforce_export import SalesforceExporter

# Initialisation
client = INSEEClient()
processor = DataProcessor(client)
exporter = SalesforceExporter()

# Traitement
df = processor.process_companies(
    "data/companies_sample.csv", 
    company_col="company_name",
    size_col="size_category"
)

# Export Salesforce
sf_data = exporter.transform_for_salesforce(df)
sf_data.to_csv("output/salesforce_export.csv", index=False)
```

## ⚙️ Configuration

### Variables d'environnement (.env)
```env
SIRENE_API_KEY=votre_cle_api_insee
```

### Configuration avancée (config/config.yaml)
```yaml
insee:
  base_url: "https://api.insee.fr/entreprises/sirene/V3.11"
  rate_limit: 30  # requêtes par minute
  delay_between_requests: 4  # secondes
  cache_enabled: true

processing:
  demo_rows: 3
  batch_size: 100
  
salesforce:
  default_status: "A réviser"
  auto_correct_effectifs: true
```

## 📊 Exemple de résultat

```csv
company_name,siren,denomination,categorie_entreprise,tranche_effectifs,date_creation,code_postal,ville,size_category
ACME Corporation,123456789,ACME CORPORATION,GE,5000 à 9999 salariés,2010-03-15,75001,PARIS,Grande entreprise
Tech Solutions SAS,987654321,TECH SOLUTIONS,ETI,250 à 499 salariés,2015-06-22,69001,LYON,ETI
Global Industries,456789123,GLOBAL INDUSTRIES,PME,50 à 99 salariés,2018-11-08,13001,MARSEILLE,PME
```

## 🔍 Optimisations

### Cache intelligent
- **Détection des doublons** : Évite les requêtes redondantes
- **Économie typique** : 30-50% de requêtes en moins
- **Statistics** : Affichage du taux d'optimisation

### Gestion des erreurs
- **Rate limiting** : Respect automatique des limites API
- **Variations de noms** : Essai de différentes variantes si échec
- **Correction automatique** : Estimation des effectifs manquants

## 🛠️ Structure du projet

```
insee_data_processor/
├── src/
│   ├── insee_client.py      # Client API avec cache et rate limiting
│   ├── data_processor.py    # Logique de traitement principal
│   └── salesforce_export.py # Export et transformations Salesforce
├── scripts/
│   └── process_companies.py # Interface CLI
├── data/
│   ├── companies_sample.csv # Données d'entrée exemple
│   └── example_output.csv   # Résultat attendu
├── config/
│   └── config.yaml         # Configuration
├── .env.example            # Template variables d'environnement
└── pyproject.toml          # Dépendances uv
```

## 🧪 Tests et validation

### Mode démo
```bash
# Tester sur 3 lignes seulement
python scripts/process_companies.py data/companies_sample.csv --demo
```

### Fichiers d'exemple
Le repository inclut des fichiers d'exemple anonymisés :
- `data/companies_sample.csv` : Données d'entrée
- `data/example_output.csv` : Résultat attendu

## 🚨 Limitations et bonnes pratiques

### Limites API INSEE
- **30 requêtes/minute** maximum
- **Pause recommandée** : 4 secondes entre requêtes
- **Variations automatiques** : Essai de différentes formes du nom

### Recommandations
- ✅ **Vérifiez votre quota** avant gros traitements
- ✅ **Utilisez le mode démo** pour tester la configuration
- ✅ **Gardez vos clés API sécurisées** (pas de commit dans git)
- ✅ **Surveillez les logs** pour identifier les problèmes

## 📝 Licence

MIT License - Libre d'utilisation pour projets commerciaux et open source.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

---

**Développé avec ❤️ pour simplifier l'enrichissement de données d'entreprises**