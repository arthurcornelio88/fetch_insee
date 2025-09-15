#!/usr/bin/env python3
"""
Script pour corriger les Effectifs_Description selon la classification réelle

Remplace les tranches INSEE spécifiques par les tranches de catégorie complètes :
- MICRO: "0 à 19 salariés" 
- PME: "20 à 249 salariés"
- ETI: "250 à 4999 salariés"  
- GE: "5000 salariés et plus"

Usage:
    python scripts/fix_effectifs_description.py input_file.csv [output_file.csv]
"""

import pandas as pd
import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_category_description(category):
    """
    Retourne la description complète selon la catégorie
    
    Args:
        category: MICRO/PME/ETI/GE
    
    Returns:
        str: Description de la tranche complète
    """
    descriptions = {
        'MICRO': "0 à 19 salariés",
        'PME': "20 à 249 salariés", 
        'ETI': "250 à 4999 salariés",
        'GE': "5000 salariés et plus"
    }
    return descriptions.get(category, "Non renseigné")

def get_category_from_effectifs(effectifs_salesforce):
    """
    Détermine la catégorie selon les effectifs numériques
    
    Args:
        effectifs_salesforce: Nombre d'employés
        
    Returns:
        str: Catégorie (MICRO/PME/ETI/GE)
    """
    if pd.isna(effectifs_salesforce):
        return None
        
    if effectifs_salesforce <= 19:
        return "MICRO"
    elif effectifs_salesforce <= 249:
        return "PME"
    elif effectifs_salesforce <= 4999:
        return "ETI"
    else:
        return "GE"

def fix_effectifs_descriptions(input_file, output_file=None):
    """
    Corrige les Effectifs_Description selon la vraie catégorie
    
    Args:
        input_file: Fichier d'entrée
        output_file: Fichier de sortie (optionnel)
    """
    # Chargement
    logger.info(f"📥 Chargement du fichier: {input_file}")
    try:
        df = pd.read_csv(input_file)
        logger.info(f"📊 {len(df)} entreprises chargées")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement: {e}")
        return False
    
    # Vérification des colonnes nécessaires
    required_cols = ['Effectifs_Salesforce', 'Effectifs_Description']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ Colonnes manquantes: {missing_cols}")
        return False
    
    # Statistiques avant correction
    logger.info("📊 AVANT correction:")
    unique_descriptions = df['Effectifs_Description'].value_counts()
    logger.info(f"   - {len(unique_descriptions)} descriptions différentes")
    for desc, count in unique_descriptions.head(5).items():
        logger.info(f"     • '{desc}': {count} entreprises")
    
    # Application des corrections
    logger.info("🔄 Correction des descriptions...")
    
    # Détermine la catégorie selon effectifs numériques
    df['Categorie_Calculee'] = df['Effectifs_Salesforce'].apply(get_category_from_effectifs)
    
    # Met à jour la description selon la catégorie
    df['Effectifs_Description_Corrigee'] = df['Categorie_Calculee'].apply(get_category_description)
    
    # Pour les cas sans effectifs, garder l'ancienne description ou "Non renseigné"
    mask_no_effectifs = df['Categorie_Calculee'].isna()
    df.loc[mask_no_effectifs, 'Effectifs_Description_Corrigee'] = df.loc[mask_no_effectifs, 'Effectifs_Description'].fillna("Non renseigné")
    
    # Remplace l'ancienne colonne
    df['Effectifs_Description'] = df['Effectifs_Description_Corrigee']
    df = df.drop(['Effectifs_Description_Corrigee', 'Categorie_Calculee'], axis=1)
    
    # Statistiques après correction
    logger.info("📊 APRÈS correction:")
    unique_descriptions_after = df['Effectifs_Description'].value_counts()
    logger.info(f"   - {len(unique_descriptions_after)} descriptions différentes")
    for desc, count in unique_descriptions_after.items():
        logger.info(f"     • '{desc}': {count} entreprises")
    
    # Exemples de corrections
    logger.info("🔍 Exemples de corrections appliquées:")
    examples = [
        ("MICRO", "15 employés → '0 à 19 salariés'"),
        ("PME", "150 employés → '20 à 249 salariés'"), 
        ("ETI", "1500 employés → '250 à 4999 salariés'"),
        ("GE", "15000 employés → '5000 salariés et plus'")
    ]
    for category, example in examples:
        count = len(df[df['Effectifs_Description'] == get_category_description(category)])
        if count > 0:
            logger.info(f"   - {category}: {count} entreprises - {example}")
    
    # Sauvegarde
    if output_file is None:
        output_file = str(Path(input_file).with_suffix('')) + "_descriptions_fixed.csv"
    
    logger.info(f"💾 Sauvegarde: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"✅ Correction des descriptions terminée!")
    
    return True

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_effectifs_description.py input_file.csv [output_file.csv]")
        print()
        print("Exemple:")
        print("  python scripts/fix_effectifs_description.py output/full_optimized_salesforce_ready_FIXED.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        logger.error(f"❌ Fichier introuvable: {input_file}")
        sys.exit(1)
    
    success = fix_effectifs_descriptions(input_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()