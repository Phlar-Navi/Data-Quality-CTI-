# 📚 Documentation Complète - Monitoring CTI

**Version** : 1.1.0  
**Date** : 2026-09-12  
**Équipe** : OCM Data Engineering

---

# Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du système](#2-architecture-du-système)
3. [Flux d'exécution](#3-flux-dexécution)
4. [Modules détaillés](#4-modules-détaillés)
5. [Configuration](#5-configuration)
6. [Checks disponibles](#6-checks-disponibles)
7. [Système de logging](#7-système-de-logging)
8. [Système d'emails](#8-système-demails)
9. [Base de données SQLite](#9-base-de-données-sqlite)
10. [Utilisation](#10-utilisation)
11. [Troubleshooting](#11-troubleshooting)
12. [Extensions futures](#12-extensions-futures)

---

# 1. Vue d'ensemble

## 🎯 Objectif

Le système de **Monitoring CTI** est un outil automatisé de surveillance des données téléphoniques (Call Center) stockées dans Oracle Database. Il vérifie quotidiennement la qualité, l'intégrité et la conformité des données, détecte les anomalies et notifie les équipes en cas de problème.

## 🔑 Fonctionnalités principales

- ✅ **Surveillance multi-dimensionnelle** : Schéma, volumétrie, doublons, valeurs nulles, outliers
- ✅ **Historisation complète** : Base SQLite avec 365 jours de rétention
- ✅ **Notifications intelligentes** : Emails conditionnels (alertes + rapports)
- ✅ **Détection d'anomalies** : Outliers statistiques (IQR, Z-Score)
- ✅ **Exports JSON** : Pour dashboard et intégration externe
- ✅ **Configuration flexible** : YAML pour tous les paramètres

## 📊 Métriques clés

| Métrique | Description |
|----------|-------------|
| **Score global** | Note de 0 à 10 calculée sur tous les checks |
| **Row count** | Nombre de lignes analysées |
| **Duplicate count** | Nombre de doublons détectés |
| **Null rate** | Taux de valeurs nulles sur colonnes critiques |
| **Outlier percent** | Pourcentage d'outliers détectés |
| **Execution time** | Temps d'exécution du monitoring |

---

# 2. Architecture du système

## 🏗️ Structure des fichiers

```
Code/
│
├── main.py                          # Point d'entrée principal
│   └─ Orchestration générale (setup, run, export, notify)
│
├── config/                          # Configuration
│   ├── config.yaml                  # Config globale (thresholds, email, db)
│   ├── .env                         # Credentials (NON COMMITÉ)
│   └── .env.example                 # Template credentials
│
├── breakpoints/                     # Définitions des checks
│   ├── bp9_dwh_oracle.yaml          # Breakpoint production DWH Oracle
│   └── bp_*.yaml                    # Autres breakpoints
│
├── checks/                          # Modules de vérification
│   ├── __init__.py                  # Exports des checks
│   ├── data_presence_check.py       # Vérif présence données
│   ├── data_quality_check.py        # Vérif qualité (schema, volumétrie)
│   ├── data_integrity_check.py      # Vérif intégrité (doublons, nulls)
│   ├── baseline_check.py            # Comparaison avec historique
│   ├── hourly_distribution_check.py # Répartition horaire
│   └── outlier.py                   # Détection outliers (NEW v1.1)
│
├── utils/                           # Utilitaires
│   ├── config_loader.py             # Chargement config YAML + .env
│   ├── db_connector.py              # Connexion Oracle Database
│   ├── breakpoint_runner.py         # Exécution d'un breakpoint
│   ├── result_logger.py             # Logging texte/JSON
│   ├── sqlite_logger.py             # Logging SQLite (NEW v1.1)
│   ├── email_sender.py              # Envoi emails (NEW v1.1)
│   └── analyze_baseline.py          # Analyse baseline pour seuils
│
├── connectors/                      # Connecteurs DB
│   └── oracle_connector.py          # Implémentation Oracle
│
├── data/                            # Données générées (IGNORÉ GIT)
│   └── monitoring.db                # Base SQLite historique
│
├── logs/                            # Logs générés (IGNORÉ GIT)
│   ├── text/                        # Logs texte
│   └── json/                        # Logs JSON
│
├── dashboard_data/                  # Exports JSON (IGNORÉ GIT)
│   ├── latest.json                  # Dernier run
│   └── run_YYYYMMDD_HHMMSS.json     # Historique runs
│
├── .gitignore                       # Fichiers exclus de Git
├── requirements.txt                 # Dépendances Python
├── README.md                        # Guide utilisateur
├── CHANGELOG.md                     # Historique versions
└── DOCUMENTATION_COMPLETE.md        # Ce fichier
```

## 🔄 Diagramme de flux général

```
┌─────────────────────────────────────────────────────────────────┐
│                        MAIN.PY (Orchestrateur)                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  1. SETUP                                 │
         │  - Charger config.yaml + .env             │
         │  - Initialiser logging                    │
         │  - Parser arguments CLI (--date, --bp)    │
         └───────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  2. LOAD BREAKPOINTS                      │
         │  - Charger breakpoints/*.yaml             │
         │  - Filtrer selon --breakpoint (optionnel) │
         └───────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  3. RUN BREAKPOINTS (Boucle)              │
         │  ┌─────────────────────────────────────┐  │
         │  │ Pour chaque breakpoint :            │  │
         │  │ - Connexion Oracle DB               │  │
         │  │ - Extraction données (query)        │  │
         │  │ - Exécution de tous les checks      │  │
         │  │ - Calcul du score (/10)             │  │
         │  └─────────────────────────────────────┘  │
         └───────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  4. EXPORT RESULTS                        │
         │  - JSON (dashboard_data/)                 │
         │  - Texte + JSON (logs/)                   │
         └───────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  5. SQLITE LOGGING (NEW v1.1)             │
         │  - Connexion à monitoring.db              │
         │  - Insert run + breakpoints + checks      │
         │  - Extract et store métriques             │
         └───────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────┐
         │  6. SEND NOTIFICATIONS (NEW v1.1)         │
         │  - Calcul scores moyens                   │
         │  - Envoi alertes (si score < 8)           │
         │  - Envoi rapport quotidien (si score < 10)│
         └───────────────────────────────────────────┘
                                 │
                                 ▼
                             [FIN]
```

---

# 3. Flux d'exécution

## 🚀 Séquence détaillée d'un run

### **Étape 1 : Initialisation (main.py → setup_logging)**

```python
# 1.1 Charger la configuration globale
config = ConfigLoader.load_config("config/config.yaml")

# 1.2 Charger les variables d'environnement (.env)
load_dotenv("config/.env")

# 1.3 Initialiser le logger
logger = setup_logging(config)

# 1.4 Parser les arguments CLI
parser = argparse.ArgumentParser()
parser.add_argument("--date", help="Date cible (YYYY-MM-DD)")
parser.add_argument("--breakpoint", help="ID d'un breakpoint spécifique")
args = parser.parse_args()
```

**Résultat** :
- ✅ Configuration chargée en mémoire
- ✅ Credentials disponibles (DWH_DSN, EMAIL_SENDER, etc.)
- ✅ Logger prêt à enregistrer
- ✅ Date cible déterminée (argument ou aujourd'hui)

---

### **Étape 2 : Chargement des breakpoints (main.py → load_breakpoints)**

```python
# 2.1 Lister tous les fichiers breakpoints/*.yaml
breakpoint_files = glob.glob("breakpoints/bp*.yaml")

# 2.2 Charger chaque breakpoint
for bp_file in breakpoint_files:
    bp_config = config_loader.load_breakpoint(bp_file)
    
    # 2.3 Filtrer selon --breakpoint (si spécifié)
    if args.breakpoint and bp_config["id"] != args.breakpoint:
        continue
    
    breakpoints.append(bp_config)
```

**Résultat** :
- ✅ Liste des breakpoints à exécuter
- ✅ Chaque breakpoint contient : id, nom, query, checks, thresholds

---

### **Étape 3 : Exécution d'un breakpoint (main.py → run_breakpoint)**

#### **3.1 Connexion à la base Oracle**

```python
# Créer le connecteur Oracle
connector = OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
)

# Tester la connexion
if not connector.test_connection():
    raise ConnectionError("Connexion Oracle impossible")
```

#### **3.2 Extraction des données**

```python
# Exécuter la requête SQL définie dans le breakpoint
query = bp_config["query"]
query = query.replace("{TARGET_DATE}", target_date)
query = query.replace("{TABLE_NAME}", os.getenv("DWH_TABLE_NAME"))

# Fetch data as pandas DataFrame
data = connector.fetch_dataframe(query)

logger.info(f"[DATA] {len(data)} lignes extraites")
```

#### **3.3 Exécution des checks**

```python
# Initialiser le runner
runner = BreakpointRunner(bp_config, connector, logger)

# Exécuter tous les checks définis dans le breakpoint YAML
result = runner.run(target_date=target_date)

# result contient :
# - breakpoint_id
# - breakpoint_name
# - status: "success" / "warning" / "failure"
# - score: 0-10
# - checks: [check1_result, check2_result, ...]
# - execution_time
# - target_date
```

**Liste des checks exécutés** (selon bp9_dwh_oracle.yaml) :

1. **schema_conformity_check** : Vérifier colonnes obligatoires
2. **min_row_count_check** : Vérifier volumétrie minimale (>= 10000)
3. **baseline_comparison_check** : Comparer avec moyenne historique (±20%)
4. **duplicate_key_check** : Détecter doublons sur CONNID (<1%)
5. **null_rate_check** : Vérifier taux de nullité (<2%)
6. **hourly_distribution_check** : Vérifier distribution horaire (±5%)
7. **outlier_detection_check** : Détecter outliers (IQR, Z-Score) (<5%)

#### **3.4 Calcul du score**

```python
# Score = (nombre de checks réussis / nombre total de checks) * 10
success_count = sum(1 for check in checks if check["status"] == "success")
total_checks = len(checks)
score = (success_count / total_checks) * 10

# Exemple : 5 checks réussis / 7 total = 7.14/10 → arrondi à 7/10
```

**Résultat** :
- ✅ BreakpointResult avec tous les détails
- ✅ Score calculé
- ✅ Status : "success" (≥8) / "warning" (5-7) / "failure" (<5)

---

### **Étape 4 : Export des résultats (main.py → export_results)**

#### **4.1 Export JSON pour dashboard**

```python
# Fichier horodaté
output_file = f"dashboard_data/run_{run_id}.json"

# Format JSON
{
    "run_id": "20260912_115206",
    "date": "2026-09-12",
    "target_date": "2026-06-22",
    "breakpoints": [
        {
            "id": "bp9_dwh_oracle",
            "name": "Datawarehouse Oracle",
            "status": "warning",
            "score": 7,
            "checks": [
                {
                    "name": "schema_conformity_check",
                    "status": "success",
                    "message": "Toutes les colonnes présentes",
                    "details": {...}
                },
                ...
            ]
        }
    ]
}

# Copier aussi dans latest.json (pour dashboard)
shutil.copy(output_file, "dashboard_data/latest.json")
```

#### **4.2 Export logs texte + JSON**

```python
# Logs texte structurés
logs/text/batch_20260912_115206.txt

# Logs JSON complets
logs/json/batch_20260912_115206.json
```

---

### **Étape 5 : Logging SQLite (main.py → après export_results)**

#### **5.1 Connexion à la base SQLite**

```python
from utils.sqlite_logger import SQLiteLogger

# Initialiser le logger SQLite
db_path = config.get("database", {}).get("path", "./data/monitoring.db")
sqlite_logger = SQLiteLogger(db_path)
```

#### **5.2 Insertion des données**

```python
# 5.2.1 Insérer le run global
run_data = {
    "run_id": run_id,
    "run_date": datetime.now(),
    "target_date": target_date,
    "total_breakpoints": len(results),
    "average_score": calculate_average_score(results),
    "status": determine_global_status(results)
}
sqlite_logger.insert_run(run_data)

# 5.2.2 Insérer chaque breakpoint
for result in results:
    bp_data = {
        "run_id": run_id,
        "breakpoint_id": result.breakpoint_id,
        "breakpoint_name": result.breakpoint_name,
        "status": result.status,
        "score": result.score,
        "execution_time": result.execution_time,
        "target_date": result.target_date,
        "checks_passed": count_passed_checks(result.checks),
        "checks_warning": count_warning_checks(result.checks),
        "checks_failed": count_failed_checks(result.checks)
    }
    sqlite_logger.insert_breakpoint_result(bp_data)
    
    # 5.2.3 Insérer chaque check
    for check in result.checks:
        check_data = {
            "run_id": run_id,
            "breakpoint_id": result.breakpoint_id,
            "check_name": check["name"],
            "check_type": check["type"],
            "status": check["status"],
            "message": check["message"],
            "details": json.dumps(check.get("details", {}))
        }
        sqlite_logger.insert_check_result(check_data)
        
        # 5.2.4 Extraire et insérer les métriques clés
        metrics = extract_metrics(check)
        sqlite_logger.insert_metrics(run_id, result.breakpoint_id, metrics)

# Fermer la connexion
sqlite_logger.close()
```

**Métriques extraites** :
- `row_count` : Nombre de lignes analysées
- `duplicate_count` : Nombre de doublons
- `null_rate` : Taux de valeurs nulles
- `outlier_count` : Nombre d'outliers
- `outlier_percent` : Pourcentage d'outliers
- `baseline_deviation` : Écart à la baseline (%)

**Résultat** :
- ✅ Toutes les données stockées dans SQLite
- ✅ Rétention de 365 jours automatique
- ✅ Indexes pour requêtes rapides

---

### **Étape 6 : Envoi des notifications (main.py → send_notifications)**

#### **6.1 Calcul des scores et détermination des alertes**

```python
from utils.email_sender import EmailSender

# Initialiser l'email sender
email_config = config.get("notifications", {}).get("email", {})
email_sender = EmailSender(
    smtp_server=email_config["smtp_server"],
    smtp_port=email_config["smtp_port"],
    sender=email_config["sender"],
    sender_password=email_config["sender_password"]
)

# Calculer scores
scores = [r.score for r in results]
avg_score = sum(scores) / len(scores)

# Déterminer les alertes à envoyer
alerts_to_send = []
for result in results:
    if result.score < 5:
        alerts_to_send.append(("critical", result))
    elif result.score < 8:
        alerts_to_send.append(("warning", result))
```

#### **6.2 Envoi des alertes individuelles**

```python
# Envoyer les alertes pour chaque breakpoint problématique
for alert_type, result in alerts_to_send:
    recipients = email_config["recipients"]["alerts"]
    
    if alert_type == "critical":
        email_sender.send_alert(
            breakpoint_name=result.breakpoint_name,
            score=result.score,
            checks=result.checks,
            severity="critical",
            recipients=recipients
        )
    elif alert_type == "warning":
        email_sender.send_alert(
            breakpoint_name=result.breakpoint_name,
            score=result.score,
            checks=result.checks,
            severity="warning",
            recipients=recipients
        )
    
    logger.info(f"[EMAIL] Alerte {alert_type} envoyée pour {result.breakpoint_name}")
```

#### **6.3 Envoi du rapport quotidien (conditionnel)**

```python
# Configuration de l'envoi conditionnel
send_daily_report = email_config.get("send_daily_report", True)
min_score_threshold = email_config.get("daily_report_min_score", 10)
send_on_failure_only = email_config.get("send_on_failure_only", True)

# Déterminer si on doit envoyer le rapport
should_send = False

if send_daily_report:
    # Envoyer si au moins un breakpoint a un score < threshold
    if any(score < min_score_threshold for score in scores):
        should_send = True
        reason = f"au moins un breakpoint avec score < {min_score_threshold}"
    elif not send_on_failure_only:
        # Envoyer quand même si envoi systématique activé
        should_send = True
        reason = "envoi systématique activé"
    else:
        logger.info(f"[EMAIL] Rapport non envoyé : tous les breakpoints OK (score moyen: {avg_score:.1f}/10)")

# Envoyer le rapport si nécessaire
if should_send:
    recipients = email_config["recipients"]["reports"]
    
    email_sender.send_daily_report(
        results=[r.__dict__ for r in results],
        date=target_date,
        recipients=recipients
    )
    
    logger.info(f"[EMAIL] Rapport quotidien envoyé ({reason})")
```

**Format du rapport quotidien** :
- 📊 **En-tête** : Date, stats globales (nb breakpoints, score moyen)
- 📈 **Compteurs** : OK / Warnings / Critiques
- 📋 **Détails par breakpoint** :
  - Nom + Score
  - Résumé des checks (X réussi(s), Y échoué(s))
  - **Grille visuelle** des checks avec statuts (✓/✗)
  - **Détails des problèmes** : Messages d'erreur pour checks échoués uniquement

**Résultat** :
- ✅ Alertes envoyées aux destinataires (alerts)
- ✅ Rapport quotidien envoyé (si nécessaire) aux destinataires (reports)
- ✅ Throttling appliqué pour éviter spam

---

# 4. Modules détaillés

## 📦 4.1 main.py (Orchestrateur)

**Rôle** : Point d'entrée, orchestration générale

**Fonctions principales** :

### `setup_logging(config: dict) -> logging.Logger`
```python
"""
Configure le système de logging avec :
- Niveau de log (INFO, DEBUG, WARNING)
- Format des messages
- Handlers (console + fichier)
"""
```

### `load_breakpoints(config: dict, config_loader: ConfigLoader) -> List[dict]`
```python
"""
Charge tous les breakpoints depuis breakpoints/*.yaml
Applique les filtres CLI (--breakpoint)
Retourne une liste de configurations de breakpoints
"""
```

### `run_breakpoint(bp_config: dict, target_date: str, logger: Logger) -> BreakpointResult`
```python
"""
Exécute un breakpoint complet :
1. Connexion DB
2. Extraction données
3. Exécution de tous les checks
4. Calcul du score
5. Détermination du status
"""
```

### `export_results(results: List[BreakpointResult], config: dict, logger: Logger)`
```python
"""
Exporte les résultats dans plusieurs formats :
- JSON horodaté (dashboard_data/run_YYYYMMDD_HHMMSS.json)
- JSON latest (dashboard_data/latest.json)
- Logs texte (logs/text/batch_YYYYMMDD_HHMMSS.txt)
- Logs JSON (logs/json/batch_YYYYMMDD_HHMMSS.json)
"""
```

### `send_notifications(results: List[BreakpointResult], config: dict, logger: Logger)`
```python
"""
Gère l'envoi des notifications :
1. Calcul des scores moyens
2. Détermination des alertes (critical, warning)
3. Envoi des alertes par email
4. Envoi du rapport quotidien (conditionnel)
"""
```

### `main()`
```python
"""
Fonction principale :
1. Setup (logging, config, args)
2. Load breakpoints
3. Run breakpoints (boucle)
4. Export results
5. SQLite logging
6. Send notifications
"""
```

---

## 📦 4.2 utils/config_loader.py

**Rôle** : Chargement de la configuration YAML + .env

**Classe principale** : `ConfigLoader`

```python
class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> dict:
        """Charge config.yaml et résout les références ${VAR}"""
        
    @staticmethod
    def load_breakpoint(bp_path: str) -> dict:
        """Charge un fichier breakpoint/*.yaml"""
        
    @staticmethod
    def resolve_env_vars(config: dict) -> dict:
        """Remplace ${VAR} par os.getenv("VAR")"""
```

**Exemple** :
```yaml
# config.yaml
email:
  sender: ${EMAIL_SENDER}  # Remplacé par os.getenv("EMAIL_SENDER")
```

---

## 📦 4.3 utils/db_connector.py + connectors/oracle_connector.py

**Rôle** : Connexion à Oracle Database

**Classe principale** : `OracleConnector`

```python
class OracleConnector:
    def __init__(self, dsn: str, user: str, password: str):
        """Initialise la connexion Oracle"""
        
    def test_connection(self) -> bool:
        """Teste la connexion"""
        
    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """Exécute une requête SQL et retourne un DataFrame pandas"""
        
    def close(self):
        """Ferme la connexion"""
```

**Dépendance** : `oracledb` (remplace `cx_Oracle`)

---

## 📦 4.4 utils/breakpoint_runner.py

**Rôle** : Exécution d'un breakpoint (extraction + checks)

**Classe principale** : `BreakpointRunner`

```python
class BreakpointRunner:
    def __init__(self, bp_config: dict, connector: DBConnector, logger: Logger):
        """Initialise le runner avec la config du breakpoint"""
        
    def run(self, target_date: str) -> BreakpointResult:
        """
        Exécute le breakpoint complet :
        1. Extraction des données (query)
        2. Exécution de tous les checks
        3. Calcul du score
        4. Agrégation des résultats
        """
        
    def _run_check(self, check_config: dict, data: pd.DataFrame) -> CheckResult:
        """Exécute un check individuel"""
        
    def _calculate_score(self, checks: List[CheckResult]) -> float:
        """Calcule le score global du breakpoint"""
```

---

## 📦 4.5 checks/*.py (Modules de vérification)

### **schema_conformity_check** (data_quality_check.py)

```python
"""
Vérifie que toutes les colonnes obligatoires sont présentes
dans le DataFrame extrait.

Config YAML :
  - type: schema_conformity_check
    expected_columns:
      - CONNID
      - STARTTIME
      - DURATION
      - ...

Résultat :
  - success : Toutes les colonnes présentes
  - failure : Colonnes manquantes
"""
```

### **min_row_count_check** (data_quality_check.py)

```python
"""
Vérifie que le nombre de lignes est supérieur à un minimum.

Config YAML :
  - type: min_row_count_check
    min_rows: 10000

Résultat :
  - success : row_count >= min_rows
  - failure : row_count < min_rows
"""
```

### **baseline_comparison_check** (baseline_check.py)

```python
"""
Compare la volumétrie actuelle avec la moyenne historique.

Config YAML :
  - type: baseline_comparison_check
    baseline_query: "SELECT AVG(row_count) FROM history WHERE date > sysdate-30"
    tolerance: 0.20  # ±20%

Résultat :
  - success : Écart < tolerance
  - warning : tolerance < Écart < tolerance*2
  - failure : Écart > tolerance*2
"""
```

### **duplicate_key_check** (data_integrity_check.py)

```python
"""
Détecte les doublons sur une ou plusieurs colonnes clés.

Config YAML :
  - type: duplicate_key_check
    key_columns:
      - CONNID
    max_duplicate_rate: 0.01  # 1%

Résultat :
  - success : duplicate_rate <= max_duplicate_rate
  - failure : duplicate_rate > max_duplicate_rate
  
Métriques extraites :
  - duplicate_count : Nombre de doublons
  - unique_duplicated_keys : Nombre de clés dupliquées
  - duplicate_rate : Pourcentage
"""
```

### **null_rate_check** (data_integrity_check.py)

```python
"""
Vérifie le taux de valeurs nulles sur colonnes critiques.

Config YAML :
  - type: null_rate_check
    critical_columns:
      - CONNID
      - STARTTIME
    max_null_rate: 0.02  # 2%

Résultat :
  - success : Taux de nullité <= max_null_rate pour toutes les colonnes
  - failure : Au moins une colonne dépasse le seuil
  
Métriques extraites :
  - null_rate_{column} : Taux de nullité par colonne
"""
```

### **hourly_distribution_check** (hourly_distribution_check.py)

```python
"""
Vérifie que la répartition horaire est conforme à la baseline.

Config YAML :
  - type: hourly_distribution_check
    datetime_column: STARTTIME
    baseline_query: "SELECT HOUR, AVG(pct) FROM hourly_baseline GROUP BY HOUR"
    tolerance: 0.05  # ±5%

Résultat :
  - success : Distribution horaire dans la tolérance
  - failure : Heures avec écart > tolerance
"""
```

### **outlier_detection_check** (outlier.py) 🆕 **v1.1**

```python
"""
Détection d'outliers statistiques sur colonnes numériques et catégorielles.

Config YAML :
  - type: outlier_detection_check
    numeric_columns:
      DURATION:
        method: iqr  # ou zscore
        threshold: 1.5  # Multiplicateur IQR ou seuil Z-Score
      RINGDURATION:
        method: zscore
        threshold: 3.0
    categorical_columns:
      ORIGDNIS:
        min_frequency: 3  # Catégories < 3 occurrences = outliers
    critical_outlier_threshold: 0.05  # 5% max

Méthodes disponibles :
  - IQR (Interquartile Range) : Q1 - 1.5*IQR, Q3 + 1.5*IQR
  - Z-Score : |Z| > 3.0 (valeurs à plus de 3 écarts-types)

Résultat :
  - success : outlier_percent <= critical_outlier_threshold
  - warning : critical < outlier_percent <= critical*2
  - failure : outlier_percent > critical*2
  
Métriques extraites :
  - outlier_count : Nombre d'outliers détectés
  - outlier_percent : Pourcentage
  - outlier_columns : Liste des colonnes avec outliers
"""
```

**Exemple de détection IQR** :
```python
# Calcul IQR
Q1 = data[column].quantile(0.25)
Q3 = data[column].quantile(0.75)
IQR = Q3 - Q1

# Seuils
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Outliers
outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)]
```

**Exemple de détection Z-Score** :
```python
from scipy import stats

# Calcul Z-Score
z_scores = np.abs(stats.zscore(data[column]))

# Outliers (|Z| > 3.0)
outliers = data[z_scores > 3.0]
```

---

## 📦 4.6 utils/sqlite_logger.py 🆕 **v1.1**

**Rôle** : Logging des résultats dans SQLite pour historisation

**Classe principale** : `SQLiteLogger`

```python
class SQLiteLogger:
    def __init__(self, db_path: str = "data/monitoring.db"):
        """Initialise la connexion SQLite et crée le schéma si nécessaire"""
        
    def log_full_run(self, run_id: str, results: List[dict], target_date: str):
        """
        Log complet d'un run :
        1. Insert dans runs
        2. Insert dans breakpoint_results (pour chaque BP)
        3. Insert dans check_results (pour chaque check)
        4. Extract et insert metrics_history
        """
        
    def _extract_metrics(self, check: dict) -> Dict[str, Any]:
        """Extrait les métriques clés d'un check pour trending"""
        
    def cleanup_old_data(self, retention_days: int = 365):
        """Supprime les données > retention_days"""
        
    def close(self):
        """Ferme la connexion SQLite"""
```

**Schéma de la base de données** :

### **Table : runs**
```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,                -- Ex: 20260912_115206
    run_date TIMESTAMP NOT NULL,            -- Date d'exécution
    target_date DATE NOT NULL,              -- Date cible analysée
    total_breakpoints INTEGER,              -- Nombre de BP exécutés
    average_score REAL,                     -- Score moyen
    status TEXT,                            -- success/warning/failure
    execution_time REAL,                    -- Durée totale (secondes)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_runs_run_date ON runs(run_date);
CREATE INDEX idx_runs_target_date ON runs(target_date);
```

### **Table : breakpoint_results**
```sql
CREATE TABLE breakpoint_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- FK vers runs
    breakpoint_id TEXT NOT NULL,            -- Ex: bp9_dwh_oracle
    breakpoint_name TEXT NOT NULL,          -- Ex: Datawarehouse Oracle
    status TEXT NOT NULL,                   -- success/warning/failure
    score REAL NOT NULL,                    -- Score /10
    execution_time REAL,                    -- Durée BP (secondes)
    target_date DATE NOT NULL,
    checks_passed INTEGER,                  -- Nb checks OK
    checks_warning INTEGER,                 -- Nb checks warnings
    checks_failed INTEGER,                  -- Nb checks KO
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX idx_bp_results_run_id ON breakpoint_results(run_id);
CREATE INDEX idx_bp_results_bp_id ON breakpoint_results(breakpoint_id);
CREATE INDEX idx_bp_results_target_date ON breakpoint_results(target_date);
```

### **Table : check_results**
```sql
CREATE TABLE check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- FK vers runs
    breakpoint_id TEXT NOT NULL,            -- FK vers breakpoint_results
    check_name TEXT NOT NULL,               -- Ex: duplicate_key_check
    check_type TEXT NOT NULL,               -- Type de check
    status TEXT NOT NULL,                   -- success/warning/failure
    message TEXT,                           -- Message d'erreur/succès
    details TEXT,                           -- JSON avec détails complets
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX idx_check_results_run_id ON check_results(run_id);
CREATE INDEX idx_check_results_bp_id ON check_results(breakpoint_id);
CREATE INDEX idx_check_results_check_name ON check_results(check_name);
```

### **Table : metrics_history**
```sql
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- FK vers runs
    breakpoint_id TEXT NOT NULL,
    target_date DATE NOT NULL,
    metric_name TEXT NOT NULL,              -- Ex: row_count, duplicate_count
    metric_value REAL NOT NULL,             -- Valeur numérique
    metric_unit TEXT,                       -- Ex: rows, percent, count
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX idx_metrics_history_run_id ON metrics_history(run_id);
CREATE INDEX idx_metrics_history_bp_id ON metrics_history(breakpoint_id);
CREATE INDEX idx_metrics_history_metric_name ON metrics_history(metric_name);
CREATE INDEX idx_metrics_history_target_date ON metrics_history(target_date);
```

**Métriques stockées** :
- `row_count` : Nombre de lignes
- `duplicate_count` : Nombre de doublons
- `null_rate` : Taux de valeurs nulles
- `outlier_count` : Nombre d'outliers
- `outlier_percent` : Pourcentage d'outliers
- `baseline_deviation` : Écart à la baseline

**Exemples de requêtes** :

```sql
-- Trending du nombre de lignes sur 30 jours
SELECT target_date, metric_value as row_count
FROM metrics_history
WHERE breakpoint_id = 'bp9_dwh_oracle'
  AND metric_name = 'row_count'
  AND target_date > date('now', '-30 days')
ORDER BY target_date;

-- Moyenne des scores sur 7 jours
SELECT breakpoint_id, AVG(score) as avg_score
FROM breakpoint_results
WHERE target_date > date('now', '-7 days')
GROUP BY breakpoint_id;

-- Derniers runs avec échecs
SELECT run_id, target_date, breakpoint_name, score
FROM breakpoint_results
WHERE status IN ('warning', 'failure')
ORDER BY created_at DESC
LIMIT 10;
```

---

## 📦 4.7 utils/email_sender.py 🆕 **v1.1**

**Rôle** : Envoi d'emails avec templates HTML

**Classe principale** : `EmailSender`

```python
class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, sender: str, sender_password: str):
        """Initialise la connexion SMTP"""
        
    def send_alert(self, breakpoint_name: str, score: float, checks: List[dict], 
                   severity: str, recipients: List[str]) -> bool:
        """
        Envoie une alerte (critical ou warning)
        
        Template : alert_critical.html ou alert_warning.html
        Contenu : Nom BP, score, liste des checks échoués
        """
        
    def send_daily_report(self, results: List[dict], date: str, 
                          recipients: List[str]) -> bool:
        """
        Envoie le rapport quotidien
        
        Template : daily_report.html
        Contenu : 
        - Stats globales
        - Détails par breakpoint
        - Grille visuelle des checks
        - Détails des problèmes
        """
        
    def test_connection(self) -> bool:
        """Teste la connexion SMTP"""
```

**Templates HTML** :

### **alert_critical.html / alert_warning.html**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Styles pour alerte critique (rouge) ou warning (orange) */
    </style>
</head>
<body>
    <div class="alert-box critical">  <!-- ou warning -->
        <h1>🚨 Alerte Critique - {{ breakpoint_name }}</h1>
        <div class="score">{{ score }}/10</div>
        
        <h2>Checks échoués</h2>
        <ul>
            {% for check in failed_checks %}
            <li>{{ check.name }} : {{ check.message }}</li>
            {% endfor %}
        </ul>
        
        <p>Date : {{ date }}</p>
    </div>
</body>
</html>
```

### **daily_report.html**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Styles pour rapport quotidien */
        .checks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
        .check-item.success { border-left-color: green; }
        .check-item.failure { border-left-color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport Quotidien - Monitoring CTI</h1>
        <p>{{ date }}</p>
    </div>
    
    <div class="stats">
        <div>Breakpoints: {{ total_breakpoints }}</div>
        <div>Score moyen: {{ average_score }}/10</div>
        <div>✅ OK: {{ ok_count }}</div>
        <div>⚠️ Warnings: {{ warning_count }}</div>
        <div>🚨 Critiques: {{ critical_count }}</div>
    </div>
    
    {% for bp in breakpoints %}
    <div class="bp-item {{ bp.status }}">
        <h2>{{ bp.breakpoint_name }} - {{ bp.score }}/10</h2>
        
        <div class="checks-summary">
            <strong>Résumé : </strong>
            ✓ {{ bp.success_count }} réussi(s) | 
            ✗ {{ bp.failure_count }} échoué(s)
        </div>
        
        <!-- Grille visuelle des checks -->
        <div class="checks-grid">
            {% for check in bp.checks %}
            <div class="check-item {{ check.status }}">
                <span class="check-icon">
                    {% if check.status == 'success' %}✓{% else %}✗{% endif %}
                </span>
                <span>{{ check.name }}</span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Détails des problèmes (checks échoués uniquement) -->
        {% if bp.failure_count > 0 %}
        <div class="details">
            <strong>Détails des problèmes :</strong>
            <ul>
                {% for check in bp.checks %}
                {% if check.status != 'success' %}
                <li><strong>{{ check.name }}</strong> : {{ check.message }}</li>
                {% endif %}
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
```

**Configuration des destinataires** :

```yaml
# config.yaml
notifications:
  enabled: true
  
  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    sender: ${EMAIL_SENDER}
    sender_password: ${EMAIL_SENDER_PASSWORD}
    
    recipients:
      alerts:                    # Alertes critiques/warnings
        - data-team@company.com
        - ops-team@company.com
      reports:                   # Rapports quotidiens
        - data-team@company.com
        - manager@company.com
      all:                       # Tous les types
        - admin@company.com
    
    # Envoi conditionnel
    send_on_failure_only: true       # true = seulement si problème
    send_daily_report: true
    daily_report_min_score: 10       # Envoyer si score < 10
    
    # Throttling anti-spam
    min_interval_between_alerts: 300  # 5 min entre alertes
    max_emails_per_hour: 10           # Max 10 emails/heure
```

**Logique d'envoi conditionnel** :

```python
# Dans send_notifications()

# 1. Envoyer alerte si score < 8
if score < 5:
    send_alert(severity="critical")  # Rouge
elif score < 8:
    send_alert(severity="warning")   # Orange

# 2. Envoyer rapport quotidien si score < daily_report_min_score
if any(score < daily_report_min_score for score in scores):
    send_daily_report()  # Rapport détaillé
else:
    log("Rapport non envoyé : tous les BP OK")
```

---

## 📦 4.8 utils/analyze_baseline.py

**Rôle** : Analyser l'historique pour déterminer les seuils optimaux

**Fonction principale** :

```python
def analyze_baseline(db_path: str, breakpoint_id: str, metric_name: str, 
                     days: int = 30) -> dict:
    """
    Analyse l'historique d'une métrique pour déterminer les seuils.
    
    Args:
        db_path: Chemin vers monitoring.db
        breakpoint_id: ID du breakpoint
        metric_name: Nom de la métrique (ex: row_count, outlier_percent)
        days: Nombre de jours d'historique à analyser
    
    Returns:
        {
            "mean": 15000.5,
            "std": 1200.3,
            "min": 12500,
            "max": 18000,
            "p25": 14000,
            "p50": 15000,  # Médiane
            "p75": 16000,
            "p95": 17500,
            "recommended_threshold": 18500  # mean + 2*std
        }
    """
```

**Exemple d'utilisation** :

```bash
# Analyser la volumétrie sur 30 jours
python utils/analyze_baseline.py --metric row_count --days 30

# Résultat :
# Moyenne : 15000 lignes
# Écart-type : 1200 lignes
# Seuil recommandé (mean + 2*std) : 17400 lignes
# Configuration suggérée :
#   min_rows: 12000  # mean - 2*std
#   baseline_tolerance: 0.20  # ±20%
```

---

# 5. Configuration

## ⚙️ 5.1 config/config.yaml (Configuration globale)

```yaml
# ==========================================
# Configuration Monitoring CTI
# ==========================================

# Logging
logging:
  level: INFO                    # DEBUG / INFO / WARNING / ERROR
  console: true
  file: true
  log_dir: ./logs

# Base de données SQLite
database:
  enabled: true
  path: ./data/monitoring.db
  retention_days: 365            # Rétention des données (jours)

# Notifications
notifications:
  enabled: true
  
  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    sender: ${EMAIL_SENDER}                   # Variable d'environnement
    sender_password: ${EMAIL_SENDER_PASSWORD}
    
    recipients:
      alerts:
        - data-team@company.com
      reports:
        - data-team@company.com
        - manager@company.com
      all:
        - admin@company.com
    
    # Envoi conditionnel
    send_on_failure_only: true    # true = seulement si problème
    send_daily_report: true
    daily_report_min_score: 10    # Envoyer si score < 10
    
    # Throttling
    min_interval_between_alerts: 300  # 5 minutes
    max_emails_per_hour: 10

# Exports
exports:
  json:
    enabled: true
    output_dir: ./dashboard_data
  text_logs:
    enabled: true
    output_dir: ./logs
```

---

## ⚙️ 5.2 config/.env (Credentials)

```bash
# ==========================================
# Credentials - Monitoring CTI
# NE JAMAIS COMMITER CE FICHIER SUR GIT
# ==========================================

# Oracle DWH
DWH_DSN=hostname:1521/XEPDB1
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=SecurePassword123!
DWH_TABLE_NAME=CTI_SCHEMA.CALLS_TABLE

# Email SMTP
EMAIL_SENDER=monitoring@company.com
EMAIL_SENDER_PASSWORD=app_password_16chars
```

**⚠️ Important** :
- Le fichier `.env` est dans `.gitignore` (jamais commité)
- Utiliser `.env.example` comme template pour les nouveaux dev
- Pour Gmail : générer un "App Password" sur https://myaccount.google.com/apppasswords

---

## ⚙️ 5.3 breakpoints/bp9_dwh_oracle.yaml (Définition d'un breakpoint)

```yaml
# ==========================================
# Breakpoint : Datawarehouse Oracle
# ==========================================

id: bp9_dwh_oracle
name: Datawarehouse Oracle
description: Surveillance quotidienne des données CTI dans Oracle DWH

# Requête SQL d'extraction
query: |
  SELECT 
    CONNID,
    STARTTIME,
    DURATION,
    RINGDURATION,
    ORIGDNIS,
    DESTDNIS,
    CALLINGPARTYNUMBER,
    ORIGINALCALLEDPARTYNUMBER,
    FINALCALLEDPARTYNUMBER
  FROM ${DWH_TABLE_NAME}
  WHERE TRUNC(STARTTIME) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')
  ORDER BY STARTTIME

# Liste des checks à exécuter
checks:
  # Check 1 : Schéma conforme
  - type: schema_conformity_check
    name: schema_conformity_check
    expected_columns:
      - CONNID
      - STARTTIME
      - DURATION
      - RINGDURATION
      - ORIGDNIS
      - DESTDNIS
      - CALLINGPARTYNUMBER
      - ORIGINALCALLEDPARTYNUMBER
      - FINALCALLEDPARTYNUMBER
  
  # Check 2 : Volumétrie minimale
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 10000
    message: "Volumétrie insuffisante (< 10000 lignes)"
  
  # Check 3 : Comparaison avec baseline
  - type: baseline_comparison_check
    name: baseline_comparison_check
    baseline_query: |
      SELECT AVG(COUNT(*)) as avg_count
      FROM ${DWH_TABLE_NAME}
      WHERE TRUNC(STARTTIME) > SYSDATE - 30
      GROUP BY TRUNC(STARTTIME)
    tolerance: 0.20  # ±20%
  
  # Check 4 : Doublons sur clé primaire
  - type: duplicate_key_check
    name: duplicate_key_check
    key_columns:
      - CONNID
    max_duplicate_rate: 0.01  # 1% max
  
  # Check 5 : Taux de valeurs nulles
  - type: null_rate_check
    name: null_rate_check
    critical_columns:
      - CONNID
      - STARTTIME
      - DURATION
    max_null_rate: 0.02  # 2% max
  
  # Check 6 : Distribution horaire
  - type: hourly_distribution_check
    name: hourly_distribution_check
    datetime_column: STARTTIME
    baseline_query: |
      SELECT 
        TO_CHAR(STARTTIME, 'HH24') as hour,
        AVG(COUNT(*) / (SELECT COUNT(*) FROM ${DWH_TABLE_NAME} WHERE TRUNC(STARTTIME) = TRUNC(h.STARTTIME))) as pct
      FROM ${DWH_TABLE_NAME} h
      WHERE TRUNC(STARTTIME) > SYSDATE - 30
      GROUP BY TO_CHAR(STARTTIME, 'HH24'), TRUNC(STARTTIME)
      GROUP BY hour
    tolerance: 0.05  # ±5%
  
  # Check 7 : Détection d'outliers (NEW v1.1)
  - type: outlier_detection_check
    name: outlier_detection_check
    numeric_columns:
      DURATION:
        method: iqr
        threshold: 1.5
      RINGDURATION:
        method: iqr
        threshold: 1.5
    categorical_columns:
      ORIGDNIS:
        min_frequency: 3
      DESTDNIS:
        min_frequency: 3
    critical_outlier_threshold: 0.05  # 5% max
```

---

# 6. Checks disponibles

## 📋 Résumé des checks

| Check | Type | Objectif | Seuils |
|-------|------|----------|--------|
| **schema_conformity** | Qualité | Colonnes obligatoires présentes | Toutes ou échec |
| **min_row_count** | Volumétrie | Nombre de lignes minimum | >= min_rows |
| **baseline_comparison** | Tendance | Écart vs moyenne historique | ±tolerance |
| **duplicate_key** | Intégrité | Doublons sur clé primaire | <= max_duplicate_rate |
| **null_rate** | Qualité | Taux de valeurs nulles | <= max_null_rate |
| **hourly_distribution** | Tendance | Distribution horaire conforme | ±tolerance |
| **outlier_detection** | Anomalies | Valeurs aberrantes (IQR, Z-Score) | <= critical_outlier_threshold |

---

# 7. Système de logging

## 📝 Niveaux de logging

| Niveau | Usage | Exemple |
|--------|-------|---------|
| **DEBUG** | Développement, debug détaillé | Requêtes SQL, valeurs intermédiaires |
| **INFO** | Production, informations générales | Début/fin de run, résultats checks |
| **WARNING** | Alertes non bloquantes | Scores dégradés (5-7), timeouts |
| **ERROR** | Erreurs bloquantes | Connexion DB échouée, checks échoués |

## 📂 Structure des logs

```
logs/
├── text/                        # Logs texte lisibles
│   ├── batch_20260912_115206.txt
│   └── ...
└── json/                        # Logs JSON structurés
    ├── batch_20260912_115206.json
    └── ...
```

**Exemple log texte** :

```
2026-09-12 11:52:06 - monitoring - INFO - [DEMARRAGE] DÉMARRAGE DU MONITORING CTI
2026-09-12 11:52:06 - monitoring - INFO - [DATE] Date cible : 2026-06-22
2026-09-12 11:52:06 - monitoring - INFO - [PACKAGE] 1 breakpoint(s) à exécuter
2026-09-12 11:52:06 - monitoring - INFO - [RECHERCHE] Exécution du breakpoint : Datawarehouse Oracle
2026-09-12 11:52:06 - monitoring - INFO - [DATA] 15049 lignes extraites
2026-09-12 11:52:06 - monitoring - INFO - [STATS] Score : 7/10
2026-09-12 11:52:06 - monitoring - INFO - [OK] schema_conformity_check : success
2026-09-12 11:52:06 - monitoring - INFO - [ECHEC] duplicate_key_check : failure (285 doublons)
```

**Exemple log JSON** :

```json
{
  "run_id": "20260912_115206",
  "date": "2026-09-12",
  "target_date": "2026-06-22",
  "breakpoints": [
    {
      "id": "bp9_dwh_oracle",
      "name": "Datawarehouse Oracle",
      "status": "warning",
      "score": 7,
      "execution_time": 6.5,
      "checks": [
        {
          "name": "schema_conformity_check",
          "status": "success",
          "message": "Toutes les colonnes présentes"
        },
        {
          "name": "duplicate_key_check",
          "status": "failure",
          "message": "285 doublons détectés",
          "details": {
            "duplicate_count": 285,
            "duplicate_rate": 0.0189
          }
        }
      ]
    }
  ]
}
```

---

# 8. Système d'emails

## 📧 Types d'emails

### 🚨 **Alerte critique** (score < 5)

**Destinataires** : `recipients.alerts`  
**Template** : `alert_critical.html`  
**Contenu** :
- Nom du breakpoint
- Score /10
- Liste des checks échoués avec messages

### ⚠️ **Alerte warning** (5 ≤ score < 8)

**Destinataires** : `recipients.alerts`  
**Template** : `alert_warning.html`  
**Contenu** :
- Nom du breakpoint
- Score /10
- Liste des checks échoués avec messages

### 📊 **Rapport quotidien** (si score < 10)

**Destinataires** : `recipients.reports`  
**Template** : `daily_report.html`  
**Contenu** :
- Stats globales (nb breakpoints, score moyen)
- Compteurs (OK/Warnings/Critiques)
- Détails par breakpoint :
  - Nom + Score
  - Résumé des checks (X réussi(s), Y échoué(s))
  - **Grille visuelle** de tous les checks avec statuts
  - **Détails des problèmes** : Messages des checks échoués uniquement

## 📅 Logique d'envoi conditionnel

```python
# Configuration
daily_report_min_score = 10
send_on_failure_only = True

# Décision d'envoi
if any(score < daily_report_min_score for score in scores):
    send_daily_report()  # Au moins un problème détecté
elif not send_on_failure_only:
    send_daily_report()  # Envoi systématique activé
else:
    log("Rapport non envoyé : tous les breakpoints OK")
```

**Scénarios** :

| Score max | `daily_report_min_score` | `send_on_failure_only` | Envoi ? |
|-----------|--------------------------|------------------------|---------|
| 10/10     | 10                       | true                   | ❌ NON   |
| 9/10      | 10                       | true                   | ✅ OUI   |
| 7/10      | 10                       | true                   | ✅ OUI   |
| 7/10      | 8                        | true                   | ✅ OUI   |
| 9/10      | 8                        | true                   | ❌ NON   |
| 10/10     | 10                       | false                  | ✅ OUI (envoi systématique) |

---

# 9. Base de données SQLite

## 🗄️ Schéma complet

Voir section **4.6 utils/sqlite_logger.py** pour le schéma détaillé.

## 📊 Requêtes utiles

### **Trending de la volumétrie**

```sql
SELECT 
    target_date,
    metric_value as row_count
FROM metrics_history
WHERE breakpoint_id = 'bp9_dwh_oracle'
  AND metric_name = 'row_count'
  AND target_date > date('now', '-30 days')
ORDER BY target_date;
```

### **Moyenne des scores sur 7 jours**

```sql
SELECT 
    breakpoint_id,
    AVG(score) as avg_score,
    COUNT(*) as total_runs
FROM breakpoint_results
WHERE target_date > date('now', '-7 days')
GROUP BY breakpoint_id;
```

### **Top 10 runs avec échecs**

```sql
SELECT 
    r.run_id,
    r.target_date,
    br.breakpoint_name,
    br.score,
    br.checks_failed
FROM runs r
JOIN breakpoint_results br ON r.run_id = br.run_id
WHERE br.status IN ('warning', 'failure')
ORDER BY r.run_date DESC
LIMIT 10;
```

### **Checks échoués par type**

```sql
SELECT 
    check_name,
    COUNT(*) as failure_count,
    AVG(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 100 as success_rate
FROM check_results
WHERE created_at > datetime('now', '-30 days')
GROUP BY check_name
ORDER BY failure_count DESC;
```

### **Détail d'un run spécifique**

```sql
SELECT 
    br.breakpoint_name,
    br.score,
    cr.check_name,
    cr.status,
    cr.message,
    cr.details
FROM runs r
JOIN breakpoint_results br ON r.run_id = br.run_id
JOIN check_results cr ON r.run_id = cr.run_id AND br.breakpoint_id = cr.breakpoint_id
WHERE r.run_id = '20260912_115206'
ORDER BY br.breakpoint_id, cr.check_name;
```

---

# 10. Utilisation

## 🚀 Installation

### **1. Cloner le repo**

```bash
git clone https://github.com/your-org/monitoring-cti.git
cd monitoring-cti/Code
```

### **2. Créer un environnement virtuel**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### **3. Installer les dépendances**

```bash
pip install -r requirements.txt
```

### **4. Configurer les credentials**

```bash
# Copier le template
copy config\.env.example config\.env

# Éditer config\.env avec vos credentials
notepad config\.env
```

### **5. Vérifier la configuration**

```bash
python check_env.py
```

## 🏃 Exécution

### **Run quotidien (date du jour)**

```bash
python main.py
```

### **Run avec date spécifique**

```bash
python main.py --date 2026-06-22
```

### **Run d'un breakpoint spécifique**

```bash
python main.py --breakpoint bp9_dwh_oracle
```

### **Run avec date + breakpoint**

```bash
python main.py --date 2026-06-22 --breakpoint bp9_dwh_oracle
```

## 🧪 Tests

### **Tester la connexion Oracle**

```bash
python test_connection.py
```

### **Tester la configuration email**

```bash
python utils/email_sender.py --test-config
```

### **Tester l'envoi d'un email**

```bash
python utils/email_sender.py --test-send --to votre-email@example.com
```

### **Analyser la baseline**

```bash
python utils/analyze_baseline.py --metric row_count --days 30
```

## 🔄 Automatisation

### **Cron (Linux/Mac)**

```bash
# Éditer crontab
crontab -e

# Ajouter une ligne pour exécution quotidienne à 8h
0 8 * * * cd /path/to/monitoring-cti/Code && /path/to/venv/bin/python main.py >> /var/log/monitoring-cti.log 2>&1
```

### **Task Scheduler (Windows)**

```powershell
# Créer une tâche planifiée
$action = New-ScheduledTaskAction -Execute "C:\path\to\venv\Scripts\python.exe" -Argument "C:\path\to\Code\main.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Monitoring CTI" -Description "Exécution quotidienne du monitoring CTI"
```

---

# 11. Troubleshooting

## 🔧 Problèmes courants

### **Erreur : "No module named 'oracledb'"**

**Solution** :
```bash
pip install oracledb
```

### **Erreur : "Oracle Instant Client not found"**

**Solution** :
1. Télécharger Oracle Instant Client : https://www.oracle.com/database/technologies/instant-client.html
2. Extraire dans `C:\oracle\instantclient_21_X`
3. Ajouter au PATH système :
   ```powershell
   $env:PATH += ";C:\oracle\instantclient_21_X"
   ```

### **Erreur : "SMTP authentication failed"**

**Solution (Gmail)** :
1. Activer la validation en 2 étapes sur votre compte Google
2. Générer un "App Password" : https://myaccount.google.com/apppasswords
3. Utiliser ce mot de passe de 16 caractères dans `.env`

### **Erreur : "UnicodeEncodeError: 'charmap' codec can't encode character"**

**Solution** : Remplacer les emojis dans le code par du texte :
```python
# Avant
logger.info("✅ Check OK")

# Après
logger.info("OK - Check OK")
```

### **Logs : Aucune donnée extraite (0 lignes)**

**Vérifications** :
1. Date cible correcte : `--date 2026-06-22`
2. Requête SQL valide dans le breakpoint YAML
3. Variable `${DWH_TABLE_NAME}` correctement définie dans `.env`
4. Connexion DB fonctionnelle : `python test_connection.py`

### **Emails non envoyés**

**Vérifications** :
1. Configuration SMTP correcte dans `config.yaml`
2. Credentials valides dans `.env`
3. Firewall/proxy n'bloque pas le port 587
4. Tester la connexion : `python utils/email_sender.py --test-config`
5. Vérifier la logique conditionnelle :
   - `send_on_failure_only: true` → Seulement si problème
   - `daily_report_min_score: 10` → Seulement si score < 10

### **SQLite : "database is locked"**

**Causes** :
- Plusieurs instances de `main.py` en parallèle
- Connexion non fermée proprement

**Solution** :
```python
# Utiliser le context manager
with SQLiteLogger(db_path) as logger:
    logger.log_full_run(...)
# Connexion fermée automatiquement
```

---

# 12. Extensions futures

## 🔮 Améliorations possibles

### **1. Dashboard web interactif**

```python
# Streamlit ou Flask
# - Graphiques de trending (row_count, score, outliers)
# - Vue temps réel des derniers runs
# - Filtres par breakpoint, date, status
# - Export PDF des rapports
```

### **2. Machine Learning pour prédiction**

```python
# Prédire les anomalies avant qu'elles n'arrivent
# - Modèle ARIMA pour prédire la volumétrie
# - Isolation Forest pour détecter les anomalies complexes
# - Alertes prédictives (J-1 : "Risque de volumétrie faible demain")
```

### **3. Intégration Slack/Teams**

```python
# Envoyer les alertes sur Slack/Teams en plus des emails
# - Webhooks Slack
# - API Microsoft Teams
# - Boutons d'action ("Ack", "Investigate", "Ignore")
```

### **4. Système de tickets automatique**

```python
# Créer automatiquement un ticket Jira/ServiceNow en cas de check échoué
# - API Jira
# - Assignation automatique selon le type de check
# - Lien vers les détails dans SQLite
```

### **5. Multi-sources de données**

```python
# Support d'autres bases de données
# - PostgreSQL
# - SQL Server
# - MongoDB
# - APIs REST
# - Fichiers CSV/Excel
```

### **6. Checks personnalisés avancés**

```python
# Nouveaux checks spécialisés
# - Détection de fraude (patterns anormaux)
# - Conformité RGPD (données sensibles exposées)
# - Performance (temps de réponse API)
# - Cohérence inter-tables (foreign keys)
```

### **7. Reporting PDF automatique**

```python
# Générer un PDF du rapport quotidien
# - Graphiques matplotlib/seaborn
# - Export mensuel récapitulatif
# - Envoi automatique aux stakeholders
```

### **8. Monitoring de la performance**

```python
# Métriques de performance du monitoring lui-même
# - Temps d'exécution par check
# - Taille des données extraites
# - Mémoire consommée
# - Alertes si le monitoring devient trop lent
```

---

# Annexes

## 📚 Ressources

- **Oracle Python Driver** : https://python-oracledb.readthedocs.io/
- **Jinja2 Templates** : https://jinja.palletsprojects.com/
- **SQLite Documentation** : https://www.sqlite.org/docs.html
- **Python logging** : https://docs.python.org/3/library/logging.html
- **SMTP avec Python** : https://docs.python.org/3/library/smtplib.html

## 🔑 Glossaire

- **Breakpoint** : Point de surveillance (ex: table Oracle à surveiller)
- **Check** : Vérification individuelle (ex: volumétrie, doublons)
- **Run** : Exécution complète du monitoring (1 run = N breakpoints)
- **Score** : Note de 0 à 10 calculée sur tous les checks d'un breakpoint
- **Baseline** : Référence historique pour comparaison
- **Outlier** : Valeur aberrante détectée statistiquement (IQR, Z-Score)
- **Throttling** : Limitation du nombre d'emails pour éviter spam

## 👥 Équipe

- **Développement** : Data Engineering Team
- **Maintenance** : Ops Team
- **Contact** : data-team@company.com

---

**Fin de la documentation**  
**Version** : 1.1.0  
**Date** : 2026-09-12
