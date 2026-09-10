# 🔧 Dépannage Oracle Database - Guide complet

## ❌ Erreur rencontrée

```
ConnectionRefusedError: [WinError 10061] Aucune connexion n'a pu être établie
```

**Cause** : Le service Oracle Database n'est pas démarré ou n'écoute pas sur le port 1521.

---

## ✅ Solution en 4 étapes

### Étape 1 : Vérifier les services Oracle

```powershell
# Lister tous les services Oracle
Get-Service | Where-Object {$_.Name -like "*Oracle*"} | Format-Table Name, Status, DisplayName -AutoSize
```

**Services à vérifier** :
- `OracleServiceXE` : Service principal de la base de données
- `OracleOraDB21Home1TNSListener` : Listener réseau (port 1521)

**Statuts attendus** : `Running`

---

### Étape 2 : Démarrer les services

```powershell
# Démarrer le service principal
Start-Service OracleServiceXE

# Démarrer le listener
Start-Service OracleOraDB21Home1TNSListener

# Attendre 10-15 secondes pour le démarrage complet
Start-Sleep -Seconds 15

# Vérifier le statut
Get-Service OracleServiceXE, OracleOraDB21Home1TNSListener
```

**Si erreur "Impossible de trouver le service"** :
```powershell
# Chercher le nom exact du service
Get-Service | Where-Object {$_.DisplayName -like "*Oracle*"}
```

Puis adapter les commandes avec le nom exact trouvé.

---

### Étape 3 : Vérifier le port 1521

```powershell
# Vérifier que le port 1521 est ouvert et en écoute
Test-NetConnection -ComputerName localhost -Port 1521
```

**Résultat attendu** :
```
TcpTestSucceeded : True
```

**Si False** :
```powershell
# Voir quel processus écoute sur 1521
netstat -ano | Select-String "1521"

# Devrait afficher quelque chose comme :
# TCP    0.0.0.0:1521    0.0.0.0:0    LISTENING    <PID>
```

---

### Étape 4 : Tester la connexion Python

```powershell
cd "c:\Users\Raphael\PROJETS\OCM\Monitoring CTI"
python test_conn.py
```

**Résultat attendu** : `✅ Connexion Oracle OK`

---

## 🔍 Diagnostic avancé

### Vérifier les logs Oracle

**Emplacement des logs** (Oracle XE 21c) :
```
C:\app\Raphael\product\21c\diag\rdbms\xe\xe\trace\
```

**Log principal** : `alert_xe.log`

```powershell
# Voir les dernières lignes du log
Get-Content "C:\app\Raphael\product\21c\diag\rdbms\xe\xe\trace\alert_xe.log" | Select-Object -Last 50
```

**Messages importants** :
- `Completed: ALTER DATABASE OPEN` → Base démarrée ✅
- `TNS-12541` → Listener non démarré ❌
- `ORA-01034` → Base non montée ❌

---

### Vérifier le fichier tnsnames.ora

**Emplacement** :
```
C:\app\Raphael\product\21c\network\admin\tnsnames.ora
```

**Contenu attendu** :
```
XE =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = XE)
    )
  )

XEPDB1 =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = XEPDB1)
    )
  )
```

---

### Connexion via SQL*Plus (si disponible)

**Emplacement SQL*Plus** :
```
C:\app\Raphael\product\21c\dbhomeXE\bin\sqlplus.exe
```

**Tester la connexion** :
```powershell
& "C:\app\Raphael\product\21c\dbhomeXE\bin\sqlplus.exe" system/Oratoria_7@localhost:1521/XE
```

---

## 🚀 Configuration automatique au démarrage

### Rendre les services automatiques

```powershell
# Service principal en automatique
Set-Service -Name OracleServiceXE -StartupType Automatic

# Listener en automatique
$listenerService = Get-Service | Where-Object {$_.DisplayName -like "*TNSListener*"} | Select-Object -First 1
if ($listenerService) {
    Set-Service -Name $listenerService.Name -StartupType Automatic
}

# Vérifier
Get-Service | Where-Object {$_.Name -like "*Oracle*"} | Select-Object Name, StartType, Status
```

---

## 🐛 Problèmes courants

### Problème 1 : Service ne démarre pas

**Symptôme** : `Start-Service` échoue

**Solutions** :
1. Vérifier l'espace disque (Oracle XE nécessite ~10GB)
2. Vérifier les droits administrateur
3. Consulter les logs : Event Viewer → Windows Logs → Application

**Commande** :
```powershell
# Event Viewer logs Oracle
Get-EventLog -LogName Application -Source "Oracle*" -Newest 20
```

---

### Problème 2 : Port 1521 déjà utilisé

