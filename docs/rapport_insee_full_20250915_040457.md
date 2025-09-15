# Rapport d'exécution INSEE - FULL

**Date d'exécution :** 15/09/2025 à 04:04:57  
**Mode :** full  
**Limite :** Aucune (traitement complet)

## 📊 Analyse du Dataset

| Métrique | Valeur |
|----------|--------|
| **Total lignes** | 3,034 |
| **Entreprises uniques** | 2,075 |
| **Entreprises dupliquées** | 590 |
| **Lignes dupliquées** | 959 |
| **Économie possible** | 959 requêtes évitées |

## 🚀 Performance d'Exécution

| Métrique | Valeur |
|----------|--------|
| **Entreprises traitées** | 3,034 |
| **Entreprises trouvées** | 0 (0.0%) |
| **Appels API** | 2,075 |
| **Cache hits** | 959 |
| **Économie réalisée** | 959 requêtes évitées |
| **Temps d'exécution** | 156.6 minutes |
| **Temps économisé** | ~48.0 minutes |

### ⚡ Efficacité du Cache
- **Taux de cache hit :** 31.6%
- **Efficacité globale :** 100.0%

## 📈 Résultats Salesforce

### 🔍 Distribution des Statuts de Révision
- **TO_REVIEW** : 1,790 (59.0%)
- **CONFLICT_TO_REVIEW** : 741 (24.4%)
- **CONFIRMED** : 489 (16.1%)
- **MISSING_EFFECTIFS** : 14 (0.5%)

### 💼 Effectifs pour Salesforce

| Métrique | Valeur |
|----------|--------|
| **Total entreprises** | 3,034 |
| **Avec valeurs numériques** | 1,341/3,034 (44.2%) |
| **Moyenne des effectifs** | 1,382 employés |
| **Médiane des effectifs** | 225 employés |
| **Min - Max** | 15 - 15,000 employés |

### 🎯 Niveaux de Confiance
- **low** : 1,601 (52.8%)
- **high** : 684 (22.5%)
- **medium** : 564 (18.6%)

## 📁 Fichiers Générés

- **Résultats INSEE :** `data/insee_optimized_full_results.csv`
- **Données Salesforce :** `data/full_optimized_salesforce_ready.csv`

## ⚙️ Configuration Technique

- **API INSEE :** v3.11
- **Limite de requêtes :** 30/minute
- **Pause entre requêtes :** 4 secondes
- **Optimisation doublons :** Activée ✅
- **Cache intelligent :** Activé ✅
- **Logique de statuts :** Intelligente ✅

---
*Rapport généré automatiquement le 15/09/2025 à 04:04:57*
