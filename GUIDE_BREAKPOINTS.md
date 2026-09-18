# 📋 Guide : Créer et Modifier des Breakpoints

**Version** : 1.1.0  
**Date** : 2026-09-12

---

# Table des matières

1. [Qu'est-ce qu'un breakpoint ?](#1-quest-ce-quun-breakpoint-)
2. [Structure d'un breakpoint YAML](#2-structure-dun-breakpoint-yaml)
3. [Créer un nouveau breakpoint](#3-créer-un-nouveau-breakpoint)
4. [Modifier un breakpoint existant](#4-modifier-un-breakpoint-existant)
5. [Checks disponibles et leur configuration](#5-checks-disponibles-et-leur-configuration)
6. [Exemples complets](#6-exemples-complets)
7. [Bonnes pratiques](#7-bonnes-pratiques)
8. [Troubleshooting](#8-troubleshooting)

---

# 1. Qu'est-ce qu'un breakpoint ?

## 🎯 Définition

Un **breakpoint** est un point de surveillance qui définit :
- **Quelle source de données** surveiller (table Oracle, API, fichier, etc.)
- **Quelle requête** exécuter pour extraire les données
- **Quels checks** effectuer sur ces données
- **Quels seuils** appliquer pour chaque check

## 📂 Localisation

Tous les breakpoints sont stockés dans le répertoire :
```
breakpoints/
├── bp9_dwh_oracle.yaml          # Breakpoint production DWH Oracle
├── bp_mon_nouveau_bp.yaml       # Votre nouveau breakpoint
└── ...
```

## 🔄 Fonctionnement

```
Breakpoint YAML
    ↓
1. Extraction des données (query)
    ↓
2. Exécution des checks (schema, volumétrie, doublons, etc.)
    ↓
3. Calcul du score (/10)
    ↓
4. Notification (email si nécessaire)
```

---

# 2. Structure d'un breakpoint YAML

## 📝 Structure minimale

```yaml
# ==========================================
# Nom de votre breakpoint
# ==========================================

# ID unique (utilisé en interne)
id: bp_mon_bp

# Nom affiché dans les rapports
name: Mon Breakpoint

# Description
description: Surveillance de ma table/API

# Requête SQL ou logique d'extraction
query: |
  SELECT * FROM ma_table
  WHERE date_field = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')

# Liste des checks à exécuter
checks:
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 1000
```

## 🔑 Champs obligatoires

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `id` | string | Identifiant unique (sans espaces) | `bp_calls_table` |
| `name` | string | Nom affiché dans les emails/rapports | `Table des appels` |
| `description` | string | Description du breakpoint | `Surveillance quotidienne` |
| `query` | string (multi-lignes) | Requête SQL d'extraction | `SELECT * FROM ...` |
| `checks` | list | Liste des checks à exécuter | Voir section 5 |

## 🔧 Variables disponibles dans les requêtes

| Variable | Description | Exemple de valeur |
|----------|-------------|-------------------|
| `{TARGET_DATE}` | Date cible du monitoring | `2026-06-22` |
| `${DWH_TABLE_NAME}` | Nom de la table (depuis .env) | `CTI_SCHEMA.CALLS` |
| `${VAR}` | Toute variable définie dans .env | `os.getenv("VAR")` |

---

# 3. Créer un nouveau breakpoint

## 🚀 Méthode rapide : Dupliquer un breakpoint existant

### **Étape 1 : Copier un breakpoint existant**

```bash
# Windows
copy breakpoints\bp9_dwh_oracle.yaml breakpoints\bp_ma_nouvelle_table.yaml

# Linux/Mac
cp breakpoints/bp9_dwh_oracle.yaml breakpoints/bp_ma_nouvelle_table.yaml
```

### **Étape 2 : Éditer le nouveau fichier**

Ouvrir `breakpoints/bp_ma_nouvelle_table.yaml` et modifier :

```yaml
# ==========================================
# Breakpoint : Ma Nouvelle Table
# ==========================================

# 1. Changer l'ID (OBLIGATOIRE, doit être unique)
id: bp_ma_nouvelle_table

# 2. Changer le nom
name: Ma Nouvelle Table

# 3. Changer la description
description: Surveillance de la table MA_NOUVELLE_TABLE

# 4. Adapter la requête SQL
query: |
  SELECT 
    ID,
    DATE_FIELD,
    VALUE_FIELD,
    CATEGORY
  FROM MA_SCHEMA.MA_NOUVELLE_TABLE
  WHERE TRUNC(DATE_FIELD) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')
  ORDER BY DATE_FIELD

# 5. Adapter les checks (voir section 5)
checks:
  # Check 1 : Colonnes attendues
  - type: schema_conformity_check
    name: schema_conformity_check
    expected_columns:
      - ID
      - DATE_FIELD
      - VALUE_FIELD
      - CATEGORY
  
  # Check 2 : Volumétrie minimale
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 5000  # Adapter selon vos besoins
  
  # Check 3 : Doublons sur ID
  - type: duplicate_key_check
    name: duplicate_key_check
    key_columns:
      - ID
    max_duplicate_rate: 0.01  # 1% max
```

### **Étape 3 : Tester le nouveau breakpoint**

```bash
# Tester avec une date spécifique
python main.py --date 2026-06-22 --breakpoint bp_ma_nouvelle_table

# Vérifier les logs
cat logs/text/batch_*.txt
```

---

## 🛠️ Méthode détaillée : Créer from scratch

### **Template complet**

```yaml
# ==========================================
# Breakpoint : [NOM DE VOTRE BREAKPOINT]
# ==========================================

id: bp_[identifiant_unique_sans_espaces]
name: [Nom Affiché]
description: |
  Description détaillée de ce que surveille ce breakpoint.
  Peut être sur plusieurs lignes.

# ====== REQUÊTE SQL ======
query: |
  SELECT 
    colonne1,
    colonne2,
    colonne3
  FROM ${DWH_TABLE_NAME}  -- Variable d'environnement
  WHERE date_colonne = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')  -- Date du monitoring
  ORDER BY colonne1

# ====== CHECKS ======
checks:
  # Check 1 : Schéma conforme
  - type: schema_conformity_check
    name: schema_conformity_check
    expected_columns:
      - colonne1
      - colonne2
      - colonne3
  
  # Check 2 : Volumétrie minimale
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 1000  # À adapter selon vos besoins
    message: "Volumétrie insuffisante (attendu >= 1000 lignes)"
  
  # Check 3 : Comparaison baseline (optionnel)
  - type: baseline_comparison_check
    name: baseline_comparison_check
    baseline_query: |
      SELECT AVG(row_count) as avg_count
      FROM (
        SELECT COUNT(*) as row_count
        FROM ${DWH_TABLE_NAME}
        WHERE date_colonne > SYSDATE - 30
        GROUP BY TRUNC(date_colonne)
      )
    tolerance: 0.20  # ±20%
  
  # Check 4 : Doublons (si vous avez une clé primaire)
  - type: duplicate_key_check
    name: duplicate_key_check
    key_columns:
      - colonne1  # Clé primaire
    max_duplicate_rate: 0.01  # 1% max
  
  # Check 5 : Taux de valeurs nulles
  - type: null_rate_check
    name: null_rate_check
    critical_columns:
      - colonne1
      - colonne2
    max_null_rate: 0.02  # 2% max
  
  # Check 6 : Distribution horaire (si vous avez un champ datetime)
  - type: hourly_distribution_check
    name: hourly_distribution_check
    datetime_column: colonne_timestamp
    baseline_query: |
      SELECT 
        TO_CHAR(colonne_timestamp, 'HH24') as hour,
        AVG(pct) as avg_pct
      FROM (
        SELECT 
          TO_CHAR(colonne_timestamp, 'HH24') as hour,
          COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY TRUNC(colonne_timestamp)) as pct
        FROM ${DWH_TABLE_NAME}
        WHERE colonne_timestamp > SYSDATE - 30
        GROUP BY TO_CHAR(colonne_timestamp, 'HH24'), TRUNC(colonne_timestamp)
      )
      GROUP BY hour
      ORDER BY hour
    tolerance: 0.05  # ±5%
  
  # Check 7 : Détection d'outliers (optionnel)
  - type: outlier_detection_check
    name: outlier_detection_check
    numeric_columns:
      colonne_numerique1:
        method: iqr
        threshold: 1.5
      colonne_numerique2:
        method: zscore
        threshold: 3.0
    categorical_columns:
      colonne_categorielle:
        min_frequency: 3  # Catégories avec < 3 occurrences = outliers
    critical_outlier_threshold: 0.05  # 5% max
```

---

# 4. Modifier un breakpoint existant

## 📝 Modifications courantes

### **4.1 Changer le seuil de volumétrie**

**Avant** :
```yaml
- type: min_row_count_check
  name: min_row_count_check
  min_rows: 10000
```

**Après** :
```yaml
- type: min_row_count_check
  name: min_row_count_check
  min_rows: 15000  # Nouvelle valeur
```

### **4.2 Ajouter une colonne au schéma**

**Avant** :
```yaml
- type: schema_conformity_check
  name: schema_conformity_check
  expected_columns:
    - CONNID
    - STARTTIME
    - DURATION
```

**Après** :
```yaml
- type: schema_conformity_check
  name: schema_conformity_check
  expected_columns:
    - CONNID
    - STARTTIME
    - DURATION
    - NOUVELLE_COLONNE  # Ajoutée
```

### **4.3 Ajouter un nouveau check**

À la fin de la liste `checks:`, ajouter :

```yaml
checks:
  # ... checks existants ...
  
  # Nouveau check : Détection d'outliers
  - type: outlier_detection_check
    name: outlier_detection_check
    numeric_columns:
      DURATION:
        method: iqr
        threshold: 1.5
    critical_outlier_threshold: 0.05
```

### **4.4 Modifier la requête SQL**

**Avant** :
```yaml
query: |
  SELECT * FROM ${DWH_TABLE_NAME}
  WHERE TRUNC(STARTTIME) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')
```

**Après** (ajouter un filtre) :
```yaml
query: |
  SELECT * FROM ${DWH_TABLE_NAME}
  WHERE TRUNC(STARTTIME) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')
    AND STATUS = 'COMPLETED'  # Nouveau filtre
    AND DURATION > 0          # Nouveau filtre
```

### **4.5 Désactiver temporairement un check**

**Méthode 1 : Commenter**
```yaml
checks:
  # - type: duplicate_key_check
  #   name: duplicate_key_check
  #   key_columns:
  #     - CONNID
  #   max_duplicate_rate: 0.01
```

**Méthode 2 : Supprimer complètement** (recommandé si permanent)

---

# 5. Checks disponibles et leur configuration

## 📋 Liste complète des checks

### **5.1 schema_conformity_check**

**Objectif** : Vérifier que toutes les colonnes attendues sont présentes

**Configuration** :
```yaml
- type: schema_conformity_check
  name: schema_conformity_check
  expected_columns:
    - COLONNE1
    - COLONNE2
    - COLONNE3
```

**Résultat** :
- ✅ **success** : Toutes les colonnes présentes
- ❌ **failure** : Au moins une colonne manquante

---

### **5.2 min_row_count_check**

**Objectif** : Vérifier que le nombre de lignes est supérieur à un minimum

**Configuration** :
```yaml
- type: min_row_count_check
  name: min_row_count_check
  min_rows: 10000
  message: "Volumétrie insuffisante"  # Optionnel
```

**Résultat** :
- ✅ **success** : row_count >= min_rows
- ❌ **failure** : row_count < min_rows

**Comment déterminer min_rows ?** :
```bash
# Analyser l'historique sur 30 jours
python utils/analyze_baseline.py --metric row_count --days 30

# Utiliser : moyenne - 2*écart-type
```

---

### **5.3 baseline_comparison_check**

**Objectif** : Comparer la volumétrie actuelle avec la moyenne historique

**Configuration** :
```yaml
- type: baseline_comparison_check
  name: baseline_comparison_check
  baseline_query: |
    SELECT AVG(row_count) as avg_count
    FROM (
      SELECT COUNT(*) as row_count
      FROM ${DWH_TABLE_NAME}
      WHERE date_field > SYSDATE - 30
      GROUP BY TRUNC(date_field)
    )
  tolerance: 0.20  # ±20%
```

**Paramètres** :
- `baseline_query` : Requête pour calculer la moyenne historique
- `tolerance` : Tolérance d'écart (0.20 = ±20%)

**Résultat** :
- ✅ **success** : Écart < tolerance
- ⚠️ **warning** : tolerance < Écart < tolerance*2
- ❌ **failure** : Écart > tolerance*2

---

### **5.4 duplicate_key_check**

**Objectif** : Détecter les doublons sur une ou plusieurs colonnes clés

**Configuration** :
```yaml
- type: duplicate_key_check
  name: duplicate_key_check
  key_columns:
    - CONNID           # Clé primaire simple
  max_duplicate_rate: 0.01  # 1% max
```

**Configuration multi-colonnes** :
```yaml
- type: duplicate_key_check
  name: duplicate_key_check
  key_columns:
    - COLONNE1         # Clé primaire composite
    - COLONNE2
  max_duplicate_rate: 0.01
```

**Résultat** :
- ✅ **success** : duplicate_rate <= max_duplicate_rate
- ❌ **failure** : duplicate_rate > max_duplicate_rate

**Métriques extraites** :
- `duplicate_count` : Nombre de doublons
- `duplicate_rate` : Pourcentage

---

### **5.5 null_rate_check**

**Objectif** : Vérifier le taux de valeurs nulles sur colonnes critiques

**Configuration** :
```yaml
- type: null_rate_check
  name: null_rate_check
  critical_columns:
    - CONNID
    - STARTTIME
    - DURATION
  max_null_rate: 0.02  # 2% max
```

**Résultat** :
- ✅ **success** : Taux de nullité <= max_null_rate pour toutes les colonnes
- ❌ **failure** : Au moins une colonne dépasse le seuil

**Métriques extraites** :
- `null_rate_COLONNE` : Taux de nullité par colonne

---

### **5.6 hourly_distribution_check**

**Objectif** : Vérifier que la répartition horaire est conforme à la baseline

**Configuration** :
```yaml
- type: hourly_distribution_check
  name: hourly_distribution_check
  datetime_column: STARTTIME  # Colonne timestamp
  baseline_query: |
    SELECT 
      TO_CHAR(STARTTIME, 'HH24') as hour,
      AVG(pct) as avg_pct
    FROM (
      SELECT 
        TO_CHAR(STARTTIME, 'HH24') as hour,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY TRUNC(STARTTIME)) as pct
      FROM ${DWH_TABLE_NAME}
      WHERE STARTTIME > SYSDATE - 30
      GROUP BY TO_CHAR(STARTTIME, 'HH24'), TRUNC(STARTTIME)
    )
    GROUP BY hour
    ORDER BY hour
  tolerance: 0.05  # ±5%
```

**Résultat** :
- ✅ **success** : Distribution horaire dans la tolérance
- ❌ **failure** : Au moins une heure avec écart > tolerance

---

### **5.7 outlier_detection_check** 🆕 **v1.1**

**Objectif** : Détecter les valeurs aberrantes statistiquement

#### **Configuration colonnes numériques** :

```yaml
- type: outlier_detection_check
  name: outlier_detection_check
  numeric_columns:
    DURATION:
      method: iqr       # IQR (Interquartile Range)
      threshold: 1.5    # Multiplicateur IQR
    RINGDURATION:
      method: zscore    # Z-Score
      threshold: 3.0    # Seuil Z-Score
  critical_outlier_threshold: 0.05  # 5% max
```

**Méthodes disponibles** :
- **`iqr`** (Interquartile Range) : Outliers = valeurs en dehors de [Q1 - threshold*IQR, Q3 + threshold*IQR]
- **`zscore`** : Outliers = valeurs avec |Z-Score| > threshold

#### **Configuration colonnes catégorielles** :

```yaml
- type: outlier_detection_check
  name: outlier_detection_check
  categorical_columns:
    ORIGDNIS:
      min_frequency: 3  # Catégories < 3 occurrences = outliers
    DESTDNIS:
      min_frequency: 5
  critical_outlier_threshold: 0.05
```

#### **Configuration mixte** :

```yaml
- type: outlier_detection_check
  name: outlier_detection_check
  numeric_columns:
    DURATION:
      method: iqr
      threshold: 1.5
  categorical_columns:
    ORIGDNIS:
      min_frequency: 3
  critical_outlier_threshold: 0.05  # 5% max
```

**Résultat** :
- ✅ **success** : outlier_percent <= critical_outlier_threshold
- ⚠️ **warning** : critical < outlier_percent <= critical*2
- ❌ **failure** : outlier_percent > critical*2

**Métriques extraites** :
- `outlier_count` : Nombre d'outliers
- `outlier_percent` : Pourcentage
- `outlier_columns` : Liste des colonnes avec outliers

**Comment déterminer les seuils ?** :
```bash
# Analyser la distribution d'une colonne
python utils/analyze_baseline.py --metric DURATION --days 30

# Résultat suggère :
# - IQR threshold: 1.5 (standard) ou 3.0 (plus permissif)
# - Z-Score threshold: 3.0 (standard) ou 4.0 (plus permissif)
```

---

# 6. Exemples complets

## 🎯 Exemple 1 : Breakpoint simple (volumétrie only)

**Cas d'usage** : Surveiller une petite table, juste vérifier qu'il y a des données

```yaml
# ==========================================
# Breakpoint : Table des utilisateurs
# ==========================================

id: bp_users_table
name: Table Utilisateurs
description: Surveillance simple de la table USERS

query: |
  SELECT * FROM MY_SCHEMA.USERS
  WHERE TRUNC(CREATED_DATE) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')

checks:
  # Vérifier qu'il y a au moins 100 utilisateurs créés par jour
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 100
    message: "Moins de 100 utilisateurs créés aujourd'hui"
```

---

## 🎯 Exemple 2 : Breakpoint complet (tous les checks)

**Cas d'usage** : Table critique en production, surveillance maximale

```yaml
# ==========================================
# Breakpoint : Transactions bancaires
# ==========================================

id: bp_bank_transactions
name: Transactions Bancaires
description: Surveillance complète de la table TRANSACTIONS

query: |
  SELECT 
    TRANSACTION_ID,
    TRANSACTION_DATE,
    AMOUNT,
    CURRENCY,
    ACCOUNT_ID,
    STATUS
  FROM BANK_SCHEMA.TRANSACTIONS
  WHERE TRUNC(TRANSACTION_DATE) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')
  ORDER BY TRANSACTION_DATE

checks:
  # Check 1 : Schéma conforme
  - type: schema_conformity_check
    name: schema_conformity_check
    expected_columns:
      - TRANSACTION_ID
      - TRANSACTION_DATE
      - AMOUNT
      - CURRENCY
      - ACCOUNT_ID
      - STATUS
  
  # Check 2 : Volumétrie minimale (au moins 10000 transactions/jour)
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 10000
    message: "Volumétrie anormalement basse (< 10000)"
  
  # Check 3 : Comparaison baseline (±20% de la moyenne sur 30 jours)
  - type: baseline_comparison_check
    name: baseline_comparison_check
    baseline_query: |
      SELECT AVG(daily_count) as avg_count
      FROM (
        SELECT COUNT(*) as daily_count
        FROM BANK_SCHEMA.TRANSACTIONS
        WHERE TRANSACTION_DATE > SYSDATE - 30
        GROUP BY TRUNC(TRANSACTION_DATE)
      )
    tolerance: 0.20
  
  # Check 4 : Doublons sur TRANSACTION_ID (0% toléré)
  - type: duplicate_key_check
    name: duplicate_key_check
    key_columns:
      - TRANSACTION_ID
    max_duplicate_rate: 0.0
  
  # Check 5 : Valeurs nulles sur colonnes critiques (max 1%)
  - type: null_rate_check
    name: null_rate_check
    critical_columns:
      - TRANSACTION_ID
      - TRANSACTION_DATE
      - AMOUNT
      - ACCOUNT_ID
    max_null_rate: 0.01
  
  # Check 6 : Distribution horaire (±5% de la baseline)
  - type: hourly_distribution_check
    name: hourly_distribution_check
    datetime_column: TRANSACTION_DATE
    baseline_query: |
      SELECT 
        TO_CHAR(TRANSACTION_DATE, 'HH24') as hour,
        AVG(pct) as avg_pct
      FROM (
        SELECT 
          TO_CHAR(TRANSACTION_DATE, 'HH24') as hour,
          COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY TRUNC(TRANSACTION_DATE)) as pct
        FROM BANK_SCHEMA.TRANSACTIONS
        WHERE TRANSACTION_DATE > SYSDATE - 30
        GROUP BY TO_CHAR(TRANSACTION_DATE, 'HH24'), TRUNC(TRANSACTION_DATE)
      )
      GROUP BY hour
    tolerance: 0.05
  
  # Check 7 : Outliers sur AMOUNT (IQR) et CURRENCY (fréquence)
  - type: outlier_detection_check
    name: outlier_detection_check
    numeric_columns:
      AMOUNT:
        method: iqr
        threshold: 3.0  # Plus permissif (transactions peuvent varier)
    categorical_columns:
      CURRENCY:
        min_frequency: 10  # Devises rares = outliers
    critical_outlier_threshold: 0.02  # 2% max
```

---

## 🎯 Exemple 3 : Breakpoint avec données API (non-Oracle)

**Cas d'usage** : Surveiller une API REST au lieu d'une DB

```yaml
# ==========================================
# Breakpoint : API Externe
# ==========================================

id: bp_external_api
name: API Externe - Données Clients
description: Surveillance de l'API externe /api/customers

# Note : Nécessite un connecteur API (à développer)
# Pour l'instant, on peut utiliser une table miroir
query: |
  SELECT 
    customer_id,
    sync_date,
    status,
    data_payload
  FROM API_MIRROR.CUSTOMERS
  WHERE TRUNC(sync_date) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')

checks:
  # Vérifier qu'on a reçu des données
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 500
    message: "API n'a pas retourné assez de données"
  
  # Vérifier qu'il n'y a pas trop d'erreurs (status != 'OK')
  # Note : Nécessite un check custom (à développer)
```

---

# 7. Bonnes pratiques

## ✅ Recommandations

### **7.1 Nommage**

```yaml
# ❌ Mauvais
id: bp1
name: BP1

# ✅ Bon
id: bp_dwh_calls_table
name: Datawarehouse - Table des Appels
```

### **7.2 Documentation**

```yaml
# ✅ Toujours ajouter une description claire
description: |
  Surveille la table CTI_SCHEMA.CALLS dans le datawarehouse Oracle.
  Vérifie :
  - Volumétrie quotidienne (attendu : 10000-20000 lignes)
  - Intégrité (doublons, nulls)
  - Outliers sur DURATION et RINGDURATION
  
  Contact : data-team@company.com
  Criticité : HAUTE
```

### **7.3 Ordre des checks**

```yaml
# Ordre recommandé :
checks:
  - schema_conformity_check      # 1. Schéma (rapide, bloquant)
  - min_row_count_check          # 2. Volumétrie (rapide)
  - baseline_comparison_check    # 3. Baseline (requête DB)
  - duplicate_key_check          # 4. Doublons (calcul)
  - null_rate_check              # 5. Nulls (calcul)
  - hourly_distribution_check    # 6. Distribution (requête DB)
  - outlier_detection_check      # 7. Outliers (calcul intensif)
```

### **7.4 Seuils progressifs**

```yaml
# Démarrer avec des seuils permissifs, puis affiner
- type: min_row_count_check
  min_rows: 5000  # Phase 1 : Seuil large
  # Après 1 semaine d'observation → ajuster à 8000
  # Après 1 mois → ajuster à 10000 (baseline stabilisée)
```

### **7.5 Commentaires**

```yaml
checks:
  # Volumétrie : Moyenne historique = 15000 lignes/jour (écart-type: 1200)
  # Seuil choisi : 10000 (mean - 4*std) pour éviter faux positifs
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 10000
```

### **7.6 Versionning**

```yaml
# Ajouter un historique des modifications en commentaire
# ==========================================
# Breakpoint : Datawarehouse Oracle
# 
# Changelog :
# - 2026-09-12 : Ajout outlier_detection_check (check #7)
# - 2026-08-15 : Augmentation min_rows de 8000 à 10000
# - 2026-07-01 : Création initiale
# ==========================================
```

---

## ⚠️ Pièges à éviter

### **❌ Ne pas faire**

```yaml
# 1. ID avec espaces ou caractères spéciaux
id: mon breakpoint 2024  # ❌ Espaces
id: bp_données_été        # ❌ Accents

# 2. Requêtes sans filtre sur la date
query: SELECT * FROM table  # ❌ Va extraire TOUTES les données

# 3. Seuils trop stricts
min_rows: 14999  # ❌ Moindre variation = échec

# 4. Checks redondants
- type: min_row_count_check
  min_rows: 10000
- type: min_row_count_check  # ❌ Doublon inutile
  min_rows: 9000
```

### **✅ Faire**

```yaml
# 1. ID sans espaces, en snake_case
id: bp_mon_bp_2024
id: bp_donnees_ete

# 2. Toujours filtrer sur {TARGET_DATE}
query: |
  SELECT * FROM table
  WHERE TRUNC(date_field) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')

# 3. Seuils réalistes avec marge
min_rows: 8000  # Moyenne - 2*std (laisse de la marge)

# 4. Un seul check par type
- type: min_row_count_check
  min_rows: 8000
```

---

# 8. Troubleshooting

## 🔧 Problèmes courants

### **Problème 1 : "Breakpoint not found"**

**Erreur** :
```
KeyError: 'bp_mon_bp'
```

**Cause** : ID breakpoint incorrect dans la commande `--breakpoint`

**Solution** :
```bash
# Lister tous les breakpoints disponibles
ls breakpoints/*.yaml

# Vérifier l'ID dans le fichier YAML
grep "^id:" breakpoints/bp_mon_bp.yaml

# Utiliser le bon ID
python main.py --breakpoint bp_mon_bp  # Sans .yaml
```

---

### **Problème 2 : "Invalid YAML syntax"**

**Erreur** :
```
yaml.scanner.ScannerError: while scanning a simple key
```

**Cause** : Erreur de syntaxe YAML (indentation, caractères spéciaux)

**Solution** :
```bash
# Valider la syntaxe YAML en ligne
# https://www.yamllint.com/

# Vérifier l'indentation (2 espaces par niveau)
checks:
  - type: min_row_count_check  # 2 espaces
    name: min_row_count_check  # 4 espaces
    min_rows: 1000             # 4 espaces
```

---

### **Problème 3 : "Query returned 0 rows"**

**Erreur** :
```
[DATA] 0 lignes extraites
[ÉCHEC] min_row_count_check : failure
```

**Causes possibles** :
1. Date cible incorrecte
2. Variable `${DWH_TABLE_NAME}` mal définie
3. Filtre WHERE trop restrictif
4. Données absentes pour cette date

**Solution** :
```bash
# 1. Vérifier la date
python main.py --date 2026-06-22  # Format YYYY-MM-DD

# 2. Vérifier les variables d'environnement
python check_env.py

# 3. Tester la requête manuellement dans SQL Developer
SELECT * FROM CTI_SCHEMA.CALLS
WHERE TRUNC(STARTTIME) = TO_DATE('2026-06-22', 'YYYY-MM-DD')

# 4. Vérifier si des données existent pour cette date
SELECT COUNT(*) FROM CTI_SCHEMA.CALLS
WHERE TRUNC(STARTTIME) = TO_DATE('2026-06-22', 'YYYY-MM-DD')
```

---

### **Problème 4 : "Column not found in DataFrame"**

**Erreur** :
```
KeyError: 'CONNID'
```

**Cause** : Colonne référencée dans un check n'existe pas dans les données extraites

**Solution** :
```yaml
# 1. Vérifier que la colonne est dans la requête
query: |
  SELECT 
    CONNID,  # ✅ Colonne présente
    STARTTIME
  FROM ...

# 2. Vérifier le nom exact (sensible à la casse en Python)
checks:
  - type: duplicate_key_check
    key_columns:
      - CONNID  # Doit correspondre EXACTEMENT au nom de la colonne
```

---

### **Problème 5 : "Check always fails"**

**Erreur** :
```
[ÉCHEC] duplicate_key_check : failure (285 doublons)
```

**Cause** : Seuil trop strict ou données réellement problématiques

**Solution** :
```bash
# 1. Analyser la baseline
python utils/analyze_baseline.py --metric duplicate_count --days 30

# Résultat :
# Moyenne : 250 doublons/jour
# Recommandation : max_duplicate_rate = 0.02 (2%)

# 2. Ajuster le seuil dans le breakpoint
- type: duplicate_key_check
  max_duplicate_rate: 0.02  # Augmenté de 0.01 à 0.02
```

---

## 🎓 Exercices pratiques

### **Exercice 1 : Créer un breakpoint simple**

**Objectif** : Surveiller une table `USERS` avec juste un check de volumétrie

**Solution** :
```yaml
id: bp_users
name: Table Utilisateurs
description: Surveillance de la table USERS

query: |
  SELECT * FROM MY_SCHEMA.USERS
  WHERE TRUNC(CREATED_DATE) = TO_DATE('{TARGET_DATE}', 'YYYY-MM-DD')

checks:
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 50
```

**Test** :
```bash
python main.py --date 2026-09-12 --breakpoint bp_users
```

---

### **Exercice 2 : Ajouter un check de doublons**

**Objectif** : Ajouter la détection de doublons sur `USER_ID`

**Solution** :
```yaml
checks:
  - type: min_row_count_check
    name: min_row_count_check
    min_rows: 50
  
  # Nouveau check
  - type: duplicate_key_check
    name: duplicate_key_check
    key_columns:
      - USER_ID
    max_duplicate_rate: 0.01
```

---

### **Exercice 3 : Modifier un seuil**

**Objectif** : Passer `min_rows` de 50 à 100

**Solution** :
```yaml
- type: min_row_count_check
  name: min_row_count_check
  min_rows: 100  # Modifié
```

---

## 📚 Ressources

- **Documentation complète** : `DOCUMENTATION_COMPLETE.md`
- **Exemple de référence** : `breakpoints/bp9_dwh_oracle.yaml`
- **Validation YAML** : https://www.yamllint.com/
- **Regex tester** : https://regex101.com/ (pour les requêtes complexes)

---

## 🆘 Support

Pour toute question ou problème :
1. Consulter `DOCUMENTATION_COMPLETE.md` section 11 (Troubleshooting)
2. Analyser les logs : `logs/text/batch_*.txt`
3. Tester la requête SQL manuellement dans SQL Developer
4. Contacter l'équipe : data-team@company.com

---

**Fin du guide**  
**Version** : 1.1.0  
**Dernière mise à jour** : 2026-09-12
