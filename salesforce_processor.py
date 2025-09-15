"""
Module de traitement des effectifs pour Salesforce
Conversion des tranches INSEE en valeurs numériques + aide à la révision
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

def process_insee_result_for_salesforce(organisation_original: str, taille_original: str, insee_result: dict) -> dict:
    """
    Traite un résultat INSEE pour Salesforce avec le bon statut
    """
    # Extraire les effectifs depuis le résultat INSEE
    effectifs_desc = extract_effectifs_from_insee_data(insee_result)
    
    # Convertir en numérique
    valeur_numerique, confiance, _ = convert_tranche_to_numeric(effectifs_desc)
    
    # Déterminer le statut final basé sur la confiance et la cohérence
    categorie_insee = insee_result.get('categorie_insee_description', '')
    statut_final = determine_smart_status(taille_original, categorie_insee, effectifs_desc, confiance)
    
    # Construire le résultat complet
    result = {
        'Organisation_Original': organisation_original,
        'Taille_Original': taille_original,
        'Statut_Recherche': statut_final,
        'Effectifs_Description': effectifs_desc,
        'Effectifs_Numerique': valeur_numerique,
        'Confiance_Effectifs': confiance,
        'Categorie_INSEE': categorie_insee,
        **insee_result  # Inclure toutes les autres données INSEE
    }
    
    return result

def determine_smart_status(taille_original: str, categorie_insee: str, effectifs_desc: str, confiance: str) -> str:
    """
    Détermine le statut en fonction de la confiance et de la cohérence des données
    """
    # Si pas d'effectifs, c'est à réviser
    if not effectifs_desc or effectifs_desc == 'Non renseigné':
        return 'MISSING_EFFECTIFS'
    
    # Vérifier la cohérence avec la taille originale
    coherence = check_size_coherence(taille_original, categorie_insee, effectifs_desc)
    
    # Si confiance élevée et données cohérentes → CONFIRMÉ
    if confiance == 'high' and coherence == 'coherent':
        return 'CONFIRMED'
    
    # Si confiance moyenne et données cohérentes → CONFIRMÉ aussi  
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

def convert_tranche_to_numeric(tranche_description: str) -> Tuple[Optional[int], str, str]:
    """
    Convertit une tranche d'effectifs INSEE en valeur numérique pour Salesforce
    
    Returns:
        (valeur_numerique, confiance, statut_revision)
    """
    if not tranche_description or tranche_description == 'Non renseigné':
        return None, 'low', 'TO_REVIEW'
    
    # Mapping des tranches vers valeurs numériques (moyenne de la tranche)
    tranche_mapping = {
        '0 salarié': (0, 'high'),
        '1 ou 2 salariés': (1.5, 'high'),      # Moyenne entre 1 et 2
        '3 à 5 salariés': (4, 'high'),         # Moyenne entre 3 et 5
        '6 à 9 salariés': (7.5, 'high'),       # Moyenne entre 6 et 9
        '10 à 19 salariés': (15, 'high'),      # Moyenne entre 10 et 19
        '20 à 49 salariés': (35, 'high'),      # Moyenne entre 20 et 49
        '50 à 99 salariés': (75, 'high'),      # Moyenne entre 50 et 99
        '100 à 199 salariés': (150, 'high'),   # Moyenne entre 100 et 199
        '200 à 249 salariés': (225, 'high'),   # Moyenne entre 200 et 249
        '250 à 499 salariés': (375, 'medium'), # Large fourchette
        '500 à 999 salariés': (750, 'medium'), # Large fourchette
        '1000 à 1999 salariés': (1500, 'medium'), # Large fourchette mais ok
        '2000 à 4999 salariés': (3500, 'medium'),    # Large mais gérable
        '5000 à 9999 salariés': (7500, 'low'),    # Très large
        '10000 salariés et plus': (15000, 'low')   # Estimation
    }
    
    if tranche_description in tranche_mapping:
        effectif_num, confiance = tranche_mapping[tranche_description]
        # Le statut sera déterminé par determine_smart_status selon la cohérence
        return effectif_num, confiance, 'PENDING'
    else:
        return None, 'low', 'TO_REVIEW'

def extract_effectifs_from_insee_data(row) -> str:
    """
    Extrait la description des effectifs depuis les données brutes INSEE
    """
    # Vérifier si l'entreprise a été trouvée
    statut = row.get('Statut_Recherche', '')
    if 'Non trouvé' in statut or 'Erreur' in statut:
        return 'Non spécifié'
    
    # Priorités d'extraction:
    # 1. Unité légale en priorité (plus représentatif de l'entreprise globale)
    if 'tranche_effectifs_unite_legale' in row and pd.notna(row.get('tranche_effectifs_unite_legale')):
        return convert_insee_code_to_description(row['tranche_effectifs_unite_legale'])
    
    # 2. Sinon, établissement
    if 'tranche_effectifs_etablissement' in row and pd.notna(row.get('tranche_effectifs_etablissement')):
        return convert_insee_code_to_description(row['tranche_effectifs_etablissement'])
    
    # 2. Essayer d'extraire depuis les données JSON brutes
    try:
        import json
        etablissements_str = row.get('etablissements', '')
        if etablissements_str and isinstance(etablissements_str, str):
            etablissements = json.loads(etablissements_str)
            
            # Chercher le siège social en priorité
            for etab in etablissements:
                if etab.get('etablissementSiege'):
                    tranche = etab.get('trancheEffectifsEtablissement')
                    if tranche:
                        return convert_insee_code_to_description(tranche)
                    
                    # Sinon essayer l'unité légale
                    unite = etab.get('uniteLegale', {})
                    tranche_ul = unite.get('trancheEffectifsUniteLegale')
                    if tranche_ul:
                        return convert_insee_code_to_description(tranche_ul)
            
            # Si pas de siège trouvé, prendre le premier établissement
            if etablissements:
                etab = etablissements[0]
                tranche = etab.get('trancheEffectifsEtablissement')
                if tranche:
                    return convert_insee_code_to_description(tranche)
                
                unite = etab.get('uniteLegale', {})
                tranche_ul = unite.get('trancheEffectifsUniteLegale')
                if tranche_ul:
                    return convert_insee_code_to_description(tranche_ul)
    
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    
    return 'Non spécifié'

def convert_insee_code_to_description(code: str) -> str:
    """
    Convertit un code tranche INSEE en description lisible
    """
    if not code or pd.isna(code):
        return 'Non spécifié'
    
    # Mapping des codes INSEE vers descriptions
    code_mapping = {
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
    
    return code_mapping.get(str(int(float(code))) if str(code).replace('.','').isdigit() else str(code), f'Code inconnu: {code}')

def analyze_data_quality(row) -> str:
    """
    Analyse la qualité des données et suggère un statut de révision
    """
    statut = row.get('Statut_Recherche', '')
    taille_original = row.get('Taille_Original', '')
    categorie_insee = row.get('Categorie_Entreprise_INSEE', '')
    effectifs_desc = row.get('Effectifs_Description', '')
    
    # Cas 1: Non trouvé dans INSEE
    if statut != 'Trouvé':
        return 'NOT_FOUND'
    
    # Cas 2: Trouvé mais pas d'effectifs
    if not effectifs_desc or effectifs_desc == 'Non renseigné':
        return 'MISSING_EFFECTIFS'
    
    # Cas 3: Cohérence entre taille originale et données INSEE
    coherence = check_size_coherence(taille_original, categorie_insee, effectifs_desc)
    
    if coherence == 'coherent':
        return 'CONFIRMED'
    elif coherence == 'incoherent':
        return 'CONFLICT_TO_REVIEW'
    else:
        return 'TO_REVIEW'

def check_size_coherence(taille_original: str, categorie_insee: str, effectifs_desc: str) -> str:
    """
    Vérifie la cohérence entre la taille d'origine et les données INSEE
    """
    # On ne vérifie que la cohérence entre taille_original et effectifs_desc
    if not all([taille_original, effectifs_desc]):
        return 'incomplete'
    
    # Mapping approximatif (les seuils peuvent varier)
    taille_mapping = {
        'MICRO': (0, 10),      # 0-9 salariés
        'PME': (10, 250),      # 10-249 salariés  
        'ETI': (250, 5000),    # 250-4999 salariés
        'GE': (5000, 999999),  # 5000+ salariés
    }
    
    # Extraire la valeur numérique des effectifs
    effectif_num, _, _ = convert_tranche_to_numeric(effectifs_desc)
    
    if effectif_num is None:
        return 'incomplete'
    
    # Vérifier la cohérence
    if taille_original in taille_mapping:
        min_expected, max_expected = taille_mapping[taille_original]
        
        if min_expected <= effectif_num <= max_expected:
            return 'coherent'
        else:
            return 'incoherent'
    
    return 'unknown'

def create_salesforce_ready_data(input_file: str, output_file: str):
    """
    Traite les données INSEE et crée un fichier prêt pour Salesforce
    """
    print("📊 Traitement des données pour Salesforce...")
    
    try:
        # Charger les données
        df = pd.read_csv(input_file)
        print(f"📄 Fichier chargé: {len(df)} entreprises")
        
        # Ajouter les nouvelles colonnes
        print("🔄 Conversion des tranches d'effectifs...")
        
        # Créer la colonne Effectifs_Description pour le traitement
        # Essayer d'extraire les effectifs depuis les données INSEE brutes
        if 'Effectifs_Description' not in df.columns:
            print("🔍 Extraction des effectifs depuis les données INSEE...")
            df['Effectifs_Description'] = df.apply(lambda row: extract_effectifs_from_insee_data(row), axis=1)
            
            # Compter les effectifs trouvés
            found_effectifs = df[df['Effectifs_Description'] != 'Non spécifié'].shape[0]
            print(f"✅ Effectifs extraits pour {found_effectifs}/{len(df)} entreprises ({found_effectifs/len(df)*100:.1f}%)")
        
        # Convertir les tranches en valeurs numériques
        if 'Effectifs_Numerique' not in df.columns:
            print("🔧 Conversion standard des tranches d'effectifs")
            df[['Effectifs_Salesforce', 'Confiance_Donnee', 'temp_status']] = df['Effectifs_Description'].apply(
                lambda x: pd.Series(convert_tranche_to_numeric(x))
            )
        else:
            print("🔧 Utilisation des effectifs pré-calculés")
            # Les effectifs ont déjà été calculés par le processeur optimisé
            df['temp_status'] = 'processed'
        
        # Analyser la qualité des données
        print("🔍 Analyse de la qualité des données...")
        
        # Vérifier si les données ont déjà été traitées par le processeur optimisé
        if 'Effectifs_Numerique' in df.columns and 'Confiance_Effectifs' in df.columns:
            print("🔧 Détection de données pré-traitées par le processeur optimisé")
            # Les données ont déjà été traitées, utiliser les colonnes existantes
            df['Effectifs_Salesforce'] = df['Effectifs_Numerique']
            df['Confiance_Donnee'] = df['Confiance_Effectifs']
            # Appliquer la logique intelligente de statut même sur les données pré-traitées
            print("🎯 Application de la logique intelligente de statuts...")
            df['Statut_Revision'] = df.apply(lambda row: determine_smart_status(
                row.get('Taille_Original', ''),
                row.get('Categorie_Entreprise', ''),
                row.get('Effectifs_Description', ''),
                row.get('Confiance_Donnee', 'low')
            ), axis=1)
        else:
            print("🔧 Traitement standard des données brutes")
            # Traitement standard pour données brutes
            df['Statut_Revision'] = df.apply(analyze_data_quality, axis=1)
        
        # Supprimer la colonne temporaire
        df = df.drop('temp_status', axis=1)
        
        # Ajouter des colonnes d'aide
        df['Match_Score'] = df.apply(calculate_match_score, axis=1)
        df['Notes_Revision'] = df.apply(generate_revision_notes, axis=1)
        
        # Réorganiser les colonnes pour Salesforce
        columns_order = [
            'Organisation_Original',
            'Taille_Original', 
            'SIREN',
            'Denomination_INSEE',
            'Effectifs_Salesforce',        # ← VALEUR NUMÉRIQUE POUR SALESFORCE
            'Effectifs_Description',       # ← DESCRIPTION ORIGINALE
            'Confiance_Donnee',           # ← NIVEAU DE CONFIANCE
            'Statut_Revision',            # ← STATUT POUR RÉVISION  
            'Match_Score',                # ← SCORE DE CORRESPONDANCE
            'Notes_Revision',             # ← NOTES POUR RÉVISION
            'Annee_Effectifs',
            'Categorie_Entreprise_INSEE',
            'SIRET',
            'Date_Creation',
            'Activite_Principale',
            'Etat_Administratif',
            'Nb_Etablissements',
            'Statut_Recherche',
            'Date_Recherche'
        ]
        
        # Réordonner avec les colonnes existantes
        existing_columns = [col for col in columns_order if col in df.columns]
        df_final = df[existing_columns]
        
        # Sauvegarder
        df_final.to_csv(output_file, index=False, encoding='utf-8')
        
        # Statistiques
        print(f"\n📈 STATISTIQUES POUR SALESFORCE:")
        print(f"   Total entreprises: {len(df_final)}")
        
        # Répartition par statut de révision
        print(f"\n🔍 STATUTS DE RÉVISION:")
        status_counts = df_final['Statut_Revision'].value_counts()
        for status, count in status_counts.items():
            print(f"   {status}: {count} ({count/len(df_final)*100:.1f}%)")
        
        # Effectifs disponibles pour Salesforce
        with_effectifs = df_final[df_final['Effectifs_Salesforce'].notna()]
        print(f"\n💼 EFFECTIFS POUR SALESFORCE:")
        print(f"   Avec valeurs numériques: {len(with_effectifs)}/{len(df_final)} ({len(with_effectifs)/len(df_final)*100:.1f}%)")
        
        if len(with_effectifs) > 0:
            print(f"   Moyenne: {with_effectifs['Effectifs_Salesforce'].mean():.0f} employés")
            print(f"   Médiane: {with_effectifs['Effectifs_Salesforce'].median():.0f} employés")
            print(f"   Min-Max: {with_effectifs['Effectifs_Salesforce'].min():.0f} - {with_effectifs['Effectifs_Salesforce'].max():.0f}")
        
        # Niveau de confiance
        print(f"\n🎯 NIVEAUX DE CONFIANCE:")
        confiance_counts = df_final['Confiance_Donnee'].value_counts()
        for conf, count in confiance_counts.items():
            print(f"   {conf}: {count} ({count/len(df_final)*100:.1f}%)")
        
        print(f"\n✅ Fichier Salesforce créé: {output_file}")
        
        return df_final
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def calculate_match_score(row) -> float:
    """
    Calcule un score de correspondance (0-100)
    """
    score = 0
    
    # Trouvé dans INSEE (+40 points)
    if row.get('Statut_Recherche') == 'Trouvé':
        score += 40
    
    # A des effectifs (+30 points)
    if row.get('Effectifs_Salesforce') is not None:
        score += 30
    
    # Cohérence taille/effectifs (+20 points)
    if row.get('Statut_Revision') == 'CONFIRMED':
        score += 20
    elif row.get('Statut_Revision') in ['TO_REVIEW', 'MISSING_EFFECTIFS']:
        score += 10
    
    # Données récentes (+10 points)
    if row.get('Annee_Effectifs') and str(row.get('Annee_Effectifs')) >= '2022':
        score += 10
    
    return min(score, 100)

def generate_revision_notes(row) -> str:
    """
    Génère des notes pour aider à la révision manuelle
    """
    notes = []
    
    statut = row.get('Statut_Revision', '')
    
    if statut == 'NOT_FOUND':
        notes.append("❌ Entreprise non trouvée dans INSEE - vérifier nom/orthographe")
    elif statut == 'MISSING_EFFECTIFS':
        notes.append("⚠️ Trouvée mais effectifs non renseignés - recherche manuelle nécessaire")
    elif statut == 'CONFLICT_TO_REVIEW':
        notes.append("🔍 Incohérence taille originale vs données INSEE - vérifier")
    elif statut == 'CONFIRMED':
        notes.append("✅ Données cohérentes et fiables")
    
    # Ajouter info sur la confiance
    confiance = row.get('Confiance_Donnee', '')
    if confiance == 'low':
        notes.append("📊 Tranche large - estimation approximative")
    elif confiance == 'medium':
        notes.append("📊 Tranche moyenne - bonne estimation")
    
    return " | ".join(notes) if notes else "Aucune note"

# Test du module
if __name__ == "__main__":
    print("🧪 Test du module de traitement Salesforce...")
    
    # Test avec les données de test
    test_file = "data/test_safe_final.csv"
    output_file = "data/salesforce_ready.csv"
    
    result = create_salesforce_ready_data(test_file, output_file)
    
    if result is not None:
        print(f"\n🎯 Test réussi ! Exemple des premières lignes:")
        print(result[['Organisation_Original', 'Effectifs_Salesforce', 'Statut_Revision']].head())
    else:
        print(f"\n❌ Test échoué")