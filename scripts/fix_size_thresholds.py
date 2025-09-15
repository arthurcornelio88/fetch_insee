#!/usr/bin/env python3
"""
Script pour corriger les seuils de taille d'entreprise selon les définitions INSEE officielles

AVANT la correction:
- MICRO: 0-10
- PME: 10-250  
- ETI: 250-5000
- GE: 5000+

APRÈS la correction (seuils INSEE officiels):
- MICRO: 0-19
- PME: 20-249
- ETI: 250-4999
- GE: 5000+

Usage:
    python scripts/fix_size_thresholds.py input_file.csv [output_file.csv]
"""

import pandas as pd
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_effectifs_from_description(effectifs_description):
    """
    Convertit une description d'effectifs INSEE en valeur numérique
    
    Args:
        effectifs_description: Description INSEE (ex: "100 à 199 salariés")
    
    Returns:
        float: Valeur numérique (moyenne de la tranche)
    """
    if pd.isna(effectifs_description) or effectifs_description == '':
        return None
    
    # Mapping des tranches INSEE vers valeurs numériques
    tranche_mapping = {
        '0 à 2 salariés': 1,
        '3 à 5 salariés': 4,
        '6 à 9 salariés': 7.5,
        '10 à 19 salariés': 15,
        '20 à 49 salariés': 35,
        '50 à 99 salariés': 75,
        '100 à 199 salariés': 150,
        '200 à 249 salariés': 225,
        '250 à 499 salariés': 375,
        '500 à 999 salariés': 750,
        '1000 à 1999 salariés': 1500,
        '2000 à 4999 salariés': 3500,
        '5000 à 9999 salariés': 7500,
        '10000 salariés et plus': 15000,
        'Non renseigné': None
    }
    
    effectifs_clean = str(effectifs_description).strip()
    return tranche_mapping.get(effectifs_clean, None)

def fix_size_classification(effectifs_description, original_size, old_effectifs_salesforce=None):
    """
    Recalcule la classification selon les seuils INSEE officiels
    
    Args:
        effectifs_description: Description INSEE (ex: "100 à 199 salariés")
        original_size: Taille d'origine (MICRO/PME/ETI/GE)
        old_effectifs_salesforce: Anciens effectifs (pour comparaison)
    
    Returns:
        tuple: (effectifs_numeric, nouvelle_classification, statut_revision, notes)
    """
    # Calcul des effectifs depuis la description INSEE
    effectifs_numeric = parse_effectifs_from_description(effectifs_description)
    
    if effectifs_numeric is None:
        # Pas de données INSEE, utiliser estimation par taille
        size_defaults = {'MICRO': 10, 'PME': 135, 'ETI': 2625, 'GE': 10000}
        estimated_effectifs = size_defaults.get(original_size, 100)
        return estimated_effectifs, original_size, "MISSING_EFFECTIFS", f"Estimation selon {original_size} (pas de données INSEE)"
    
    # Seuils INSEE officiels
    if effectifs_numeric <= 19:
        correct_size = "MICRO"
    elif effectifs_numeric <= 249:
        correct_size = "PME"
    elif effectifs_numeric <= 4999:
        correct_size = "ETI"
    else:
        correct_size = "GE"
    
    # Vérification cohérence
    if correct_size == original_size:
        return effectifs_numeric, correct_size, "CONFIRMED", f"Classification cohérente - {int(effectifs_numeric)} employés selon INSEE"
    else:
        return effectifs_numeric, correct_size, "CONFLICT_TO_REVIEW", f"Incohérence: {original_size} déclaré mais {correct_size} selon INSEE ({int(effectifs_numeric)} employés)"

def fix_size_classification_numeric(effectifs_numeric, original_size):
    """
    Version simplifiée pour fichiers avec seulement Effectifs_Salesforce
    """
    if pd.isna(effectifs_numeric):
        return original_size, "MISSING_EFFECTIFS", "Effectifs non disponibles"
    
    # Seuils INSEE officiels
    if effectifs_numeric <= 19:
        correct_size = "MICRO"
    elif effectifs_numeric <= 249:
        correct_size = "PME"
    elif effectifs_numeric <= 4999:
        correct_size = "ETI"
    else:
        correct_size = "GE"
    
    # Vérification cohérence
    if correct_size == original_size:
        return correct_size, "CONFIRMED", f"Classification cohérente - {int(effectifs_numeric)} employés"
    else:
        return correct_size, "CONFLICT_TO_REVIEW", f"Incohérence: {original_size} déclaré mais {correct_size} selon effectifs ({int(effectifs_numeric)})"

def recalculate_confidence(effectifs_numeric):
    """Recalcule le niveau de confiance selon la précision des tranches"""
    if pd.isna(effectifs_numeric):
        return "low"
    elif effectifs_numeric <= 50:
        return "high"  # Tranches précises
    elif effectifs_numeric <= 1000:
        return "medium"  # Tranches moyennes
    else:
        return "low"  # Grandes tranches

