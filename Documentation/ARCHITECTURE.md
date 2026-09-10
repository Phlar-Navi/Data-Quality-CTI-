# Architecture du système de monitoring CTI

## Vue d'ensemble

Le système de monitoring CTI est construit selon une architecture en couches découplées permettant une extensibilité maximale et une maintenance facilitée.

## Diagramme de flux

```
┌──────────────────────────────────────────────────────────────┐
│                        main.py                                │
│  - Parse arguments CLI (--date, --breakpoint, --config)       │
│  - Charge config globale (config.yaml)                        │
│  - Initialise logging                                         │
│  - Orchestre l'exécution                                      │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ↓
┌──────────────────────────────────────────────────────────────┐
│                  BreakpointRunner                             │
│  - Charge config du breakpoint (YAML)                         │
│  - Instancie le connecteur                                    │
│  - Récupère les données                                       │
│  - Exécute les checks                                         │
│  - Agrège les résultats                                       │
│  - Calcule le score global                                    │
└───────────┬──────────────────────┬───────────────────────────┘
            │                      │
            ↓                      ↓
┌─────────────────────┐  ┌──────────────────────┐
│    Connecteurs      │  │       Checks         │
│                     │  │                      │
│  BaseConnector      │  │  BaseCheck           │
│  ├─ OracleConnector │  │  ├─ MinRowCount      │
│  └─ (futurs)        │  │  ├─ Baseline         │
│                     │  │  ├─ SchemaConformity │
│                     │  │  ├─ DuplicateKey     │
│                     │  │  ├─ NullRate         │
│                     │  │  └─ HourlyDistrib    │
└──────────┬──────────┘  └──────────┬───────────┘
           │                        │
           ↓                        ↓
┌─────────────────────────────────────────────────┐
│           Source de données                      │
│  - Oracle DWH                                    │
│  - (futur : SFTP, APIs, etc.)                   │
└─────────────────────────────────────────────────┘
```

## Couches applicatives

### 1. Couche Présentation (main.py)

**Responsabilité** : Interface utilisateur et orchestration globale

- Parse les arguments CLI
- Charge la configuration globale
- Initialise le système de logging
- Exécute les breakpoints (un ou tous)
- Exporte les résultats (JSON pour dashboard)
- Gère les notifications (email, push)

**Fichiers** :
- `main.py`

### 2. Couche Orchestration (BreakpointRunner)

**Responsabilité** : Gestion du cycle de vie d'un breakpoint

- Charge la configuration du breakpoint (YAML)
- Instancie le connecteur configuré
- Récupère les données via le connecteur
- Prépare les données spécifiques pour chaque check
- Exécute tous les checks
- Calcule les baselines (volumétrie, distribution)
- Agrège les résultats
- Calcule le score global

**Fichiers** :
- `utils/breakpoint_runner.py`

**Registres** :
- `CHECK_REGISTRY` : mapping type → classe de check
- `CONNECTOR_REGISTRY` : mapping type → classe de connecteur

### 3. Couche Connecteurs

**Responsabilité** : Accès aux sources de données

**Classe de base** : `BaseConnector`
- Context manager (with)
- Méthodes abstraites : `connect()`, `disconnect()`

**Implémentations** :

#### OracleConnector
- Connexion read-only (refuse non-SELECT)
- Méthodes :
  - `query(sql, params)` → DataFrame
  - `execute_scalar(sql, params)` → valeur unique
  - `get_table_columns(table)` → liste colonnes
- Sécurité : validation requêtes, paramètres bindés

**Fichiers** :
- `connectors/base.py`
- `connectors/oracle_connector.py`

### 4. Couche Checks

**Responsabilité** : Validation des données

**Classe de base** : `BaseCheck`
- Méthode abstraite : `run(data) → CheckResult`
- Méthode utilitaire : `_create_result(...)`

**Implémentations** :

#### Volumétrie (`checks/volumetry.py`)
- **MinRowCountCheck** : Volumétrie minimale
- **BaselineComparisonCheck** : Comparaison à baseline historique

#### Qualité (`checks/quality.py`)
- **SchemaConformityCheck** : Présence colonnes obligatoires
- **DuplicateKeyCheck** : Doublons sur clé primaire
- **NullRateCheck** : Taux de nullité par champ

#### Distribution (`checks/distribution.py`)
- **HourlyDistributionCheck** : Distribution horaire vs baseline

**Fichiers** :
- `checks/base.py`
- `checks/volumetry.py`
- `checks/quality.py`
- `checks/distribution.py`

### 5. Couche Modèles

**Responsabilité** : Structures de données

#### CheckResult
```python
@dataclass
class CheckResult:
    name: str
    check_type: str
    status: CheckStatus        # Normal, Dégradé, Critique
    confidence: CheckConfidence # Direct, Déduit
    score: int                 # 0-10
    message: str
    details: dict
    timestamp: datetime
```

