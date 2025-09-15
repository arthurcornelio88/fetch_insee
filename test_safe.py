"""
Version optimisée qui respecte les limites de l'API INSEE (30 req/min)
"""

import pandas as pd
import time
from datetime import datetime
from insee_api_v3 import INSEEApiClient
import math

def safe_test_companies(num_companies: int = 20):
    """
    Test sécurisé avec respect strict des limites de l'API
    """
    print(f"🧪 TEST SÉCURISÉ AVEC {num_companies} ENTREPRISES")
    print("=" * 50)
    print("⚠️  Respect strict de la limite: 30 requêtes/minute")
    
    # Charger le fichier original
    try:
        df = pd.read_csv("data/face_raw.csv")
        print(f"📄 Fichier chargé: {len(df)} entreprises au total")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return
    
    # Prendre un échantillon
    sample_df = df.head(num_companies).copy()
    
    print(f"📋 Test avec {len(sample_df)} entreprises:")
    taille_counts = sample_df['Taille d\'entreprise'].value_counts()
    for taille, count in taille_counts.items():
        print(f"     {taille}: {count}")
    
    client = INSEEApiClient()
    
    # Calculer les pauses nécessaires
    # Limite: 30 req/min = 1 requête toutes les 2 secondes minimum
    # Pour être sûr, on fait 1 requête toutes les 3 secondes
    pause_between_requests = 3.0
    
    estimated_time = num_companies * pause_between_requests / 60
    print(f"⏱️  Temps estimé: {estimated_time:.1f} minutes")
    print(f"🔄 Pause entre requêtes: {pause_between_requests}s")
    
    results = []
    start_time = time.time()
    
    for idx, row in sample_df.iterrows():
        company_name = row['Organisation']
        real_idx = idx + 1
        
        print(f"\n📊 [{real_idx}/{num_companies}] {company_name}")
        
        try:
            # Une seule tentative par entreprise pour éviter les variations multiples
            search_result = client.search_company_by_name(company_name, max_results=3)
            
            if search_result and search_result.get('etablissements'):
                company_info = client.extract_company_info(search_result)
                
                if company_info:
                    result = {
                        'Organisation_Original': company_name,
                        'Taille_Original': row['Taille d\'entreprise'],
                        'SIREN': company_info['siren'],
                        'Denomination_INSEE': company_info['denomination'],
                        'Tranche_Effectifs_Code': company_info['tranche_effectifs'],
                        'Effectifs_Description': client.get_effectif_description(company_info['tranche_effectifs']),
                        'Annee_Effectifs': company_info['annee_effectifs'],
                        'Categorie_Entreprise_INSEE': company_info['categorie_entreprise'],
                        'SIRET': company_info['siret'],
                        'Date_Creation': company_info['date_creation'],
                        'Activite_Principale': company_info['activite_principale'],
                        'Etat_Administratif': company_info['etat_administratif'],
                        'Nb_Etablissements': company_info['nb_etablissements_total'],
                        'Statut_Recherche': 'Trouvé',
                        'Date_Recherche': datetime.now().isoformat()
                    }
                    
                    print(f"   ✅ {company_info['denomination']}")
                    print(f"   👥 {client.get_effectif_description(company_info['tranche_effectifs'])}")
                else:
                    result = create_simple_not_found_result(company_name, row['Taille d\'entreprise'], "Données incomplètes")
                    print(f"   ⚠️  Données incomplètes")
            else:
                result = create_simple_not_found_result(company_name, row['Taille d\'entreprise'], "Non trouvé")
                print(f"   ❌ Non trouvé")
                
        except Exception as e:
            print(f"   💥 Erreur: {e}")
            result = create_simple_not_found_result(company_name, row['Taille d\'entreprise'], f"Erreur: {str(e)}")
        
        results.append(result)
        
        # Sauvegarde incrémentale toutes les 5 entreprises
        if len(results) % 5 == 0:
            temp_df = pd.DataFrame(results)
            temp_df.to_csv("data/test_safe_progress.csv", index=False, encoding='utf-8')
            
            found = len(temp_df[temp_df['Statut_Recherche'] == 'Trouvé'])
            print(f"   📊 Progression: {found}/{len(results)} trouvées ({found/len(results)*100:.1f}%)")
        
        # Pause obligatoire entre les requêtes (sauf pour la dernière)
        if real_idx < num_companies:
            print(f"   ⏸️  Pause {pause_between_requests}s...")
            time.sleep(pause_between_requests)
    
    # Résultats finaux
    if results:
        final_df = pd.DataFrame(results)
        
        elapsed_time = time.time() - start_time
        
        # Sauvegarde finale
        final_df.to_csv("data/test_safe_final.csv", index=False, encoding='utf-8')
        
        print(f"\n" + "=" * 50)
        print(f"🎉 TEST TERMINÉ !")
        print(f"⏱️  Temps total: {elapsed_time/60:.1f} minutes")
        
        # Statistiques
        found = len(final_df[final_df['Statut_Recherche'] == 'Trouvé'])
        total = len(final_df)
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   Total: {total}")
        print(f"   ✅ Trouvées: {found} ({found/total*100:.1f}%)")
        print(f"   ❌ Non trouvées: {total-found} ({(total-found)/total*100:.1f}%)")
        
        # Effectifs disponibles
        with_effectifs = final_df[
            (final_df['Statut_Recherche'] == 'Trouvé') & 
            (final_df['Tranche_Effectifs_Code'].notna()) &
            (final_df['Tranche_Effectifs_Code'] != '')
        ]
        
        print(f"\n📈 EFFECTIFS:")
        print(f"   Avec données d'effectifs: {len(with_effectifs)}/{found}")
        
        if len(with_effectifs) > 0:
            print(f"   Répartition:")
            effectifs_counts = with_effectifs['Effectifs_Description'].value_counts()
            for effectif, count in effectifs_counts.head(5).items():
                print(f"     {effectif}: {count}")
        
        print(f"\n✅ Fichier final: data/test_safe_final.csv")
        
        return final_df
    else:
        print("❌ Aucun résultat")
        return None

def create_simple_not_found_result(company_name: str, taille_original: str, status: str):
    """
    Crée un résultat simple pour une entreprise non trouvée
    """
    return {
        'Organisation_Original': company_name,
        'Taille_Original': taille_original,
        'SIREN': None,
        'Denomination_INSEE': None,
        'Tranche_Effectifs_Code': None,
        'Effectifs_Description': None,
        'Annee_Effectifs': None,
        'Categorie_Entreprise_INSEE': None,
        'SIRET': None,
        'Date_Creation': None,
        'Activite_Principale': None,
        'Etat_Administratif': None,
        'Nb_Etablissements': None,
        'Statut_Recherche': status,
        'Date_Recherche': datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Test sécurisé avec respect des limites API...")
    
    # Attendre un peu pour laisser l'API se reposer
    print("⏳ Attente 30s pour reset de la limite API...")
    time.sleep(30)
    
    results = safe_test_companies(20)  # Test avec 20 entreprises seulement
    
    if results is not None:
        print(f"\n🎯 Test réussi ! Système prêt.")
    else:
        print(f"\n❌ Problèmes détectés")