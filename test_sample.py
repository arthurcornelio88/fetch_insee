"""
Test rapide avec un échantillon d'entreprises
"""

import pandas as pd
from main_search import process_companies_batch
from datetime import datetime

def test_sample():
    """
    Test avec un petit échantillon
    """
    print("🧪 Test avec un échantillon d'entreprises")
    
    # Charger le fichier original
    df = pd.read_csv("data/face_raw.csv")
    
    # Prendre les 5 premières entreprises pour le test
    sample_df = df.head(5).copy()
    
    print(f"📋 Entreprises de test:")
    for idx, row in sample_df.iterrows():
        print(f"   {idx + 1}. {row['Organisation']} ({row['Taille d\'entreprise']})")
    
    # Traiter l'échantillon
    print(f"\n🔍 Démarrage de la recherche...")
    results = process_companies_batch(sample_df, 0, 5)
    
    # Afficher les résultats
    print(f"\n📊 Résultats du test:")
    for idx, row in results.iterrows():
        status = "✅" if row['Statut_Recherche'] == 'Trouvé' else "❌"
        print(f"   {status} {row['Organisation_Original']}")
        if row['Statut_Recherche'] == 'Trouvé':
            print(f"      SIREN: {row['SIREN']}")
            print(f"      Effectifs: {row['Effectifs_Description']}")
    
    # Sauvegarder le test
    results.to_csv("data/test_sample_results.csv", index=False, encoding='utf-8')
    print(f"\n💾 Résultats du test sauvegardés: data/test_sample_results.csv")
    
    return results

if __name__ == "__main__":
    test_sample()