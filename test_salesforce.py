#!/usr/bin/env python3
"""
Test du module de transformation Salesforce
"""

import pandas as pd
from salesforce_processor import convert_tranche_to_numeric, create_salesforce_ready_data, analyze_data_quality

def test_salesforce_processor():
    """Test du processeur Salesforce avec les données du test sécurisé"""
    print("🧪 TEST DU PROCESSEUR SALESFORCE")
    print("=" * 50)
    
    # 1. Test de conversion des tranches
    print("\n📊 Test de conversion des tranches d'effectifs:")
    test_tranches = [
        "1 ou 2 salariés",
        "10 à 19 salariés", 
        "100 à 199 salariés",
        "1000 à 1999 salariés",
        "2000 à 4999 salariés",
        "5000 à 9999 salariés",
        "Non renseigné",
        None,
        ""
    ]
    
    for tranche in test_tranches:
        numeric, confiance, statut = convert_tranche_to_numeric(tranche)
        print(f"   '{tranche}' → {numeric} (conf: {confiance}, statut: {statut})")
    
    # 2. Test avec les données réelles du test sécurisé
    print("\n📄 Chargement des données de test...")
    try:
        df_test = pd.read_csv("data/test_safe_final.csv")
        print(f"   ✅ {len(df_test)} entreprises chargées")
        print(f"   Colonnes: {list(df_test.columns)}")
        
        # Traitement Salesforce
        print("\n🔄 Traitement Salesforce...")
        output_file = "data/test_salesforce_ready.csv"
        input_file = "data/test_safe_final.csv"
        
        sf_data = create_salesforce_ready_data(input_file, output_file)
        
        if sf_data is not None:
            print(f"   ✅ {len(sf_data)} entreprises traitées")
            print(f"   Nouvelles colonnes: {list(sf_data.columns)}")
        else:
            print("   ❌ Erreur lors du traitement")
            return False
        
        # Analyse des résultats
        print("\n📈 ANALYSE DES RÉSULTATS:")
        print(f"   Total entreprises: {len(sf_data)}")
        
        # Répartition par statut
        statuts = sf_data['Statut_Revision'].value_counts()
        for statut, count in statuts.items():
            print(f"   {statut}: {count} ({count/len(sf_data)*100:.1f}%)")
        
        # Statistiques sur les effectifs numériques
        effectifs_num = sf_data['Effectifs_Salesforce'].dropna()
        if len(effectifs_num) > 0:
            print(f"\n💼 EFFECTIFS NUMÉRIQUES:")
            print(f"   Entreprises avec effectifs: {len(effectifs_num)}/{len(sf_data)}")
            print(f"   Moyenne: {effectifs_num.mean():.0f} employés")
            print(f"   Médiane: {effectifs_num.median():.0f} employés")
            print(f"   Min: {effectifs_num.min():.0f}, Max: {effectifs_num.max():.0f}")
        
        # Aperçu des données
        print("\n📋 APERÇU DES DONNÉES TRANSFORMÉES:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(sf_data[['Organisation_Original', 'Denomination_INSEE', 'Effectifs_Description', 'Effectifs_Salesforce', 'Statut_Revision']].head(10))
        
        # Sauvegarde
        print(f"\n💾 Données sauvegardées: {output_file}")
        
        return True
        
    except FileNotFoundError:
        print("   ❌ Fichier test_safe_final.csv non trouvé")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_salesforce_processor()
    if success:
        print("\n🎉 Test Salesforce réussi !")
    else:
        print("\n❌ Test Salesforce échoué")