"""
Script principal pour récupérer les effectifs des entreprises via l'API INSEE
"""

import pandas as pd
import time
from datetime import datetime
from insee_api_v3 import INSEEApiClient
import json

def process_companies_batch(companies_df: pd.DataFrame, start_idx: int = 0, batch_size: int = 50):
    """
    Traite un lot d'entreprises via l'API INSEE
    """
    client = INSEEApiClient()
    
    total_companies = len(companies_df)
    end_idx = min(start_idx + batch_size, total_companies)
    
    print(f"🏭 Traitement des entreprises {start_idx + 1} à {end_idx} sur {total_companies}")
    
    results = []
    
    for idx in range(start_idx, end_idx):
        row = companies_df.iloc[idx]
        company_name = row['Organisation']
        
        print(f"\n📊 [{idx + 1}/{total_companies}] Recherche: {company_name}")
        
        try:
            # Recherche de l'entreprise
            search_result = client.search_alternative_names(company_name)
            
            if search_result and search_result.get('etablissements'):
                # Extraire les informations
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
                    
                    print(f"   ✅ Trouvé: {company_info['denomination']}")
                    print(f"   📈 SIREN: {company_info['siren']}")
                    print(f"   👥 Effectifs: {client.get_effectif_description(company_info['tranche_effectifs'])}")
                    print(f"   📅 Année: {company_info['annee_effectifs']}")
                    print(f"   🏢 Catégorie: {company_info['categorie_entreprise']}")
                else:
                    result = create_not_found_result(company_name, row['Taille d\'entreprise'], "Données incomplètes")
                    print(f"   ⚠️  Données incomplètes")
            else:
                result = create_not_found_result(company_name, row['Taille d\'entreprise'], "Non trouvé")
                print(f"   ❌ Non trouvé")
                
        except Exception as e:
            print(f"   💥 Erreur: {e}")
            result = create_not_found_result(company_name, row['Taille d\'entreprise'], f"Erreur: {str(e)}")
        
        results.append(result)
        
        # Pause entre les requêtes pour respecter les limites de l'API
        time.sleep(0.5)
    
    return pd.DataFrame(results)

def create_not_found_result(company_name: str, taille_original: str, status: str):
    """
    Crée un résultat pour une entreprise non trouvée
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

def save_results_incrementally(results_df: pd.DataFrame, output_file: str = "data/entreprises_effectifs.csv"):
    """
    Sauvegarde les résultats de manière incrémentale
    """
    try:
        results_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Résultats sauvegardés: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Erreur de sauvegarde: {e}")
        return False

def analyze_results(results_df: pd.DataFrame):
    """
    Analyse les résultats obtenus
    """
    total = len(results_df)
    found = len(results_df[results_df['Statut_Recherche'] == 'Trouvé'])
    not_found = total - found
    
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   Total traité: {total}")
    print(f"   ✅ Trouvées: {found} ({found/total*100:.1f}%)")
    print(f"   ❌ Non trouvées: {not_found} ({not_found/total*100:.1f}%)")
    
    if found > 0:
        print(f"\n📈 Répartition des effectifs trouvés:")
        effectifs_counts = results_df[results_df['Statut_Recherche'] == 'Trouvé']['Effectifs_Description'].value_counts()
        for effectif, count in effectifs_counts.head(10).items():
            print(f"   {effectif}: {count} entreprises")

def main():
    """
    Fonction principale
    """
    print("🚀 Démarrage de la recherche d'effectifs d'entreprises INSEE")
    
    # Charger le fichier CSV
    csv_path = "data/face_raw.csv"
    try:
        df = pd.read_csv(csv_path)
        print(f"📄 Fichier chargé: {len(df)} entreprises")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return
    
    # Traitement par lots pour éviter de surcharger l'API
    batch_size = 20  # Commencer avec un petit lot
    all_results = []
    
    for start_idx in range(0, len(df), batch_size):
        print(f"\n🔄 Traitement du lot {start_idx//batch_size + 1}")
        
        batch_results = process_companies_batch(df, start_idx, batch_size)
        all_results.append(batch_results)
        
        # Sauvegarder les résultats intermédiaires
        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            save_results_incrementally(combined_results)
        
        # Pause entre les lots
        if start_idx + batch_size < len(df):
            print(f"⏸️  Pause de 2 secondes avant le prochain lot...")
            time.sleep(2)
    
    # Combiner tous les résultats
    if all_results:
        final_results = pd.concat(all_results, ignore_index=True)
        
        # Sauvegarde finale
        save_results_incrementally(final_results, "data/entreprises_effectifs_final.csv")
        
        # Analyse des résultats
        analyze_results(final_results)
        
        print(f"\n✅ Traitement terminé!")
        print(f"   Fichier final: data/entreprises_effectifs_final.csv")
    else:
        print("❌ Aucun résultat obtenu")

if __name__ == "__main__":
    main()