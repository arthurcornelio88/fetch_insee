"""
INSEE Data Processor - Module pour enrichir des données d'entreprises avec l'API Sirene INSEE

Ce module permet de :
- Rechercher des entreprises dans la base Sirene INSEE
- Enrichir les données avec effectifs, SIREN, catégories
- Exporter au format compatible Salesforce
- Gérer intelligemment les doublons et rate limits API
"""

__version__ = "1.0.0"
__author__ = "Data INSEE Team"

from .insee_client import INSEEClient
from .data_processor import DataProcessor
from .salesforce_export import SalesforceExporter

__all__ = ["INSEEClient", "DataProcessor", "SalesforceExporter"]