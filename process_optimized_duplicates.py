#!/usr/bin/env python3
"""
Processeur INSEE optimisé avec gestion des doublons
Évite les requêtes inutiles en cachant les résultats pour les entreprises dupliquées
"""

import os
import time
import pandas as pd
from datetime import datetime
from insee_api_v3 import INSEEApiClient
from salesforce_processor import process_insee_result_for_salesforce
from salesforce_processor import create_salesforce_ready_data

def get_default_effectifs_by_taille(taille: str) -> tuple:
    """
    Retourne les effectifs par défaut selon la taille d'entreprise
    Returns: (effectifs_numerique, effectifs_description, confiance)
    """
    mapping = {
        'MICRO': (5, '3 à 5 salariés', 'medium'),      # Milieu de gamme MICRO
        'PME': (100, '100 à 199 salariés', 'medium'),   # Milieu de gamme PME  
        'ETI': (1000, '1000 à 1999 salariés', 'medium'), # Milieu de gamme ETI
        'GE': (10000, '10000 salariés et plus', 'low')   # Estimation GE
    }
    
    return mapping.get(taille, (None, 'Non spécifié', 'low'))

def fix_missing_effectifs_inline(df: pd.DataFrame) -> tuple:
    """
    Corrige les effectifs "Non spécifié" en utilisant la Taille_Original
    Returns: (df_corrected, corrections_count)
    """
    print(f"\n🔧 Correction des effectifs manquants...")
    
    # Identifier les lignes avec effectifs manquants
    missing_mask = df['Effectifs_Description'] == 'Non spécifié'
    missing_count = missing_mask.sum()
    
    print(f"🔍 Effectifs manquants: {missing_count} ({missing_count/len(df)*100:.1f}%)")
    
    if missing_count == 0:
        print("✅ Aucun effectif manquant à corriger")
        return df, 0
    
    # Statistiques par taille avant correction
    print(f"📈 RÉPARTITION DES MANQUANTS PAR TAILLE:")
    missing_by_taille = df[missing_mask]['Taille_Original'].value_counts()
    for taille, count in missing_by_taille.items():
        print(f"   {taille}: {count} entreprises")
    
    # Appliquer les corrections
    corrections = 0
    df_copy = df.copy()
    
    for idx, row in df_copy[missing_mask].iterrows():
        taille = row['Taille_Original']
        effectifs_num, effectifs_desc, confiance = get_default_effectifs_by_taille(taille)
        
        if effectifs_num is not None:
            # Mettre à jour les colonnes
            df_copy.at[idx, 'Effectifs_Salesforce'] = effectifs_num
            df_copy.at[idx, 'Effectifs_Description'] = effectifs_desc
            df_copy.at[idx, 'Confiance_Donnee'] = confiance
            df_copy.at[idx, 'Notes_Revision'] = f"📊 Effectifs estimés par script selon Taille_Original ({taille})"
            
            corrections += 1
    
    print(f"✅ CORRECTIONS APPLIQUÉES: {corrections}")
    still_missing = (df_copy['Effectifs_Description'] == 'Non spécifié').sum()
    print(f"   Effectifs encore manquants: {still_missing}")
    
    return df_copy, corrections

def analyze_duplicates(df_companies):
    """Analyser les doublons dans le dataset"""
    print("🔍 Analyse des doublons...")
    
    # Compter les occurrences de chaque entreprise
    counts = df_companies['Organisation'].value_counts()
    duplicates = counts[counts > 1]
    
    total_companies = len(df_companies)
    unique_companies = len(counts)
    duplicate_companies = len(duplicates)
    total_duplicates = duplicates.sum() - duplicate_companies  # Nombre de lignes en trop
    
    print(f"📊 ANALYSE DU DATASET:")
    print(f"   📄 Total lignes: {total_companies}")
    print(f"   🏢 Entreprises uniques: {unique_companies}")
    print(f"   🔄 Entreprises dupliquées: {duplicate_companies}")
    print(f"   ⚠️  Lignes dupliquées: {total_duplicates}")
    print(f"   💡 Économie possible: {total_duplicates} requêtes évitées!")
    
    if duplicate_companies > 0:
        print(f"\n🔢 TOP 10 doublons:")
        for company, count in duplicates.head(10).items():
            print(f"   {company}: {count} fois")
    
    # Retourner un dictionnaire avec toutes les statistiques
    return {
        'total_lignes': total_companies,
        'entreprises_uniques': unique_companies,
        'entreprises_dupliquees': duplicate_companies,
        'lignes_dupliquees': total_duplicates,
        'top_doublons': list(duplicates.head(10).items())
    }

