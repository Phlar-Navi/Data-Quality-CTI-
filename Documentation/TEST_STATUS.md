# 📊 État des tests - Monitoring CTI

**Dernière mise à jour** : 2026-09-10

---

## ✅ Phase 1 : Installation Oracle XE - TERMINÉE

### Configuration Oracle

| Élément | Valeur | Statut |
|---------|--------|--------|
| **Version** | Oracle Database 21c Express Edition | ✅ Installé |
| **Services** | OracleServiceXE, TNSListener | ✅ Running |
| **IP/Port** | 172.16.16.169:1521 | ✅ Accessible |
| **CDB** | XE | ✅ Opérationnel |
| **PDB** | XEPDB1 | ✅ Opérationnel |

### Utilisateurs créés

| Utilisateur | Mot de passe | Rôle | Statut |
|-------------|--------------|------|--------|
| **dwh_cti_test** | DwhTest123 | Propriétaire données | ✅ Créé |
| **monitoring_user** | MonitorTest123 | Read-only | ✅ Créé |

### Connexion

```python
# ✅ Connexion SYSTEM (admin)
conn = oracledb.connect(user='system', password='Oratoria_7', dsn='172.16.16.169:1521/XEPDB1')

# ✅ Connexion dwh_cti_test (propriétaire)
conn = oracledb.connect(user='dwh_cti_test', password='DwhTest123', dsn='172.16.16.169:1521/XEPDB1')

# ✅ Connexion monitoring_user (read-only)
conn = oracledb.connect(user='monitoring_user', password='MonitorTest123', dsn='172.16.16.169:1521/XEPDB1')
```

### Fichiers créés

- ✅ `test_conn.py` - Script de test de connexion
- ✅ `.env.test` - Configuration credentials test
- ✅ `test_utils/create_users.py` - Script création utilisateurs
- ✅ `ORACLE_SOLUTION.md` - Documentation solution
- ✅ `ORACLE_TROUBLESHOOTING.md` - Guide dépannage

---

## ⏳ Phase 2 : Analyse des données - EN COURS

### Données disponibles

| Fichier | Taille | Lignes estimées | Statut |
|---------|--------|-----------------|--------|
| **extract_dwh_20241120.csv** | 147 MB | ~2M+ | ⏳ À analyser |

### Prochaine étape

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
python test_utils\analyze_csv.py
```

**Objectif** : Identifier la structure des colonnes pour créer la table Oracle.

---

## 📋 Phase 3 : Import données - À FAIRE

**Dépend de** : Phase 2 (structure des colonnes)

### Étapes prévues

1. ⏳ Créer la table `CDR_EVENTS` selon structure détectée
2. ⏳ Créer les index (EVENT_DATE, etc.)
3. ⏳ Importer le CSV dans Oracle
4. ⏳ Donner les droits SELECT à monitoring_user
5. ⏳ Vérifier les données importées

---

## 📋 Phase 4 : Configuration monitoring - À FAIRE

### Fichiers à créer

- ⏳ `config/config_test.yaml` - Config globale test
- ⏳ `breakpoints/bp_test_local.yaml` - Breakpoint test

### Configuration

```yaml
# bp_test_local.yaml
id: bp_test_local
name: "Test Local - Oracle XE"

connector:
  type: oracle
  params:
    dsn: ${DWH_DSN}  # 172.16.16.169:1521/XEPDB1
    user: ${DWH_READONLY_USER}
    password: ${DWH_READONLY_PASSWORD}

data_source:
  table: ${DWH_TABLE_NAME}
  date_column: EVENT_DATE  # À adapter selon CSV

# ... checks configurés
```

---

## 📋 Phase 5-7 : Tests - À FAIRE

- ⏳ Tests unitaires (checks individuels)
- ⏳ Tests d'intégration (run complet)
- ⏳ Validation finale

---

## 🎯 Résumé

| Phase | Statut | Durée estimée restante |
|-------|--------|------------------------|
| 1. Installation Oracle | ✅ TERMINÉ | - |
| 2. Analyse données | ⏳ EN COURS | 5 min |
| 3. Import données | ⏳ À FAIRE | 1h |
| 4. Config monitoring | ⏳ À FAIRE | 15 min |
| 5. Tests unitaires | ⏳ À FAIRE | 30 min |
| 6. Tests intégration | ⏳ À FAIRE | 30 min |
| 7. Validation | ⏳ À FAIRE | 15 min |

**Temps restant estimé** : ~2h30

---

## 🚀 Prochaines commandes à exécuter

```powershell
# 1. Analyser le CSV
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
python test_utils\analyze_csv.py

# 2. Après analyse, créer la table Oracle
# (adapter selon colonnes détectées)

# 3. Importer les données
# python test_utils\import_to_oracle.py

# 4. Tester le monitoring
# python main.py --breakpoint bp_test_local --config config\config_test.yaml
```

---

## 📞 Support

### Problème résolu : Connexion Oracle

**Erreur** : `ConnectionRefusedError: [WinError 10061]`

**Cause** : Oracle écoute sur l'IP locale (172.16.16.169) et non localhost

**Solution** : Utiliser `172.16.16.169:1521/XEPDB1` dans le DSN

**Documentation** : Voir `ORACLE_SOLUTION.md`

---

## ✅ Checklist de progression

### Installation & Configuration
- [x] Oracle Database installé
- [x] Services démarrés
- [x] Port 1521 accessible
- [x] Connexion Python réussie
- [x] Utilisateurs créés
- [x] .env.test créé
- [x] Scripts de test créés

### Données
- [ ] CSV analysé (structure identifiée)
- [ ] Table Oracle créée
- [ ] Données importées
- [ ] Index créés
- [ ] Droits SELECT accordés

### Monitoring
- [ ] config_test.yaml créé
- [ ] bp_test_local.yaml créé
- [ ] test_connection.py OK
- [ ] test_checks.py OK
- [ ] Run complet réussi
- [ ] Score ≥7/10
- [ ] Logs créés
- [ ] Dashboard JSON valide

---

**Statut actuel** : ✅ Phase 1 terminée, Phase 2 prête à démarrer

**Prochaine action** : Analyser le CSV avec `python test_utils\analyze_csv.py`