**Symptôme** : Listener ne démarre pas, port occupé

**Solution** :
```powershell
# Trouver le processus qui utilise 1521
netstat -ano | Select-String "1521"
# Noter le PID

# Voir quel processus
Get-Process -Id <PID>

# Si ce n'est pas Oracle, arrêter le processus ou changer le port Oracle
```

**Changer le port Oracle** (si nécessaire) :
1. Éditer `C:\app\Raphael\product\21c\network\admin\listener.ora`
2. Changer `PORT = 1521` en `PORT = 1522`
3. Redémarrer le listener
4. Adapter le DSN : `localhost:1522/XE`

---

### Problème 3 : Mot de passe invalide

**Symptôme** : `ORA-01017: invalid username/password`

**Solution** :
```powershell
# Réinitialiser le mot de passe system (nécessite droits admin)
& "C:\app\Raphael\product\21c\dbhomeXE\bin\sqlplus.exe" / as sysdba

# Dans SQL*Plus :
# ALTER USER system IDENTIFIED BY NouveauMotDePasse;
# EXIT;
```

---

### Problème 4 : Service XE introuvable

**Symptôme** : `Get-Service OracleServiceXE` échoue

**Solution** :
```powershell
# Lister TOUS les services Oracle
Get-Service | Where-Object {$_.DisplayName -like "*Oracle*"} | Format-Table Name, DisplayName

# Le service peut s'appeler différemment selon la version
# Exemples : OracleServiceXE, OracleServiceORCL, OracleVssWriterXE
```

---

## 📋 Checklist de vérification complète

Exécutez ce script PowerShell pour un diagnostic complet :

```powershell
Write-Host "`n=== DIAGNOSTIC ORACLE DATABASE ===" -ForegroundColor Cyan

# 1. Services
Write-Host "`n1. Services Oracle :" -ForegroundColor Yellow
Get-Service | Where-Object {$_.Name -like "*Oracle*"} | Format-Table Name, Status, DisplayName -AutoSize

# 2. Port 1521
Write-Host "`n2. Test port 1521 :" -ForegroundColor Yellow
$portTest = Test-NetConnection -ComputerName localhost -Port 1521 -WarningAction SilentlyContinue
if ($portTest.TcpTestSucceeded) {
    Write-Host "   ✅ Port 1521 accessible" -ForegroundColor Green
} else {
    Write-Host "   ❌ Port 1521 inaccessible" -ForegroundColor Red
}

# 3. Processus écoutant sur 1521
Write-Host "`n3. Processus sur port 1521 :" -ForegroundColor Yellow
$netstat = netstat -ano | Select-String "1521.*LISTENING"
if ($netstat) {
    Write-Host "   $netstat"
} else {
    Write-Host "   ❌ Aucun processus en écoute sur 1521" -ForegroundColor Red
}

# 4. Fichiers Oracle
Write-Host "`n4. Répertoires Oracle :" -ForegroundColor Yellow
$oracleBase = "C:\app\Raphael\product\21c"
if (Test-Path $oracleBase) {
    Write-Host "   ✅ Oracle installé : $oracleBase" -ForegroundColor Green
} else {
    Write-Host "   ❌ Répertoire Oracle introuvable" -ForegroundColor Red
}

# 5. Test connexion Python
Write-Host "`n5. Test connexion Python :" -ForegroundColor Yellow
$testScript = @"
import oracledb
try:
    conn = oracledb.connect(user='system', password='Oratoria_7', dsn='localhost:1521/XE')
    print('   ✅ Connexion réussie')
    conn.close()
except Exception as e:
    print(f'   ❌ Échec: {e}')
"@

python -c $testScript

Write-Host "`n=== FIN DU DIAGNOSTIC ===" -ForegroundColor Cyan
```

---

## 🎯 Solution rapide (résumé)

Si vous êtes pressé, exécutez simplement :

```powershell
# 1. Démarrer les services
Start-Service OracleServiceXE
Start-Service OracleOraDB21Home1TNSListener
Start-Sleep -Seconds 15

# 2. Tester
python test_conn.py
```

Si ça ne marche toujours pas, exécutez le script de diagnostic complet ci-dessus.

---

## 📞 Support

Si le problème persiste après ces étapes :

1. Consulter les logs Oracle : `C:\app\Raphael\product\21c\diag\rdbms\xe\xe\trace\alert_xe.log`
2. Vérifier Event Viewer Windows (Application logs)
3. Réinstaller Oracle Database 21c Express Edition

---

**Prochaine étape après connexion réussie** : 
→ Créer les utilisateurs de test (voir TESTING_PLAN.md Phase 1.3)