def process_with_duplicate_cache(df_companies, output_file, demo_limit=None):
    """Traiter les entreprises avec cache pour éviter les doublons"""
    
    # Analyser les doublons
    duplicates = analyze_duplicates(df_companies)
    
    # Limiter pour le mode demo
    if demo_limit:
        df_companies = df_companies.head(demo_limit)
        print(f"\n🧪 MODE DEMO: Traitement limité à {demo_limit} entreprises")
    
    client = INSEEApiClient()
    cache = {}  # Cache: nom_entreprise -> résultat_api
    all_results = []
    
    start_time = time.time()
    api_calls = 0
    cache_hits = 0
    
    print(f"\n🚀 Début du traitement: {time.strftime('%H:%M:%S')}")
    
    for i, row in df_companies.iterrows():
        company_name = row['Organisation']
        company_size = row.get('Taille d\'entreprise', 'N/A')
        
        # Progression
        progress = (i + 1) / len(df_companies) * 100
        elapsed = time.time() - start_time
        eta = elapsed / (i + 1) * (len(df_companies) - i - 1) if i > 0 else 0
        
        print(f"\n📊 [{i+1}/{len(df_companies)}] {company_name}")
        print(f"   ⏱️  Progression: {progress:.1f}% | ETA: {eta/60:.0f}min")
        
        # Vérifier le cache
        if company_name in cache:
            print(f"   💾 CACHE HIT - Réutilisation des données")
            cached_result = cache[company_name]
            cache_hits += 1
            
            # Créer le résultat avec les données cachées
            if cached_result:
                # Traiter avec le processeur Salesforce pour obtenir le bon statut
                salesforce_result = process_insee_result_for_salesforce(
                    company_name, company_size, cached_result
                )
                result_data = salesforce_result
            else:
                result_data = {
                    'Organisation_Original': company_name,
                    'Taille_Original': company_size,
                    'Statut_Recherche': 'NOT_FOUND'
                }
        else:
            # Nouvelle recherche API
            print(f"   🔍 Nouvelle recherche API...")
            try:
                result = client.search_alternative_names(company_name)
                api_calls += 1
                
                if result:
                    print(f"   ✅ Trouvé: {len(result.get('etablissements', []))} établissement(s)")
                    
                    # Extraire les effectifs plus efficacement
                    effectifs_info = extract_better_effectifs(result)
                    
                    result_enhanced = {**result, **effectifs_info}
                    cache[company_name] = result_enhanced
                    
                    # Traiter avec le processeur Salesforce pour obtenir le bon statut
                    salesforce_result = process_insee_result_for_salesforce(
                        company_name, company_size, result_enhanced
                    )
                    result_data = salesforce_result
                    
                    # Pause après un appel API réel pour respecter le rate limit
                    if i < len(df_companies) - 1:
                        print(f"   ⏸️  Pause 4s (respect rate limit + variations)...")
                        time.sleep(4)  # 4s pour tenir compte des variations multiples
                else:
                    print(f"   ❌ Non trouvé")
                    cache[company_name] = None
                    result_data = {
                        'Organisation_Original': company_name,
                        'Taille_Original': company_size,
                        'Statut_Recherche': 'NOT_FOUND'
                    }
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                cache[company_name] = None
                result_data = {
                    'Organisation_Original': company_name,
                    'Taille_Original': company_size,
                    'Statut_Recherche': 'ERROR'
                }
        
        all_results.append(result_data)
    
    # Sauvegarder les résultats
    temp_df = pd.DataFrame(all_results)
    temp_df.to_csv(output_file, index=False, encoding='utf-8')
    
    elapsed_total = time.time() - start_time
    print(f"\n✅ Traitement terminé en {elapsed_total/60:.1f} minutes")
    print(f"📄 Résultats: {output_file}")
    
    # Statistiques d'optimisation
    found = len([r for r in all_results if 'Trouvé' in r.get('Statut_Recherche', '')])
    print(f"\n📊 STATISTIQUES:")
    print(f"   🏢 Entreprises traitées: {len(all_results)}")
    print(f"   ✅ Trouvées: {found} ({found/len(all_results)*100:.1f}%)")
    print(f"   🔗 Appels API: {api_calls}")
    print(f"   💾 Cache hits: {cache_hits}")
    print(f"   ⚡ Économie: {cache_hits} requêtes évitées!")
    print(f"   🕰️  Temps gagné: ~{cache_hits * 3 / 60:.1f} minutes")
    
    # Retourner les statistiques pour le rapport
    stats = {
        'dataset': duplicates,
        'execution': {
            'entreprises_traitees': len(all_results),
            'entreprises_trouvees': found,
            'taux_reussite': found/len(all_results)*100 if all_results else 0,
            'appels_api': api_calls,
            'cache_hits': cache_hits,
            'temps_execution': elapsed_total/60,
            'temps_economise': cache_hits * 3 / 60
        },
        'fichiers': {
            'resultats_insee': output_file
        }
    }
    
    return stats

