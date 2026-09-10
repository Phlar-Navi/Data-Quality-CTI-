# Monitoring CTI - Datawarehouse Oracle

Système de monitoring modulaire pour le Datawarehouse CTI Oracle avec architecture connecteurs/checks/config.

## 📋 Table des matières

- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Ajouter un nouveau breakpoint](#ajouter-un-nouveau-breakpoint)
- [Ajouter un nouveau check](#ajouter-un-nouveau-check)
- [Logs et résultats](#logs-et-résultats)
- [Dashboard](#dashboard)

---

## 🏗️ Architecture

Le système est construit sur 3 couches découplées :

```
┌─────────────────────────────────────────┐
│          main.py (Runner)               │
│  ┌────────────────────────────────────┐ │
│  │   BreakpointRunner (Orchestrateur) │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
              ↓           ↓
    ┌─────────────┐  ┌──────────┐
    │ Connecteurs │  │  Checks  │
    └─────────────┘  └──────────┘
         ↓                ↓
    ┌──────────────────────────┐
    │    Source de données     │
    │   (Oracle DWH, etc.)     │
    └──────────────────────────┘
```

### Principes

- **Modularité** : Chaque composant est indépendant et réutilisable
- **Ajustabilité** : Configuration YAML pour tous les paramètres
- **Extensibilité** : Ajout de nouveaux connecteurs/checks sans modifier le code existant
- **Sécurité** : Connecteurs read-only, validation des requêtes

---

## 🔧 Prérequis

- **Python 3.8+**
- **Dépendances Python** :
  - `oracledb` (connecteur Oracle)
  - `pandas` (manipulation de données)
  - `PyYAML` (lecture config)

---

## 📦 Installation

### 1. Installer les dépendances

```powershell
pip install oracledb pandas pyyaml
```

### 2. Configurer les credentials Oracle

Créer un fichier `.env` à la racine du projet :

```bash
cp config/.env.example .env
```

Éditer le fichier `.env` avec vos credentials :

```env
# Connexion Oracle DWH
DWH_DSN=host:port/service_name
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=votre_mot_de_passe

# Nom de la table principale
DWH_TABLE_NAME=DWH_CTI.CDR_EVENTS
```

⚠️ **Sécurité** : Ne jamais commiter le fichier `.env` ! Il est déjà dans `.gitignore`.

### 3. Vérifier l'installation

```powershell
python main.py --help
```

---

## ⚙️ Configuration

### Configuration globale (`config/config.yaml`)

Paramètres partagés par tous les breakpoints :

- **Logging** : niveau, répertoire, rotation
- **Exécution** : mode (single/all), timeout, parallélisation
- **Notifications** : email, push (ntfy)
- **Dashboard** : export JSON, taille historique
- **Seuils par défaut** : volumétrie, qualité, distribution

### Configuration par breakpoint (`breakpoints/*.yaml`)

Chaque breakpoint a sa propre configuration YAML :

```yaml
id: bp9_dwh_oracle
name: "BP9 - DWH Oracle Direct"
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
  check_offset_days: 1  # Contrôle des données J-1

checks:
  - type: min_row_count_check
    params:
      min_lines: 50000
    force_zero_on_failure: true
  
  - type: baseline_comparison_check
    params:
      baseline_days: 14
      tolerance_percent: 20.0
  
  # ... autres checks
```

**Substitution de variables** : Les variables `${VAR}` sont remplacées par les variables d'environnement.

---

## 🚀 Utilisation

### Exécution basique

Exécuter tous les breakpoints configurés (mode par défaut) :

```powershell
python main.py
```

### Exécution d'un breakpoint spécifique

```powershell
python main.py --breakpoint bp9_dwh_oracle
```

### Spécifier une date cible

Par défaut, le système contrôle les données de J-1 (ou selon `check_offset_days`). Pour forcer une date :

```powershell
python main.py --date 2026-09-01
```

### Combiner les options

```powershell
python main.py --breakpoint bp9_dwh_oracle --date 2026-09-01
```

### Spécifier un fichier de config alternatif

```powershell
python main.py --config config/config_prod.yaml
```

---

## 📁 Structure du projet

```
Code/
├── main.py                     # Runner principal
├── config/
│   ├── config.yaml             # Configuration globale
│   ├── .env.example            # Template pour credentials
│   └── config_loader.py        # Loader de config YAML
├── connectors/
│   ├── base.py                 # Classe BaseConnector
│   └── oracle_connector.py     # Connecteur Oracle read-only
├── checks/
│   ├── base.py                 # Classe BaseCheck
│   ├── volumetry.py            # Checks volumétriques
│   ├── quality.py              # Checks qualité
│   └── distribution.py         # Checks distribution
├── breakpoints/
│   └── bp9_dwh_oracle.yaml     # Config breakpoint BP9
├── utils/
│   ├── models.py               # Modèles de données (CheckResult, etc.)
│   ├── breakpoint_runner.py    # Orchestrateur de checks
│   └── result_logger.py        # Logger de résultats JSON/TXT
├── logs/                       # Logs d'exécution
│   ├── json/                   # Résultats JSON (machine-readable)
│   └── text/                   # Résultats TXT (human-readable)
└── dashboard_data/             # Export JSON pour le dashboard React
```

---

## ➕ Ajouter un nouveau breakpoint

### 1. Créer le fichier YAML

Créer `breakpoints/bp10_nouveau.yaml` :

```yaml
id: bp10_nouveau
name: "BP10 - Nouvelle source"
access: direct

connector:
  type: oracle
  params:
    dsn: ${DWH_DSN}
    user: ${DWH_READONLY_USER}
    password: ${DWH_READONLY_PASSWORD}

data_source:
  table: NOUVELLE_TABLE
  date_column: DATE_COL

schedule:
  check_offset_days: 1

checks:
  - type: min_row_count_check
    params:
      min_lines: 1000
```

### 2. Exécuter le nouveau breakpoint

```powershell
python main.py --breakpoint bp10_nouveau
```

C'est tout ! Le système charge automatiquement la nouvelle configuration.

---

## 🔍 Ajouter un nouveau check

### 1. Créer la classe du check

Ajouter dans `checks/custom.py` :

```python
from .base import BaseCheck
from ..utils.models import CheckResult, CheckStatus, CheckConfidence

class MonNouveauCheck(BaseCheck):
    """Description du check."""
    
    def __init__(self, params: dict):
        super().__init__(name="Mon Nouveau Check", params=params)
    
    def run(self, data) -> CheckResult:
        # Logique du check
        
        if condition_ok:
            return self._create_result(
                status=CheckStatus.NORMAL,
                confidence=CheckConfidence.DIRECT,
                score=10,
                message="Tout est OK"
            )
        else:
            return self._create_result(
                status=CheckStatus.CRITIQUE,
                confidence=CheckConfidence.DIRECT,
                score=0,
                message="Problème détecté"
            )
```

### 2. Enregistrer le check

Dans `utils/breakpoint_runner.py`, ajouter dans `CHECK_REGISTRY` :

```python
CHECK_REGISTRY = {
    # ... checks existants
    "mon_nouveau_check": MonNouveauCheck
}
```

### 3. Utiliser le check

Dans un fichier breakpoint YAML :

```yaml
checks:
  - type: mon_nouveau_check
    params:
      param1: valeur1
```

---

## 📊 Logs et résultats

### Logs texte

Logs d'exécution quotidiens dans `logs/` :

```
logs/monitoring_20260903.log
```

### Résultats JSON (machine-readable)

Pour l'intégration dashboard/API :

```
logs/json/bp9_dwh_oracle_20260903_143022.json
logs/json/batch_20260903_143022.json
```

### Résultats TXT (human-readable)

Pour lecture manuelle :

```
logs/text/bp9_dwh_oracle_20260903_143022.txt
logs/text/batch_20260903_143022.txt
```

### Rotation automatique

Les logs de plus de 30 jours (configurable dans `config.yaml`) sont automatiquement supprimés.

---

## 📈 Dashboard

### Export JSON

Le système exporte automatiquement les résultats dans `dashboard_data/` :

- `latest.json` : Dernier run (utilisé par le dashboard React)
- `run_YYYYMMDD_HHMMSS.json` : Historique des runs

### Format JSON

```json
{
  "run_timestamp": "20260903_143022",
  "run_date": "2026-09-03T14:30:22",
  "breakpoints": [
    {
      "breakpoint_id": "bp9_dwh_oracle",
      "breakpoint_name": "BP9 - DWH Oracle Direct",
      "status": "Normal",
      "score": 10,
      "checks": [...]
    }
  ]
}
```

### Intégration React

Le dashboard React (à implémenter) consomme `dashboard_data/latest.json` pour afficher :

- Vue d'ensemble (statuts macro + alertes)
- Détail par breakpoint (checks individuels)
- Historique (courbes de score)
- Configuration (paramètres actifs)

---

## 🎯 Système de scoring

### Calcul du score

Le score d'un breakpoint est la **moyenne des scores de ses checks** (sur 10).

**Cas particulier** : Si un check avec `force_zero_on_failure: true` échoue, le score global est **forcé à 0**.

### Détermination du statut

| Score   | Statut     | Badge      |
|---------|------------|------------|
| 10/10   | ✅ Normal  | Vert       |
| 6-9/10  | ⚠️ Dégradé | Orange     |
| ≤5/10   | ❌ Critique| Rouge      |
| -       | 🔄 En cours| Bleu       |
| -       | ❓ Inconnu | Gris       |

---

## 🛡️ Sécurité

### Connecteur read-only

Le `OracleConnector` refuse toute requête non-SELECT :

```python
# ✅ Autorisé
df = conn.query("SELECT * FROM table WHERE date = :date")

# ❌ Bloqué (ValueError)
conn.query("DELETE FROM table")
conn.query("UPDATE table SET col = 1")
```

### Variables d'environnement

Les credentials ne sont **jamais** en dur dans le code. Toujours utiliser `.env` et `${VAR}`.

---

## 🐛 Dépannage

### Erreur de connexion Oracle

```
ORA-12154: TNS:could not resolve the connect identifier specified
```

➡️ Vérifier `DWH_DSN` dans `.env` (format : `host:port/service_name`)

### Check échoue avec score 0

➡️ Vérifier les logs détaillés dans `logs/text/` pour le message d'erreur spécifique.

### Aucun résultat dans dashboard_data/

➡️ Vérifier que `dashboard.export_enabled: true` dans `config/config.yaml`.

---

## 📞 Support

Pour toute question ou problème :

1. Consulter les logs dans `logs/`
2. Vérifier la configuration YAML
3. Activer le mode DEBUG dans `config.yaml` :

```yaml
logging:
  log_level: DEBUG
```

---

## 🚧 TODO / Améliorations futures

- [ ] Implémenter les notifications email/push (module `send_notifications`)
- [ ] Ajouter un connecteur SFTP pour les contrôles fichiers
- [ ] Créer le dashboard React avec charte Orange
- [ ] Ajouter des checks de réconciliation DWH ↔ SFTP
- [ ] Implémenter la base de données de métriques (historisation avancée)
- [ ] Ajouter des tests unitaires
- [ ] Créer un script d'installation automatique (`setup.py`)

---

## 📄 Licence

Interne OCM. Tous droits réservés.
