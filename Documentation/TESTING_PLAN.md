# 🧪 Plan de test complet - Monitoring CTI

Plan détaillé pour tester le système de monitoring avec un environnement Oracle local et des données réelles issues d'extractions Excel/CSV.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Phase 1 : Installation Oracle XE](#phase-1--installation-oracle-xe)
3. [Phase 2 : Préparation des données](#phase-2--préparation-des-données)
4. [Phase 3 : Import des données](#phase-3--import-des-données)
5. [Phase 4 : Configuration monitoring](#phase-4--configuration-monitoring)
6. [Phase 5 : Tests unitaires](#phase-5--tests-unitaires)
7. [Phase 6 : Tests d'intégration](#phase-6--tests-dintégration)
8. [Phase 7 : Validation finale](#phase-7--validation-finale)

---

## 🎯 Vue d'ensemble

### Objectifs

- ✅ Installer Oracle Database XE (gratuit) localement
- ✅ Créer un schéma DWH_CTI_TEST
- ✅ Importer les données d'extractions Excel/CSV
- ✅ Tester tous les checks du système
- ✅ Valider le scoring et les statuts
- ✅ Générer des rapports de test

### Données sources disponibles

Selon `data_presence.md`, nous avons :
- ✅ `extract_dwh_20241120.csv` (147 MB, 2M+ lignes)
- ✅ Autres extractions potentielles

### Timeline estimée

| Phase | Durée | Tâches |
|-------|-------|--------|
| Phase 1 | 1h | Installation Oracle XE |
| Phase 2 | 30min | Préparation données CSV |
| Phase 3 | 1h | Import données Oracle |
| Phase 4 | 15min | Configuration monitoring |
| Phase 5 | 30min | Tests unitaires |
| Phase 6 | 30min | Tests intégration |
| Phase 7 | 15min | Validation finale |
| **TOTAL** | **~4h** | |

---

## 📦 Phase 1 : Installation Oracle XE

### 1.1 Télécharger Oracle Database XE

Oracle Database Express Edition (XE) est **gratuit** et parfait pour les tests.

**Option 1 : Installation native Windows**

1. Aller sur : https://www.oracle.com/database/technologies/xe-downloads.html
2. Télécharger : Oracle Database 21c Express Edition for Windows x64
3. Taille : ~2.5 GB

**Option 2 : Docker (plus rapide, recommandé)**

```powershell
# Installer Docker Desktop si pas déjà fait
# https://www.docker.com/products/docker-desktop/

# Télécharger l'image Oracle XE
docker pull container-registry.oracle.com/database/express:latest

# Lancer le conteneur
docker run -d `
  --name oracle-xe `
  -p 1521:1521 `
  -p 5500:5500 `
  -e ORACLE_PWD=OracleTest123 `
  -v oracle-data:/opt/oracle/oradata `
  container-registry.oracle.com/database/express:latest

# Attendre le démarrage (2-3 minutes)
docker logs -f oracle-xe
# Attendre le message "DATABASE IS READY TO USE!"
```

### 1.2 Vérifier l'installation

```powershell
# Test connexion avec SQL*Plus (si installé)
sqlplus sys/OracleTest123@localhost:1521/XE as sysdba

# OU via Python
python -c "
import oracledb
conn = oracledb.connect(user='system', password='OracleTest123', dsn='localhost:1521/XE')
print('✅ Connexion Oracle OK')
conn.close()
"
```

### 1.3 Créer l'utilisateur monitoring

```sql
-- Se connecter en tant que SYSTEM
sqlplus system/OracleTest123@localhost:1521/XE

-- Créer le schéma de test
CREATE USER dwh_cti_test IDENTIFIED BY DwhTest123;

-- Accorder les droits nécessaires
GRANT CONNECT, RESOURCE TO dwh_cti_test;
GRANT CREATE TABLE, CREATE VIEW TO dwh_cti_test;
GRANT UNLIMITED TABLESPACE TO dwh_cti_test;

-- Créer l'utilisateur read-only pour monitoring
CREATE USER monitoring_user IDENTIFIED BY MonitorTest123;
GRANT CONNECT TO monitoring_user;
GRANT SELECT ON dwh_cti_test.CDR_EVENTS TO monitoring_user;

-- Vérifier
SELECT username, account_status FROM dba_users WHERE username IN ('DWH_CTI_TEST', 'MONITORING_USER');
```

---

## 📊 Phase 2 : Préparation des données

### 2.1 Analyser le CSV existant

```powershell
# Aller dans le répertoire des données
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Test_python_pipeline\Scratch_Pipeline"

# Examiner les premières lignes
Get-Content extract_dwh_20241120.csv | Select-Object -First 5
```

### 2.2 Créer un script d'analyse

Créer `Code\test_utils\analyze_csv.py` :

```python
"""Analyse du CSV d'extraction pour comprendre la structure."""
import pandas as pd
from pathlib import Path

csv_path = Path(r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Test_python_pipeline\Scratch_Pipeline\extract_dwh_20241120.csv")

print("🔍 Analyse du fichier CSV...")
print(f"Taille : {csv_path.stat().st_size / (1024**2):.1f} MB")

# Lire un échantillon
df_sample = pd.read_csv(csv_path, nrows=10000, encoding='utf-8', low_memory=False)

print(f"\n📊 Nombre de colonnes : {len(df_sample.columns)}")
print(f"📊 Nombre de lignes (échantillon) : {len(df_sample)}")

print("\n📋 Colonnes trouvées :")
for i, col in enumerate(df_sample.columns, 1):
    print(f"  {i:2}. {col:30} (dtype: {df_sample[col].dtype})")

print("\n🔍 Aperçu des données :")
print(df_sample.head(3))

print("\n📈 Statistiques :")
print(df_sample.describe(include='all'))

# Identifier la colonne de date
date_columns = [col for col in df_sample.columns if 'date' in col.lower() or 'time' in col.lower()]
print(f"\n📅 Colonnes date/time trouvées : {date_columns}")

# Identifier les colonnes critiques
critical_columns = [col for col in df_sample.columns if any(x in col.upper() for x in ['CONN', 'CALL', 'NUMBER', 'ID'])]
print(f"\n🔑 Colonnes critiques identifiées : {critical_columns}")

# Taux de nullité
print("\n❓ Taux de nullité par colonne :")
null_rates = (df_sample.isnull().sum() / len(df_sample) * 100).sort_values(ascending=False)
for col, rate in null_rates.head(10).items():
    print(f"  {col:30} : {rate:5.2f}%")
```

### 2.3 Créer un échantillon de test

Créer `Code\test_utils\create_test_sample.py` :

```python
"""Crée un échantillon de données pour tests rapides."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

csv_path = Path(r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Test_python_pipeline\Scratch_Pipeline\extract_dwh_20241120.csv")
output_dir = Path(r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code\test_data")
output_dir.mkdir(exist_ok=True)

print("🔍 Lecture du CSV complet...")
# Lire tout le fichier (adapter selon la RAM disponible)
df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)

print(f"✅ {len(df)} lignes chargées")

# Identifier la colonne de date
date_col = None
for col in df.columns:
    if 'date' in col.lower():
        date_col = col
        break

if date_col:
    print(f"📅 Colonne date identifiée : {date_col}")
    
    # Convertir en datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Extraire plusieurs jours de données
    dates = sorted(df[date_col].dropna().dt.date.unique())
    print(f"📅 Plage de dates : {dates[0]} à {dates[-1]}")
    
    # Prendre 3 jours consécutifs récents
    test_dates = dates[-3:] if len(dates) >= 3 else dates
    
    for test_date in test_dates:
        df_day = df[df[date_col].dt.date == test_date]
        output_file = output_dir / f"test_data_{test_date.strftime('%Y%m%d')}.csv"
        df_day.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Créé : {output_file.name} ({len(df_day)} lignes)")

else:
    # Si pas de colonne date, prendre un échantillon aléatoire
    df_sample = df.sample(n=min(50000, len(df)))
    output_file = output_dir / "test_data_sample.csv"
    df_sample.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Créé : {output_file.name} ({len(df_sample)} lignes)")

print("\n✅ Échantillons de test créés dans test_data/")
```

---

## 📥 Phase 3 : Import des données

### 3.1 Créer la table Oracle

Créer `Code\test_utils\create_oracle_table.sql` :

```sql
-- Se connecter : sqlplus dwh_cti_test/DwhTest123@localhost:1521/XE

-- Supprimer la table si elle existe
DROP TABLE CDR_EVENTS CASCADE CONSTRAINTS;

-- Créer la table (adapter selon les colonnes réelles)
CREATE TABLE CDR_EVENTS (
    CONN_ID VARCHAR2(50) PRIMARY KEY,
    EVENT_DATE DATE NOT NULL,
    EVENT_HOUR NUMBER(2),
    CALLING_NUMBER VARCHAR2(20),
    CALLED_NUMBER VARCHAR2(20),
    CALL_TYPE VARCHAR2(20),
    DURATION NUMBER(10),
    STATUS VARCHAR2(20),
    NETWORK VARCHAR2(50),
    CELL_ID VARCHAR2(20),
    -- Ajouter d'autres colonnes selon l'analyse du CSV
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer des index pour performance
CREATE INDEX IDX_EVENT_DATE ON CDR_EVENTS(EVENT_DATE);
CREATE INDEX IDX_EVENT_HOUR ON CDR_EVENTS(EVENT_HOUR);

-- Vérifier
DESC CDR_EVENTS;
```

### 3.2 Script d'import Python

Créer `Code\test_utils\import_to_oracle.py` :

```python
"""Import des données CSV vers Oracle."""
import oracledb
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
DSN = "localhost:1521/XE"
USER = "dwh_cti_test"
PASSWORD = "DwhTest123"
TABLE_NAME = "CDR_EVENTS"

# Fichiers à importer
test_data_dir = Path(r"c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code\test_data")
csv_files = list(test_data_dir.glob("test_data_*.csv"))

print(f"🔍 {len(csv_files)} fichiers CSV trouvés")

# Connexion Oracle
print("🔌 Connexion à Oracle...")
conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
cursor = conn.cursor()

total_inserted = 0

for csv_file in csv_files:
    print(f"\n📂 Import de {csv_file.name}...")
    
    # Lire le CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"   📊 {len(df)} lignes à importer")
    
    # Adapter les colonnes selon la structure réelle
    # TODO: Mapper les colonnes du CSV aux colonnes Oracle
    
    # Insertion par lots (batch insert pour performance)
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        # Préparer les données
        data_to_insert = []
        for _, row in batch.iterrows():
            # Adapter selon les colonnes
            data_to_insert.append((
                row.get('CONN_ID', ''),
                row.get('EVENT_DATE', datetime.now()),
                # ... autres colonnes
            ))
        
        # INSERT
        sql = f"""
            INSERT INTO {TABLE_NAME} 
            (CONN_ID, EVENT_DATE, EVENT_HOUR, ...)
            VALUES (:1, :2, :3, ...)
        """
        
        try:
            cursor.executemany(sql, data_to_insert)
            conn.commit()
            total_inserted += len(data_to_insert)
            print(f"   ✅ {i + len(batch)}/{len(df)} lignes importées")
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            conn.rollback()
            break

cursor.close()
conn.close()

print(f"\n✅ Import terminé : {total_inserted} lignes au total")
```

### 3.3 Alternative : SQL*Loader (plus rapide)

Créer `Code\test_utils\load_data.ctl` :

```
LOAD DATA
INFILE 'test_data_20241120.csv'
APPEND INTO TABLE CDR_EVENTS
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
TRAILING NULLCOLS
(
    CONN_ID,
    EVENT_DATE DATE "YYYY-MM-DD",
    EVENT_HOUR,
    CALLING_NUMBER,
    CALLED_NUMBER,
    -- ... autres colonnes
)
```

Exécuter :

```powershell
sqlldr dwh_cti_test/DwhTest123@localhost:1521/XE control=load_data.ctl log=load_data.log
```

---

## ⚙️ Phase 4 : Configuration monitoring

### 4.1 Créer le fichier .env de test

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"

# Créer .env.test
@"
# Configuration TEST - Oracle XE local
DWH_DSN=localhost:1521/XE
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=MonitorTest123
DWH_TABLE_NAME=DWH_CTI_TEST.CDR_EVENTS
"@ | Out-File -FilePath .env.test -Encoding utf8
```

### 4.2 Adapter la config pour tests

Créer `config/config_test.yaml` :

```yaml
# Configuration pour environnement de test
logging:
  log_level: DEBUG  # Plus verbeux pour tests
  log_dir: ./logs_test
  retention_days: 7

execution:
  mode: all
  parallel_execution: false  # Séquentiel pour debug
  timeout_seconds: 300

dashboard:
  export_enabled: true
  export_dir: ./dashboard_data_test

# Seuils plus permissifs pour tests
default_thresholds:
  volumetry:
    min_rows: 1000  # Réduit pour tests
  quality:
    duplicate_tolerance: 0
    null_rate_max_percent: 5.0  # Plus permissif
  distribution:
    hourly_tolerance_percent: 10.0  # Plus permissif
```

### 4.3 Créer un breakpoint de test

Créer `breakpoints/bp_test_local.yaml` :

```yaml
id: bp_test_local
name: "Test Local - Oracle XE"
access: direct

connector:
  type: oracle
  params:
    dsn: ${DWH_DSN}
    user: ${DWH_READONLY_USER}
    password: ${DWH_READONLY_PASSWORD}

data_source:
  table: ${DWH_TABLE_NAME}
  date_column: EVENT_DATE

schedule:
  check_offset_days: 1

checks:
  # Check 1 : Volumétrie minimale (seuil bas pour test)
  - type: min_row_count_check
    params:
      min_lines: 1000
    force_zero_on_failure: true
  
  # Check 2 : Comparaison baseline (7 jours pour test)
  - type: baseline_comparison_check
    params:
      baseline_days: 7
      tolerance_percent: 30.0
  
  # Check 3 : Schéma (colonnes essentielles uniquement)
  - type: schema_conformity_check
    params:
      required_columns:
        - CONN_ID
        - EVENT_DATE
        - EVENT_HOUR
    force_zero_on_failure: true
  
  # Check 4 : Doublons
  - type: duplicate_key_check
    params:
      key_column: CONN_ID
      tolerance: 0
      ignore_blanks: true
  
  # Check 5 : Nullité (colonnes critiques)
  - type: null_rate_check
    params:
      critical_columns:
        - CONN_ID
        - EVENT_DATE
      max_null_rate_percent: 2.0
  
  # Check 6 : Distribution horaire
  - type: hourly_distribution_check
    params:
      hour_column: EVENT_HOUR
      tolerance_percent: 10.0
      exclude_hours: [0, 1, 2, 3, 4]
      baseline_days: 7
```

---

## 🧪 Phase 5 : Tests unitaires

### 5.1 Tester la connexion Oracle

Créer `Code\tests\test_connection.py` :

```python
"""Test de connexion Oracle."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors import OracleConnector
from dotenv import load_dotenv
import os

# Charger .env.test
load_dotenv('.env.test')

dsn = os.getenv('DWH_DSN')
user = os.getenv('DWH_READONLY_USER')
password = os.getenv('DWH_READONLY_PASSWORD')

print("🧪 Test de connexion Oracle")
print(f"DSN: {dsn}")
print(f"User: {user}")

try:
    with OracleConnector(dsn=dsn, user=user, password=password) as conn:
        print("✅ Connexion établie")
        
        # Test query simple
        result = conn.execute_scalar("SELECT COUNT(*) FROM DUAL")
        print(f"✅ Query test: {result}")
        
        # Test table exists
        table_name = os.getenv('DWH_TABLE_NAME')
        count = conn.execute_scalar(f"SELECT COUNT(*) FROM {table_name}")
        print(f"✅ Table {table_name}: {count} lignes")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

print("\n✅ Test de connexion réussi")
```

### 5.2 Tester chaque check individuellement

Créer `Code\tests\test_checks.py` :

```python
"""Tests unitaires des checks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from checks import (
    MinRowCountCheck,
    BaselineComparisonCheck,
    SchemaConformityCheck,
    DuplicateKeyCheck,
    NullRateCheck,
    HourlyDistributionCheck
)

print("🧪 Tests unitaires des checks\n")

# Données de test
df_test = pd.DataFrame({
    'CONN_ID': ['A001', 'A002', 'A003', 'A004', 'A005'],
    'EVENT_DATE': pd.date_range('2024-11-20', periods=5),
    'EVENT_HOUR': [10, 11, 12, 13, 14],
    'CALLING_NUMBER': ['0612345678', '0623456789', None, '0645678901', '0656789012'],
    'DURATION': [120, 150, 180, 90, 200]
})

# Test 1: MinRowCountCheck
print("1️⃣ Test MinRowCountCheck")
check1 = MinRowCountCheck(params={'min_lines': 3})
result1 = check1.run(df_test)
print(f"   Status: {result1.status.value}, Score: {result1.score}/10")
print(f"   Message: {result1.message}\n")

# Test 2: SchemaConformityCheck
print("2️⃣ Test SchemaConformityCheck")
check2 = SchemaConformityCheck(params={'required_columns': ['CONN_ID', 'EVENT_DATE']})
result2 = check2.run(df_test)
print(f"   Status: {result2.status.value}, Score: {result2.score}/10")
print(f"   Message: {result2.message}\n")

# Test 3: DuplicateKeyCheck
print("3️⃣ Test DuplicateKeyCheck")
check3 = DuplicateKeyCheck(params={'key_column': 'CONN_ID', 'tolerance': 0})
result3 = check3.run(df_test)
print(f"   Status: {result3.status.value}, Score: {result3.score}/10")
print(f"   Message: {result3.message}\n")

# Test 4: NullRateCheck
print("4️⃣ Test NullRateCheck")
check4 = NullRateCheck(params={'critical_columns': ['CALLING_NUMBER'], 'max_null_rate_percent': 10.0})
result4 = check4.run(df_test)
print(f"   Status: {result4.status.value}, Score: {result4.score}/10")
print(f"   Message: {result4.message}\n")

# Test 5: HourlyDistributionCheck
print("5️⃣ Test HourlyDistributionCheck")
df_test['EVENT_HOUR'] = df_test['EVENT_HOUR']
baseline = {str(h): 1 for h in range(24)}  # Baseline uniforme
check5 = HourlyDistributionCheck(params={'hour_column': 'EVENT_HOUR', 'tolerance_percent': 20.0})
result5 = check5.run({'data': df_test, 'baseline': baseline})
print(f"   Status: {result5.status.value}, Score: {result5.score}/10")
print(f"   Message: {result5.message}\n")

print("✅ Tous les tests unitaires terminés")
```

---

## 🔄 Phase 6 : Tests d'intégration

### 6.1 Test avec vraies données

```powershell
# Charger le .env.test
$env:DWH_DSN = "localhost:1521/XE"
$env:DWH_READONLY_USER = "monitoring_user"
$env:DWH_READONLY_PASSWORD = "MonitorTest123"
$env:DWH_TABLE_NAME = "DWH_CTI_TEST.CDR_EVENTS"

# Lancer le monitoring sur le breakpoint de test
python main.py --breakpoint bp_test_local --config config/config_test.yaml
```

### 6.2 Test sur plusieurs dates

```powershell
# Tester J-1
python main.py --breakpoint bp_test_local --date (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')

# Tester J-2
python main.py --breakpoint bp_test_local --date (Get-Date).AddDays(-2).ToString('yyyy-MM-dd')

# Tester J-3
python main.py --breakpoint bp_test_local --date (Get-Date).AddDays(-3).ToString('yyyy-MM-dd')
```

### 6.3 Analyser les résultats

```powershell
# Voir les logs
Get-Content logs_test\monitoring_*.log | Select-Object -Last 50

# Voir le dernier rapport
Get-ChildItem logs_test\text\batch_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

# Voir le JSON dashboard
Get-Content dashboard_data_test\latest.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## ✅ Phase 7 : Validation finale

### 7.1 Checklist de validation

Créer `Code\tests\validation_checklist.md` :

```markdown
# ✅ Checklist de validation

## Connexion
- [ ] Connexion Oracle réussie
- [ ] Query SELECT fonctionne
- [ ] Sécurité read-only respectée (refus UPDATE/DELETE)

## Checks individuels
- [ ] MinRowCountCheck : statut correct
- [ ] BaselineComparisonCheck : calcul baseline OK
- [ ] SchemaConformityCheck : détection colonnes manquantes
- [ ] DuplicateKeyCheck : détection doublons
- [ ] NullRateCheck : calcul taux nullité
- [ ] HourlyDistributionCheck : comparaison distribution

## Scoring
- [ ] Score individuel (0-10) correct
- [ ] Score agrégé (moyenne) correct
- [ ] force_zero_on_failure fonctionne
- [ ] Statut (Normal/Dégradé/Critique) correct

## Logs et exports
- [ ] Logs applicatifs créés
- [ ] JSON exporté (logs_test/json/)
- [ ] TXT exporté (logs_test/text/)
- [ ] Dashboard JSON créé (dashboard_data_test/latest.json)

## Edge cases
- [ ] Table vide (0 lignes) géré
- [ ] Colonnes manquantes détectées
- [ ] Doublons détectés
- [ ] Nullité excessive détectée
- [ ] Distribution anormale détectée

## Performance
- [ ] Temps d'exécution < 1 minute (pour ~50k lignes)
- [ ] Mémoire stable (pas de fuite)
```

### 7.2 Script de validation automatique

Créer `Code\tests\run_validation.py` :

```python
"""Script de validation complète."""
import subprocess
import json
from pathlib import Path
from datetime import datetime

print("="*60)
print("🧪 VALIDATION COMPLÈTE DU SYSTÈME DE MONITORING")
print("="*60)

results = {
    "timestamp": datetime.now().isoformat(),
    "tests": []
}

# Test 1: Environnement
print("\n1️⃣ Vérification environnement...")
result = subprocess.run(["python", "check_env.py"], capture_output=True, text=True)
test1 = {
    "name": "Environnement",
    "passed": result.returncode == 0,
    "output": result.stdout
}
results["tests"].append(test1)
print("   ✅ OK" if test1["passed"] else "   ❌ ÉCHEC")

# Test 2: Connexion Oracle
print("\n2️⃣ Test connexion Oracle...")
result = subprocess.run(["python", "tests/test_connection.py"], capture_output=True, text=True)
test2 = {
    "name": "Connexion Oracle",
    "passed": result.returncode == 0,
    "output": result.stdout
}
results["tests"].append(test2)
print("   ✅ OK" if test2["passed"] else "   ❌ ÉCHEC")

# Test 3: Checks unitaires
print("\n3️⃣ Tests unitaires checks...")
result = subprocess.run(["python", "tests/test_checks.py"], capture_output=True, text=True)
test3 = {
    "name": "Checks unitaires",
    "passed": result.returncode == 0,
    "output": result.stdout
}
results["tests"].append(test3)
print("   ✅ OK" if test3["passed"] else "   ❌ ÉCHEC")

# Test 4: Intégration (run complet)
print("\n4️⃣ Test intégration (run complet)...")
result = subprocess.run([
    "python", "main.py",
    "--breakpoint", "bp_test_local",
    "--config", "config/config_test.yaml"
], capture_output=True, text=True)
test4 = {
    "name": "Run complet",
    "passed": result.returncode == 0,
    "output": result.stdout
}
results["tests"].append(test4)
print("   ✅ OK" if test4["passed"] else "   ❌ ÉCHEC")

# Résumé
print("\n" + "="*60)
print("📊 RÉSUMÉ")
print("="*60)
total = len(results["tests"])
passed = sum(1 for t in results["tests"] if t["passed"])
print(f"Tests réussis : {passed}/{total}")

for test in results["tests"]:
    status = "✅" if test["passed"] else "❌"
    print(f"{status} {test['name']}")

# Sauvegarder rapport
report_file = Path("validation_report.json")
with open(report_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n📄 Rapport complet : {report_file}")

if passed == total:
    print("\n🎉 VALIDATION RÉUSSIE !")
    exit(0)
else:
    print("\n❌ VALIDATION ÉCHOUÉE")
    exit(1)
```

---

## 📊 Livrables attendus

À l'issue des tests, vous aurez :

1. ✅ **Base Oracle XE opérationnelle** avec données réelles
2. ✅ **Données importées** (structure validée)
3. ✅ **Tous les checks testés** individuellement et en intégration
4. ✅ **Rapports de test** (JSON + TXT)
5. ✅ **Rapport de validation** complet
6. ✅ **Documentation des écarts** (si bugs trouvés)

---

## 🐛 Dépannage prévu

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| Import Oracle échoue | Structure CSV ≠ table | Adapter script import |
| Check échoue toujours | Seuils trop stricts | Ajuster dans bp_test_local.yaml |
| Pas de baseline | < 7 jours de données | Réduire baseline_days |
| Performance lente | Trop de données | Limiter avec WHERE date |
| Connexion refuse | Firewall/port | Vérifier 1521 ouvert |

---

## 📝 Prochaines étapes après validation

1. 🐛 Corriger les bugs identifiés
2. 📊 Affiner les seuils selon données réelles
3. 🚀 Déployer sur Oracle de production (avec credentials réels)
4. 📈 Implémenter le dashboard React
5. ⏰ Automatiser l'exécution quotidienne

---

**Prêt à commencer ? Démarrez par la Phase 1 !** 🚀
