# Rapport d'exécution INSEE - DEMO (50 entreprises)

**Date d'exécution :** 15/09/2025 à 01:22:29  
**Mode :** demo  
**Limite :** 50

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
| **Entreprises traitées** | 50 |
| **Entreprises trouvées** | 0 (0.0%) |
| **Appels API** | 34 |
| **Cache hits** | 16 |
| **Économie réalisée** | 16 requêtes évitées |
| **Temps d'exécution** | 1.5 minutes |
| **Temps économisé** | ~0.8 minutes |

### ⚡ Efficacité du Cache
- **Taux de cache hit :** 32.0%
- **Efficacité globale :** 100.0%

## 📈 Résultats Salesforce

### 🔍 Distribution des Statuts de Révision
- **TO_REVIEW** : 28 (56.0%)
- **CONFIRMED** : 11 (22.0%)
- **CONFLICT_TO_REVIEW** : 11 (22.0%)

### 💼 Effectifs pour Salesforce

| Métrique | Valeur |
|----------|--------|
| **Total entreprises** | 50 |
| **Avec valeurs numériques** | 25/50 (50.0%) |
| **Moyenne des effectifs** | 922 employés |
| **Médiane des effectifs** | 75 employés |
| **Min - Max** | 15 - 7,500 employés |

### 🎯 Niveaux de Confiance
- **low** : 24 (48.0%)
- **high** : 18 (36.0%)
- **medium** : 5 (10.0%)

## 📁 Fichiers Générés

- **Résultats INSEE :** `data/insee_optimized_demo_50_results.csv`
- **Données Salesforce :** `data/demo_50_optimized_salesforce_ready.csv`

## ⚙️ Configuration Technique

- **API INSEE :** v3.11
- **Limite de requêtes :** 30/minute
- **Pause entre requêtes :** 2.5 secondes
- **Optimisation doublons :** Activée ✅
- **Cache intelligent :** Activé ✅
- **Logique de statuts :** Intelligente ✅

---
*Rapport généré automatiquement le 15/09/2025 à 01:22:29*
