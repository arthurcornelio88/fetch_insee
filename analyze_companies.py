"""
Analyseur du fichier face_raw.csv
Analyse les entreprises et prépare les données pour la recherche INSEE
"""

import pandas as pd
import os
from typing import List, Dict, Any

def analyze_companies_csv(csv_path: str = "data/face_raw.csv") -> pd.DataFrame:
    """
    Analyse le fichier CSV des entreprises
    """
    try:
        # Lire le fichier CSV
        df = pd.read_csv(csv_path)
        
        print(f"📊 Analyse du fichier: {csv_path}")
        print(f"   Nombre total d'entreprises: {len(df)}")
        print(f"   Colonnes disponibles: {list(df.columns)}")
        
        # Afficher un aperçu des données
        print(f"\n📋 Aperçu des données:")
        print(df.head(10))
        
        # Statistiques sur les tailles d'entreprise
        if 'Taille d\'entreprise' in df.columns:
            print(f"\n📈 Répartition par taille d'entreprise:")
            taille_counts = df['Taille d\'entreprise'].value_counts()
            for taille, count in taille_counts.items():
                print(f"   {taille}: {count} entreprises")
        
        # Nettoyer les noms d'entreprises
        df_clean = df.copy()
        df_clean['Organisation_clean'] = df_clean['Organisation'].str.strip()
        
        # Supprimer les doublons potentiels
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['Organisation_clean'])
        final_count = len(df_clean)
        
        if initial_count != final_count:
            print(f"\n🔄 Doublons supprimés: {initial_count - final_count}")
            print(f"   Entreprises uniques: {final_count}")
        
        # Ajouter des colonnes pour les résultats de recherche
        df_clean['SIREN'] = None
        df_clean['Denomination_INSEE'] = None
        df_clean['Tranche_Effectifs_INSEE'] = None
        df_clean['Effectifs_Description'] = None
        df_clean['Statut_Recherche'] = 'Non traité'
        df_clean['Date_Recherche'] = None
        
        return df_clean
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse du fichier: {e}")
        return pd.DataFrame()

def get_companies_list(df: pd.DataFrame) -> List[str]:
    """
    Extrait la liste des noms d'entreprises
    """
    return df['Organisation_clean'].tolist()

def save_analysis_results(df: pd.DataFrame, output_path: str = "data/face_analyzed.csv"):
    """
    Sauvegarde les résultats de l'analyse
    """
    try:
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ Résultats sauvegardés dans: {output_path}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")

def create_sample_for_testing(df: pd.DataFrame, sample_size: int = 10) -> pd.DataFrame:
    """
    Crée un échantillon pour les tests
    """
    sample = df.head(sample_size).copy()
    print(f"🧪 Échantillon créé: {sample_size} entreprises pour les tests")
    return sample

# Script principal
if __name__ == "__main__":
    print("🔍 Analyse du fichier des entreprises...")
    
    # Analyser le fichier
    df = analyze_companies_csv()
    
    if not df.empty:
        # Afficher quelques statistiques
        print(f"\n📊 Résumé de l'analyse:")
        print(f"   Entreprises à traiter: {len(df)}")
        
        # Créer un échantillon pour les tests
        sample = create_sample_for_testing(df, 5)
        print(f"\n🏢 Échantillon pour tests:")
        for idx, row in sample.iterrows():
            print(f"   {idx+1}. {row['Organisation_clean']} ({row['Taille d\'entreprise']})")
        
        # Sauvegarder les résultats
        save_analysis_results(df)
        
        # Sauvegarder l'échantillon
        save_analysis_results(sample, "data/face_sample.csv")
        
        print(f"\n✅ Analyse terminée! Prêt pour la recherche INSEE.")
        
    else:
        print("❌ Impossible d'analyser le fichier.")