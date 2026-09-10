# 📚 Index de la documentation - Monitoring CTI

Guide pour naviguer dans toute la documentation du projet.

---

## 🚀 Par où commencer ?

### Vous êtes... 👤

#### **Nouveau sur le projet** → **[QUICKSTART.md](QUICKSTART.md)** ⚡
Démarrage en 5 minutes avec installation, premier run, et interprétation résultats.

#### **Prêt à tester** → **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** 🧪
Guide une page pour tests avec Oracle XE local (30 min).

#### **Chef de projet / Product Owner** → **[PROJECT_STATUS.md](PROJECT_STATUS.md)** 📊
État d'avancement, livrables, métriques, prochaines étapes.

#### **Développeur** → **[README.md](README.md)** 📖
Documentation technique complète (architecture, installation, usage).

#### **Architecte** → **[ARCHITECTURE.md](ARCHITECTURE.md)** 🏗️
Architecture détaillée (couches, flux, extensibilité, sécurité).

#### **Ops / DevOps** → **[COMMANDS.md](COMMANDS.md)** 💻
Référence complète des commandes PowerShell.

#### **QA / Testeur** → **[TESTING_PLAN.md](TESTING_PLAN.md)** ✅
Plan de test détaillé en 7 phases (4h).

---

## 📚 Documentation par catégorie

### 🎯 Démarrage rapide

| Fichier | Description | Temps lecture | Audience |
|---------|-------------|---------------|----------|
| **[QUICKSTART.md](QUICKSTART.md)** | Guide démarrage 5 min | 5 min | Tous |
| **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** | Tests en 30 min | 10 min | Développeurs, QA |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | État projet | 5 min | Management |

### 📖 Documentation technique

| Fichier | Description | Temps lecture | Audience |
|---------|-------------|---------------|----------|
| **[README.md](README.md)** | Doc complète système | 20 min | Développeurs |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Architecture technique | 15 min | Architectes, Dev senior |
| **[FILES_SUMMARY.md](FILES_SUMMARY.md)** | Récapitulatif fichiers | 10 min | Développeurs |

### 💻 Guides opérationnels

| Fichier | Description | Temps lecture | Audience |
|---------|-------------|---------------|----------|
| **[COMMANDS.md](COMMANDS.md)** | Commandes PowerShell | 15 min | Ops, DevOps |
| **[check_env.py](check_env.py)** | Script vérification env | - | Tous |

### 🧪 Tests et validation

| Fichier | Description | Temps lecture | Audience |
|---------|-------------|---------------|----------|
| **[TESTING_PLAN.md](TESTING_PLAN.md)** | Plan test détaillé 7 phases | 30 min | QA, Développeurs |
| **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** | Résumé tests + checklist | 10 min | QA |
| **[test_utils/analyze_csv.py](test_utils/analyze_csv.py)** | Script analyse CSV | - | Développeurs |

---

## 🗺️ Parcours recommandés

### 🎓 Parcours "Découverte" (30 min)

1. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** (5 min)
   → Comprendre l'état global

2. **[QUICKSTART.md](QUICKSTART.md)** (10 min)
   → Installation et premier run

3. **[README.md](README.md)** - Sections : Architecture, Utilisation (15 min)
   → Comprendre le fonctionnement

### 🔧 Parcours "Développeur" (1h30)

1. **[README.md](README.md)** (20 min)
   → Documentation complète

2. **[ARCHITECTURE.md](ARCHITECTURE.md)** (20 min)
   → Architecture technique

3. **[FILES_SUMMARY.md](FILES_SUMMARY.md)** (15 min)
   → Structure du code

4. **[COMMANDS.md](COMMANDS.md)** (15 min)
   → Commandes utiles

5. **Lire le code** (20 min)
   → `main.py`, `breakpoint_runner.py`, checks

### 🧪 Parcours "QA / Tests" (2h)

1. **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** (10 min)
   → Vue d'ensemble tests

2. **[TESTING_PLAN.md](TESTING_PLAN.md)** (30 min)
   → Plan détaillé

3. **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** (10 min)
   → Guide pratique

4. **Exécuter les tests** (1h10)
   → Suivre TESTING_PLAN.md

