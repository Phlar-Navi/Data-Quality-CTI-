"""
Script pour créer les utilisateurs Oracle de test.
Crée dwh_cti_test (propriétaire) et monitoring_user (read-only).
"""
import oracledb
import sys

# Configuration (adapter l'IP selon votre machine)
DSN = "172.16.16.169:1521/XEPDB1"  # PDB au lieu de CDB
ADMIN_USER = "system"
ADMIN_PASSWORD = "Oratoria_7"

print("="*60)
print("  CREATION DES UTILISATEURS ORACLE")
print("="*60)

try:
    # Connexion en tant que SYSTEM
    print(f"\n[1] Connexion a Oracle en tant que {ADMIN_USER}...")
    conn = oracledb.connect(user=ADMIN_USER, password=ADMIN_PASSWORD, dsn=DSN)
    cursor = conn.cursor()
    print("    [OK] Connecte")
    
    # Créer dwh_cti_test
    print("\n[2] Creation de l'utilisateur dwh_cti_test...")
    try:
        cursor.execute("DROP USER dwh_cti_test CASCADE")
        print("    [INFO] Ancien utilisateur supprime")
    except:
        pass
    
    cursor.execute("""
        CREATE USER dwh_cti_test IDENTIFIED BY DwhTest123
    """)
    print("    [OK] Utilisateur cree")
    
    cursor.execute("GRANT CONNECT, RESOURCE TO dwh_cti_test")
    cursor.execute("GRANT UNLIMITED TABLESPACE TO dwh_cti_test")
    cursor.execute("GRANT CREATE TABLE, CREATE VIEW TO dwh_cti_test")
    print("    [OK] Droits accordes")
    
    # Créer monitoring_user
    print("\n[3] Creation de l'utilisateur monitoring_user...")
    try:
        cursor.execute("DROP USER monitoring_user CASCADE")
        print("    [INFO] Ancien utilisateur supprime")
    except:
        pass
    
    cursor.execute("""
        CREATE USER monitoring_user IDENTIFIED BY MonitorTest123
    """)
    print("    [OK] Utilisateur cree")
    
    cursor.execute("GRANT CONNECT TO monitoring_user")
    cursor.execute("GRANT SELECT ANY TABLE TO monitoring_user")  # Pour tests
    print("    [OK] Droits accordes")
    
    # Vérifier
    print("\n[4] Verification des utilisateurs...")
    cursor.execute("""
        SELECT username, account_status, created
        FROM dba_users
        WHERE username IN ('DWH_CTI_TEST', 'MONITORING_USER')
        ORDER BY username
    """)
    
    for row in cursor:
        print(f"    [OK] {row[0]:20} - {row[1]:15} - Cree: {row[2].strftime('%Y-%m-%d')}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Test des connexions
    print("\n[5] Test des connexions...")
    
    # Test dwh_cti_test
    conn_test = oracledb.connect(user='dwh_cti_test', password='DwhTest123', dsn=DSN)
    print("    [OK] Connexion dwh_cti_test reussie")
    conn_test.close()
    
    # Test monitoring_user
    conn_mon = oracledb.connect(user='monitoring_user', password='MonitorTest123', dsn=DSN)
    print("    [OK] Connexion monitoring_user reussie")
    conn_mon.close()
    
    print("\n" + "="*60)
    print("  SUCCES - Utilisateurs crees et testes")
    print("="*60)
    print("\nCredentials crees :")
    print("  dwh_cti_test / DwhTest123       (proprietaire des donnees)")
    print("  monitoring_user / MonitorTest123 (read-only)")
    print(f"\nDSN : {DSN}")
    print("\nProchaine etape :")
    print("  1. Creer le fichier .env.test avec ces credentials")
    print("  2. Analyser le CSV : python test_utils\\analyze_csv.py")
    print("  3. Creer la table selon la structure detectee")
    print("="*60)
    
    sys.exit(0)

except oracledb.DatabaseError as e:
    error, = e.args
    print(f"\n[ERROR] Erreur Oracle : {error.message}")
    print(f"        Code : {error.code}")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)
