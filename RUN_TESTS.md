# 🚀 Lancer les tests du monitoring CTI

## ✅ État actuel

- ✅ Oracle Database opérationnel
- ✅ Utilisateurs créés (dwh_cti_test, monitoring_user)
- ✅ Table CDR_EVENTS_V2 créée avec **148,451 lignes**
- ✅ Données importées du 19 au 29 juin 2026
- ✅ **776 doublons** inclus (test robustesse)
- ✅ Configuration test prête

## 📊 Données disponibles

```
Période : 2026-06-19 → 2026-06-29 (11 jours)
Total   : 148,451 lignes
Uniques : 147,675 CONNID
Doublons: 776 (pour tester DuplicateKeyCheck)

Volumétrie par jour :
  2026-06-19 : 15,096 lignes
  2026-06-20 : 13,886 lignes
  2026-06-21 : 13,028 lignes
  2026-06-22 : 15,049 lignes
  2026-06-23 : 15,297 lignes
  2026-06-24 : 15,537 lignes
  2026-06-26 : 14,672 lignes (note: pas de 25)
  2026-06-27 : 16,294 lignes
  2026-06-28 : 13,410 lignes
  2026-06-29 : 16,171 lignes
```

## 🧪 Lancer les tests

### 1. Charger les variables d'environnement

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"

# Charger .env.test
Get-Content .env.test | ForEach-Object {
    if ($_ -match '^(\w+)=(.+)$') {
        Set-Item -Path "env:$($matches[1])" -Value $matches[2]
        Write-Host "  $($matches[1]) = $($matches[2])"
    }
}
```

### 2. Activer l'environnement virtuel

```powershell
.\.db_env\Scripts\activate.ps1
```

### 3. Tester la connexion

```powershell
python -c "import oracledb; conn=oracledb.connect(user='monitoring_user',password='MonitorTest123',dsn='172.16.16.169:1521/XEPDB1'); print('OK')"
```

**Attendu** : `OK`

### 4. Test unitaire : vérifier les données

```powershell
python -c "import oracledb; conn=oracledb.connect(user='monitoring_user',password='MonitorTest123',dsn='172.16.16.169:1521/XEPDB1'); c=conn.cursor(); c.execute('SELECT COUNT(*) FROM DWH_CTI_TEST.CDR_EVENTS_V2'); print(f'Lignes: {c.fetchone()[0]:,}')"
```

**Attendu** : `Lignes: 148,451`

### 5. Lancer le monitoring complet

```powershell
python main.py --breakpoint bp_test_local --config config\config_test.yaml
```

**Ce qui va être testé** :
1. ✅ MinRowCountCheck → 10k seuil, devrait être ✅ Normal (~14k/jour)
2. ✅ BaselineComparisonCheck → ±30%, devrait être ✅ Normal
3. ✅ SchemaConformityCheck → Colonnes présentes, devrait être ✅ Normal
4. ⚠️ DuplicateKeyCheck → **776 doublons** détectés, devrait être ❌ Critique
5. ✅ NullRateCheck → < 2%, devrait être ✅ Normal
6. ✅ HourlyDistributionCheck → ±15%, devrait être ✅ Normal

**Score attendu** : ~8-9/10 (baisse due aux doublons)

### 6. Analyser les résultats

```powershell
# Voir les logs
Get-Content logs_test\monitoring_*.log | Select-Object -Last 50

# Voir le rapport texte
Get-ChildItem logs_test\text\*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

# Voir le JSON dashboard
Get-Content dashboard_data_test\latest.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

---

## 🎯 Résultats attendus

### Statut global
- **Score** : 8-9/10 (bon malgré doublons)
- **Statut** : ⚠️ Dégradé (à cause des doublons)

### Détail par check

| Check | Attendu | Raison |
|-------|---------|--------|
| MinRowCount | ✅ Normal | 14k lignes > 10k seuil |
| Baseline | ✅ Normal | Variance < 30% |
| Schema | ✅ Normal | Toutes colonnes présentes |
| Duplicate | ❌ Critique | 776 doublons (tolérance 0) |
| NullRate | ✅ Normal | < 2% nullité |
| HourlyDistrib | ✅ Normal | Distribution régulière |

---

## 🐛 Dépannage

### Problème : Erreur de connexion

**Solution** : Vérifier les variables d'environnement

```powershell
$env:DWH_DSN
$env:DWH_READONLY_USER
$env:DWH_TABLE_NAME
```

### Problème : Table non trouvée

**Solution** : Vérifier le nom de la table

```powershell
python -c "import oracledb; conn=oracledb.connect(user='dwh_cti_test',password='DwhTest123',dsn='172.16.16.169:1521/XEPDB1'); c=conn.cursor(); c.execute(\"SELECT table_name FROM user_tables\"); print([r[0] for r in c])"
```

### Problème : Module non trouvé

**Solution** : Activer l'environnement virtuel

```powershell
.\.db_env\Scripts\activate.ps1
pip install -r requirements.txt
```

---

## 📊 Logs générés

Après l'exécution, vous trouverez :

```
logs_test/
  ├── monitoring_20260910.log           # Log applicatif
  ├── json/
  │   └── batch_20260910_HHMMSS.json   # Résultats JSON
  └── text/
      └── batch_20260910_HHMMSS.txt    # Résultats lisibles

dashboard_data_test/
  └── latest.json                       # Pour dashboard React
```

---

## ✅ Checklist de validation

- [ ] Variables d'environnement chargées
- [ ] Connexion monitoring_user OK
- [ ] Table accessible (148k lignes)
- [ ] Monitoring lancé sans erreur
- [ ] Score calculé (8-9/10)
- [ ] Doublons détectés (776)
- [ ] Logs créés (JSON + TXT)
- [ ] Dashboard JSON généré

---

**Prêt pour les tests ! 🚀**

Commande rapide tout-en-un :

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
Get-Content .env.test | ForEach-Object { if ($_ -match '^(\w+)=(.+)$') { Set-Item -Path "env:$($matches[1])" -Value $matches[2] }}
.\.db_env\Scripts\activate.ps1
python main.py --breakpoint bp_test_local --config config\config_test.yaml
```