### 🚀 Parcours "Déploiement" (1h)

1. **[README.md](README.md)** - Sections : Installation, Configuration (15 min)
   
2. **[COMMANDS.md](COMMANDS.md)** - Sections : Automatisation (15 min)
   
3. **[check_env.py](check_env.py)** (5 min)
   → Vérifier environnement production
   
4. **Configuration production** (25 min)
   → Créer .env, ajuster config.yaml, tester

---

## 📊 Documentation par besoin

### "J'ai besoin de..."

#### **...installer le système** 
→ **[README.md](README.md)** Section "Installation"  
→ **[QUICKSTART.md](QUICKSTART.md)** Étapes 1-3

#### **...comprendre l'architecture**
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** Sections "Vue d'ensemble", "Couches"

#### **...ajouter un nouveau check**
→ **[README.md](README.md)** Section "Ajouter un nouveau check"  
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** Section "Extensibilité"

#### **...ajouter un nouveau breakpoint**
→ **[README.md](README.md)** Section "Ajouter un nouveau breakpoint"  
→ Copier `breakpoints/bp9_dwh_oracle.yaml`

#### **...tester le système**
→ **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** (tests rapides)  
→ **[TESTING_PLAN.md](TESTING_PLAN.md)** (tests complets)

#### **...comprendre les commandes**
→ **[COMMANDS.md](COMMANDS.md)**  
→ **[README.md](README.md)** Section "Utilisation"

#### **...automatiser l'exécution**
→ **[COMMANDS.md](COMMANDS.md)** Section "Automatisation"  
→ **[QUICKSTART.md](QUICKSTART.md)** Section "Automatisation"

#### **...interpréter les résultats**
→ **[QUICKSTART.md](QUICKSTART.md)** Section "Comprendre les résultats"  
→ **[README.md](README.md)** Section "Système de scoring"

#### **...dépanner un problème**
→ **[README.md](README.md)** Section "Dépannage"  
→ **[COMMANDS.md](COMMANDS.md)** Section "Dépannage"  
→ **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** Section "Dépannage express"

#### **...voir l'état d'avancement**
→ **[PROJECT_STATUS.md](PROJECT_STATUS.md)**

---

## 🔍 Documentation par composant

### Connecteurs

