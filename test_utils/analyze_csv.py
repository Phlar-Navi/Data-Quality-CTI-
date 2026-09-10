"""
Analyse du CSV d'extraction pour comprendre la structure des données.
Identifie les colonnes, types, taux de nullité, et génère des recommandations.
"""
import pandas as pd
from pathlib import Path
import sys

def analyze_csv(csv_path: str, sample_size: int = 10000):
    """
    Analyse un fichier CSV et affiche ses caractéristiques.
    
    Args:
        csv_path: Chemin vers le fichier CSV
        sample_size: Nombre de lignes à analyser (None = tout)
    """
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"❌ Fichier non trouvé : {csv_path}")
        return False
    
    print("="*80)
    print("🔍 ANALYSE DU FICHIER CSV")
    print("="*80)
    
    # Informations fichier
    file_size_mb = csv_file.stat().st_size / (1024**2)
    print(f"\n📂 Fichier : {csv_file.name}")
    print(f"📊 Taille  : {file_size_mb:.1f} MB")
    
    # Lecture
    print(f"\n⏳ Lecture de l'échantillon ({sample_size:,} lignes)...")
    try:
        df = pd.read_csv(
            csv_path,
            nrows=sample_size,
            encoding='utf-8',
            low_memory=False,
            on_bad_lines='skip'
        )
    except Exception as e:
        print(f"❌ Erreur de lecture : {e}")
        return False
    
    print(f"✅ {len(df):,} lignes chargées")
    print(f"✅ {len(df.columns)} colonnes trouvées")
    
    # Structure
    print("\n" + "="*80)
    print("📋 STRUCTURE DES COLONNES")
    print("="*80)
    
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        null_rate = (1 - non_null / len(df)) * 100
        
        # Échantillon de valeurs
        sample_values = df[col].dropna().head(3).tolist()
        sample_str = ", ".join(str(v)[:30] for v in sample_values)
        
        print(f"\n{i:2}. {col}")
        print(f"    Type      : {dtype}")
        print(f"    Nullité   : {null_rate:.1f}%")
        print(f"    Échantillon: {sample_str}")
    
    # Identification colonnes clés
    print("\n" + "="*80)
    print("🔑 COLONNES CLÉS IDENTIFIÉES")
    print("="*80)
    
    # Colonnes date/time
    date_columns = [
        col for col in df.columns
        if any(keyword in col.upper() for keyword in ['DATE', 'TIME', 'TIMESTAMP', 'DT'])
    ]
    print(f"\n📅 Colonnes date/time ({len(date_columns)}) :")
    for col in date_columns:
        print(f"   - {col}")
    
    # Colonnes ID
    id_columns = [
        col for col in df.columns
        if any(keyword in col.upper() for keyword in ['ID', 'KEY', 'NUMBER', 'NUM'])
    ]
    print(f"\n🆔 Colonnes identifiants ({len(id_columns)}) :")
    for col in id_columns:
        unique_count = df[col].nunique()
        print(f"   - {col:30} ({unique_count:,} valeurs uniques)")
    
    # Taux de nullité
    print("\n" + "="*80)
    print("❓ TAUX DE NULLITÉ PAR COLONNE")
    print("="*80)
    
    null_rates = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    print("\nTop 10 colonnes avec le plus de nullité :")
    for col, rate in null_rates.head(10).items():
        print(f"   {col:30} : {rate:5.2f}%")
    
    # Statistiques
    print("\n" + "="*80)
    print("📊 STATISTIQUES DESCRIPTIVES")
    print("="*80)
    
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        print(f"\nColonnes numériques ({len(numeric_cols)}) :")
        print(df[numeric_cols].describe())
    
    # Distribution dates (si trouvées)
    if date_columns:
        print("\n" + "="*80)
        print("📅 DISTRIBUTION TEMPORELLE")
        print("="*80)
        
        for date_col in date_columns[:2]:  # Max 2 colonnes date
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                min_date = df[date_col].min()
                max_date = df[date_col].max()
                unique_dates = df[date_col].dt.date.nunique()
                
                print(f"\n{date_col} :")
                print(f"   Période      : {min_date} → {max_date}")
                print(f"   Jours uniques: {unique_dates}")
                
                # Volumétrie par date
                if unique_dates <= 10:
                    daily_counts = df[date_col].dt.date.value_counts().sort_index()
                    print(f"\n   Volumétrie par jour :")
                    for date, count in daily_counts.items():
                        print(f"      {date} : {count:,} lignes")
                
            except Exception as e:
                print(f"   ⚠️ Impossible d'analyser : {e}")
    
    # Recommandations pour la table Oracle
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS POUR LA TABLE ORACLE")
    print("="*80)
    
    print("\nTypes de colonnes suggérés :")
    for col in df.columns:
        dtype = df[col].dtype
        max_len = df[col].astype(str).str.len().max() if dtype == 'object' else 0
        
        if dtype == 'object':
            if max_len <= 50:
                oracle_type = f"VARCHAR2({max_len + 10})"
            else:
                oracle_type = f"VARCHAR2({min(max_len + 50, 4000)})"
        elif dtype in ['int64', 'int32']:
            oracle_type = "NUMBER(10)"
        elif dtype in ['float64', 'float32']:
            oracle_type = "NUMBER(10,2)"
        elif 'datetime' in str(dtype):
            oracle_type = "DATE" if 'time' not in col.lower() else "TIMESTAMP"
        else:
            oracle_type = "VARCHAR2(4000)"
        
        print(f"   {col:30} → {oracle_type}")
    
    # Clé primaire suggérée
    print("\n🔑 Clé primaire suggérée :")
    for col in id_columns:
        unique_rate = df[col].nunique() / len(df) * 100
        null_rate = df[col].isnull().sum() / len(df) * 100
        
        if unique_rate > 95 and null_rate < 1:
            print(f"   ✅ {col} (unicité: {unique_rate:.1f}%, nullité: {null_rate:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)
    
    return True


if __name__ == "__main__":
    # Chemin par défaut - données CTI Mail
    default_path = r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Data\CTI_MAIL_20260620.csv"
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = default_path
    
    # Taille échantillon
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    
    success = analyze_csv(csv_path, sample_size)
    sys.exit(0 if success else 1)
