# 🚀 Démarrage rapide - Monitoring CTI

Guide pour démarrer en 5 minutes.

## 📋 Prérequis

- Python 3.8 ou supérieur installé
- Accès au Datawarehouse Oracle (credentials)

## 🛠️ Installation en 4 étapes

### 1️⃣ Installer les dépendances

```powershell
pip install -r requirements.txt
```

### 2️⃣ Configurer les credentials Oracle

Copier le template :

```powershell
cp config\.env.example .env
```

Éditer `.env` avec vos credentials :

```env
DWH_DSN=oracle-host:1521/service_name
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=your_password
DWH_TABLE_NAME=DWH_CTI.CDR_EVENTS
```

### 3️⃣ Vérifier l'environnement

```powershell
python check_env.py
```

Si tout est ✅, vous êtes prêt !

### 4️⃣ Premier run

```powershell
python main.py
```

## 📊 Comprendre les résultats

### Console

```
═══════════════════════════════════════════════════
🔍 Exécution du breakpoint : BP9 - DWH Oracle Direct (bp9_dwh_oracle)
═══════════════════════════════════════════════════
✅ Statut : Normal
📊 Score : 10/10
📅 Date cible : 2026-09-02
🕒 Exécuté à : 2026-09-03 14:30:22

📋 Détail des checks (6) :
  ✅ Volumétrie minimale : Normal (score: 10/10)
  ✅ Comparaison baseline : Normal (score: 10/10)
  ✅ Conformité schéma : Normal (score: 10/10)
  ✅ Détection doublons : Normal (score: 10/10)
  ✅ Taux de nullité : Normal (score: 10/10)
  ✅ Distribution horaire : Normal (score: 10/10)
```

### Fichiers générés

```
logs/
  ├── monitoring_20260903.log          # Log applicatif
  ├── json/
  │   └── batch_20260903_143022.json   # Résultats machine-readable
  └── text/
      └── batch_20260903_143022.txt    # Résultats human-readable

dashboard_data/
  └── latest.json                       # Pour le dashboard React
```

## 🎯 Cas d'usage courants

### Contrôler une date spécifique

```powershell
python main.py --date 2026-08-15
```

### Exécuter un seul breakpoint

```powershell
python main.py --breakpoint bp9_dwh_oracle
```

### Combiner date et breakpoint

```powershell
python main.py --breakpoint bp9_dwh_oracle --date 2026-08-15
```

### Mode DEBUG

Éditer `config/config.yaml` :

```yaml
logging:
  log_level: DEBUG
```

## 🔍 Interpréter les statuts

| Emoji | Statut     | Score  | Signification                      |
|-------|------------|--------|------------------------------------|
| ✅    | Normal     | 10/10  | Tout est conforme                  |
| ⚠️    | Dégradé    | 6-9/10 | Écarts tolérables, surveiller      |
| ❌    | Critique   | ≤5/10  | Problème majeur, action immédiate  |
| 🔄    | En cours   | -      | Exécution en cours                 |
| ❓    | Inconnu    | -      | Erreur technique                   |

## 📝 Personnaliser la configuration

### Modifier les seuils d'un check

Éditer `breakpoints/bp9_dwh_oracle.yaml` :

```yaml
checks:
  - type: min_row_count_check
    params:
      min_lines: 100000  # Modifier ici
```

### Ajouter un check

```yaml
checks:
  # ... checks existants
  - type: null_rate_check
    params:
      critical_columns:
        - CONN_ID
        - CALLING_NUMBER
      max_null_rate_percent: 1.0
```

### Désactiver un check

Commenter ou supprimer l'entrée dans le YAML.

## 🆘 Dépannage

### ❌ ImportError: No module named 'oracledb'

➡️ Installer les dépendances : `pip install -r requirements.txt`

### ❌ FileNotFoundError: .env

➡️ Créer le fichier : `cp config\.env.example .env`

### ❌ ORA-12154: TNS:could not resolve

➡️ Vérifier `DWH_DSN` dans `.env` (format: `host:port/service`)

### ❌ ValueError: Query is not a SELECT statement

➡️ L'OracleConnector est read-only, seules les requêtes SELECT sont autorisées

### ⚠️ Check échoue avec score 0

➡️ Consulter les logs détaillés :
```powershell
Get-Content logs\text\batch_*.txt | Select-Object -Last 50
```

## 📚 Documentation complète

- **README.md** : Documentation complète
- **ARCHITECTURE.md** : Architecture technique détaillée
- **Documentation/Plan_de_Monitoring_DWH.md** : Spécifications fonctionnelles

## 🎯 Prochaines étapes

1. ✅ Exécuter un premier run de test
2. ⚙️ Ajuster les seuils selon vos besoins
3. 📊 Consulter les résultats JSON pour préparer le dashboard
4. 🔔 Configurer les notifications (email/push)
5. 🚀 Automatiser via cron/Task Scheduler

### Automatisation Windows (Task Scheduler)

Créer un script PowerShell `run_monitoring.ps1` :

```powershell
cd "C:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
python main.py
```

Puis planifier dans Task Scheduler :
- Trigger : Tous les jours à 8h00
- Action : `powershell.exe -File "C:\...\run_monitoring.ps1"`

## 💡 Conseils

- **Première exécution** : Utiliser `--date` avec une date récente connue
- **Baselines** : Les 14 premiers jours peuvent avoir des scores dégradés (baseline en construction)
- **Logs** : Consulter régulièrement `logs/text/` pour comprendre les écarts
- **Configuration** : Commencer avec des seuils larges, resserrer progressivement

---

Besoin d'aide ? Consultez le **README.md** pour plus de détails !
