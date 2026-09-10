# ✅ Solution Oracle - Connexion réussie !

## 🎯 Problème identifié

Oracle Listener écoute sur l'**IP locale** `172.16.16.169:1521` et **non sur localhost:1521**.

## ✅ Solution

Utilisez l'IP locale dans le DSN :

```python
# ❌ Ne marche PAS
conn = oracledb.connect(user='system', password='Oratoria_7', dsn='localhost:1521/XE')

# ✅ Marche !
conn = oracledb.connect(user='system', password='Oratoria_7', dsn='172.16.16.169:1521/XE')
```

## 🔧 Configuration pour le monitoring

### Fichier .env.test

```env
# Configuration TEST - Oracle XE local (votre machine)
DWH_DSN=172.16.16.169:1521/XE
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=MonitorTest123
DWH_TABLE_NAME=DWH_CTI_TEST.CDR_EVENTS
```

**Note** : Remplacez `172.16.16.169` par votre IP locale si elle change.

## 🔍 Comment trouver votre IP locale Oracle

```powershell
# 1. Trouver le PID du listener
Get-Process | Where-Object {$_.ProcessName -like "*tnslsnr*"}

# 2. Voir sur quel port/IP il écoute (remplacer <PID> par le PID trouvé)
netstat -ano | Select-String "<PID>" | Select-String "LISTENING"
```

Cherchez la ligne avec `:1521` et notez l'IP avant.

## 🚀 Prochaines étapes

Maintenant qu'Oracle est accessible, vous pouvez :

### 1. Créer les utilisateurs de test

```powershell
# Ouvrir PowerShell en tant qu'administrateur
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
```

Créer un fichier `create_users.sql` :

```sql
-- Connexion en tant que SYSTEM
-- sqlplus system/Oratoria_7@172.16.16.169:1521/XE

-- Créer l'utilisateur propriétaire des données
CREATE USER dwh_cti_test IDENTIFIED BY DwhTest123;
GRANT CONNECT, RESOURCE TO dwh_cti_test;
GRANT UNLIMITED TABLESPACE TO dwh_cti_test;

-- Créer l'utilisateur read-only pour monitoring
CREATE USER monitoring_user IDENTIFIED BY MonitorTest123;
GRANT CONNECT TO monitoring_user;

-- Note : Les droits SELECT seront donnés après création de la table

SELECT username, account_status FROM dba_users 
WHERE username IN ('DWH_CTI_TEST', 'MONITORING_USER');
```

### 2. Tester via Python

```python
import oracledb

# Test utilisateur SYSTEM (admin)
conn = oracledb.connect(
    user='system',
    password='Oratoria_7',
    dsn='172.16.16.169:1521/XE'
)
print("✅ Connexion SYSTEM OK")
conn.close()

# Test utilisateur dwh_cti_test (après création)
conn = oracledb.connect(
    user='dwh_cti_test',
    password='DwhTest123',
    dsn='172.16.16.169:1521/XE'
)
print("✅ Connexion dwh_cti_test OK")
conn.close()
```

### 3. Analyser les données CSV

```powershell
python test_utils\analyze_csv.py
```

### 4. Créer la table et importer les données

Suivre **TESTING_PLAN.md** Phase 3.

---

## 📝 Notes importantes

### Pourquoi pas localhost ?

Oracle Listener peut être configuré pour :
- **Écouter sur localhost uniquement** : sécurisé, mais accessible que depuis la machine locale
- **Écouter sur l'IP locale** : accessible depuis le réseau local
- **Écouter sur 0.0.0.0** : accessible de partout

Par défaut, Oracle XE écoute sur l'IP locale pour permettre les connexions réseau.

### Changer la configuration (optionnel)

Si vous voulez qu'Oracle écoute sur localhost, éditez :

**Fichier** : `C:\app\Raphael\product\21c\network\admin\listener.ora`

```
# Avant
LISTENER =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = 172.16.16.169)(PORT = 1521))
    )
  )

# Après (pour localhost)
LISTENER =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = TCP)(HOST = 127.0.0.1)(PORT = 1521))
    )
  )
```

Puis redémarrer le listener :

```powershell
Stop-Service OracleOraDB21Home1TNSListener
Start-Service OracleOraDB21Home1TNSListener
```

**⚠️ Recommandation** : Gardez la configuration actuelle (IP locale) qui fonctionne bien !

---

## ✅ Checklist de vérification

- [x] Oracle Database installé
- [x] Services démarrés (OracleServiceXE, TNSListener)
- [x] Port 1521 en écoute
- [x] Connexion Python réussie avec IP locale
- [ ] Utilisateurs créés (dwh_cti_test, monitoring_user)
- [ ] Données CSV analysées
- [ ] Table créée
- [ ] Données importées
- [ ] Tests du système de monitoring

---

**Statut** : ✅ CONNEXION ORACLE OPÉRATIONNELLE !

**Prochaine étape** : Créer les utilisateurs et la table (Phase 1.3 du TESTING_PLAN.md)