def fix_salesforce_file(input_file, output_file=None):
    """
    Corrige un fichier Salesforce avec les nouveaux seuils
    
    Args:
        input_file: Chemin vers le fichier d'entrée
        output_file: Chemin vers le fichier de sortie (optionnel)
    """
    # Chargement du fichier
    logger.info(f"📥 Chargement du fichier: {input_file}")
    try:
        df = pd.read_csv(input_file)
        logger.info(f"📊 {len(df)} entreprises chargées")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement: {e}")
        return False
    
    # Vérification des colonnes nécessaires
    required_cols = ['Taille_Original']
    optional_cols = ['Effectifs_Description', 'Effectifs_Salesforce']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ Colonnes manquantes: {missing_cols}")
        return False
    
    # Utiliser Effectifs_Description si disponible, sinon Effectifs_Salesforce
    has_description = 'Effectifs_Description' in df.columns
    logger.info(f"📊 Mode: {'Description INSEE' if has_description else 'Effectifs numériques'}")
    
    # Statistiques avant correction
    logger.info("📊 AVANT correction:")
    if 'Statut_Revision' in df.columns:
        logger.info(f"   - CONFIRMED: {len(df[df['Statut_Revision'] == 'CONFIRMED'])}")
        logger.info(f"   - TO_REVIEW: {len(df[df['Statut_Revision'] == 'TO_REVIEW'])}")
        logger.info(f"   - CONFLICT_TO_REVIEW: {len(df[df['Statut_Revision'] == 'CONFLICT_TO_REVIEW'])}")
    
    # Application des corrections
    logger.info("🔄 Application des corrections...")
    
    if has_description:
        # Mode 1: Recalcul depuis Effectifs_Description
        corrections = df.apply(lambda row: fix_size_classification(
            row.get('Effectifs_Description'), 
            row.get('Taille_Original'),
            row.get('Effectifs_Salesforce')
        ), axis=1)
        
        # Extraction des résultats avec nouveaux effectifs
        df['Effectifs_Salesforce'] = [corr[0] for corr in corrections]
        df['Taille_Corrigee'] = [corr[1] for corr in corrections]
        df['Statut_Revision'] = [corr[2] for corr in corrections]
        df['Notes_Revision'] = [corr[3] for corr in corrections]
        
    else:
        # Mode 2: Vérification depuis Effectifs_Salesforce existants
        corrections = df.apply(lambda row: fix_size_classification_numeric(
            row.get('Effectifs_Salesforce'), 
            row.get('Taille_Original')
        ), axis=1)
        
        # Extraction des résultats
        df['Taille_Corrigee'] = [corr[0] for corr in corrections]
        df['Statut_Revision'] = [corr[1] for corr in corrections]
        df['Notes_Revision'] = [corr[2] for corr in corrections]
    
    # Recalcul de la confiance
    df['Confiance_Donnee'] = df['Effectifs_Salesforce'].apply(recalculate_confidence)
    
    # Statistiques après correction
    logger.info("📊 APRÈS correction:")
    logger.info(f"   - CONFIRMED: {len(df[df['Statut_Revision'] == 'CONFIRMED'])}")
    logger.info(f"   - TO_REVIEW: {len(df[df['Statut_Revision'] == 'TO_REVIEW'])}")
    logger.info(f"   - CONFLICT_TO_REVIEW: {len(df[df['Statut_Revision'] == 'CONFLICT_TO_REVIEW'])}")
    logger.info(f"   - MISSING_EFFECTIFS: {len(df[df['Statut_Revision'] == 'MISSING_EFFECTIFS'])}")
    
    # Exemples de corrections
    conflicts = df[df['Statut_Revision'] == 'CONFLICT_TO_REVIEW'].head(5)
    if len(conflicts) > 0:
        logger.info("🔍 Exemples de conflits détectés:")
        for _, row in conflicts.iterrows():
            logger.info(f"   - {row['Organisation_Original']}: {row['Taille_Original']} → {row['Taille_Corrigee']} ({row['Effectifs_Salesforce']} employés)")
    
    # Sauvegarde
    if output_file is None:
        output_file = str(Path(input_file).with_suffix('')) + "_corrected.csv"
    
    logger.info(f"💾 Sauvegarde: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"✅ Correction terminée!")
    
    return True

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_size_thresholds.py input_file.csv [output_file.csv]")
        print()
        print("Exemple:")
        print("  python scripts/fix_size_thresholds.py output/full_optimized_salesforce_ready.csv")
        print("  python scripts/fix_size_thresholds.py data.csv data_corrected.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        logger.error(f"❌ Fichier introuvable: {input_file}")
        sys.exit(1)
    
    success = fix_salesforce_file(input_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()