def extract_better_effectifs(api_result):
    """Extraction améliorée des effectifs depuis l'API INSEE"""
    effectifs_data = {
        'effectifs_etablissement': None,
        'effectifs_unite_legale': None,
        'tranche_effectifs_etablissement': None,
        'tranche_effectifs_unite_legale': None,
        'annee_effectifs': None
    }
    
    try:
        etablissements = api_result.get('etablissements', [])
        if not etablissements:
            return effectifs_data
        
        # Prendre le siège social en priorité
        siege = None
        for etab in etablissements:
            if etab.get('etablissementSiege'):
                siege = etab
                break
        
        # Sinon prendre le premier établissement
        etab = siege or etablissements[0]
        unite_legale = etab.get('uniteLegale', {})
        
        # Extraire les données d'effectifs
        effectifs_data.update({
            'tranche_effectifs_etablissement': etab.get('trancheEffectifsEtablissement'),
            'annee_effectifs_etablissement': etab.get('anneeEffectifsEtablissement'),
            'tranche_effectifs_unite_legale': unite_legale.get('trancheEffectifsUniteLegale'),
            'annee_effectifs_unite_legale': unite_legale.get('anneeEffectifsUniteLegale'),
            'denomination': unite_legale.get('denominationUniteLegale'),
            'siren': etab.get('siren'),
            'siret': etab.get('siret'),
            'categorie_entreprise': unite_legale.get('categorieEntreprise'),
            'activite_principale': unite_legale.get('activitePrincipaleUniteLegale')
        })
        
    except Exception as e:
        print(f"   ⚠️  Erreur extraction effectifs: {e}")
    
    return effectifs_data

def main():
    """Fonction principale"""
    if len(os.sys.argv) < 2:
        print("Usage: python process_optimized_duplicates.py [demo|full] [limite_demo]")
        return
    
    mode = os.sys.argv[1]
    
    # Charger le dataset
    try:
        df_companies = pd.read_csv('data/face_raw_full.csv')
        print(f"📄 Dataset chargé: {len(df_companies)} entreprises")
    except FileNotFoundError:
        print("❌ Fichier data/face_raw_full.csv non trouvé")
        return
    
    if mode == "demo":
        demo_limit = int(os.sys.argv[2]) if len(os.sys.argv) > 2 else 50
        output_file = f"data/insee_optimized_demo_{demo_limit}_results.csv"
        stats = process_with_duplicate_cache(df_companies, output_file, demo_limit)
        
        # Transformation Salesforce
        print(f"\n🔄 Transformation Salesforce...")
        salesforce_file = f"data/demo_{demo_limit}_optimized_salesforce_ready.csv"
        create_salesforce_ready_data(output_file, salesforce_file)
        
        # Correction automatique des effectifs manquants
        print(f"\n🔧 Correction automatique des effectifs manquants...")
        df_salesforce = pd.read_csv(salesforce_file)
        df_corrected, corrections_count = fix_missing_effectifs_inline(df_salesforce)
        
        # Sauvegarder le fichier corrigé avec suffixe _refactor
        corrected_file = f"data/demo_{demo_limit}_optimized_salesforce_ready_refactor.csv"
        df_corrected.to_csv(corrected_file, index=False, encoding='utf-8')
        print(f"📄 Fichier corrigé sauvegardé: {corrected_file}")
        
        # Utiliser le fichier corrigé pour les statistiques
        salesforce_file = corrected_file
        
        # Collecter les statistiques Salesforce
        salesforce_stats = collect_salesforce_stats(salesforce_file)
        stats['salesforce'] = salesforce_stats
        stats['fichiers']['donnees_salesforce'] = salesforce_file
        
        # Générer le rapport markdown
        print(f"\n📝 Génération du rapport...")
        markdown_content, timestamp = generate_markdown_report(stats, mode, demo_limit)
        report_path = save_markdown_report(markdown_content, timestamp, mode, demo_limit)
        print(f"📄 Rapport généré: {report_path}")
        
    elif mode == "full":
        output_file = "data/insee_optimized_full_results.csv"
        stats = process_with_duplicate_cache(df_companies, output_file)
        
        # Transformation Salesforce
        print(f"\n🔄 Transformation Salesforce...")
        salesforce_file = "data/full_optimized_salesforce_ready.csv"
        create_salesforce_ready_data(output_file, salesforce_file)
        
        # Correction automatique des effectifs manquants
        print(f"\n🔧 Correction automatique des effectifs manquants...")
        df_salesforce = pd.read_csv(salesforce_file)
        df_corrected, corrections_count = fix_missing_effectifs_inline(df_salesforce)
        
        # Sauvegarder le fichier corrigé avec suffixe _refactor
        corrected_file = "data/full_optimized_salesforce_ready_refactor.csv"
        df_corrected.to_csv(corrected_file, index=False, encoding='utf-8')
        print(f"📄 Fichier corrigé sauvegardé: {corrected_file}")
        
        # Utiliser le fichier corrigé pour les statistiques
        salesforce_file = corrected_file
        
        # Collecter les statistiques Salesforce
        salesforce_stats = collect_salesforce_stats(salesforce_file)
        stats['salesforce'] = salesforce_stats
        stats['fichiers']['donnees_salesforce'] = salesforce_file
        
        # Générer le rapport markdown
        print(f"\n📝 Génération du rapport...")
        markdown_content, timestamp = generate_markdown_report(stats, mode)
        report_path = save_markdown_report(markdown_content, timestamp, mode)
        print(f"📄 Rapport généré: {report_path}")
        
    else:
        print("❌ Mode invalide. Utilisez 'demo' ou 'full'")

