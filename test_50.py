"""
Test avec 50 entreprises pour valider le système avant traitement complet
"""

import pandas as pd
from main_search import process_companies_batch, analyze_results, save_results_incrementally
from datetime import datetime
import time

def test_50_companies():
    """
    Test avec les 50 premières entreprises du fichier
    """
    print("🧪 TEST AVEC 50 ENTREPRISES")
    print("=" * 50)
    
    # Charger le fichier original
    try:
        df = pd.read_csv("data/face_raw.csv")
        print(f"📄 Fichier chargé: {len(df)} entreprises au total")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return
    
    # Prendre les 50 premières entreprises
    sample_df = df.head(50).copy()
    
    print(f"📋 Test avec {len(sample_df)} entreprises:")
    print(f"   Répartition par taille:")
    taille_counts = sample_df['Taille d\'entreprise'].value_counts()
    for taille, count in taille_counts.items():
        print(f"     {taille}: {count} entreprises")
    
    print(f"\n🔍 Démarrage de la recherche...")
    print(f"⏱️  Estimation: ~3-5 minutes")
    
    start_time = time.time()
    
    # Traiter par lots de 10 pour avoir des retours réguliers
    batch_size = 10
    all_results = []
    
    for start_idx in range(0, len(sample_df), batch_size):
        batch_num = start_idx // batch_size + 1
        total_batches = (len(sample_df) + batch_size - 1) // batch_size
        
        print(f"\n🔄 Lot {batch_num}/{total_batches} (entreprises {start_idx + 1} à {min(start_idx + batch_size, len(sample_df))})")
        
        batch_results = process_companies_batch(sample_df, start_idx, batch_size)
        all_results.append(batch_results)
        
        # Sauvegarder les résultats intermédiaires
        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            save_results_incrementally(combined_results, "data/test_50_results_partial.csv")
            
            # Statistiques rapides
            found = len(combined_results[combined_results['Statut_Recherche'] == 'Trouvé'])
            total_processed = len(combined_results)
            print(f"   📊 Progression: {found}/{total_processed} trouvées ({found/total_processed*100:.1f}%)")
        
        # Pause entre les lots (plus courte pour le test)
        if start_idx + batch_size < len(sample_df):
            print(f"   ⏸️  Pause 1s...")
            time.sleep(1)
    
    # Combiner tous les résultats
    if all_results:
        final_results = pd.concat(all_results, ignore_index=True)
        
        # Calculer le temps total
        elapsed_time = time.time() - start_time
        
        # Sauvegarde finale
        save_results_incrementally(final_results, "data/test_50_results_final.csv")
        
        print(f"\n" + "=" * 50)
        print(f"🎉 TEST TERMINÉ !")
        print(f"⏱️  Temps total: {elapsed_time:.1f} secondes")
        print(f"⚡ Vitesse: {len(sample_df)/elapsed_time:.1f} entreprises/seconde")
        
        # Analyse détaillée des résultats
        analyze_results(final_results)
        
        # Analyse par taille d'entreprise
        print(f"\n📊 ANALYSE PAR TAILLE D'ENTREPRISE:")
        for taille in final_results['Taille_Original'].unique():
            subset = final_results[final_results['Taille_Original'] == taille]
            found = len(subset[subset['Statut_Recherche'] == 'Trouvé'])
            total = len(subset)
            print(f"   {taille}: {found}/{total} trouvées ({found/total*100:.1f}%)")
        
        # Effectifs trouvés
        effectifs_avec_donnees = final_results[
            (final_results['Statut_Recherche'] == 'Trouvé') & 
            (final_results['Tranche_Effectifs_Code'].notna()) &
            (final_results['Tranche_Effectifs_Code'] != '')
        ]
        
        print(f"\n📈 EFFECTIFS DISPONIBLES:")
        print(f"   Entreprises avec effectifs: {len(effectifs_avec_donnees)}")
        
        if len(effectifs_avec_donnees) > 0:
            print(f"   Répartition des effectifs:")
            effectifs_counts = effectifs_avec_donnees['Effectifs_Description'].value_counts()
            for effectif, count in effectifs_counts.head(8).items():
                print(f"     {effectif}: {count} entreprises")
        
        # Estimation pour le traitement complet
        total_companies = len(df)
        estimated_time = (elapsed_time / len(sample_df)) * total_companies
        estimated_minutes = estimated_time / 60
        
        print(f"\n🚀 ESTIMATION POUR LE TRAITEMENT COMPLET:")
        print(f"   Entreprises totales: {total_companies}")
        print(f"   Temps estimé: {estimated_minutes:.1f} minutes")
        print(f"   Taux de succès attendu: ~{len(final_results[final_results['Statut_Recherche'] == 'Trouvé'])/len(final_results)*100:.1f}%")
        
        print(f"\n✅ Fichiers générés:")
        print(f"   📄 data/test_50_results_final.csv")
        print(f"   📄 data/test_50_results_partial.csv")
        
        return final_results
        
    else:
        print("❌ Aucun résultat obtenu")
        return None

if __name__ == "__main__":
    print("🚀 Démarrage du test avec 50 entreprises...")
    results = test_50_companies()
    
    if results is not None:
        print(f"\n🎯 Le système est prêt pour le traitement complet !")
        print(f"   Pour lancer le traitement complet:")
        print(f"   uv run python main_search.py")
    else:
        print(f"\n❌ Problèmes détectés, vérifier la configuration")