"""
Explorateur des endpoints INSEE pour comprendre les données d'effectifs
"""

import json
from insee_api_v3 import INSEEApiClient

def explore_api_responses():
    """
    Explore les différents endpoints pour comprendre la structure des données
    """
    client = INSEEApiClient()
    
    # Test avec ADECCO qui a donné de bons résultats
    test_company = "ADECCO"
    
    print(f"🔍 Exploration des endpoints avec '{test_company}'")
    print("=" * 60)
    
    # 1. Test endpoint SIRET (ce qu'on utilise actuellement)
    print(f"\n📍 1. ENDPOINT /siret (recherche par nom)")
    print(f"URL: {client.base_url}/siret")
    
    siret_result = client.search_company_by_name(test_company, max_results=1)
    
    if siret_result and 'etablissements' in siret_result:
        etablissement = siret_result['etablissements'][0]
        siren = etablissement.get('siren')
        
        print(f"✅ Résultat trouvé:")
        print(f"   SIREN trouvé: {siren}")
        print(f"   SIRET: {etablissement.get('siret')}")
        
        # Extraire les effectifs depuis l'unité légale
        unite_legale = etablissement.get('uniteLegale', {})
        tranche_effectifs_ul = unite_legale.get('trancheEffectifsUniteLegale')
        tranche_effectifs_etab = etablissement.get('trancheEffectifsEtablissement')
        
        print(f"   📊 Effectifs Unité Légale: {tranche_effectifs_ul}")
        print(f"   📊 Effectifs Établissement: {tranche_effectifs_etab}")
        print(f"   📋 Catégorie Entreprise: {unite_legale.get('categorieEntreprise')}")
        
        # 2. Test endpoint SIREN direct
        if siren:
            print(f"\n📍 2. ENDPOINT /siren/{siren} (accès direct)")
            print(f"URL: {client.base_url}/siren/{siren}")
            
            siren_result = get_siren_details(client, siren)
            
            if siren_result and 'uniteLegale' in siren_result:
                unite_legale_directe = siren_result['uniteLegale']
                print(f"✅ Données unité légale directe:")
                print(f"   📊 Effectifs: {unite_legale_directe.get('trancheEffectifsUniteLegale')}")
                print(f"   📅 Année effectifs: {unite_legale_directe.get('anneeEffectifsUniteLegale')}")
                print(f"   🏢 Catégorie: {unite_legale_directe.get('categorieEntreprise')}")
                print(f"   📋 Dénomination: {unite_legale_directe.get('denominationUniteLegale')}")
        
        # 3. Afficher la structure complète pour comprendre
        print(f"\n📍 3. STRUCTURE COMPLÈTE DES DONNÉES")
        print("=" * 40)
        print(f"Structure uniteLegale depuis /siret:")
        print_json_structure(unite_legale, prefix="  ")
        
    else:
        print(f"❌ Aucun résultat trouvé")

def get_siren_details(client: INSEEApiClient, siren: str):
    """
    Récupère les détails d'une entreprise via l'endpoint SIREN
    """
    headers = client.get_headers()
    url = f"{client.base_url}/siren/{siren}"
    
    try:
        import requests
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:200]}")
            return {}
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {}

def print_json_structure(data, prefix="", max_depth=2, current_depth=0):
    """
    Affiche la structure d'un objet JSON de manière lisible
    """
    if current_depth >= max_depth:
        return
        
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}: ({type(value).__name__})")
                if current_depth < max_depth - 1:
                    print_json_structure(value, prefix + "  ", max_depth, current_depth + 1)
            else:
                print(f"{prefix}{key}: {value}")
    elif isinstance(data, list) and data:
        print(f"{prefix}[0]: ({type(data[0]).__name__})")
        if current_depth < max_depth - 1:
            print_json_structure(data[0], prefix + "  ", max_depth, current_depth + 1)

def test_multiple_companies():
    """
    Test avec plusieurs entreprises pour voir les variations
    """
    client = INSEEApiClient()
    companies = ["ADECCO", "AIR FRANCE", "ALLIANZ"]
    
    print(f"\n🧪 TEST COMPARATIF - Effectifs par entreprise")
    print("=" * 60)
    
    for company in companies:
        print(f"\n--- {company} ---")
        result = client.search_company_by_name(company, max_results=1)
        
        if result and 'etablissements' in result:
            etab = result['etablissements'][0]
            ul = etab.get('uniteLegale', {})
            
            print(f"SIREN: {etab.get('siren')}")
            print(f"Dénomination: {ul.get('denominationUniteLegale')}")
            print(f"Effectifs UL: {ul.get('trancheEffectifsUniteLegale')}")
            print(f"Année: {ul.get('anneeEffectifsUniteLegale')}")
            print(f"Catégorie: {ul.get('categorieEntreprise')}")
        else:
            print("❌ Non trouvé")

if __name__ == "__main__":
    print("🕵️ Exploration des endpoints INSEE Sirene")
    
    explore_api_responses()
    test_multiple_companies()
    
    print(f"\n💡 CONCLUSION:")
    print(f"   ✅ Utiliser /siret pour chercher par nom")
    print(f"   ✅ Extraire trancheEffectifsUniteLegale (pas Etablissement)")
    print(f"   ✅ L'endpoint /siren/{{siren}} donne les mêmes infos")
    print(f"   ⚠️  Certaines entreprises n'ont pas d'effectifs renseignés")