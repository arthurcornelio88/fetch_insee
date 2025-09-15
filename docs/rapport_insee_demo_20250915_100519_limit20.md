# Rapport d'exécution INSEE - DEMO (20 entreprises)

**Date d'exécution :** 15/09/2025 à 10:05:19  
**Mode :** demo  
**Limite :** 20

## 📊 Analyse du Dataset

| Métrique | Valeur |
|----------|--------|
| **Total lignes** | 3,034 |
| **Entreprises uniques** | 2,075 |
| **Entreprises dupliquées** | 590 |
| **Lignes dupliquées** | 959 |
| **Économie possible** | 959 requêtes évitées |

### 🔢 TOP 10 Doublons
1. **Colas** : 11 fois
2. **EDF** : 9 fois
3. **Devoteam** : 9 fois
4. **Oddo & Cie** : 8 fois
5. **ORANGE** : 8 fois
6. **Niji** : 8 fois
7. **Groupe Polylogis** : 8 fois
8. **Infopro Digital** : 8 fois
9. **Talan** : 8 fois
10. **Arkema** : 7 fois

## 🚀 Performance d'Exécution

| Métrique | Valeur |
|----------|--------|
| **Entreprises traitées** | 20 |
| **Entreprises trouvées** | 0 (0.0%) |
| **Appels API** | 11 |
| **Cache hits** | 9 |
| **Économie réalisée** | 9 requêtes évitées |
| **Temps d'exécution** | 0.7 minutes |
| **Temps économisé** | ~0.5 minutes |

### ⚡ Efficacité du Cache
- **Taux de cache hit :** 45.0%
- **Efficacité globale :** 100.0%

## 📈 Résultats Salesforce

### 🔍 Distribution des Statuts de Révision
- **CONFIRMED** : 8 (40.0%)
- **TO_REVIEW** : 7 (35.0%)
- **CONFLICT_TO_REVIEW** : 5 (25.0%)

### 💼 Effectifs pour Salesforce

| Métrique | Valeur |
|----------|--------|
| **Total entreprises** | 20 |
| **Avec valeurs numériques** | 20/20 (100.0%) |
| **Moyenne des effectifs** | 1,457 employés |
| **Médiane des effectifs** | 875 employés |
| **Min - Max** | 35 - 10,000 employés |

### 🎯 Niveaux de Confiance
- **medium** : 10 (50.0%)
- **high** : 8 (40.0%)
- **low** : 2 (10.0%)

## 📁 Fichiers Générés

- **Résultats INSEE :** `data/insee_optimized_demo_20_results.csv`
- **Données Salesforce :** `data/demo_20_optimized_salesforce_ready_refactor.csv`

## ⚙️ Configuration Technique

- **API INSEE :** v3.11
- **Limite de requêtes :** 30/minute
- **Pause entre requêtes :** 4 secondes
- **Optimisation doublons :** Activée ✅
- **Cache intelligent :** Activé ✅
- **Logique de statuts :** Intelligente ✅

---
*Rapport généré automatiquement le 15/09/2025 à 10:05:19*
