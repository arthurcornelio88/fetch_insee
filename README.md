# Projet INSEE → Salesforce

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
