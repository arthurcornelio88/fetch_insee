#!/usr/bin/env python3
"""
Traitement complet du dataset pour Salesforce
167 entreprises avec respect des limites API INSEE
"""

import pandas as pd
from main_search import process_companies_batch
from salesforce_processor import create_salesforce_ready_data
import time

def main():
    """Traitement complet avec transformation Salesforce"""
    print("🚀 TRAITEMENT COMPLET POUR SALESFORCE")
    print("=" * 60)
    
    # 1. Vérifier si on a déjà les données INSEE complètes
    try:
        df_existing = pd.read_csv("data/insee_search_results_complete.csv")
        print(f"📄 Données INSEE existantes trouvées: {len(df_existing)} entreprises")
        
        # Vérifier si le fichier est complet
        df_original = pd.read_csv("data/face_raw.csv")
        
        if len(df_existing) >= len(df_original):
            print("✅ Données INSEE complètes, passage direct à Salesforce")
            use_existing = True
        else:
            print(f"⚠️  Données incomplètes ({len(df_existing)}/{len(df_original)})")
            use_existing = False
            
    except FileNotFoundError:
        print("📄 Aucune donnée INSEE existante, traitement complet nécessaire")
        use_existing = False
    
    # 2. Traitement INSEE si nécessaire
    if not use_existing:
        print("\n🔍 ÉTAPE 1: RECHERCHE INSEE COMPLÈTE")
        print("-" * 40)
        print("⏱️  Temps estimé: 8-9 minutes (167 entreprises × 3s)")
        print("📊 Limite API: 30 requêtes/minute")
        
        confirmation = input("\n❓ Lancer la recherche complète ? (y/N): ")
        if confirmation.lower() != 'y':
            print("❌ Traitement annulé")
            return
        
        # Lancer le traitement INSEE
        print("\n🚀 Démarrage du traitement INSEE...")
        
        # Charger les données originales
        df_companies = pd.read_csv("data/face_raw.csv")
        print(f"📄 {len(df_companies)} entreprises à traiter")
        
        # Traitement par batch de toutes les entreprises
        process_companies_batch(df_companies, start_idx=0, batch_size=len(df_companies))
        
        # Vérifier si ça a réussi
        try:
            df_result = pd.read_csv("data/insee_search_results_complete.csv")
            print(f"✅ Traitement INSEE terminé: {len(df_result)} entreprises")
        except FileNotFoundError:
            print("❌ Échec du traitement INSEE")
            return
    
    # 3. Transformation Salesforce
    print("\n🔄 ÉTAPE 2: TRANSFORMATION SALESFORCE")
    print("-" * 40)
    
    input_file = "data/insee_search_results_complete.csv"
    output_file = "data/face_raw_salesforce_ready.csv"
    
    print(f"📁 Fichier source: {input_file}")
    print(f"📁 Fichier destination: {output_file}")
    
    # Lancer la transformation
    sf_data = create_salesforce_ready_data(input_file, output_file)
    
    if sf_data is not None:
        print(f"\n🎉 TRAITEMENT TERMINÉ AVEC SUCCÈS!")
        print(f"📊 {len(sf_data)} entreprises traitées")
        print(f"💾 Fichier Salesforce: {output_file}")
        
        # Statistiques finales
        print("\n📈 STATISTIQUES FINALES:")
        statuts = sf_data['Statut_Revision'].value_counts()
        for statut, count in statuts.items():
            print(f"   {statut}: {count} ({count/len(sf_data)*100:.1f}%)")
        
        effectifs_num = sf_data['Effectifs_Salesforce'].dropna()
        if len(effectifs_num) > 0:
            print(f"\n💼 EFFECTIFS SALESFORCE:")
            print(f"   Avec données numériques: {len(effectifs_num)}/{len(sf_data)} ({len(effectifs_num)/len(sf_data)*100:.1f}%)")
            print(f"   Moyenne: {effectifs_num.mean():.0f} employés")
            
        print(f"\n✅ Fichier prêt pour Salesforce: {output_file}")
        
    else:
        print("❌ Échec de la transformation Salesforce")

if __name__ == "__main__":
    main()