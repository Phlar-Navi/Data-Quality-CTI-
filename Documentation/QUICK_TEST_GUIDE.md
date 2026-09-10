# ⚡ Guide de test rapide - Une page

## 🎯 Objectif
Tester le système de monitoring avec Oracle XE local + données CSV réelles

---

## 📋 Prérequis (5 min)

```powershell
# 1. Vérifier Python
python --version  # ≥3.8

# 2. Installer dépendances
pip install -r requirements.txt

# 3. Vérifier Docker (recommandé) ou préparer Oracle XE natif
docker --version
```

---

## 🚀 Lancement rapide (30 min)

### Étape 1 : Lancer Oracle XE (Docker)

```powershell
# Télécharger et lancer
docker run -d `
  --name oracle-xe `
  -p 1521:1521 `
  -e ORACLE_PWD=OracleTest123 `
  container-registry.oracle.com/database/express:latest

# Attendre 2-3 minutes
docker logs -f oracle-xe
# Attendre "DATABASE IS READY TO USE!"
```

### Étape 2 : Créer les utilisateurs

```powershell
# Connexion à Oracle
docker exec -it oracle-xe sqlplus system/OracleTest123@XE
```

```sql
-- Dans SQL*Plus
CREATE USER dwh_cti_test IDENTIFIED BY DwhTest123;
GRANT CONNECT, RESOURCE TO dwh_cti_test;
GRANT UNLIMITED TABLESPACE TO dwh_cti_test;

CREATE USER monitoring_user IDENTIFIED BY MonitorTest123;
GRANT CONNECT TO monitoring_user;

EXIT;
```

### Étape 3 : Analyser les données CSV

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"

# Analyser le CSV
python test_utils\analyze_csv.py
```

**Action requise** : Noter les colonnes identifiées (surtout date, ID, critiques)

### Étape 4 : Créer la table Oracle

Créer `test_utils\create_table.sql` basé sur l'analyse :

```sql
-- Adapter selon colonnes trouvées
CREATE TABLE dwh_cti_test.CDR_EVENTS (
    CONN_ID VARCHAR2(50) PRIMARY KEY,
    EVENT_DATE DATE NOT NULL,
    EVENT_HOUR NUMBER(2),
    -- ... autres colonnes selon analyse
);

GRANT SELECT ON dwh_cti_test.CDR_EVENTS TO monitoring_user;

CREATE INDEX IDX_EVENT_DATE ON dwh_cti_test.CDR_EVENTS(EVENT_DATE);
```

Exécuter :

```powershell
docker exec -i oracle-xe sqlplus dwh_cti_test/DwhTest123@XE < test_utils\create_table.sql
```

### Étape 5 : Importer les données

**Option simple** : Créer un échantillon puis importer manuellement via pandas :

```powershell
python test_utils\create_test_sample.py
# Puis adapter test_utils\import_to_oracle.py selon structure
python test_utils\import_to_oracle.py
```

### Étape 6 : Configurer l'environnement de test

```powershell
# Créer .env.test
@"
DWH_DSN=localhost:1521/XE
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=MonitorTest123
DWH_TABLE_NAME=DWH_CTI_TEST.CDR_EVENTS
"@ | Out-File -FilePath .env.test -Encoding utf8

# Copier les variables
Get-Content .env.test | ForEach-Object {
    if ($_ -match '^(\w+)=(.+)$') {
        Set-Item -Path "env:$($matches[1])" -Value $matches[2]
    }
}
```

### Étape 7 : Premier test

```powershell
# Test connexion
python tests\test_connection.py

# Test checks unitaires
python tests\test_checks.py

# Test run complet
python main.py --breakpoint bp_test_local --config config\config_test.yaml
```

---

## ✅ Vérification des résultats

```powershell
# 1. Voir les logs
Get-Content logs_test\monitoring_*.log | Select-Object -Last 30

# 2. Voir le rapport texte
Get-ChildItem logs_test\text\batch_*.txt | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    Get-Content

# 3. Voir le JSON dashboard
Get-Content dashboard_data_test\latest.json | ConvertFrom-Json
```

---

## 📊 Résultats attendus

| Check | Attendu | Si échec |
|-------|---------|----------|
| MinRowCount | ✅ Normal | Vérifier `min_lines` dans bp_test_local.yaml |
| Baseline | ⚠️ Dégradé si <7j données | Réduire `baseline_days` |
| Schema | ✅ Normal | Ajouter colonnes manquantes dans table |
| Duplicate | ✅ Normal | Vérifier unicité CONN_ID |
| NullRate | ✅ Normal | Ajuster `max_null_rate_percent` |
| HourlyDistrib | ✅ Normal | Ajuster `tolerance_percent` |

**Score global attendu** : **7-10/10**

---

## 🐛 Dépannage express

| Problème | Solution rapide |
|----------|----------------|
| Docker ne démarre pas | `docker start oracle-xe` |
| Connexion refusée | Attendre 2-3 min après docker run |
| Import échoue | Vérifier structure table = structure CSV |
| Tous checks échouent | Vérifier données importées : `SELECT COUNT(*) FROM ...` |
| Baseline vide | Importer 3+ jours de données ou réduire baseline_days |

---

## 📞 Commandes utiles

```powershell
# Vérifier Oracle
docker ps | Select-String oracle
docker exec -it oracle-xe sqlplus monitoring_user/MonitorTest123@XE

# Compter les lignes importées
# Dans SQL*Plus: SELECT COUNT(*) FROM dwh_cti_test.CDR_EVENTS;

# Re-run monitoring avec date spécifique
python main.py --breakpoint bp_test_local --date 2024-11-20

# Mode DEBUG
# Éditer config\config_test.yaml : log_level: DEBUG
```

---

## 📚 Documentation complète

- **TESTING_PLAN.md** : Plan détaillé en 7 phases (4h)
- **TESTING_SUMMARY.md** : Vue d'ensemble + checklist
- **README.md** : Documentation système complète
- **COMMANDS.md** : Référence commandes PowerShell

---

## 🎯 Checklist succès

- [ ] Oracle XE lancé et accessible
- [ ] Table CDR_EVENTS créée avec bonnes colonnes
- [ ] Données importées (vérifier COUNT)
- [ ] test_connection.py : ✅
- [ ] test_checks.py : ✅ (tous les checks)
- [ ] main.py : ✅ (score ≥7/10)
- [ ] Logs créés (JSON + TXT)
- [ ] Dashboard JSON valide

---

## ⏱️ Timeline

| Étape | Durée | Total |
|-------|-------|-------|
| Oracle XE | 5 min | 5 min |
| Utilisateurs | 2 min | 7 min |
| Analyse CSV | 3 min | 10 min |
| Création table | 5 min | 15 min |
| Import données | 10 min | 25 min |
| Config env | 2 min | 27 min |
| Tests | 3 min | **30 min** |

---

**Prêt en 30 minutes ! Let's go ! 🚀**

Pour plus de détails → **TESTING_PLAN.md**
