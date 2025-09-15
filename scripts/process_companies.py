#!/usr/bin/env python3
"""
Script principal pour enrichir des données d'entreprises avec l'API INSEE Sirene

Usage:
    python scripts/process_companies.py input.csv --company-col "Company Name" --size-col "Size" --output output.csv

Le script:
1. Lit un fichier CSV avec des noms d'entreprises
2. Enrichit les données via l'API INSEE Sirene
3. Applique les transformations pour Salesforce
4. Corrige automatiquement les effectifs manquants
5. Exporte le résultat final
"""

import argparse
import logging
import sys
import os
import pandas as pd
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.insee_client import INSEEClient
from src.data_processor import DataProcessor
from src.salesforce_export import SalesforceExporter

def setup_logging(verbose: bool = False):
    """Configure le logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_input_file(file_path: str, company_col: str, size_col: str = None) -> tuple:
    """Valide et charge le fichier d'entrée"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        logging.info(f"📄 Fichier chargé: {len(df)} lignes")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du CSV: {e}")
    
    # Vérifier que la colonne entreprise existe
    if company_col not in df.columns:
        available_cols = list(df.columns)
        raise ValueError(f"Colonne '{company_col}' non trouvée. Colonnes disponibles: {available_cols}")
    
    # Vérifier la colonne taille si spécifiée
    if size_col and size_col not in df.columns:
        available_cols = list(df.columns)
        logging.warning(f"Colonne taille '{size_col}' non trouvée. Colonnes disponibles: {available_cols}")
        logging.warning("Continuera sans information de taille")
        size_col = None  # Important: réinitialiser à None
    
    logging.info(f"✅ Colonne entreprises: '{company_col}'")
    if size_col:
        logging.info(f"✅ Colonne taille: '{size_col}'")
    else:
        logging.info("ℹ️  Pas de colonne taille spécifiée")
    
    return df, size_col  # Retourner aussi size_col modifié

def process_companies_pipeline(input_file: str, 
                             company_col: str, 
                             size_col: str = None,
                             output_file: str = None,
                             delay: float = 4.0,
                             demo_limit: int = None) -> str:
    """
    Pipeline complet de traitement des entreprises
    
    Returns:
        Chemin du fichier de sortie généré
    """
    
    # 1. Validation et chargement
    logging.info("🔍 Validation du fichier d'entrée...")
    df, size_col = validate_input_file(input_file, company_col, size_col)
    
    # Limitation demo si spécifiée
    if demo_limit:
        df = df.head(demo_limit)
        logging.info(f"🧪 Mode démo: limité à {demo_limit} entreprises")
    
    # 2. Initialisation des composants
    logging.info("⚙️ Initialisation des composants...")
    insee_client = INSEEClient(delay_between_requests=delay)
    processor = DataProcessor(insee_client)
    exporter = SalesforceExporter()
    
    # 3. Traitement INSEE
    logging.info("🚀 Début du traitement INSEE...")
    df_enriched = processor.process_companies(df, company_col, size_col)
    
    # 4. Transformation Salesforce
    logging.info("🔄 Transformation pour Salesforce...")
    df_salesforce = exporter.transform_for_salesforce(df_enriched)
    
    # 5. Génération du nom de fichier de sortie
    if not output_file:
        input_path = Path(input_file)
        if demo_limit:
            output_file = f"output/demo_{demo_limit}_{input_path.stem}_enriched.csv"
        else:
            output_file = f"output/{input_path.stem}_enriched.csv"
    
    # Créer le répertoire de sortie
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 6. Sauvegarde
    df_salesforce.to_csv(output_file, index=False, encoding='utf-8')
    logging.info(f"✅ Fichier enrichi sauvegardé: {output_file}")
    
    # 7. Statistiques finales
    stats = insee_client.get_stats()
    logging.info(f"\n📊 STATISTIQUES FINALES:")
    logging.info(f"   🔗 Appels API: {stats['api_calls']}")
    logging.info(f"   💾 Cache hits: {stats['cache_hits']}")
    logging.info(f"   ✅ Taux de réussite: {stats['success_rate_percent']}%")
    logging.info(f"   ⚡ Efficacité cache: {stats['cache_rate_percent']}%")
    
    return output_file

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Enrichissement de données d'entreprises avec l'API INSEE Sirene",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

1. Traitement basique:
   python scripts/process_companies.py data/companies.csv --company-col "Company Name"

2. Avec colonne taille:
   python scripts/process_companies.py data/companies.csv --company-col "Organisation" --size-col "Taille"

3. Mode démo (50 entreprises):
   python scripts/process_companies.py data/companies.csv --company-col "Company Name" --demo 50

4. Sortie personnalisée:
   python scripts/process_companies.py data/companies.csv --company-col "Company Name" --output results/enriched.csv

5. Délai personnalisé (plus rapide, plus risqué):
   python scripts/process_companies.py data/companies.csv --company-col "Company Name" --delay 2.0

Configuration requise:
- Fichier .env avec SIRENE_API_KEY=votre_clé_api
- Ou variable d'environnement SIRENE_API_KEY
        """
    )
    
    # Arguments obligatoires
    parser.add_argument('input_file', 
                       help='Fichier CSV d\'entrée avec les données d\'entreprises')
    parser.add_argument('--company-col', 
                       required=True,
                       help='Nom de la colonne contenant les noms d\'entreprises')
    
    # Arguments optionnels
    parser.add_argument('--size-col', 
                       help='Nom de la colonne contenant la taille d\'entreprise (optionnel)')
    parser.add_argument('--output', 
                       help='Fichier de sortie (défaut: output/[input]_enriched.csv)')
    parser.add_argument('--delay', 
                       type=float, 
                       default=4.0,
                       help='Délai entre requêtes API en secondes (défaut: 4.0)')
    parser.add_argument('--demo', 
                       type=int,
                       help='Mode démo: limiter le traitement à N entreprises')
    parser.add_argument('--verbose', 
                       action='store_true',
                       help='Activer les logs détaillés')
    
    args = parser.parse_args()
    
    # Configuration du logging
    setup_logging(args.verbose)
    
    try:
        # Vérification de la clé API
        if not os.getenv('SIRENE_API_KEY'):
            logging.error("❌ Variable SIRENE_API_KEY non définie")
            logging.error("   Créez un fichier .env avec: SIRENE_API_KEY=votre_clé")
            logging.error("   Ou définissez la variable d'environnement")
            sys.exit(1)
        
        # Exécution du pipeline
        logging.info("🚀 Début du traitement d'enrichissement INSEE")
        logging.info(f"📄 Fichier d'entrée: {args.input_file}")
        logging.info(f"🏢 Colonne entreprises: {args.company_col}")
        if args.size_col:
            logging.info(f"📏 Colonne taille: {args.size_col}")
        if args.demo:
            logging.info(f"🧪 Mode démo: {args.demo} entreprises")
        
        output_file = process_companies_pipeline(
            input_file=args.input_file,
            company_col=args.company_col,
            size_col=args.size_col,
            output_file=args.output,
            delay=args.delay,
            demo_limit=args.demo
        )
        
        logging.info(f"\n🎉 Traitement terminé avec succès!")
        logging.info(f"📄 Résultat: {output_file}")
        
    except Exception as e:
        logging.error(f"❌ Erreur: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()