# INSEE Data Processor

Un module Python professionnel pour enrichir des données d'entreprises avec l'API INSEE Sirene.

## 🎯 Fonctionnalités

- **Enrichissement automatique** : Récupère SIREN, effectifs, catégories d'entreprise depuis l'API Sirene
- **Optimisation des doublons** : Cache intelligent pour éviter les requêtes redondantes  
- **Respect du rate limiting** : Gestion automatique des limites API (30 req/min)
- **Format Salesforce** : Export optimisé avec statuts de révision intelligents
- **Correction automatique** : Estimation des effectifs manquants selon la taille d'entreprise
- **Interface flexible** : Support de noms de colonnes personnalisés
- **Production ready** : Gestion d'erreurs robuste et logging détaillé

## 🚀 Installation

### Prérequis

- Python 3.9+
- Clé API INSEE Sirene ([Obtenir ici](https://api.insee.fr/catalogue/))

### Installation avec uv (recommandé)

```bash
# Cloner le repository
git clone https://github.com/votre-username/insee-data-processor.git
cd insee-data-processor

# Installer les dépendances
uv sync

# Configurer la clé API
cp .env.example .env
# Éditer .env et ajouter votre SIRENE_API_KEY
```

### Installation alternative avec pip

```bash
git clone https://github.com/votre-username/insee-data-processor.git
cd insee-data-processor
pip install -e .

# Configuration
cp .env.example .env
# Éditer .env et ajouter votre SIRENE_API_KEY
```

## 📋 Configuration

### 1. Clé API INSEE

Créez un fichier `.env` avec votre clé API :

```bash
SIRENE_API_KEY=votre_cle_api_insee_ici
```

### 2. Format du fichier d'entrée

Votre fichier CSV doit contenir au minimum :
- **Une colonne avec les noms d'entreprises** (nom flexible)
- **Une colonne avec la taille d'entreprise** (optionnel, mais recommandé)

Exemple :
```csv
Company Name,Size,Other Data
RENAULT,GE,Data1
SNCF,GE,Data2
Boulangerie Martin,MICRO,Data3
```

Les tailles supportées : `MICRO`, `PME`, `ETI`, `GE`

## 🎮 Utilisation

### Interface en ligne de commande

```bash
# Traitement basique
python scripts/process_companies.py data/companies.csv --company-col "Company Name"

# Avec colonne taille
python scripts/process_companies.py data/companies.csv --company-col "Company Name" --size-col "Size"

# Mode démo (50 entreprises)
python scripts/process_companies.py data/companies.csv --company-col "Company Name" --demo 50

# Sortie personnalisée
python scripts/process_companies.py data/companies.csv --company-col "Company Name" --output results/enriched.csv
```

### Utilisation programmatique

```python
from src.insee_client import INSEEClient
from src.data_processor import DataProcessor
from src.salesforce_export import SalesforceExporter
import pandas as pd

# Charger vos données
df = pd.read_csv('companies.csv')

# Initialiser les composants
client = INSEEClient()
processor = DataProcessor(client)
exporter = SalesforceExporter()

# Pipeline complet
df_enriched = processor.process_companies(df, 'Company Name', 'Size')
df_salesforce = exporter.transform_for_salesforce(df_enriched)

# Sauvegarder
df_salesforce.to_csv('output/enriched.csv', index=False)
```

## 📊 Structure des données de sortie

Le fichier de sortie contient :

| Colonne | Description |
|---------|-------------|
| `Organisation_Original` | Nom d'entreprise original |
| `Taille_Original` | Taille d'entreprise originale |
| `SIREN` | Numéro SIREN (9 chiffres) |
| `SIRET` | Numéro SIRET (14 chiffres) |
| `Denomination_INSEE` | Dénomination officielle INSEE |
| `Effectifs_Salesforce` | Effectifs au format numérique |
| `Effectifs_Description` | Description de la tranche d'effectifs |
| `Confiance_Donnee` | Niveau de confiance (`high`, `medium`, `low`) |
| `Statut_Revision` | Statut pour révision (`CONFIRMED`, `TO_REVIEW`, `CONFLICT_TO_REVIEW`) |
| `Notes_Revision` | Notes explicatives |

## 🔧 Configuration avancée

### Fichier config/config.yaml

```yaml
api:
  delay_between_requests: 4.0  # Respecter limite 30req/min
  max_results: 5

salesforce:
  auto_fix_missing: true
  size_mapping:
    MICRO:
      default_employees: 5
      description: "3 à 5 salariés"
```

### Variables d'environnement

```bash
SIRENE_API_KEY=votre_cle     # Obligatoire
INSEE_API_DELAY=4.0          # Optionnel
LOG_LEVEL=INFO               # Optionnel
```

## 📈 Optimisations et performances

### Cache intelligent
- **Doublons automatiquement détectés** : Évite les requêtes redondantes
- **Économie typique** : 30-50% de requêtes API en moins
- **Temps gagné** : ~3 secondes par doublon évité

### Gestion du rate limiting
- **Délai automatique** : 4 secondes entre requêtes (respecte 30 req/min)
- **Gestion d'erreurs** : Retry automatique en cas de HTTP 429
- **Variations intelligentes** : Teste plusieurs formes du nom d'entreprise

### Exemple de performance

```
📊 STATISTIQUES FINALES:
   🔗 Appels API: 1,250
   💾 Cache hits: 750
   ✅ Taux de réussite: 85.2%
   ⚡ Efficacité cache: 37.5%
   🕰️ Temps total: 1h 23min
```

## 🎯 Cas d'usage

### 1. Enrichissement Salesforce
```bash
python scripts/process_companies.py salesforce_export.csv \
  --company-col "Account Name" \
  --size-col "Company Size" \
  --output salesforce_enriched.csv
```

### 2. Due diligence financière
```bash
python scripts/process_companies.py portfolio.csv \
  --company-col "Portfolio Company" \
  --demo 100  # Test sur échantillon
```

### 3. Analyse sectorielle
```bash
python scripts/process_companies.py sector_analysis.csv \
  --company-col "Entreprise" \
  --delay 2.0  # Plus rapide (risqué)
```

## 🐛 Dépannage

### Erreurs courantes

**❌ Variable SIRENE_API_KEY non définie**
```bash
# Solution : créer le fichier .env
cp .env.example .env
# Puis éditer .env avec votre clé
```

**❌ Colonne 'Company' non trouvée**
```bash
# Solution : vérifier le nom exact de la colonne
python scripts/process_companies.py data.csv --company-col "Company Name"
```

**❌ Rate limit exceeded (HTTP 429)**
```bash
# Solution : augmenter le délai
python scripts/process_companies.py data.csv --company-col "Company" --delay 6.0
```

### Logs détaillés

```bash
python scripts/process_companies.py data.csv --company-col "Company" --verbose
```

## 📊 Algorithme de matching

### Stratégies de recherche
1. **Nom exact** : Recherche avec le nom original
2. **Majuscules** : Conversion en MAJUSCULES si différent
3. **Premier mot** : Extraction du premier mot si espaces présents

### Niveaux de confiance
- **High** : Tranches précises (≤50 employés)
- **Medium** : Tranches moyennes (50-1000 employés)  
- **Low** : Grandes tranches (>1000 employés)

### Statuts de révision
- **CONFIRMED** : Données cohérentes et fiables
- **TO_REVIEW** : Confiance faible, révision recommandée
- **CONFLICT_TO_REVIEW** : Incohérence détectée
- **NOT_FOUND** : Entreprise introuvable

## 🔄 Workflow de production

```bash
# 1. Mode démo pour validation
python scripts/process_companies.py data.csv --company-col "Company" --demo 50

# 2. Traitement complet si OK
python scripts/process_companies.py data.csv --company-col "Company"

# 3. Vérification qualité
# -> Analyser les statuts TO_REVIEW et CONFLICT_TO_REVIEW
# -> Valider les corrections automatiques
```

## 📚 Architecture technique

```
src/
├── insee_client.py      # Client API avec cache et rate limiting
├── data_processor.py    # Traitement principal et doublons  
└── salesforce_export.py # Transformation et correction

scripts/
└── process_companies.py # Interface CLI utilisateur

config/
└── config.yaml         # Configuration flexible
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -am 'Add amelioration'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Créer une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🏷️ Changelog

### v1.0.0 (2025-09-15)
- ✨ Refactoring complet en modules
- 🚀 Interface CLI flexible 
- ⚡ Optimisation cache et rate limiting
- 🔧 Correction automatique effectifs manquants
- 📊 Système de statuts intelligent
- 📚 Documentation complète

## 🎯 Objectif
Récupérer les effectifs d'employés pour **3000 entreprises** via l'API INSEE Sirene et convertir ces données en format numérique compatible Salesforce.

## 📁 Structure du Projet

```
data_insee/
├── data/
│   ├── face_raw_full.csv                    # 📥 DONNÉES D'ENTRÉE (3000 entreprises)
│   ├── face_raw.csv                         # Ancien fichier test (167 entreprises)
│   ├── test_safe_final.csv                  # 🧪 Test sécurisé (20 entreprises)
│   ├── insee_search_results_complete_full.csv # Résultats INSEE complets
│   └── face_raw_full_salesforce_ready.csv   # 🎯 FICHIER FINAL SALESFORCE
├── .env                                     # Clés API INSEE
├── insee_api_v3.py                         # Client API INSEE
├── salesforce_processor.py                 # Transformation Salesforce
├── process_full_3000.py                   # 🚀 SCRIPT PRINCIPAL 3000 entreprises
├── process_optimized.py                   # Script optimisé général
├── test_safe.py                           # Test sécurisé 20 entreprises
└── final_report.py                        # Rapport final
```

## 📄 Description des Fichiers CSV

### 📥 **face_raw_full.csv** - DONNÉES D'ENTRÉE PRINCIPALES
**Source**: Fichier original fourni (PRINCIPAL)
**Contenu**: 3000+ entreprises avec leurs informations de base  
**Colonnes principales**:
- `Organisation`: Nom de l'entreprise
- `Taille d'entreprise`: PME, ETI, GE, FEDERATION

**⭐ C'EST LE FICHIER PRINCIPAL À TRAITER**

---

### 📥 **face_raw.csv** - ANCIEN FICHIER TEST
**Source**: Ancien fichier (OBSOLÈTE)
**Contenu**: 167 entreprises (pour tests historiques)
**Utilisation**: Tests uniquement, remplacé par face_raw_full.csv

---

### 🧪 **test_safe_final.csv** - RÉSULTATS TEST SÉCURISÉ
**Source**: Généré par `test_safe.py`  
**Contenu**: 20 premières entreprises après recherche INSEE  
**Utilisation**: Validation du système avant traitement complet

---

### 🎯 **face_raw_full_salesforce_ready.csv** - FICHIER FINAL POUR SALESFORCE
**Source**: Résultat final du traitement des 3000 entreprises
**Contenu**: Données prêtes pour import Salesforce  
**Colonnes clés**:
- `Organisation_Original`: Nom d'entreprise d'origine
- `Denomination_INSEE`: Nom officiel INSEE
- `Effectifs_Salesforce`: **EFFECTIFS NUMÉRIQUES** 🎯
- `Confiance_Donnee`: Niveau de fiabilité des données
- `Statut_Revision`: Action requise avant import

**💡 C'EST CE FICHIER QUE VOUS DEVEZ UTILISER POUR SALESFORCE**

---

### 📊 Évolution des Données

```
face_raw_full.csv (3000 entreprises)
    ↓ [API INSEE - 2.5h]
insee_search_results_complete_full.csv (3000 avec données INSEE)
    ↓ [Transformation Salesforce]
face_raw_full_salesforce_ready.csv (FICHIER FINAL) 🎯
```

## 🔧 Configuration

### API INSEE
- **URL**: `https://api.insee.fr/api-sirene/3.11`
- **Authentification**: `X-INSEE-Api-Key-Integration`
- **Limite**: 30 requêtes/minute
- **Délai sécurité**: 3 secondes entre requêtes

### Environnement
```bash
# Installation
uv init
uv add pandas numpy requests python-dotenv

# Variables d'environnement (.env)
SIRENE_API_KEY=e27d72b1-69aa-43d3-bd72-b169aae3d3bc
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

## 🚀 Utilisation

### 1. Script Principal - 3000 Entreprises 🎯
```bash
uv run python process_full_3000.py
```
**Options disponibles:**
- 🚀 Traitement complet (3000 entreprises - 2.5h)
- 🧪 Demo rapide (100 entreprises - 5 min)
- 🔄 Reprendre traitement interrompu
- 📊 Transformer données existantes → Salesforce

### 2. Test Rapide (20 entreprises)
```bash
uv run python test_safe.py
```

### 3. Rapport Final
```bash
uv run python final_report.py
```

## 📊 Résultats

### Fichier Final: `face_raw_salesforce_ready.csv`

#### Colonnes Principales
- `Organisation_Original`: Nom d'entreprise original
- `Denomination_INSEE`: Nom officiel INSEE
- `Effectifs_Salesforce`: **Nombre d'employés (numérique)** 🎯
- `Confiance_Donnee`: Fiabilité (high/medium/low)
- `Statut_Revision`: Action requise
- `Match_Score`: Score de correspondance (0-100)
- `Notes_Revision`: Instructions détaillées

#### Statuts de Révision
- ✅ **CONFIRMED**: Données fiables, prêt pour import
- ⚠️ **CONFLICT_TO_REVIEW**: Incohérence taille vs INSEE
- 🔍 **MISSING_EFFECTIFS**: Entreprise trouvée, effectifs manquants
- ❌ **NOT_FOUND**: Entreprise non trouvée dans INSEE

## 🎯 Transformation des Effectifs

### Mapping INSEE → Salesforce
```python
"1 ou 2 salariés" → 1.5 employés
"10 à 19 salariés" → 15 employés
"100 à 199 salariés" → 150 employés
"1000 à 1999 salariés" → 1500 employés
"2000 à 4999 salariés" → 3500 employés
"Non renseigné" → null
```

### 📋 Exemples Concrets de Transformation

#### Exemple 1: Cas Simple ✅
```csv
# AVANT (face_raw.csv)
Organisation: "ADECCO"
Taille d'entreprise: "PME"

# APRÈS RECHERCHE INSEE (test_safe_final.csv)  
Organisation_Original: "ADECCO"
Denomination_INSEE: "ADECCO TRAINING"
Effectifs_Description: "100 à 199 salariés"
Statut_Recherche: "Trouvé"

# APRÈS TRANSFORMATION SALESFORCE (face_raw_salesforce_ready.csv)
Organisation_Original: "ADECCO"
Denomination_INSEE: "ADECCO TRAINING"
Effectifs_Salesforce: 150.0  ← VALEUR NUMÉRIQUE POUR SALESFORCE
Confiance_Donnee: "high"
Statut_Revision: "CONFIRMED"  ← PRÊT POUR IMPORT
```

#### Exemple 2: Conflit à Réviser ⚠️
```csv
# AVANT
Organisation: "Allianz"  
Taille d'entreprise: "PME"  ← Déclaré comme PME

# APRÈS
Denomination_INSEE: "ALLIANZ VIE"
Effectifs_Salesforce: 3500.0  ← Mais INSEE dit 2000-4999 salariés
Statut_Revision: "CONFLICT_TO_REVIEW"  ← Incohérence à vérifier
Notes_Revision: "🔍 Incohérence taille originale vs données INSEE"
```

#### Exemple 3: Données Manquantes 🔍
```csv
# AVANT
Organisation: "Adobe"

# APRÈS  
Denomination_INSEE: "ADOBE"
Effectifs_Salesforce: null  ← Pas d'effectifs dans INSEE
Statut_Revision: "MISSING_EFFECTIFS"  ← Recherche manuelle nécessaire
Notes_Revision: "⚠️ Trouvée mais effectifs non renseignés"
```

### Niveaux de Confiance
- 🟢 **HIGH**: Tranches précises (0-249 salariés)
- 🟡 **MEDIUM**: Tranches moyennes (250-1999 salariés)
- 🔴 **LOW**: Tranches larges (2000+ salariés) ou données manquantes

## 📈 Performance

### Test Sécurisé (20 entreprises)
- ✅ **Taux de succès**: 90% (18/20 trouvées)
- ⏱️ **Temps**: 1 minute
- 🎯 **Effectifs numériques**: 60% (12/20)

### Projection Complète (3000 entreprises)
- ⏱️ **Temps estimé**: 2.5-3 heures
- 📊 **Requêtes**: 3000 × 3s = ~2.5 heures
- 💾 **Sauvegarde par blocs**: Tous les 100 traitements
- 🔄 **Reprise automatique**: En cas d'interruption

## 🔄 Pipeline de Traitement

1. **Recherche INSEE**: `insee_api_v3.py`
   - Recherche par nom d'entreprise
   - Variations orthographiques
   - Extraction SIREN, effectifs, secteur

2. **Transformation Salesforce**: `salesforce_processor.py`
   - Conversion tranches → numérique
   - Calcul scores de confiance
   - Génération statuts de révision

3. **Export Final**: CSV UTF-8 compatible Salesforce

## 🛠️ Outils Disponibles

### Scripts de Test
- `test_safe.py`: Test avec 20 entreprises
- `test_salesforce.py`: Test transformation Salesforce

### Scripts de Production
- `process_optimized.py`: Traitement complet optimisé
- `final_report.py`: Rapport détaillé

## 📋 Prochaines Étapes

1. **Révision Manuelle**
   - Vérifier entreprises `CONFLICT_TO_REVIEW`
   - Rechercher entreprises `NOT_FOUND`
   - Compléter effectifs `MISSING_EFFECTIFS`

2. **Import Salesforce**
   - Utiliser `face_raw_salesforce_ready.csv`
   - Mapper colonnes selon besoins Salesforce
   - Traiter statuts de révision

3. **Extension**
   - Traitement des 3000 entreprises complètes
   - Automatisation des révisions
   - Intégration API Salesforce directe

## 🔗 API INSEE

### Endpoints Utilisés
- **Recherche**: `/api-sirene/3.11/siret`
- **Paramètre**: `q=denominationUniteLegale:"NOM_ENTREPRISE"`
- **Limite**: `nombre=3` (top 3 résultats)

### Données Extraites
- SIREN/SIRET
- Dénomination officielle
- Tranche d'effectifs
- Catégorie d'entreprise (PME/ETI/GE)
- Secteur d'activité (NAF)
- Date de création

## ✅ Succès du Projet

🎯 **Objectif atteint**: Conversion des tranches d'effectifs INSEE en valeurs numériques pour Salesforce

📊 **Résultat**: Fichier CSV prêt à l'import avec 60% d'effectifs numériques et système de révision intelligent

🔧 **Outils**: Pipeline complet de traitement avec respect des limites API et gestion d'erreurs robuste

## ❓ FAQ - Questions Fréquentes

### Q: Quel fichier dois-je utiliser pour Salesforce ?
**R**: `face_raw_full_salesforce_ready.csv` - C'est le fichier final avec les effectifs des 3000 entreprises en format numérique.

### Q: Combien de temps pour traiter 3000 entreprises ?
**R**: Environ 2.5-3 heures avec les limites API INSEE (30 req/min). Le système sauvegarde automatiquement la progression.

### Q: Que signifient les statuts de révision ?
**R**: 
- `CONFIRMED` = Prêt pour import direct
- `CONFLICT_TO_REVIEW` = Vérifier l'incohérence entre taille déclarée et INSEE
- `MISSING_EFFECTIFS` = Entreprise trouvée mais effectifs manquants
- `NOT_FOUND` = Entreprise non trouvée dans INSEE

### Q: Pourquoi certains effectifs sont "null" ?
**R**: L'INSEE ne renseigne pas toujours les effectifs. Ces entreprises nécessitent une recherche manuelle.

### Q: Comment interpréter les "Effectifs_Salesforce" ?
**R**: Ce sont les moyennes des tranches INSEE converties en nombres:
- "100 à 199 salariés" devient 150 employés
- "1000 à 1999 salariés" devient 1500 employés

### Q: Dois-je faire confiance aux données "low confidence" ?
**R**: Les données "low" correspondent aux grandes entreprises (2000+ salariés) où les tranches INSEE sont très larges. Vérifiez manuellement si précision nécessaire.

### Q: Comment traiter les 3000 entreprises complètes ?
**R**: Utilisez `process_full_3000.py` option 1. Le système gère automatiquement la reprise en cas d'interruption.

### Q: Les données sont-elles à jour ?
**R**: Les données INSEE sont mises à jour régulièrement. Le champ `Annee_Effectifs` indique l'année de référence.
