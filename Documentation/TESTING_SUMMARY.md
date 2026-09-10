# 🎯 Résumé du plan de test

## Vue d'ensemble en 7 phases

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Installation Oracle XE (1h)                       │
│  ├─ Docker: docker run oracle/express                       │
│  ├─ Créer utilisateurs: dwh_cti_test + monitoring_user      │
│  └─ Vérifier connexion                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Analyse des données (30min)                       │
│  ├─ Analyser extract_dwh_20241120.csv (147 MB)              │
│  ├─ Identifier colonnes (date, ID, critiques)               │
│  └─ Créer échantillons de test                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Import dans Oracle (1h)                           │
│  ├─ Créer table CDR_EVENTS (structure adaptée)              │
│  ├─ Importer données CSV → Oracle                           │
│  └─ Créer indexes (performance)                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: Configuration monitoring (15min)                  │
│  ├─ .env.test (credentials Oracle XE local)                 │
│  ├─ config_test.yaml (seuils permissifs)                    │
│  └─ bp_test_local.yaml (breakpoint test)                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Tests unitaires (30min)                           │
│  ├─ test_connection.py → Oracle                             │
│  ├─ test_checks.py → Chaque check individuellement          │
│  └─ Vérifier scoring et statuts                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 6: Tests d'intégration (30min)                       │
│  ├─ Run complet: python main.py --breakpoint bp_test_local  │
│  ├─ Tester plusieurs dates (J-1, J-2, J-3)                  │
│  └─ Analyser résultats (logs, JSON)                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 7: Validation finale (15min)                         │
│  ├─ Checklist de validation                                 │
│  ├─ run_validation.py (tests automatiques)                  │
│  └─ Rapport final (validation_report.json)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Démarrage rapide

### Option A : Docker (RECOMMANDÉ)

```powershell
# 1. Lancer Oracle XE
docker run -d --name oracle-xe -p 1521:1521 -e ORACLE_PWD=OracleTest123 container-registry.oracle.com/database/express:latest

# 2. Analyser les données
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
python test_utils\analyze_csv.py

# 3. Importer dans Oracle (après analyse)
# TODO: Adapter import selon structure détectée

# 4. Tester
python tests\test_connection.py
python main.py --breakpoint bp_test_local --config config\config_test.yaml
```

### Option B : Installation native

```powershell
# 1. Télécharger Oracle Database 21c XE
# https://www.oracle.com/database/technologies/xe-downloads.html

# 2. Installer (suivre assistant)

# 3. Créer utilisateurs (voir TESTING_PLAN.md Phase 1.3)

# 4. Suite identique à Option A
```

---

## 📊 Fichiers créés pour les tests

```
Code/
├── tests/                          # 🧪 Tests automatisés
│   ├── test_connection.py          # Test connexion Oracle
│   ├── test_checks.py              # Tests unitaires checks
│   ├── run_validation.py           # Validation complète
│   └── validation_checklist.md     # Checklist manuelle
│
├── test_utils/                     # 🛠️ Scripts utilitaires
│   ├── analyze_csv.py              # ✅ Analyse structure CSV
│   ├── create_test_sample.py       # Crée échantillons test
│   ├── import_to_oracle.py         # Import CSV → Oracle
│   ├── create_oracle_table.sql     # Création table
│   └── load_data.ctl               # SQL*Loader config
│
├── test_data/                      # 📁 Données de test
│   ├── test_data_20241120.csv      # (créé par create_test_sample)
│   └── ...
│
├── config/
│   ├── config_test.yaml            # Config test (seuils permissifs)
│   └── .env.test                   # Credentials Oracle XE local
│
├── breakpoints/
│   └── bp_test_local.yaml          # Breakpoint pour tests
│
├── logs_test/                      # 📊 Logs de test
│   ├── json/
│   └── text/
│
└── dashboard_data_test/            # 📈 Export JSON test
    └── latest.json
```

---

## ✅ Checklist avant de commencer

- [ ] Python 3.8+ installé
- [ ] Docker Desktop installé (ou Oracle XE natif prévu)
- [ ] Dépendances installées : `pip install -r requirements.txt`
- [ ] Fichier CSV disponible : `extract_dwh_20241120.csv` (147 MB)
- [ ] Espace disque : ~5 GB pour Oracle XE
- [ ] Port 1521 disponible