#### BreakpointResult
```python
@dataclass
class BreakpointResult:
    breakpoint_id: str
    breakpoint_name: str
    access_type: str
    target_date: str
    run_timestamp: datetime
    run_state: str            # in_progress, completed, failed
    status: BreakpointStatus  # Normal, Dégradé, Critique, En cours, Inconnu
    score: int                # 0-10
    checks: List[CheckResult]
```

**Fichiers** :
- `utils/models.py`

### 6. Couche Configuration

**Responsabilité** : Gestion de la configuration

#### ConfigLoader
- Charge config globale (`config/config.yaml`)
- Charge config par breakpoint (`breakpoints/*.yaml`)
- Substitution variables d'environnement (`${VAR}`)
- Validation structure YAML

**Fichiers** :
- `config/config_loader.py`
- `config/config.yaml`
- `breakpoints/*.yaml`

### 7. Couche Logging

**Responsabilité** : Persistance des résultats

#### CheckResultLogger
- Sauvegarde JSON (machine-readable)
- Sauvegarde TXT (human-readable)
- Historique des runs
- Rotation automatique

**Fichiers** :
- `utils/result_logger.py`

## Flux de données

### Exécution d'un breakpoint

```
1. main.py charge config globale
   ↓
2. main.py identifie les breakpoints à exécuter
   ↓
3. Pour chaque breakpoint :
   a. BreakpointRunner charge la config YAML
   b. BreakpointRunner instancie le connecteur
   c. BreakpointRunner récupère les données (via connecteur)
   d. BreakpointRunner calcule les baselines (si nécessaire)
   e. Pour chaque check configuré :
      - Instanciation du check
      - Préparation des données spécifiques
      - Exécution du check
      - Collecte du CheckResult
   f. BreakpointRunner agrège les résultats
   g. BreakpointRunner calcule le score global
   h. Retour du BreakpointResult
   ↓
4. main.py agrège tous les BreakpointResult
   ↓
5. main.py exporte les résultats (JSON, logs)
   ↓
6. main.py envoie notifications (si configuré)
```

## Système de scoring

### Score d'un check

Chaque check retourne un score de **0 à 10** :
- `10` = Normal (données conformes)
- `6-9` = Dégradé (écarts tolérables)
- `0-5` = Critique (écarts importants)

### Score d'un breakpoint

Le score d'un breakpoint est la **moyenne des scores de ses checks**.

**Exception** : Si un check marqué `force_zero_on_failure: true` échoue, le score du breakpoint est **forcé à 0**.

### Statut d'un breakpoint

| Score    | Statut     |
|----------|------------|
| 10/10    | Normal     |
| 6-9/10   | Dégradé    |
| ≤5/10    | Critique   |
| (running)| En cours   |
| (error)  | Inconnu    |

## Extensibilité

### Ajouter un nouveau connecteur

1. Créer une classe héritant de `BaseConnector`
2. Implémenter `connect()` et `disconnect()`
3. Ajouter les méthodes d'accès aux données
4. Enregistrer dans `CONNECTOR_REGISTRY`

### Ajouter un nouveau check

1. Créer une classe héritant de `BaseCheck`
2. Implémenter `run(data) → CheckResult`
3. Enregistrer dans `CHECK_REGISTRY`

### Ajouter un nouveau breakpoint

1. Créer un fichier YAML dans `breakpoints/`
2. Configurer connecteur, data_source, checks
3. Exécuter : `python main.py --breakpoint <id>`

## Sécurité

### Principe de moindre privilège

- Connecteurs read-only par défaut
- OracleConnector refuse INSERT/UPDATE/DELETE/DROP
- Validation de toutes les requêtes SQL

### Gestion des credentials

- Variables d'environnement (`.env`)
- Substitution YAML (`${VAR}`)
- `.env` dans `.gitignore` (jamais commité)

### Requêtes paramétrées

Tous les paramètres utilisateur sont bindés (protection injection SQL) :

```python
conn.query("SELECT * FROM table WHERE date = :date", params={"date": target_date})
```

## Performance

### Optimisations actuelles

- Requêtes SQL optimisées (indexes attendus côté DWH)
- Calcul de baselines avec `FETCH FIRST N ROWS`
- Utilisation de pandas pour manipulation mémoire

### Optimisations futures

- Parallélisation des checks (ThreadPoolExecutor)
- Cache des baselines (éviter recalcul multiple fois/jour)
- Exécution parallèle de breakpoints (multiprocessing)

## Monitoring du monitoring

### Logs

- Logs applicatifs : `logs/monitoring_YYYYMMDD.log`
- Résultats JSON : `logs/json/`
- Résultats TXT : `logs/text/`

### Métriques

- Score global (moyenne des breakpoints)
- Durée d'exécution par breakpoint
- Nombre de checks en échec
- Exit code (0 = OK, 1 = au moins un critique)

### Alertes

- Notifications email (si configuré)
- Notifications push/ntfy (si configuré)
- Exit code pour intégration CI/CD
