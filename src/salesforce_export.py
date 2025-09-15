"""
Module d'export et transformation des données pour Salesforce
"""

import pandas as pd
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class SalesforceExporter:
    """Exporteur pour transformer les données INSEE en format Salesforce"""
    
    def __init__(self):
        """Initialise l'exporteur"""
        self.size_mapping = {
            'MICRO': {'range': (0, 10), 'default': 5},
            'PME': {'range': (10, 250), 'default': 100}, 
            'ETI': {'range': (250, 5000), 'default': 1000},
            'GE': {'range': (5000, float('inf')), 'default': 10000}
        }
    
    def transform_for_salesforce(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforme les données INSEE en format compatible Salesforce
        
        Args:
            df: DataFrame avec données INSEE brutes
            
        Returns:
            DataFrame transformé pour Salesforce
        """
        logger.info(f"📊 Traitement des données pour Salesforce...")
        logger.info(f"📄 Fichier chargé: {len(df)} entreprises")
        
        df_salesforce = df.copy()
        
        logger.info(f"🔄 Conversion des tranches d'effectifs...")
        
        # Conversion des effectifs en format numérique Salesforce
        df_salesforce['Effectifs_Salesforce'] = df_salesforce.apply(
            self._convert_effectifs_to_salesforce, axis=1
        )
        
        # Détermination du niveau de confiance
        df_salesforce['Confiance_Donnee'] = df_salesforce.apply(
            self._determine_confidence_level, axis=1
        )
        
        # Détermination du statut de révision intelligent
        df_salesforce['Statut_Revision'] = df_salesforce.apply(
            self._determine_revision_status, axis=1
        )
        
        # Génération des notes de révision
        df_salesforce['Notes_Revision'] = df_salesforce.apply(
            self._generate_revision_notes, axis=1
        )
        
        # Correction automatique des effectifs manquants
        df_salesforce = self._fix_missing_effectifs(df_salesforce)
        
        # Statistiques finales
        self._log_salesforce_stats(df_salesforce)
        
        return df_salesforce
    
    def _convert_effectifs_to_salesforce(self, row: pd.Series) -> float:
        """Convertit les tranches d'effectifs en valeurs numériques"""
        if pd.notna(row.get('Effectifs_Numeric')):
            return float(row['Effectifs_Numeric'])
        return None
    
    def _determine_confidence_level(self, row: pd.Series) -> str:
        """Détermine le niveau de confiance des données"""
        if row.get('Statut_Recherche') == 'Non trouvé':
            return 'none'
        
        if pd.isna(row.get('Effectifs_Numeric')):
            return 'low'
        
        effectifs = row.get('Effectifs_Numeric', 0)
        
        # Confiance basée sur la précision de la tranche
        if effectifs <= 50:
            return 'high'  # Tranches petites = plus précises
        elif effectifs <= 1000:
            return 'medium'
        else:
            return 'low'  # Grandes tranches = moins précises
    
    def _determine_revision_status(self, row: pd.Series) -> str:
        """Détermine le statut de révision intelligent"""
        if row.get('Statut_Recherche') == 'Non trouvé':
            return 'NOT_FOUND'
        
        # Vérification cohérence avec taille originale
        coherence = self._check_size_coherence(row)
        confiance = row.get('Confiance_Donnee', 'low')
        
        # Si confiance élevée et cohérent → CONFIRMÉ
        if confiance == 'high' and coherence == 'coherent':
            return 'CONFIRMED'
        
        # Si confiance moyenne et cohérent → CONFIRMÉ aussi  
        if confiance == 'medium' and coherence == 'coherent':
            return 'CONFIRMED'
        
        # Si incohérent → conflit à réviser
        if coherence == 'incoherent':
            return 'CONFLICT_TO_REVIEW'
        
        # Si confiance faible → toujours à réviser
        if confiance == 'low':
            return 'TO_REVIEW'
        
        # Cas par défaut
        return 'TO_REVIEW'
    
    def _check_size_coherence(self, row: pd.Series) -> str:
        """Vérifie la cohérence entre taille originale et effectifs INSEE"""
        taille_original = row.get('Taille_Original', '')
        effectifs = row.get('Effectifs_Numeric')
        
        if not effectifs or pd.isna(effectifs):
            return 'unknown'
        
        # Mapping des tailles vers ranges d'effectifs attendus
        if taille_original == 'MICRO' and effectifs <= 10:
            return 'coherent'
        elif taille_original == 'PME' and 10 < effectifs <= 250:
            return 'coherent'
        elif taille_original == 'ETI' and 250 < effectifs <= 5000:
            return 'coherent'
        elif taille_original == 'GE' and effectifs > 5000:
            return 'coherent'
        elif taille_original in ['Non spécifié', '', 'UNKNOWN']:
            return 'unknown'
        else:
            return 'incoherent'
    
    def _generate_revision_notes(self, row: pd.Series) -> str:
        """Génère des notes explicatives pour la révision"""
        statut = row.get('Statut_Revision', '')
        effectifs_desc = row.get('Effectifs_Description', '')
        
        if statut == 'CONFIRMED':
            return f"✅ Données cohérentes - {effectifs_desc}"
        elif statut == 'CONFLICT_TO_REVIEW':
            return f"⚠️ Incohérence détectée - Vérifier {effectifs_desc}"
        elif statut == 'TO_REVIEW':
            return f"📊 Tranche large - estimation approximative"
        elif statut == 'NOT_FOUND':
            return f"❌ Entreprise non trouvée dans Sirene"
        else:
            return f"📋 À réviser - {effectifs_desc}"
    
    def _fix_missing_effectifs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corrige les effectifs manquants selon la taille d'entreprise"""
        logger.info(f"\n🔧 Correction automatique des effectifs manquants...")
        
        missing_mask = df['Effectifs_Description'] == 'Non spécifié'
        missing_count = missing_mask.sum()
        
        logger.info(f"🔍 Effectifs manquants: {missing_count} ({missing_count/len(df)*100:.1f}%)")
        
        if missing_count == 0:
            logger.info("✅ Aucun effectif manquant à corriger")
            return df
        
        # Statistiques par taille avant correction
        logger.info(f"📈 RÉPARTITION DES MANQUANTS PAR TAILLE:")
        missing_by_taille = df[missing_mask]['Taille_Original'].value_counts()
        for taille, count in missing_by_taille.items():
            logger.info(f"   {taille}: {count} entreprises")
        
        corrections = 0
        df_copy = df.copy()
        
        for idx, row in df_copy[missing_mask].iterrows():
            taille = row['Taille_Original']
            effectifs_num, effectifs_desc, confiance = self._get_default_effectifs_by_taille(taille)
            
            if effectifs_num is not None:
                # Mettre à jour les colonnes
                df_copy.at[idx, 'Effectifs_Salesforce'] = effectifs_num
                df_copy.at[idx, 'Effectifs_Description'] = effectifs_desc
                df_copy.at[idx, 'Confiance_Donnee'] = confiance
                df_copy.at[idx, 'Notes_Revision'] = f"📊 Effectifs estimés par script selon Taille_Original ({taille})"
                
                corrections += 1
        
        logger.info(f"✅ CORRECTIONS APPLIQUÉES: {corrections}")
        still_missing = (df_copy['Effectifs_Description'] == 'Non spécifié').sum()
        logger.info(f"   Effectifs encore manquants: {still_missing}")
        
        return df_copy
    
    def _get_default_effectifs_by_taille(self, taille: str) -> Tuple[Optional[int], str, str]:
        """
        Retourne les effectifs par défaut selon la taille d'entreprise
        Returns: (effectifs_numerique, effectifs_description, confiance)
        """
        mapping = {
            'MICRO': (5, '3 à 5 salariés', 'medium'),      # Milieu de gamme MICRO
            'PME': (100, '100 à 199 salariés', 'medium'),   # Milieu de gamme PME  
            'ETI': (1000, '1000 à 1999 salariés', 'medium'), # Milieu de gamme ETI
            'GE': (10000, '10000 salariés et plus', 'low')   # Estimation GE
        }
        
        return mapping.get(taille, (None, 'Non spécifié', 'low'))
    
    def _log_salesforce_stats(self, df: pd.DataFrame):
        """Affiche les statistiques du fichier Salesforce généré"""
        total_entreprises = len(df)
        avec_valeurs_numeriques = df['Effectifs_Salesforce'].notna().sum()
        
        # Distribution des statuts de révision
        statuts_revision = df['Statut_Revision'].value_counts().to_dict()
        
        # Niveaux de confiance
        niveaux_confiance = df['Confiance_Donnee'].value_counts().to_dict()
        
        # Statistiques sur les effectifs
        effectifs_numeriques = df['Effectifs_Salesforce'].dropna()
        
        logger.info(f"\n📈 STATISTIQUES POUR SALESFORCE:")
        logger.info(f"   Total entreprises: {total_entreprises}")
        logger.info(f"")
        logger.info(f"🔍 STATUTS DE RÉVISION:")
        for statut, count in statuts_revision.items():
            pourcentage = count / total_entreprises * 100
            logger.info(f"   {statut}: {count} ({pourcentage:.1f}%)")
        
        logger.info(f"\n💼 EFFECTIFS POUR SALESFORCE:")
        logger.info(f"   Avec valeurs numériques: {avec_valeurs_numeriques}/{total_entreprises} ({avec_valeurs_numeriques/total_entreprises*100:.1f}%)")
        if len(effectifs_numeriques) > 0:
            logger.info(f"   Moyenne: {effectifs_numeriques.mean():.0f} employés")
            logger.info(f"   Médiane: {effectifs_numeriques.median():.0f} employés")
            logger.info(f"   Min-Max: {effectifs_numeriques.min():.0f} - {effectifs_numeriques.max():.0f}")
        
        logger.info(f"\n🎯 NIVEAUX DE CONFIANCE:")
        for niveau, count in niveaux_confiance.items():
            pourcentage = count / total_entreprises * 100
            logger.info(f"   {niveau}: {count} ({pourcentage:.1f}%)")