#!/usr/bin/env python3
"""
Rapport final du traitement INSEE → Salesforce
"""

import pandas as pd

def generate_final_report():
    """Générer le rapport final de la transformation"""
    print("📊 RAPPORT FINAL - TRANSFORMATION INSEE → SALESFORCE")
    print("=" * 70)
    
    try:
        # Chercher le fichier Salesforce (priorité au fichier complet)
        salesforce_files = [
            "data/face_raw_full_salesforce_ready.csv",
            "data/face_raw_salesforce_ready.csv", 
            "data/demo_100_salesforce_ready.csv",
            "data/test_salesforce_ready.csv"
        ]
        
        df_sf = None
        used_file = None
        
        for file_path in salesforce_files:
            try:
                df_sf = pd.read_csv(file_path)
                used_file = file_path
                break
            except FileNotFoundError:
                continue
        
        if df_sf is None:
            print("❌ Aucun fichier Salesforce trouvé")
            return False
        
        print(f"\n✅ FICHIER SALESFORCE GÉNÉRÉ AVEC SUCCÈS")
        print(f"📄 Fichier: {used_file}")
        print(f"📊 Total entreprises: {len(df_sf)}")
        
        # Analyse des statuts de révision
        print(f"\n🔍 STATUTS DE RÉVISION:")
        statuts = df_sf['Statut_Revision'].value_counts()
        for statut, count in statuts.items():
            percentage = count/len(df_sf)*100
            print(f"   📋 {statut}: {count} entreprises ({percentage:.1f}%)")
        
        # Analyse des effectifs
        effectifs = df_sf['Effectifs_Salesforce'].dropna()
        print(f"\n💼 EFFECTIFS SALESFORCE:")
        print(f"   📊 Avec données numériques: {len(effectifs)}/{len(df_sf)} ({len(effectifs)/len(df_sf)*100:.1f}%)")
        
        if len(effectifs) > 0:
            print(f"   📈 Moyenne: {effectifs.mean():.0f} employés")
            print(f"   📊 Médiane: {effectifs.median():.0f} employés")
            print(f"   📉 Min: {effectifs.min():.0f} employés")
            print(f"   📈 Max: {effectifs.max():.0f} employés")
        
        # Analyse des niveaux de confiance
        print(f"\n🎯 NIVEAUX DE CONFIANCE:")
        confiances = df_sf['Confiance_Donnee'].value_counts()
        for conf, count in confiances.items():
            percentage = count/len(df_sf)*100
            icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "⚪")
            print(f"   {icon} {conf}: {count} entreprises ({percentage:.1f}%)")
        
        # Recommandations par statut
        print(f"\n📋 RECOMMANDATIONS PAR STATUT:")
        
        confirmed = len(df_sf[df_sf['Statut_Revision'] == 'CONFIRMED'])
        if confirmed > 0:
            print(f"   ✅ CONFIRMED ({confirmed} entreprises):")
            print(f"      → Prêt pour import direct dans Salesforce")
        
        conflict = len(df_sf[df_sf['Statut_Revision'] == 'CONFLICT_TO_REVIEW'])
        if conflict > 0:
            print(f"   ⚠️  CONFLICT_TO_REVIEW ({conflict} entreprises):")
            print(f"      → Vérifier incohérences taille déclarée vs INSEE")
            print(f"      → Révision manuelle recommandée")
        
        missing = len(df_sf[df_sf['Statut_Revision'] == 'MISSING_EFFECTIFS'])
        if missing > 0:
            print(f"   🔍 MISSING_EFFECTIFS ({missing} entreprises):")
            print(f"      → Entreprises trouvées mais effectifs non renseignés")
            print(f"      → Recherche manuelle nécessaire")
        
        not_found = len(df_sf[df_sf['Statut_Revision'] == 'NOT_FOUND'])
        if not_found > 0:
            print(f"   ❌ NOT_FOUND ({not_found} entreprises):")
            print(f"      → Entreprises non trouvées dans INSEE")
            print(f"      → Vérifier orthographe ou chercher manuellement")
        
        # Colonnes importantes pour Salesforce
        print(f"\n📊 COLONNES CLÉS POUR SALESFORCE:")
        print(f"   🏢 Organisation_Original: Nom d'entreprise original")
        print(f"   🏛️  Denomination_INSEE: Nom officiel INSEE")
        print(f"   👥 Effectifs_Salesforce: Nombre d'employés (numérique)")
        print(f"   🎯 Confiance_Donnee: Niveau de fiabilité (high/medium/low)")
        print(f"   📋 Statut_Revision: Action requise")
        print(f"   💯 Match_Score: Score de correspondance (0-100)")
        print(f"   📝 Notes_Revision: Instructions détaillées")
        
        # Aperçu des meilleures correspondances
        high_conf = df_sf[df_sf['Confiance_Donnee'] == 'high'].head(5)
        if len(high_conf) > 0:
            print(f"\n🌟 APERÇU DES MEILLEURES CORRESPONDANCES:")
            for _, row in high_conf.iterrows():
                org = row['Organisation_Original']
                insee = row['Denomination_INSEE']
                effectifs = row['Effectifs_Salesforce']
                if pd.notna(effectifs):
                    print(f"   ✅ {org} → {insee} ({effectifs:.0f} employés)")
                else:
                    print(f"   ✅ {org} → {insee} (effectifs N/A)")
        
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"   1. Réviser les entreprises avec statut CONFLICT_TO_REVIEW")
        print(f"   2. Rechercher manuellement les entreprises NOT_FOUND")
        print(f"   3. Compléter les effectifs pour MISSING_EFFECTIFS")
        print(f"   4. Importer le fichier dans Salesforce")
        
        print(f"\n💾 FICHIER PRÊT POUR SALESFORCE:")
        print(f"   📄 {used_file}")
        print(f"   🔧 Format: CSV UTF-8")
        print(f"   📊 {len(df_sf)} lignes, {len(df_sf.columns)} colonnes")
        
        return True
        
    except FileNotFoundError:
        print("❌ Fichier Salesforce non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    generate_final_report()