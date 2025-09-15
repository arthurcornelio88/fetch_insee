#!/usr/bin/env python3
"""
Version optimisée pour traitement complet avec respect strict des limites API
"""

import pandas as pd
import time
from insee_api_v3 import INSEEApiClient
from salesforce_processor import create_salesforce_ready_data

def main():
    """Traitement sécurisé avec meilleure gestion des limites"""
    print("🚀 TRAITEMENT OPTIMISÉ POUR SALESFORCE - 3000 ENTREPRISES")
    print("=" * 70)
    
    # Vérifier le fichier existant
    try:
        df_existing = pd.read_csv("data/insee_search_results_complete_full.csv")
        print(f"📄 Données INSEE existantes: {len(df_existing)} entreprises")
        use_existing = True
    except FileNotFoundError:
        print("📄 Aucune donnée INSEE existante pour le fichier complet")
        use_existing = False
    
    if not use_existing:
        print("\n⚠️  ATTENTION: Traitement du fichier COMPLET (3000+ entreprises)")
        print("🕐 Temps estimé: 2.5-3 heures (3000 entreprises)")
        print("📊 Limite stricte: 30 requêtes/minute = 1 requête toutes les 2 secondes")
        print("⏱️  Délai de sécurité: 3 secondes entre requêtes")
        
        choice = input("\n❓ Options:\n1. Traitement complet (TRÈS LONG - 3h)\n2. Demo avec 50 entreprises\n3. Transformer données existantes\n\nChoix (1/2/3): ")
        
        if choice == "1":
            batch_size = 3033  # Toutes les entreprises (3034 - 1 header)
            demo_mode = False
        elif choice == "2":
            batch_size = 50  # Demo plus réaliste
            demo_mode = True
        elif choice == "3":
            # Passer directement à Salesforce
            if process_existing_data():
                return
            else:
                print("❌ Aucune donnée à transformer")
                return
        else:
            print("❌ Traitement annulé")
            return
        
        # Traitement INSEE
        success = process_insee_data(batch_size, demo_mode)
        if not success:
            print("❌ Échec du traitement INSEE")
            return
    
    # Transformation Salesforce
    process_salesforce_data()

def process_existing_data():
    """Traiter les données INSEE existantes pour Salesforce"""
    try:
        # Chercher tous les fichiers possibles
        files_to_try = [
            "data/insee_search_results_complete_full.csv",
            "data/insee_search_results_complete.csv",
            "data/test_safe_final.csv",
            "data/insee_search_results.csv"
        ]
        
        for file_path in files_to_try:
            try:
                df = pd.read_csv(file_path)
                print(f"✅ Fichier trouvé: {file_path} ({len(df)} entreprises)")
                
                # Transformation Salesforce
                output_file = "data/face_raw_full_salesforce_ready.csv"
                sf_data = create_salesforce_ready_data(file_path, output_file)
                
                if sf_data is not None:
                    print(f"🎉 Transformation réussie: {output_file}")
                    show_final_stats(sf_data)
                    return True
                    
            except FileNotFoundError:
                continue
                
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def process_insee_data(batch_size, demo_mode):
    """Traitement INSEE avec gestion optimisée des limites"""
    print(f"\n🔍 TRAITEMENT INSEE ({batch_size} entreprises)")
    print("-" * 50)
    
    try:
        # Charger les données originales
        df_companies = pd.read_csv("data/face_raw_full.csv")
        
        # Prendre seulement le nombre demandé
        if demo_mode:
            df_companies = df_companies.head(batch_size)
            print(f"📊 Mode démo: {len(df_companies)} entreprises")
        else:
            print(f"📊 Mode complet: {len(df_companies)} entreprises")
        
        # Initialiser le client
        client = INSEEApiClient()
        
        # Traitement sécurisé
        results = []
        start_time = time.time()
        
        print(f"⏱️  Début: {time.strftime('%H:%M:%S')}")
        print(f"📊 Limite: 30 req/min = 1 req/2s (sécurité: 3s)")
        
        for i, row in df_companies.iterrows():
            company_name = row['Organisation']
            
            print(f"\n📊 [{i+1}/{len(df_companies)}] {company_name}")
            
            # Recherche avec gestion d'erreur
            try:
                result = client.search_alternative_names(company_name)
                
                if result:
                    print(f"   ✅ Trouvé: {result.get('denomination', 'N/A')}")
                    result_data = {
                        'Organisation_Original': company_name,
                        'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                        **result
                    }
                else:
                    print(f"   ❌ Non trouvé")
                    result_data = {
                        'Organisation_Original': company_name,
                        'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                        'Statut_Recherche': 'Non trouvé'
                    }
                    
                results.append(result_data)
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                results.append({
                    'Organisation_Original': company_name,
                    'Taille_Original': row.get('Taille d\'entreprise', 'N/A'),
                    'Statut_Recherche': 'Erreur'
                })
            
            # Pause de sécurité
            if i < len(df_companies) - 1:  # Pas de pause après le dernier
                print(f"   ⏸️  Pause 3s...")
                time.sleep(3)
            
            # Sauvegarde intermédiaire tous les 10
            if (i + 1) % 10 == 0:
                temp_df = pd.DataFrame(results)
                temp_file = f"data/insee_temp_batch_{i+1}.csv"
                temp_df.to_csv(temp_file, index=False, encoding='utf-8')
                print(f"   💾 Sauvegarde: {temp_file}")
        
        # Sauvegarde finale
        final_df = pd.DataFrame(results)
        output_file = "data/insee_search_results_complete_full.csv" if not demo_mode else "data/insee_demo_full_results.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        elapsed = time.time() - start_time
        print(f"\n✅ Traitement terminé en {elapsed/60:.1f} minutes")
        print(f"📄 Résultats: {output_file}")
        
        # Statistiques
        found = len([r for r in results if r.get('Statut_Recherche') == 'Trouvé'])
        print(f"📊 Trouvées: {found}/{len(results)} ({found/len(results)*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        return False

def process_salesforce_data():
    """Transformation finale pour Salesforce"""
    print(f"\n🔄 TRANSFORMATION SALESFORCE")
    print("-" * 40)
    
    # Chercher le fichier de données INSEE
    input_files = [
        "data/insee_search_results_complete_full.csv",
        "data/insee_search_results_complete.csv",
        "data/insee_demo_full_results.csv",
        "data/insee_demo_results.csv",
        "data/test_safe_final.csv"
    ]
    
    input_file = None
    for file_path in input_files:
        try:
            df = pd.read_csv(file_path)
            input_file = file_path
            print(f"📁 Source: {file_path} ({len(df)} entreprises)")
            break
        except FileNotFoundError:
            continue
    
    if not input_file:
        print("❌ Aucun fichier INSEE trouvé")
        return
    
    # Transformation
    output_file = "data/face_raw_full_salesforce_ready.csv"
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