---

## 🎯 Objectifs de validation

### Tests fonctionnels

| Check | Test | Critère de succès |
|-------|------|-------------------|
| **MinRowCount** | Table avec 1000+ lignes | ✅ Status Normal si ≥ seuil |
| **Baseline** | 7 jours de données | ✅ Compare à moyenne historique |
| **Schema** | Colonnes obligatoires présentes | ✅ Détecte colonnes manquantes |
| **Duplicate** | Clé primaire unique | ✅ Détecte doublons |
| **NullRate** | Taux nullité < 2% | ✅ Calcul correct par colonne |
| **HourlyDistrib** | Distribution 24h | ✅ Compare à baseline horaire |

### Tests techniques

| Aspect | Test | Critère de succès |
|--------|------|-------------------|
| **Connexion** | OracleConnector | ✅ Connexion établie |
| **Sécurité** | Tentative UPDATE | ✅ Rejeté (read-only) |
| **Performance** | 50k lignes | ✅ < 1 minute |
| **Scoring** | Agrégation | ✅ Moyenne correcte |
| **Export** | JSON dashboard | ✅ Fichier créé + valide |
| **Logs** | Rotation | ✅ JSON + TXT créés |

---

## 📈 Métriques attendues

### Avec données réelles (extract_dwh_20241120.csv)

**Hypothèses** :
- ~2M lignes (147 MB CSV)
- Plusieurs jours de données
- Colonnes : CONN_ID, EVENT_DATE, EVENT_HOUR, CALLING_NUMBER, etc.

**Résultats attendus** :
- ✅ MinRowCount : **Normal** (>50k lignes par jour)
- ✅ Baseline : **Normal** (variance < 20%)
- ✅ Schema : **Normal** (colonnes présentes)
- ⚠️ Duplicate : **À vérifier** (qualité données)
- ⚠️ NullRate : **À vérifier** (selon extraction)
- ✅ HourlyDistrib : **Normal** (distribution régulière)

**Score global attendu** : **8-10/10** (si données de bonne qualité)

---

## 🐛 Problèmes anticipés et solutions

| Problème | Cause | Solution |
|----------|-------|----------|
| **Docker n'installe pas Oracle** | Pas de compte Oracle | S'inscrire sur container-registry.oracle.com |
| **CSV trop gros (RAM)** | 147 MB = beaucoup en RAM | Créer échantillon avec `create_test_sample.py` |
| **Colonnes incompatibles** | Structure CSV ≠ attente | Adapter `create_oracle_table.sql` après analyse |
| **Import très lent** | INSERT ligne par ligne | Utiliser SQL*Loader ou BATCH insert |
| **Baseline vide** | Pas assez de données | Réduire `baseline_days` à 3-5 |
| **Tous les checks échouent** | Seuils trop stricts | Utiliser `config_test.yaml` (permissif) |

---

## 📞 Support

### Commandes de dépannage

```powershell
# Vérifier Oracle est lancé
docker ps | Select-String oracle

# Voir les logs Oracle
docker logs oracle-xe

# Tester connexion SQL*Plus
docker exec -it oracle-xe sqlplus system/OracleTest123@XE

# Réinitialiser Oracle
docker stop oracle-xe
docker rm oracle-xe
# Relancer docker run...

# Analyser un CSV différent
python test_utils\analyze_csv.py "chemin\vers\autre.csv" 5000
```

### Documentation de référence

- **TESTING_PLAN.md** : Plan détaillé complet
- **README.md** : Documentation système
- **COMMANDS.md** : Toutes les commandes PowerShell
- **ARCHITECTURE.md** : Architecture technique

---

## 🎉 Succès attendu

À la fin des tests, vous aurez :

1. ✅ **Oracle XE fonctionnel** avec données réelles importées
2. ✅ **Tous les checks validés** avec vraies données CTI
3. ✅ **Scoring vérifié** (calcul correct)
4. ✅ **Logs et exports** générés et validés
5. ✅ **Rapport de validation** (validation_report.json)
6. ✅ **Système prêt** pour déploiement production

---

**Prêt ? Démarrez avec Phase 1 du TESTING_PLAN.md !** 🚀

**Temps estimé total : ~4 heures**
