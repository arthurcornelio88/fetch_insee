"""
Module pour l'API INSEE Sirene V3
Utilise l'authentification par clés API directement dans les headers
Basé sur la documentation officielle INSEE
"""

import os
import requests
import json
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import time
import urllib.parse

# Charger les variables d'environnement
load_dotenv()

class INSEEApiClient:
    """Client pour l'API INSEE Sirene V3"""
    
    def __init__(self):
        # L'API INSEE Sirene utilise une clé API spécifique
        self.api_key = os.getenv('SIRENE_API_KEY')
        # URL de base correcte pour l'API Sirene 3.11
        self.base_url = 'https://api.insee.fr/api-sirene/3.11'
        
        if not self.api_key:
            raise ValueError("SIRENE_API_KEY doit être définie dans le fichier .env")
        
        print(f"✅ Client INSEE initialisé")
        print(f"   API Key: {self.api_key[:10]}...")
        print(f"   Base URL: {self.base_url}")
    
    def get_headers(self) -> Dict[str, str]:
        """Prépare les headers d'authentification pour l'API INSEE"""
        return {
            'X-INSEE-Api-Key-Integration': self.api_key,
            'Accept': 'application/json',
            'User-Agent': 'Data-INSEE-Analysis/1.0'
        }
    
    def search_company_by_name(self, company_name: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Recherche une entreprise par son nom dans l'API Sirene
        """
        headers = self.get_headers()
        
        # Nettoyer le nom de l'entreprise pour la recherche
        clean_name = company_name.strip().replace('"', '')
        
        # URL pour rechercher dans les unités légales
        url = f"{self.base_url}/siret"
        
        # Paramètres de recherche
        params = {
            'q': f'denominationUniteLegale:"{clean_name}"',
            'nombre': max_results
        }
        
        try:
            print(f"🔍 Recherche de: {company_name}")
            print(f"   URL: {url}")
            print(f"   Paramètres: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            
            print(f"📊 Code de réponse: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                nb_etablissements = len(result.get('etablissements', []))
                print(f"✅ {nb_etablissements} établissement(s) trouvé(s)")
                return result
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(f"   Réponse: {response.text[:300]}...")
                return {}
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la recherche de {company_name}: {e}")
            return {}
    
    def search_alternative_names(self, company_name: str) -> Dict[str, Any]:
        """
        Recherche avec des variantes du nom d'entreprise (optimisé pour rate limit)
        """
        # Créer les variations possibles
        variations = [company_name]
        
        # Ajouter variation en majuscules si différente
        upper_name = company_name.upper()
        if upper_name != company_name:
            variations.append(upper_name)
        
        # Ajouter premier mot si il y a des espaces
        if ' ' in company_name:
            first_word = company_name.split()[0]
            if first_word not in variations:
                variations.append(first_word)
        
        for i, variation in enumerate(variations):
            if variation != company_name:
                print(f"🔄 Essai avec variation: {variation}")
            
            result = self.search_company_by_name(variation, max_results=5)
            if result and result.get('etablissements'):
                return result
                
            # Pause entre variations pour éviter le rate limit
            if i < len(variations) - 1:
                print(f"   ⏸️  Pause 2s entre variations...")
                time.sleep(2)
        
        print(f"❌ Aucun résultat trouvé pour {company_name} et ses variations")
        return {}
    
    def extract_company_info(self, search_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrait les informations principales d'une entreprise depuis les résultats de recherche
        """
        try:
            if not search_result or 'etablissements' not in search_result:
                return None
            
            etablissements = search_result['etablissements']
            if not etablissements:
                return None
            
            # Prendre le premier établissement (généralement le siège)
            etablissement = etablissements[0]
            unite_legale = etablissement.get('uniteLegale', {})
            
            return {
                'siren': etablissement.get('siren'),
                'denomination': unite_legale.get('denominationUniteLegale'),
                'tranche_effectifs': unite_legale.get('trancheEffectifsUniteLegale'),
                'annee_effectifs': unite_legale.get('anneeEffectifsUniteLegale'),
                'categorie_entreprise': unite_legale.get('categorieEntreprise'),
                'date_creation': unite_legale.get('dateCreationUniteLegale'),
                'siret': etablissement.get('siret'),
                'nb_etablissements_total': len(etablissements),
                'activite_principale': unite_legale.get('activitePrincipaleUniteLegale'),
                'etat_administratif': unite_legale.get('etatAdministratifUniteLegale')
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des infos: {e}")
            return None
    
    def get_effectif_description(self, tranche_code: str) -> str:
        """
        Convertit le code de tranche d'effectifs en description lisible
        Codes officiels INSEE 2025
        """
        if not tranche_code:
            return 'Non renseigné'
            
        tranches = {
            'NN': 'Non renseigné',
            '00': '0 salarié',
            '01': '1 ou 2 salariés',
            '02': '3 à 5 salariés',
            '03': '6 à 9 salariés',
            '11': '10 à 19 salariés',
            '12': '20 à 49 salariés',
            '21': '50 à 99 salariés',
            '22': '100 à 199 salariés',
            '31': '200 à 249 salariés',
            '32': '250 à 499 salariés',
            '41': '500 à 999 salariés',
            '42': '1000 à 1999 salariés',
            '51': '2000 à 4999 salariés',
            '52': '5000 à 9999 salariés',
            '53': '10000 salariés et plus'
        }
        return tranches.get(str(tranche_code), f'Code inconnu: {tranche_code}')

# Test du module
if __name__ == "__main__":
    try:
        print("🚀 Test du client INSEE API...")
        client = INSEEApiClient()
        
        # Test avec une entreprise connue
        print("\n🔍 Test de recherche...")
        test_companies = ["ADECCO", "AIR FRANCE", "ALLIANZ"]
        
        for company in test_companies:
            print(f"\n--- Test avec {company} ---")
            result = client.search_company_by_name(company)
            
            if result:
                info = client.extract_company_info(result)
                if info:
                    print(f"✅ Trouvé: {info['denomination']}")
                    print(f"   SIREN: {info['siren']}")
                    print(f"   Effectifs: {client.get_effectif_description(info['tranche_effectifs'])}")
                    break  # Arrêter après le premier succès
            else:
                print(f"❌ Pas de résultat pour {company}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()