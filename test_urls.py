"""
Test des différentes URLs possibles pour l'API INSEE
"""

import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

def test_insee_urls():
    """Test différentes URLs de l'API INSEE"""
    
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    
    # Créer l'authentification Basic
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Accept': 'application/json'
    }
    
    # URLs à tester
    test_urls = [
        'https://api.insee.fr/entreprises/sirene/V3/siret',
        'https://api.insee.fr/entreprises/sirene/v3/siret',
        'https://api.insee.fr/enterprises/sirene/V3/siret',
        'https://api.insee.fr/sirene/V3/siret',
        'https://api.insee.fr/sirene/v3/siret',
        'https://www.sirene.fr/sirene/public/search',
        'https://api.insee.fr/entreprises/sirene/V3.11/siret'
    ]
    
    params = {
        'q': 'denominationUniteLegale:"ADECCO"',
        'nombre': 1
    }
    
    for url in test_urls:
        print(f"\n🔍 Test de l'URL: {url}")
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"   📊 Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Succès! Contenu: {response.text[:200]}...")
                break
            elif response.status_code == 401:
                print(f"   🔐 Erreur d'authentification")
            elif response.status_code == 404:
                print(f"   ❌ URL non trouvée")
            else:
                print(f"   ⚠️  Autre erreur: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    # Test de l'endpoint de token aussi
    print(f"\n🔑 Test des endpoints de token...")
    token_urls = [
        'https://api.insee.fr/token',
        'https://api.insee.fr/oauth/token',
        'https://auth.insee.fr/token'
    ]
    
    token_data = {
        'grant_type': 'client_credentials'
    }
    
    for token_url in token_urls:
        print(f"\n🔍 Test token URL: {token_url}")
        try:
            response = requests.post(
                token_url, 
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=token_data,
                auth=(client_id, client_secret),
                timeout=10
            )
            print(f"   📊 Code: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Token obtenu!")
                token_response = response.json()
                print(f"   🎫 Token: {token_response.get('access_token', '')[:20]}...")
                break
            else:
                print(f"   ❌ Erreur: {response.text[:100]}...")
        except Exception as e:
            print(f"   💥 Exception: {e}")

if __name__ == "__main__":
    print("🧪 Test des URLs de l'API INSEE...")
    test_insee_urls()