#!/usr/bin/env python3
"""
Traitement optimisé pour 3000 entreprises - face_raw_full.csv
Système de reprise automatique et traitement par blocs
"""

import pandas as pd
import time
import os
from insee_api_v3 import INSEEApiClient
from salesforce_processor import create_salesforce_ready_data

def main():
    """Traitement principal pour 3000 entreprises"""
    print("🚀 TRAITEMENT COMPLET - 3000 ENTREPRISES")
    print("=" * 70)
    
    # Vérifier le fichier source
    if not os.path.exists("data/face_raw_full.csv"):
        print("❌ Fichier face_raw_full.csv non trouvé")
        return
    
    df_full = pd.read_csv("data/face_raw_full.csv")
    print(f"📄 Fichier chargé: {len(df_full)} entreprises")
    
    # Options de traitement
    print("\n📊 OPTIONS DE TRAITEMENT:")
    print("1. 🚀 Traitement complet (3000 entreprises - 2.5h)")
    print("2. 🧪 Demo rapide (100 entreprises - 5 min)")
    print("3. 🔄 Reprendre traitement interrompu")
    print("4. 📊 Transformer données existantes → Salesforce")
    
    choice = input("\nChoix (1/2/3/4): ").strip()
    
    if choice == "1":
        process_full_dataset(df_full)
    elif choice == "2":
        process_demo(df_full.head(100))
    elif choice == "3":
        resume_processing(df_full)
    elif choice == "4":
        transform_to_salesforce()
    else:
        print("❌ Choix invalide")

def process_full_dataset(df_companies):
    """Traitement complet avec sauvegarde par blocs"""
    total = len(df_companies)
    block_size = 100  # Sauvegarder tous les 100
    
    print(f"\n🔍 TRAITEMENT COMPLET: {total} entreprises")
    print(f"⏱️  Temps estimé: {total * 3 / 60:.0f} minutes ({total * 3 / 3600:.1f}h)")
    print(f"💾 Sauvegarde tous les {block_size} traitements")
    
    confirm = input("\n❓ Confirmer le traitement complet ? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Traitement annulé")
        return
    
    start_idx = 0
    output_file = "data/insee_search_results_complete_full.csv"
    
    # Vérifier si on a déjà des résultats partiels
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        start_idx = len(existing_df)
        print(f"📄 Reprise à partir de l'entreprise {start_idx + 1}")
    
    if start_idx >= total:
        print("✅ Traitement déjà terminé !")
        transform_to_salesforce()
        return
    
    process_companies_range(df_companies, start_idx, total, block_size, output_file)

def process_demo(df_demo):
    """Traitement demo rapide"""
    print(f"\n🧪 DEMO: {len(df_demo)} entreprises")
    print(f"⏱️  Temps estimé: {len(df_demo) * 3 / 60:.1f} minutes")
    
    output_file = "data/insee_demo_100_results.csv"
    process_companies_range(df_demo, 0, len(df_demo), 25, output_file)
    
    # Transformation Salesforce automatique
    print("\n🔄 Transformation Salesforce...")
    sf_output = "data/demo_100_salesforce_ready.csv"
    create_salesforce_ready_data(output_file, sf_output)
    print(f"✅ Demo terminée: {sf_output}")

