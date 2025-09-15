"""
Module d'authentification pour l'API INSEE Sirene
Gère l'authentification OAuth2 et les appels API
"""

import os
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()

class INSEEAPIClient:
    """Client pour l'API INSEE Sirene"""
    
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.base_url = 'https://api.insee.fr/entreprises/sirene/V3'
        self.token_url = 'https://api.insee.fr/token'
        self.access_token = None
        self.token_expires_at = 0
        
        if not self.client_id or not self.client_secret:
            raise ValueError("CLIENT_ID et CLIENT_SECRET doivent être définis dans le fichier .env")
    
    def get_access_token(self) -> str:
        """Obtient un token d'accès OAuth2"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        auth = (self.client_id, self.client_secret)
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data, auth=auth)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token expire généralement en 1 heure, on soustrait 5 minutes de sécurité
            self.token_expires_at = time.time() + token_data.get('expires_in', 3600) - 300
            
            print("✅ Token d'accès obtenu avec succès")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de l'obtention du token: {e}")
            raise
    
    def search_company_by_name(self, company_name: str) -> Dict[str, Any]:
        """Recherche une entreprise par son nom via l'API Sirene"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # URL pour rechercher dans les unités légales
        url = f"{self.base_url}/siret"
        
        params = {
            'q': f'denominationUniteLegale:"{company_name}"',
            'nombre': 20  # Limiter les résultats
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la recherche de {company_name}: {e}")
            return {}
    
    def get_company_details_by_siren(self, siren: str) -> Dict[str, Any]:
        """Récupère les détails d'une entreprise par son SIREN"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}/siret"
        
        params = {
            'q': f'siren:{siren}'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des détails pour SIREN {siren}: {e}")
            return {}
    
    def extract_employee_count(self, company_data: Dict[str, Any]) -> Optional[str]:
        """Extrait le nombre d'employés des données de l'entreprise"""
        try:
            if 'etablissements' in company_data:
                for etablissement in company_data['etablissements']:
                    # Chercher la tranche d'effectif
                    unite_legale = etablissement.get('uniteLegale', {})
                    tranche_effectif = unite_legale.get('trancheEffectifsUniteLegale')
                    
                    if tranche_effectif:
                        return tranche_effectif
                        
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction du nombre d'employés: {e}")
            return None

# Test du module
if __name__ == "__main__":
    try:
        client = INSEEAPIClient()
        print("🔧 Test de l'authentification...")
        token = client.get_access_token()
        print(f"✅ Token obtenu: {token[:20]}...")
        
        print("🔍 Test de recherche d'entreprise...")
        result = client.search_company_by_name("ADECCO")
        print(f"✅ Résultat obtenu: {len(result.get('etablissements', []))} établissement(s) trouvé(s)")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")