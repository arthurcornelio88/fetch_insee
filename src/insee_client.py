"""
Client API INSEE Sirene optimisé avec gestion du rate limiting et cache intelligent
"""

import requests
import time
import os
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class INSEEClient:
    """Client pour l'API INSEE Sirene avec gestion optimisée des requêtes"""
    
    def __init__(self, api_key: str = None, delay_between_requests: float = 4.0):
        """
        Initialise le client INSEE
        
        Args:
            api_key: Clé API INSEE (ou lecture depuis .env)
            delay_between_requests: Délai entre requêtes (défaut: 4s pour respecter 30req/min)
        """
        self.api_key = api_key or os.getenv('SIRENE_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API INSEE requise (SIRENE_API_KEY dans .env ou paramètre)")
            
        self.base_url = "https://api.insee.fr/api-sirene/3.11"
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'X-INSEE-Api-Key-Integration': self.api_key,
            'Accept': 'application/json',
            'User-Agent': 'Data-INSEE-Analysis/1.0'
        })
        
        # Cache pour éviter requêtes dupliquées
        self.cache = {}
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'found': 0,
            'not_found': 0
        }
        
        logger.info(f"✅ Client INSEE initialisé")
        logger.info(f"   API Key: {self.api_key[:10]}...")
        logger.info(f"   Base URL: {self.base_url}")
        
    def search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Recherche une entreprise avec gestion du cache et variations de noms
        
        Args:
            company_name: Nom de l'entreprise à rechercher
            
        Returns:
            Dictionnaire avec les données INSEE ou None si non trouvé
        """
        # Vérification cache
        if company_name in self.cache:
            self.stats['cache_hits'] += 1
            logger.debug(f"💾 Cache hit pour {company_name}")
            return self.cache[company_name]
        
        # Tentative de recherche avec variations
        variations = self._generate_name_variations(company_name)
        
        for i, variation in enumerate(variations):
            try:
                if variation != company_name:
                    logger.info(f"🔄 Essai avec variation: {variation}")
                    
                result = self._api_search(variation)
                if result:
                    # Mise en cache et statistiques
                    self.cache[company_name] = result
                    self.stats['found'] += 1
                    logger.info(f"✅ {company_name} trouvé avec variation '{variation}'")
                    return result
                    
                # Pause entre variations pour éviter rate limit
                if i < len(variations) - 1:
                    logger.info(f"   ⏸️  Pause 2s entre variations...")
                    time.sleep(2)
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit atteint, pause de 10s...")
                    time.sleep(10)
                    continue
                else:
                    logger.error(f"Erreur HTTP {e.response.status_code}: {e}")
                    continue
        
        # Aucune variation trouvée
        self.cache[company_name] = None
        self.stats['not_found'] += 1
        logger.warning(f"❌ {company_name} non trouvé après {len(variations)} variations")
        return None
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Génère des variations intelligentes du nom d'entreprise"""
        variations = [name]  # Nom original
        
        # Variation majuscules si différente
        upper_name = name.upper()
        if upper_name != name:
            variations.append(upper_name)
        
        # Premier mot si espaces présents
        if ' ' in name:
            first_word = name.split()[0]
            if first_word not in variations:
                variations.append(first_word)
        
        return variations
    
    def _api_search(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Effectue la requête API pour un nom d'entreprise"""
        url = f"{self.base_url}/siret"
        params = {
            'q': f'denominationUniteLegale:"{company_name.strip()}"',
            'nombre': 5
        }
        
        self.stats['api_calls'] += 1
        logger.debug(f"🔍 Recherche de: {company_name}")
        logger.debug(f"   URL: {url}")
        logger.debug(f"   Paramètres: {params}")
        
        response = self.session.get(url, params=params)
        logger.debug(f"📊 Code de réponse: {response.status_code}")
        
        if response.status_code == 404:
            logger.debug(f"❌ Erreur HTTP 404")
            logger.debug(f"   Réponse: {response.text[:300]}...")
            return None
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError(response=response)
        
        response.raise_for_status()
        
        # Pause après requête pour respecter rate limit
        time.sleep(self.delay)
        
        data = response.json()
        
        # Vérification si résultats trouvés
        if (data.get('header', {}).get('total', 0) > 0 and 
            data.get('etablissements')):
            
            nb_etablissements = len(data['etablissements'])
            logger.debug(f"✅ {nb_etablissements} établissement(s) trouvé(s)")
            return self._extract_company_data(data['etablissements'][0])
        
        return None
    
    def _extract_company_data(self, etablissement: Dict) -> Dict[str, Any]:
        """Extrait les données pertinentes d'un établissement INSEE"""
        unite_legale = etablissement.get('uniteLegale', {})
        
        # Extraction des effectifs (priorité unité légale)
        tranche_ul = unite_legale.get('trancheEffectifsUniteLegale')
        tranche_etab = etablissement.get('trancheEffectifsEtablissement')
        
        effectifs_data = self._decode_tranche_effectifs(tranche_ul or tranche_etab)
        
        return {
            'Statut_Recherche': 'Trouvé',
            'SIREN': etablissement.get('siren'),
            'SIRET': etablissement.get('siret'),
            'Denomination_INSEE': unite_legale.get('denominationUniteLegale'),
            'Categorie_Entreprise_INSEE': unite_legale.get('categorieEntreprise'),
            'Date_Creation': unite_legale.get('dateCreationUniteLegale'),
            'Activite_Principale': unite_legale.get('activitePrincipaleUniteLegale'),
            'Etat_Administratif': unite_legale.get('etatAdministratifUniteLegale'),
            'Etablissement_Siege': etablissement.get('etablissementSiege'),
            'Nombre_Etablissements': unite_legale.get('nombrePeriodesUniteLegale'),
            **effectifs_data
        }
    
    def _decode_tranche_effectifs(self, code_tranche: str) -> Dict[str, Any]:
        """Décode les tranches d'effectifs INSEE en données exploitables"""
        if not code_tranche:
            return {
                'tranche_effectifs_unite_legale': None,
                'Effectifs_Description': 'Non spécifié',
                'Effectifs_Numeric': None
            }
        
        # Mapping des codes INSEE vers descriptions et valeurs numériques
        tranches_mapping = {
            'NN': ('Non renseigné', None),
            '00': ('0 salarié', 0),
            '01': ('1 ou 2 salariés', 1.5),
            '02': ('3 à 5 salariés', 4),
            '03': ('6 à 9 salariés', 7.5),
            '11': ('10 à 19 salariés', 15),
            '12': ('20 à 49 salariés', 35),
            '21': ('50 à 99 salariés', 75),
            '22': ('100 à 199 salariés', 150),
            '31': ('200 à 249 salariés', 225),
            '32': ('250 à 499 salariés', 375),
            '41': ('500 à 999 salariés', 750),
            '42': ('1000 à 1999 salariés', 1500),
            '51': ('2000 à 4999 salariés', 3500),
            '52': ('5000 à 9999 salariés', 7500),
            '53': ('10000 salariés et plus', 15000)
        }
        
        desc, numeric = tranches_mapping.get(str(code_tranche), ('Code inconnu', None))
        
        return {
            'tranche_effectifs_unite_legale': code_tranche,
            'Effectifs_Description': desc,
            'Effectifs_Numeric': numeric
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du client"""
        total_processed = self.stats['found'] + self.stats['not_found']
        cache_rate = (self.stats['cache_hits'] / max(1, total_processed + self.stats['cache_hits'])) * 100
        success_rate = (self.stats['found'] / max(1, total_processed)) * 100
        
        return {
            **self.stats,
            'total_processed': total_processed,
            'cache_rate_percent': round(cache_rate, 1),
            'success_rate_percent': round(success_rate, 1)
        }