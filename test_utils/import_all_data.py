"""
Script d'import COMPLET des données CTI dans Oracle.
Importe TOUT y compris les doublons pour tester la robustesse du monitoring.
"""
import oracledb
import csv
from pathlib import Path
from datetime import datetime
import sys

# Configuration
DSN = "172.16.16.169:1521/XEPDB1"
USER = "dwh_cti_test"
PASSWORD = "DwhTest123"
DATA_DIR = Path(r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Data")

print("="*80)
print("  IMPORT COMPLET DES DONNEES CTI (avec doublons)")
print("="*80)

# Connexion
print(f"\n[1] Connexion a Oracle...")
conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
cursor = conn.cursor()
print("    [OK] Connecte")

# Créer la table (avec ID auto-incrémenté)
print("\n[2] Creation de la table CDR_EVENTS...")
try:
    cursor.execute("DROP TABLE CDR_EVENTS_V2 CASCADE CONSTRAINTS PURGE")
    print("    [INFO] Ancienne table supprimee")
except:
    print("    [INFO] Pas de table existante")

create_table_sql = """
CREATE TABLE CDR_EVENTS_V2 (
    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    EVENT_TIME VARCHAR2(50),
    EVENT_DATE DATE,
    FILE_DATE DATE,
    TS NUMBER(15),
    CONNID VARCHAR2(50),
    ANI VARCHAR2(20),
    DNIS VARCHAR2(20),
    LAST_VQ VARCHAR2(100),
    PLACE_KEY NUMBER(10),
    UD_SITE_CHOISI VARCHAR2(50),
    UD_SITE_CIBLE VARCHAR2(50),
    TECHNICAL_RESULT VARCHAR2(50),
    TECHNICAL_RESULT_CODE VARCHAR2(50),
    RESULT_REASON VARCHAR2(100),
    RESULT_REASON_CODE VARCHAR2(100),
    INTERACTION_TYPE VARCHAR2(50),
    INTERACTION_TYPE_CODE VARCHAR2(50),
    PLACE VARCHAR2(50),
    RESOURCE_TYPE VARCHAR2(50),
    RESOURCE_NAME VARCHAR2(50),
    NOM VARCHAR2(100),
    DUREE_CONVERSATION NUMBER(10),
    DUREE_FILE NUMBER(10),
    TECHNICAL_DESCRIPTOR_KEY NUMBER(10),
    SEGMENT VARCHAR2(100),
    ORIGINAL_FILE_NAME VARCHAR2(200),
    ORIGINAL_FILE_DATE DATE,
    ORIGINAL_FILE_SIZE NUMBER(15),
    ORIGINAL_FILE_LINE_COUNT NUMBER(10),
    INSERT_DATE TIMESTAMP,
    LOADED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

cursor.execute(create_table_sql)
print("    [OK] Table creee avec ID auto-incremente")

# Index
print("\n[3] Creation des index...")
indexes = [
    "CREATE INDEX IDX_CONNID ON CDR_EVENTS_V2(CONNID)",
    "CREATE INDEX IDX_EVENT_DATE ON CDR_EVENTS_V2(EVENT_DATE)",
    "CREATE INDEX IDX_TECHNICAL_RESULT ON CDR_EVENTS_V2(TECHNICAL_RESULT)"
]
for idx in indexes:
    try:
        cursor.execute(idx)
        print(f"    [OK] {idx.split()[2]}")
    except:
        print(f"    [SKIP] {idx.split()[2]}")
print("    [OK] Index traites")

# Colonne EVENT_HOUR calculée
try:
    cursor.execute("""
        ALTER TABLE CDR_EVENTS_V2 ADD EVENT_HOUR NUMBER(2) 
        GENERATED ALWAYS AS (TO_NUMBER(SUBSTR(EVENT_TIME, 12, 2))) VIRTUAL
    """)
    cursor.execute("CREATE INDEX IDX_EVENT_HOUR ON CDR_EVENTS_V2(EVENT_HOUR)")
    print("    [OK] Colonne EVENT_HOUR creee")
except:
    print("    [SKIP] Colonne EVENT_HOUR existe deja")

# Droits
cursor.execute("GRANT SELECT ON CDR_EVENTS_V2 TO monitoring_user")
conn.commit()

# Import
print(f"\n[4] Import des fichiers CSV...")
csv_files = sorted(DATA_DIR.glob("CTI_MAIL_*.csv"))
print(f"    [INFO] {len(csv_files)} fichiers a traiter")

insert_sql = """
    INSERT INTO CDR_EVENTS_V2 (
        EVENT_TIME, TS, CONNID, ANI, DNIS, LAST_VQ,
        TECHNICAL_RESULT, TECHNICAL_RESULT_CODE,
        RESULT_REASON, RESULT_REASON_CODE,
        DUREE_CONVERSATION, PLACE_KEY, UD_SITE_CHOISI,
        INTERACTION_TYPE, INTERACTION_TYPE_CODE,
        PLACE, RESOURCE_TYPE, RESOURCE_NAME, NOM,
        DUREE_FILE, ORIGINAL_FILE_NAME, ORIGINAL_FILE_DATE,
        ORIGINAL_FILE_SIZE, ORIGINAL_FILE_LINE_COUNT,
        INSERT_DATE, UD_SITE_CIBLE, TECHNICAL_DESCRIPTOR_KEY,
        SEGMENT, EVENT_DATE, FILE_DATE
    ) VALUES (
        :1, :2, :3, :4, :5, :6, :7, :8, :9, :10,
        :11, :12, :13, :14, :15, :16, :17, :18, :19, :20,
        :21, :22, :23, :24, :25, :26, :27, :28, :29, :30
    )
"""

total_imported = 0
total_skipped = 0

for csv_file in csv_files:
    print(f"\n    Fichier: {csv_file.name}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        batch = []
        
        for row in reader:
            try:
                # Parse dates
                event_date = datetime.strptime(row['EVENT_DATE'], '%Y-%m-%d') if row['EVENT_DATE'] else None
                file_date = datetime.strptime(row['FILE_DATE'], '%Y-%m-%d') if row['FILE_DATE'] else None
                orig_file_date = datetime.strptime(row['ORIGINAL_FILE_DATE'], '%Y-%m-%d') if row['ORIGINAL_FILE_DATE'] else None
                
                # Parse timestamp INSERT_DATE
                insert_date_str = row['INSERT_DATE']
                if insert_date_str:
                    # Enlever le timezone pour simplifier
                    insert_date_str = insert_date_str.split('+')[0].split('.')[0]
                    insert_date = datetime.strptime(insert_date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    insert_date = None
                
                # Parse numbers
                ts = int(row['TS']) if row['TS'] else None
                place_key = int(row['PLACE_KEY']) if row['PLACE_KEY'] else None
                duree_conv = int(row['DUREE_CONVERSATION']) if row['DUREE_CONVERSATION'] else 0
                duree_file = int(row['DUREE_FILE']) if row['DUREE_FILE'] else 0
                tech_desc_key = int(row['TECHNICAL_DESCRIPTOR_KEY']) if row['TECHNICAL_DESCRIPTOR_KEY'] else None
                orig_size = int(row['ORIGINAL_FILE_SIZE']) if row['ORIGINAL_FILE_SIZE'] else None
                orig_lines = int(row['ORIGINAL_FILE_LINE_COUNT']) if row['ORIGINAL_FILE_LINE_COUNT'] else None
                
                # Remplacer valeurs spéciales
                site_choisi = None if row['UD_SITE_CHOISI'] == 'none' else row['UD_SITE_CHOISI']
                place = None if row['PLACE'] == 'NO_VALUE' else row['PLACE']
                
                batch.append((
                    row['EVENT_TIME'], ts, row['CONNID'], row['ANI'], row['DNIS'],
                    row['LAST_VQ'], row['TECHNICAL_RESULT'], row['TECHNICAL_RESULT_CODE'],
                    row['RESULT_REASON'], row['RESULT_REASON_CODE'],
                    duree_conv, place_key, site_choisi,
                    row['INTERACTION_TYPE'], row['INTERACTION_TYPE_CODE'],
                    place, row['RESOURCE_TYPE'], row['RESOURCE_NAME'], row['NOM'],
                    duree_file, row['ORIGINAL_FILE_NAME'], orig_file_date,
                    orig_size, orig_lines, insert_date,
                    row['UD_SITE_CIBLE'], tech_desc_key, row['SEGMENT'],
                    event_date, file_date
                ))
                
                # Batch insert
                if len(batch) >= 500:
                    cursor.executemany(insert_sql, batch)
                    conn.commit()
                    total_imported += len(batch)
                    print(f"        {total_imported:,} lignes importees...", end='\r')
                    batch = []
                    
            except Exception as e:
                total_skipped += 1
                if total_skipped <= 3:
                    print(f"\n        [WARN] Ligne ignoree: {e}")
        
        # Reste du batch
        if batch:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            total_imported += len(batch)
    
    print(f"        [OK] Import termine")

# Stats finales
print(f"\n[5] Verification...")
cursor.execute("SELECT COUNT(*) FROM CDR_EVENTS_V2")
count = cursor.fetchone()[0]
print(f"    Total lignes : {count:,}")

cursor.execute("SELECT COUNT(DISTINCT CONNID) FROM CDR_EVENTS_V2")
distinct = cursor.fetchone()[0]
duplicates = count - distinct
print(f"    CONNID distincts : {distinct:,}")
print(f"    Doublons detectes : {duplicates:,} (c'est normal !)")

cursor.execute("SELECT MIN(EVENT_DATE), MAX(EVENT_DATE) FROM CDR_EVENTS_V2")
min_date, max_date = cursor.fetchone()
print(f"    Periode : {min_date.strftime('%Y-%m-%d')} -> {max_date.strftime('%Y-%m-%d')}")

cursor.execute("""
    SELECT EVENT_DATE, COUNT(*) 
    FROM CDR_EVENTS_V2 
    GROUP BY EVENT_DATE 
    ORDER BY EVENT_DATE
""")
print(f"\n    Volumetrie par jour :")
for row in cursor:
    print(f"      {row[0].strftime('%Y-%m-%d')} : {row[1]:,} lignes")

cursor.close()
conn.close()

print("\n" + "="*80)
print("  IMPORT TERMINE - Donnees pretes pour tests")
print("="*80)
print(f"\nStatistiques :")
print(f"  Lignes importees : {total_imported:,}")
print(f"  Doublons inclus  : {duplicates:,}")
print(f"  Lignes ignorees  : {total_skipped}")
print(f"\nTable : DWH_CTI_TEST.CDR_EVENTS_V2")
print(f"\nProchaine etape :")
print(f"  1. Charger variables env : Get-Content .env.test | ForEach-Object {{")
print(f"       if ($_ -match '^(\\w+)=(.+)$') {{ $env:($matches[1]) = $matches[2] }}")
print(f"     }}")
print(f"  2. Tester monitoring : python main.py --breakpoint bp_test_local")
print("="*80)
