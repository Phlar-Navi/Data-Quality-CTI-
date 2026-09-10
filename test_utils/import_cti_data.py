"""
Script d'import des données CTI dans Oracle.
Crée la table et importe les fichiers CSV du répertoire Data/.
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
print("  IMPORT DES DONNEES CTI DANS ORACLE")
print("="*80)

# 1. Connexion
print(f"\n[1] Connexion a Oracle en tant que {USER}...")
try:
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    cursor = conn.cursor()
    print("    [OK] Connecte")
except Exception as e:
    print(f"    [ERROR] {e}")
    sys.exit(1)

# 2. Créer la table
print("\n[2] Creation de la table CDR_EVENTS...")

# Supprimer si existe
try:
    cursor.execute("DROP TABLE CDR_EVENTS CASCADE CONSTRAINTS")
    print("    [INFO] Ancienne table supprimee")
except:
    pass

# Créer la table
create_table_sql = """
CREATE TABLE CDR_EVENTS (
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

try:
    cursor.execute(create_table_sql)
    print("    [OK] Table creee")
except Exception as e:
    print(f"    [ERROR] {e}")
    sys.exit(1)

# Créer les index
print("\n[3] Creation des index...")
indexes = [
    "CREATE INDEX IDX_EVENT_DATE ON CDR_EVENTS(EVENT_DATE)",
    "CREATE INDEX IDX_FILE_DATE ON CDR_EVENTS(FILE_DATE)",
    "CREATE INDEX IDX_TECHNICAL_RESULT ON CDR_EVENTS(TECHNICAL_RESULT)",
    "CREATE INDEX IDX_SEGMENT ON CDR_EVENTS(SEGMENT)",
    "CREATE INDEX IDX_SITE_CIBLE ON CDR_EVENTS(UD_SITE_CIBLE)"
]

for idx_sql in indexes:
    try:
        cursor.execute(idx_sql)
        print(f"    [OK] {idx_sql.split()[2]}")
    except Exception as e:
        print(f"    [WARN] {e}")

# Colonne calculée EVENT_HOUR
try:
    cursor.execute("""
        ALTER TABLE CDR_EVENTS ADD EVENT_HOUR NUMBER(2) 
        GENERATED ALWAYS AS (TO_NUMBER(SUBSTR(EVENT_TIME, 12, 2))) VIRTUAL
    """)
    cursor.execute("CREATE INDEX IDX_EVENT_HOUR ON CDR_EVENTS(EVENT_HOUR)")
    print("    [OK] Colonne EVENT_HOUR creee")
except Exception as e:
    print(f"    [WARN] {e}")

conn.commit()

# 3. Accorder droits à monitoring_user
print("\n[4] Droits SELECT pour monitoring_user...")
try:
    cursor.execute("GRANT SELECT ON CDR_EVENTS TO monitoring_user")
    print("    [OK] Droits accordes")
except Exception as e:
    print(f"    [WARN] {e}")

# 4. Import des données
print(f"\n[5] Import des fichiers CSV depuis {DATA_DIR}...")

csv_files = sorted(DATA_DIR.glob("CTI_MAIL_*.csv"))
print(f"    [INFO] {len(csv_files)} fichiers trouves")

total_imported = 0
total_errors = 0

insert_sql = """
    INSERT INTO CDR_EVENTS (
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

for csv_file in csv_files:
    print(f"\n    Fichier: {csv_file.name}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            batch = []
            line_count = 0
            
            for row in reader:
                line_count += 1
                
                # Convertir les valeurs
                try:
                    # Dates
                    event_date = datetime.strptime(row['EVENT_DATE'], '%Y-%m-%d') if row['EVENT_DATE'] else None
                    file_date = datetime.strptime(row['FILE_DATE'], '%Y-%m-%d') if row['FILE_DATE'] else None
                    orig_file_date = datetime.strptime(row['ORIGINAL_FILE_DATE'], '%Y-%m-%d') if row['ORIGINAL_FILE_DATE'] else None
                    insert_date = datetime.fromisoformat(row['INSERT_DATE'].replace('+01:00', '')) if row['INSERT_DATE'] else None
                    
                    # Nombres
                    ts = int(row['TS']) if row['TS'] else None
                    place_key = int(row['PLACE_KEY']) if row['PLACE_KEY'] and row['PLACE_KEY'] != '-2' else -2
                    duree_conv = int(row['DUREE_CONVERSATION']) if row['DUREE_CONVERSATION'] else 0
                    duree_file = int(row['DUREE_FILE']) if row['DUREE_FILE'] else 0
                    tech_desc_key = int(row['TECHNICAL_DESCRIPTOR_KEY']) if row['TECHNICAL_DESCRIPTOR_KEY'] else None
                    orig_size = int(row['ORIGINAL_FILE_SIZE']) if row['ORIGINAL_FILE_SIZE'] else None
                    orig_lines = int(row['ORIGINAL_FILE_LINE_COUNT']) if row['ORIGINAL_FILE_LINE_COUNT'] else None
                    
                    # Remplacer 'none' par None
                    site_choisi = row['UD_SITE_CHOISI'] if row['UD_SITE_CHOISI'] != 'none' else None
                    place = row['PLACE'] if row['PLACE'] != 'NO_VALUE' else None
                    
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
                    
                    # Insertion par batch de 500 (réduit pour éviter timeout)
                    if len(batch) >= 500:
                        try:
                            cursor.executemany(insert_sql, batch)
                            conn.commit()
                            total_imported += len(batch)
                            print(f"        [INFO] {total_imported:,} lignes importees...", end='\r')
                            batch = []
                        except Exception as e:
                            # Si erreur batch, essayer ligne par ligne
                            for row_data in batch:
                                try:
                                    cursor.execute(insert_sql, row_data)
                                    total_imported += 1
                                except:
                                    total_errors += 1
                            conn.commit()
                            batch = []
                        
                except Exception as e:
                    total_errors += 1
                    if total_errors <= 5:  # Afficher seulement les 5 premières erreurs
                        print(f"        [WARN] Ligne {line_count}: {e}")
            
            # Insérer le reste
            if batch:
                try:
                    cursor.executemany(insert_sql, batch)
                    conn.commit()
                    total_imported += len(batch)
                except Exception as e:
                    # Si erreur, essayer ligne par ligne
                    for row_data in batch:
                        try:
                            cursor.execute(insert_sql, row_data)
                            total_imported += 1
                        except:
                            total_errors += 1
                    conn.commit()
            
            print(f"        [OK] {line_count:,} lignes lues, {line_count - total_errors:,} importees")
            
    except Exception as e:
        print(f"        [ERROR] {e}")
        continue

# 6. Vérification finale
print(f"\n[6] Verification...")
cursor.execute("SELECT COUNT(*) FROM CDR_EVENTS")
count = cursor.fetchone()[0]
print(f"    [OK] Total lignes importees : {count:,}")

cursor.execute("SELECT MIN(EVENT_DATE), MAX(EVENT_DATE) FROM CDR_EVENTS")
min_date, max_date = cursor.fetchone()
print(f"    [OK] Periode : {min_date.strftime('%Y-%m-%d')} -> {max_date.strftime('%Y-%m-%d')}")

cursor.execute("SELECT EVENT_DATE, COUNT(*) FROM CDR_EVENTS GROUP BY EVENT_DATE ORDER BY EVENT_DATE")
print(f"\n    Volumetrie par jour :")
for row in cursor:
    print(f"      {row[0].strftime('%Y-%m-%d')} : {row[1]:,} lignes")

cursor.close()
conn.close()

print("\n" + "="*80)
print("  IMPORT TERMINE")
print("="*80)
print(f"\nStatistiques :")
print(f"  Fichiers traites : {len(csv_files)}")
print(f"  Lignes importees : {total_imported:,}")
print(f"  Erreurs          : {total_errors}")
print(f"\nTable : DWH_CTI_TEST.CDR_EVENTS")
print(f"DSN   : {DSN}")
print("\nProchaine etape :")
print("  Tester le monitoring : python main.py --breakpoint bp_test_local")
print("="*80)
