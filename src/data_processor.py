"""
Processeur principal pour l'enrichissement des données d'entreprises
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from .insee_client import INSEEClient

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processeur pour enrichir des données d'entreprises avec l'API INSEE"""
    
    def __init__(self, insee_client: INSEEClient):
        """
        Initialise le processeur
        
        Args:
            insee_client: Instance du client INSEE configuré
        """
        self.client = insee_client
        self.duplicate_cache = {}
        
    def process_companies(self, df: pd.DataFrame, 
                         company_col: str, 
                         size_col: str = None,
                         batch_size: int = 100) -> pd.DataFrame:
        """
        Traite un DataFrame d'entreprises pour enrichissement INSEE
        
        Args:
            df: DataFrame avec les données d'entreprises
            company_col: Nom de la colonne contenant les noms d'entreprises
            size_col: Nom de la colonne contenant la taille d'entreprise (optionnel)
            batch_size: Taille des lots pour sauvegarde intermédiaire
            
        Returns:
            DataFrame enrichi avec données INSEE
        """
        logger.info(f"Traitement de {len(df)} entreprises avec optimisation des doublons")
        
        # Analyse des doublons
        duplicates_analysis = self._analyze_duplicates(df, company_col)
        logger.info(f"Doublons détectés: {duplicates_analysis['total_duplicates']} lignes dupliquées")
        
        results = []
        cache_hits = 0
        api_calls = 0
        
        for idx, row in df.iterrows():
            company_name = str(row[company_col]).strip()
            size_original = str(row[size_col]).strip() if size_col and pd.notna(row[size_col]) else 'Non spécifié'
            
            # Vérification cache doublons
            if company_name in self.duplicate_cache:
                logger.debug(f"[{idx+1}/{len(df)}] {company_name} - 💾 CACHE HIT")
                result_data = self.duplicate_cache[company_name].copy()
                cache_hits += 1
            else:
                # Nouvelle recherche
                logger.info(f"[{idx+1}/{len(df)}] {company_name} - 🔍 Nouvelle recherche API...")
                insee_data = self.client.search_company(company_name)
                api_calls += 1
                
                if insee_data:
                    result_data = {
                        'Organisation_Original': company_name,
                        'Taille_Original': size_original,
                        'Statut_Recherche': 'Trouvé',
                        **insee_data
                    }
                    logger.info(f"   ✅ Trouvé: {insee_data.get('Denomination_INSEE', 'N/A')}")
                else:
                    result_data = {
                        'Organisation_Original': company_name,
                        'Taille_Original': size_original,
                        'Statut_Recherche': 'Non trouvé',
                        'SIREN': None,
                        'SIRET': None,
                        'Denomination_INSEE': None,
                        'Effectifs_Description': 'Non spécifié',
                        'Effectifs_Numeric': None
                    }
                    logger.warning(f"   ❌ Non trouvé")
                
                # Mise en cache
                self.duplicate_cache[company_name] = result_data.copy()
                
                # Pause entre requêtes déjà gérée dans le client
            
            results.append(result_data)
            
            # Progress info
            if (idx + 1) % 10 == 0:
                progress = (idx + 1) / len(df) * 100
                eta_minutes = (len(df) - idx - 1) * 4 / 60  # Estimation basée sur 4s par requête
                logger.info(f"   ⏱️  Progression: {progress:.1f}% | ETA: {eta_minutes:.0f}min")
        
        # Statistiques finales
        found = len([r for r in results if r.get('Statut_Recherche') == 'Trouvé'])
        logger.info(f"\n📊 STATISTIQUES:")
        logger.info(f"   🏢 Entreprises traitées: {len(results)}")
        logger.info(f"   ✅ Trouvées: {found} ({found/len(results)*100:.1f}%)")
        logger.info(f"   🔗 Appels API: {api_calls}")
        logger.info(f"   💾 Cache hits: {cache_hits}")
        logger.info(f"   ⚡ Économie: {cache_hits} requêtes évitées!")
        
        return pd.DataFrame(results)
    
    def _analyze_duplicates(self, df: pd.DataFrame, company_col: str) -> Dict[str, Any]:
        """Analyse les doublons dans le dataset"""
        logger.info("🔍 Analyse des doublons...")
        
        # Compter les occurrences de chaque entreprise
        counts = df[company_col].value_counts()
        duplicates = counts[counts > 1]
        
        total_companies = len(df)
        unique_companies = len(counts)
        duplicate_companies = len(duplicates)
        total_duplicates = duplicates.sum() - duplicate_companies  # Nombre de lignes en trop
        
        logger.info(f"📊 ANALYSE DU DATASET:")
        logger.info(f"   📄 Total lignes: {total_companies}")
        logger.info(f"   🏢 Entreprises uniques: {unique_companies}")
        logger.info(f"   🔄 Entreprises dupliquées: {duplicate_companies}")
        logger.info(f"   ⚠️  Lignes dupliquées: {total_duplicates}")
        logger.info(f"   💡 Économie possible: {total_duplicates} requêtes évitées!")
        
        if duplicate_companies > 0:
            logger.info(f"\n🔢 TOP 10 doublons:")
            for company, count in duplicates.head(10).items():
                logger.info(f"   {company}: {count} fois")
        
        return {
            'total_companies': total_companies,
            'unique_companies': unique_companies,
            'duplicate_companies': duplicate_companies,
            'total_duplicates': total_duplicates,
            'most_duplicated': list(duplicates.head(10).items())
        }