def collect_salesforce_stats(salesforce_file: str) -> dict:
    """
    Collecte les statistiques du fichier Salesforce généré
    """
    try:
        df = pd.read_csv(salesforce_file)
        
        # Statistiques de base
        total_entreprises = len(df)
        avec_valeurs_numeriques = df['Effectifs_Salesforce'].notna().sum()
        
        # Distribution des statuts de révision
        statuts_revision = df['Statut_Revision'].value_counts().to_dict()
        
        # Niveaux de confiance
        niveaux_confiance = df['Confiance_Donnee'].value_counts().to_dict()
        
        # Statistiques sur les effectifs
        effectifs_numeriques = df['Effectifs_Salesforce'].dropna()
        
        stats = {
            'total_entreprises': total_entreprises,
            'avec_valeurs_numeriques': avec_valeurs_numeriques,
            'pourcentage_valeurs_numeriques': (avec_valeurs_numeriques / total_entreprises * 100) if total_entreprises > 0 else 0,
            'statuts_revision': statuts_revision,
            'niveaux_confiance': niveaux_confiance,
            'moyenne_effectifs': effectifs_numeriques.mean() if len(effectifs_numeriques) > 0 else 0,
            'mediane_effectifs': effectifs_numeriques.median() if len(effectifs_numeriques) > 0 else 0,
            'min_effectifs': effectifs_numeriques.min() if len(effectifs_numeriques) > 0 else 0,
            'max_effectifs': effectifs_numeriques.max() if len(effectifs_numeriques) > 0 else 0
        }
        
        return stats
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la collecte des statistiques Salesforce: {e}")
        return {
            'total_entreprises': 0,
            'avec_valeurs_numeriques': 0,
            'pourcentage_valeurs_numeriques': 0,
            'statuts_revision': {},
            'niveaux_confiance': {},
            'moyenne_effectifs': 0,
            'mediane_effectifs': 0,
            'min_effectifs': 0,
            'max_effectifs': 0
        }

def generate_markdown_report(stats: dict, mode: str, limit: int = None) -> tuple:
    """
    Génère un rapport en markdown avec les statistiques du run
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Titre du rapport
    title = f"Rapport d'exécution INSEE - {mode.upper()}"
    if limit:
        title += f" ({limit} entreprises)"
    
    markdown_content = f"""# {title}

**Date d'exécution :** {now.strftime("%d/%m/%Y à %H:%M:%S")}  
**Mode :** {mode}  
**Limite :** {limit if limit else "Aucune (traitement complet)"}

## 📊 Analyse du Dataset

| Métrique | Valeur |
|----------|--------|
| **Total lignes** | {stats['dataset']['total_lignes']:,} |
| **Entreprises uniques** | {stats['dataset']['entreprises_uniques']:,} |
| **Entreprises dupliquées** | {stats['dataset']['entreprises_dupliquees']:,} |
| **Lignes dupliquées** | {stats['dataset']['lignes_dupliquees']:,} |
| **Économie possible** | {stats['dataset']['lignes_dupliquees']:,} requêtes évitées |

