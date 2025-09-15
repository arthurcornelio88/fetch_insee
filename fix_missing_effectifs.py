#!/usr/bin/env python3
"""
Script de matching pour les effectifs "Non spécifié"
Utilise la Taille_Original pour estimer les effectifs manquants
"""

import pandas as pd
import numpy as np

def get_default_effectifs_by_taille(taille: str) -> tuple:
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

def fix_missing_effectifs(input_file: str, output_file: str):
    """
    Corrige les effectifs "Non spécifié" en utilisant la Taille_Original
    """
    print(f"📄 Chargement du fichier: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"📊 Dataset: {len(df)} entreprises")
    
    # Identifier les lignes avec effectifs manquants
    missing_mask = df['Effectifs_Description'] == 'Non spécifié'
    missing_count = missing_mask.sum()
    
    print(f"🔍 Effectifs manquants: {missing_count} ({missing_count/len(df)*100:.1f}%)")
    
    if missing_count == 0:
        print("✅ Aucun effectif manquant à corriger")
        df.to_csv(output_file, index=False, encoding='utf-8')
        return
    
    # Statistiques par taille avant correction
    print(f"\n📈 RÉPARTITION DES MANQUANTS PAR TAILLE:")
    missing_by_taille = df[missing_mask]['Taille_Original'].value_counts()
    for taille, count in missing_by_taille.items():
        print(f"   {taille}: {count} entreprises")
    
    # Appliquer les corrections
    corrections = 0
    
    for idx, row in df[missing_mask].iterrows():
        taille = row['Taille_Original']
        effectifs_num, effectifs_desc, confiance = get_default_effectifs_by_taille(taille)
        
        if effectifs_num is not None:
            # Mettre à jour les colonnes
            df.at[idx, 'Effectifs_Salesforce'] = effectifs_num
            df.at[idx, 'Effectifs_Description'] = effectifs_desc
            df.at[idx, 'Confiance_Donnee'] = confiance
            df.at[idx, 'Notes_Revision'] = f"📊 Effectifs estimés par script selon Taille_Original ({taille})"
            
            corrections += 1
    
    print(f"\n✅ CORRECTIONS APPLIQUÉES:")
    print(f"   Entreprises corrigées: {corrections}")
    print(f"   Entreprises non corrigées: {missing_count - corrections}")
    
    # Statistiques finales
    still_missing = (df['Effectifs_Description'] == 'Non spécifié').sum()
    print(f"   Effectifs encore manquants: {still_missing}")
    
    # Sauvegarder
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n📄 Fichier corrigé sauvegardé: {output_file}")
    
    # Statistiques des corrections par taille
    print(f"\n📊 DÉTAIL DES CORRECTIONS:")
    corrected_mask = df['Notes_Revision'].str.contains('Effectifs estimés par script', na=False)
    corrected_by_taille = df[corrected_mask]['Taille_Original'].value_counts()
    
    for taille, count in corrected_by_taille.items():
        effectifs_num, effectifs_desc, confiance = get_default_effectifs_by_taille(taille)
        print(f"   {taille}: {count} → {effectifs_num} employés ({effectifs_desc})")

def main():
    """Point d'entrée principal"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python fix_missing_effectifs.py <input_file> <output_file>")
        print("Example: python fix_missing_effectifs.py data/full_optimized_salesforce_ready.csv data/full_optimized_salesforce_ready_refactor.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        fix_missing_effectifs(input_file, output_file)
        print("\n🎉 Correction terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()