| Composant | Code | Documentation |
|-----------|------|---------------|
| BaseConnector | `connectors/base.py` | [README.md](README.md#connecteurs) |
| OracleConnector | `connectors/oracle_connector.py` | [ARCHITECTURE.md](ARCHITECTURE.md#couche-connecteurs) |

### Checks

| Composant | Code | Documentation |
|-----------|------|---------------|
| MinRowCount | `checks/volumetry.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#volumetrypy) |
| Baseline | `checks/volumetry.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#volumetrypy) |
| Schema | `checks/quality.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#qualitypy) |
| Duplicate | `checks/quality.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#qualitypy) |
| NullRate | `checks/quality.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#qualitypy) |
| HourlyDistrib | `checks/distribution.py` | [FILES_SUMMARY.md](FILES_SUMMARY.md#distributionpy) |

### Configuration

| Composant | Fichier | Documentation |
|-----------|---------|---------------|
| Config globale | `config/config.yaml` | [README.md](README.md#configuration-globale) |
| Config breakpoint | `breakpoints/*.yaml` | [README.md](README.md#configuration-par-breakpoint) |
| ConfigLoader | `config/config_loader.py` | [ARCHITECTURE.md](ARCHITECTURE.md#couche-configuration) |

### Utilitaires

| Composant | Code | Documentation |
|-----------|------|---------------|
| Models | `utils/models.py` | [ARCHITECTURE.md](ARCHITECTURE.md#couche-modèles) |
| BreakpointRunner | `utils/breakpoint_runner.py` | [ARCHITECTURE.md](ARCHITECTURE.md#couche-orchestration) |
| CheckResultLogger | `utils/result_logger.py` | [ARCHITECTURE.md](ARCHITECTURE.md#couche-logging) |

---

## 📏 Niveaux de documentation

### 🟢 Niveau 1 : Essentiel (tout le monde)

- ✅ [QUICKSTART.md](QUICKSTART.md)
- ✅ [PROJECT_STATUS.md](PROJECT_STATUS.md)
- ✅ [README.md](README.md) (sections : Installation, Utilisation)

**Temps total** : ~30 minutes

### 🟡 Niveau 2 : Avancé (développeurs, ops)

- ✅ [README.md](README.md) (complet)
- ✅ [ARCHITECTURE.md](ARCHITECTURE.md)
- ✅ [COMMANDS.md](COMMANDS.md)
- ✅ [FILES_SUMMARY.md](FILES_SUMMARY.md)

**Temps total** : ~1h30

### 🔴 Niveau 3 : Expert (architectes, QA)

- ✅ Tout le niveau 2
- ✅ [TESTING_PLAN.md](TESTING_PLAN.md)
- ✅ [TESTING_SUMMARY.md](TESTING_SUMMARY.md)
- ✅ Lecture du code source

**Temps total** : ~3h

---

## 📝 Checklist lecture

### Pour démarrer (cochez au fur et à mesure)

- [ ] Lu [PROJECT_STATUS.md](PROJECT_STATUS.md) → État global compris
- [ ] Lu [QUICKSTART.md](QUICKSTART.md) → Installation comprise
- [ ] Exécuté `python check_env.py` → Environnement validé
- [ ] Lu [README.md](README.md) sections Installation/Utilisation
- [ ] Premier run réussi : `python main.py --help`

### Pour développer

- [ ] Lu [ARCHITECTURE.md](ARCHITECTURE.md) → Architecture comprise
- [ ] Lu [FILES_SUMMARY.md](FILES_SUMMARY.md) → Structure connue
- [ ] Parcouru le code : `main.py`, `breakpoint_runner.py`
- [ ] Lu [COMMANDS.md](COMMANDS.md) → Commandes maîtrisées
- [ ] Testé ajout d'un check/breakpoint

### Pour tester

- [ ] Lu [TESTING_SUMMARY.md](TESTING_SUMMARY.md) → Vue d'ensemble
- [ ] Lu [TESTING_PLAN.md](TESTING_PLAN.md) → Plan détaillé
- [ ] Lu [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) → Guide pratique
- [ ] Oracle XE installé et opérationnel
- [ ] Tous les tests passés avec succès

---

## 🔗 Liens rapides

### Documentation métier (hors Code/)

- **Plan de monitoring** : `../Documentation/Plan_de_Monitoring_DWH.md`
- **KPI et Dashboard** : `../Documentation/Recapitulatif_KPI_et_Dashboard.md`
- **Maquette dashboard** : `../Documentation/Maquette/dashboard_mockup.html`

### Données de test

- **CSV d'extraction** : `../Test_python_pipeline/Scratch_Pipeline/extract_dwh_20241120.csv`

---

## 💡 Conseils de lecture

1. **Commencez léger** : PROJECT_STATUS → QUICKSTART → README (sections utiles)
2. **Pratiquez** : Installez et lancez le système avant de lire toute la doc
3. **Approfondir** : Une fois le système compris, lisez ARCHITECTURE
4. **Référence** : Gardez COMMANDS.md sous la main pour les commandes
5. **Tests** : Suivez QUICK_TEST_GUIDE pour valider rapidement

---

## 📊 Statistiques documentation

| Type | Fichiers | Lignes | Mots |
|------|----------|--------|------|
| **Guides rapides** | 3 | ~650 | ~8,000 |
| **Documentation technique** | 3 | ~1,150 | ~14,000 |
| **Guides opérationnels** | 1 | ~500 | ~6,000 |
| **Tests** | 2 | ~850 | ~10,000 |
| **TOTAL** | **9** | **~3,150** | **~38,000** |

---

## 🎯 Documentation manquante (TODO)

- [ ] Guide d'architecture du dashboard React (futur)
- [ ] Guide de contribution (pour équipe élargie)
- [ ] Changelog (versions, évolutions)
- [ ] FAQ (après retours utilisateurs)
- [ ] Guide de troubleshooting avancé (après production)

---

**🎉 Bonne lecture ! Commencez par [QUICKSTART.md](QUICKSTART.md) !**

---

_Dernière mise à jour : 2026-09-03_  
_Version : 1.0.0_  
_Statut : ✅ Ready for testing_