### 🔢 TOP 10 Doublons
"""
    
    for i, (nom, count) in enumerate(stats['dataset']['top_doublons'][:10], 1):
        markdown_content += f"{i}. **{nom}** : {count} fois\n"
    
    markdown_content += f"""
## 🚀 Performance d'Exécution

| Métrique | Valeur |
|----------|--------|
| **Entreprises traitées** | {stats['execution']['entreprises_traitees']:,} |
| **Entreprises trouvées** | {stats['execution']['entreprises_trouvees']:,} ({stats['execution']['taux_reussite']:.1f}%) |
| **Appels API** | {stats['execution']['appels_api']:,} |
| **Cache hits** | {stats['execution']['cache_hits']:,} |
| **Économie réalisée** | {stats['execution']['cache_hits']:,} requêtes évitées |
| **Temps d'exécution** | {stats['execution']['temps_execution']:.1f} minutes |
| **Temps économisé** | ~{stats['execution']['temps_economise']:.1f} minutes |

### ⚡ Efficacité du Cache
- **Taux de cache hit :** {(stats['execution']['cache_hits'] / max(stats['execution']['entreprises_traitees'], 1) * 100):.1f}%
- **Efficacité globale :** {((stats['execution']['cache_hits'] + stats['execution']['appels_api']) / max(stats['execution']['entreprises_traitees'], 1) * 100):.1f}%

## 📈 Résultats Salesforce

### 🔍 Distribution des Statuts de Révision
"""
    
    for statut, count in stats['salesforce']['statuts_revision'].items():
        pourcentage = (count / stats['salesforce']['total_entreprises'] * 100) if stats['salesforce']['total_entreprises'] > 0 else 0
        markdown_content += f"- **{statut}** : {count:,} ({pourcentage:.1f}%)\n"
    
    markdown_content += f"""
### 💼 Effectifs pour Salesforce

| Métrique | Valeur |
|----------|--------|
| **Total entreprises** | {stats['salesforce']['total_entreprises']:,} |
| **Avec valeurs numériques** | {stats['salesforce']['avec_valeurs_numeriques']:,}/{stats['salesforce']['total_entreprises']:,} ({stats['salesforce']['pourcentage_valeurs_numeriques']:.1f}%) |
| **Moyenne des effectifs** | {stats['salesforce']['moyenne_effectifs']:,.0f} employés |
| **Médiane des effectifs** | {stats['salesforce']['mediane_effectifs']:,.0f} employés |
| **Min - Max** | {stats['salesforce']['min_effectifs']:,.0f} - {stats['salesforce']['max_effectifs']:,.0f} employés |

### 🎯 Niveaux de Confiance
"""
    
    for niveau, count in stats['salesforce']['niveaux_confiance'].items():
        pourcentage = (count / stats['salesforce']['total_entreprises'] * 100) if stats['salesforce']['total_entreprises'] > 0 else 0
        markdown_content += f"- **{niveau}** : {count:,} ({pourcentage:.1f}%)\n"
    
    markdown_content += f"""
## 📁 Fichiers Générés

- **Résultats INSEE :** `{stats['fichiers']['resultats_insee']}`
- **Données Salesforce :** `{stats['fichiers']['donnees_salesforce']}`

## ⚙️ Configuration Technique

- **API INSEE :** v3.11
- **Limite de requêtes :** 30/minute
- **Pause entre requêtes :** 4 secondes
- **Optimisation doublons :** Activée ✅
- **Cache intelligent :** Activé ✅
- **Logique de statuts :** Intelligente ✅

---
*Rapport généré automatiquement le {now.strftime("%d/%m/%Y à %H:%M:%S")}*
"""
    
    return markdown_content, timestamp

def save_markdown_report(content: str, timestamp: str, mode: str, limit: int = None) -> str:
    """
    Sauvegarde le rapport markdown avec horodatage
    """
    # Créer le répertoire docs s'il n'existe pas
    os.makedirs("docs", exist_ok=True)
    
    # Nom du fichier avec horodatage
    filename = f"rapport_insee_{mode}_{timestamp}"
    if limit:
        filename += f"_limit{limit}"
    filename += ".md"
    
    filepath = f"docs/{filename}"
    
    # Sauvegarder le fichier
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

if __name__ == "__main__":
    main()