def process_companies_range(df_companies, start_idx, end_idx, block_size, output_file):
    """Traiter une plage d'entreprises avec sauvegarde par blocs"""
    client = INSEEApiClient()
    all_results = []
    
    # Charger les résultats existants si le fichier existe
    if os.path.exists(output_file) and start_idx > 0:
        existing_df = pd.read_csv(output_file)
        all_results = existing_df.to_dict('records')
        print(f"📄 {len(all_results)} résultats existants chargés")
    
    start_time = time.time()
    processed = start_idx
    
    print(f"\n🚀 Début du traitement: {time.strftime('%H:%M:%S')}")
    
    for i in range(start_idx, min(end_idx, len(df_companies))):
        row = df_companies.iloc[i]
        company_name = row['Organisation']
        
        # Progression
        progress = (i - start_idx + 1) / (end_idx - start_idx) * 100
        elapsed = time.time() - start_time
        eta = elapsed / (i - start_idx + 1) * (end_idx - i - 1) if i > start_idx else 0
        
        print(f"\n📊 [{i+1}/{len(df_companies)}] {company_name}")
        print(f"   ⏱️  Progression: {progress:.1f}% | ETA: {eta/60:.0f}min")
        
        try:
            result = client.search_alternative_names(company_name)
            
            if result:
                print(f"   ✅ Trouvé: {result.get('denomination', 'N/A')}")
                result_data = {
                    'Organisation_Original': company_name,
                    'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                    'Statut_Recherche': 'Trouvé',  # 🔥 COLONNE MANQUANTE AJOUTÉE !
                    **result
                }
            else:
                print(f"   ❌ Non trouvé")
                result_data = {
                    'Organisation_Original': company_name,
                    'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                    'Statut_Recherche': 'Non trouvé'
                }
                
            all_results.append(result_data)
            processed += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            all_results.append({
                'Organisation_Original': company_name,
                'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                'Statut_Recherche': 'Erreur'
            })
        
        # Sauvegarde par blocs
        if (i + 1) % block_size == 0 or i == end_idx - 1:
            temp_df = pd.DataFrame(all_results)
            temp_df.to_csv(output_file, index=False, encoding='utf-8')
            found = len([r for r in all_results if r.get('Statut_Recherche') == 'Trouvé'])
            print(f"   💾 Sauvegarde: {len(all_results)} entreprises ({found} trouvées)")
        
        # Pause de sécurité
        if i < end_idx - 1:
            print(f"   ⏸️  Pause 3s...")
            time.sleep(3)
    
    elapsed_total = time.time() - start_time
    print(f"\n✅ Traitement terminé en {elapsed_total/60:.1f} minutes")
    print(f"📄 Résultats: {output_file}")
    
    # Statistiques finales
    found = len([r for r in all_results if r.get('Statut_Recherche') == 'Trouvé'])
    print(f"📊 Trouvées: {found}/{len(all_results)} ({found/len(all_results)*100:.1f}%)")

def resume_processing(df_full):
    """Reprendre un traitement interrompu"""
    output_file = "data/insee_search_results_complete_full.csv"
    
    if not os.path.exists(output_file):
        print("❌ Aucun traitement en cours à reprendre")
        return
    
    existing_df = pd.read_csv(output_file)
    start_idx = len(existing_df)
    total = len(df_full)
    
    if start_idx >= total:
        print("✅ Traitement déjà terminé !")
        transform_to_salesforce()
        return
    
    print(f"📄 Reprise du traitement:")
    print(f"   Déjà traité: {start_idx}/{total} ({start_idx/total*100:.1f}%)")
    print(f"   Restant: {total - start_idx} entreprises")
    print(f"   Temps estimé: {(total - start_idx) * 3 / 60:.0f} minutes")
    
    confirm = input("\n❓ Reprendre le traitement ? (y/N): ")
    if confirm.lower() == 'y':
        process_companies_range(df_full, start_idx, total, 100, output_file)

def transform_to_salesforce():
    """Transformer les données INSEE → Salesforce"""
    print(f"\n🔄 TRANSFORMATION SALESFORCE")
    print("-" * 40)
    
    # Chercher le fichier de données INSEE
    input_files = [
        "data/insee_search_results_complete_full.csv",
        "data/insee_demo_100_results.csv"
    ]
    
    input_file = None
    for file_path in input_files:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            input_file = file_path
            print(f"📁 Source: {file_path} ({len(df)} entreprises)")
            break
    
    if not input_file:
        print("❌ Aucun fichier INSEE trouvé")
        return
    
    # Déterminer le fichier de sortie
    if "complete_full" in input_file:
        output_file = "data/face_raw_full_salesforce_ready.csv"
    else:
        output_file = "data/demo_100_salesforce_ready.csv"
    
    # Transformation
    print(f"📁 Destination: {output_file}")
    sf_data = create_salesforce_ready_data(input_file, output_file)
    
    if sf_data is not None:
        print(f"\n🎉 TRANSFORMATION TERMINÉE!")
        print(f"📄 Fichier Salesforce: {output_file}")
        show_final_stats(sf_data)
    else:
        print("❌ Échec de la transformation Salesforce")

def show_final_stats(sf_data):
    """Afficher les statistiques finales"""
    print(f"\n📈 STATISTIQUES FINALES:")
    print(f"   Total: {len(sf_data)} entreprises")
    
    # Statuts
    statuts = sf_data['Statut_Revision'].value_counts()
    for statut, count in statuts.items():
        print(f"   {statut}: {count} ({count/len(sf_data)*100:.1f}%)")
    
    # Effectifs
    effectifs = sf_data['Effectifs_Salesforce'].dropna()
    if len(effectifs) > 0:
        print(f"\n💼 EFFECTIFS SALESFORCE:")
        print(f"   Avec données: {len(effectifs)}/{len(sf_data)} ({len(effectifs)/len(sf_data)*100:.1f}%)")
        print(f"   Moyenne: {effectifs.mean():.0f} employés")

if __name__ == "__main__":
    main()