# Script de démarrage et diagnostic Oracle Database
# Usage: .\start_oracle.ps1

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔧 DÉMARRAGE ET DIAGNOSTIC ORACLE DATABASE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Fonction pour afficher un message de statut
function Write-Status {
    param(
        [string]$Message,
        [string]$Status  # "OK", "ERROR", "INFO", "WAITING"
    )
    
    $prefix = switch ($Status) {
        "OK"      { "[OK]" }
        "ERROR"   { "[ERROR]" }
        "INFO"    { "[INFO]" }
        "WAITING" { "[WAIT]" }
        default   { "[*]" }
    }
    
    $color = switch ($Status) {
        "OK"      { "Green" }
        "ERROR"   { "Red" }
        "INFO"    { "Cyan" }
        "WAITING" { "Yellow" }
        default   { "White" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $color
}

# 1. Vérifier les services Oracle
Write-Host "`n[1] Recherche des services Oracle..." -ForegroundColor Yellow
$oracleServices = Get-Service | Where-Object {$_.Name -like "*Oracle*"}

if ($oracleServices.Count -eq 0) {
    Write-Status "Aucun service Oracle trouvé !" "ERROR"
    Write-Host "    Vérifiez que Oracle est bien installé." -ForegroundColor Red
    exit 1
}

Write-Status "Services Oracle trouvés : $($oracleServices.Count)" "OK"
$oracleServices | Format-Table Name, Status, DisplayName -AutoSize

# 2. Identifier les services critiques
Write-Host "`n[2] Identification des services critiques..." -ForegroundColor Yellow

$serviceXE = Get-Service | Where-Object {$_.Name -like "*ServiceXE*"} | Select-Object -First 1
$listener = Get-Service | Where-Object {$_.DisplayName -like "*TNSListener*"} | Select-Object -First 1

if ($serviceXE) {
    Write-Status "Service Base de données : $($serviceXE.Name)" "INFO"
} else {
    Write-Status "Service Base de données non trouvé" "ERROR"
}

if ($listener) {
    Write-Status "Service Listener : $($listener.Name)" "INFO"
} else {
    Write-Status "Service Listener non trouvé" "ERROR"
}

# 3. Démarrer les services
Write-Host "`n[3] Démarrage des services..." -ForegroundColor Yellow

# Démarrer le service principal
if ($serviceXE) {
    if ($serviceXE.Status -ne "Running") {
        Write-Status "Démarrage de $($serviceXE.Name)..." "WAITING"
        try {
            Start-Service $serviceXE.Name -ErrorAction Stop
            Write-Status "Service $($serviceXE.Name) démarré" "OK"
        } catch {
            Write-Status "Échec du démarrage : $_" "ERROR"
        }
    } else {
        Write-Status "$($serviceXE.Name) déjà démarré" "OK"
    }
}

# Attendre que la base soit prête
Write-Status "Attente du démarrage complet (15 secondes)..." "WAITING"
Start-Sleep -Seconds 15

# Démarrer le listener
if ($listener) {
    if ($listener.Status -ne "Running") {
        Write-Status "Démarrage de $($listener.Name)..." "WAITING"
        try {
            Start-Service $listener.Name -ErrorAction Stop
            Write-Status "Service $($listener.Name) démarré" "OK"
        } catch {
            Write-Status "Échec du démarrage : $_" "ERROR"
        }
    } else {
        Write-Status "$($listener.Name) déjà démarré" "OK"
    }
}

# 4. Vérifier le statut final
Write-Host "`n[4] Vérification du statut final..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

if ($serviceXE) {
    $serviceXE.Refresh()
    if ($serviceXE.Status -eq "Running") {
        Write-Status "Base de données : Running" "OK"
    } else {
        Write-Status "Base de données : $($serviceXE.Status)" "ERROR"
    }
}

if ($listener) {
    $listener.Refresh()
    if ($listener.Status -eq "Running") {
        Write-Status "Listener : Running" "OK"
    } else {
        Write-Status "Listener : $($listener.Status)" "ERROR"
    }
}

# 5. Test du port 1521
Write-Host "`n[5] Test du port 1521..." -ForegroundColor Yellow
$portTest = Test-NetConnection -ComputerName localhost -Port 1521 -WarningAction SilentlyContinue -InformationLevel Quiet

if ($portTest) {
    Write-Status "Port 1521 accessible" "OK"
} else {
    Write-Status "Port 1521 inaccessible" "ERROR"
    Write-Host "    Le listener n'écoute pas sur le port 1521" -ForegroundColor Red
    Write-Host "    Vérifiez les logs Oracle" -ForegroundColor Red
}

# 6. Processus sur le port 1521
Write-Host "`n[6] Processus écoutant sur 1521..." -ForegroundColor Yellow
$netstatOutput = netstat -ano | Select-String "1521.*LISTENING"

if ($netstatOutput) {
    Write-Status "Processus trouvé" "OK"
    Write-Host "    $netstatOutput" -ForegroundColor Gray
} else {
    Write-Status "Aucun processus en écoute" "ERROR"
}

# 7. Test de connexion Python
Write-Host "`n[7] Test de connexion Python..." -ForegroundColor Yellow

$testScript = @"
import oracledb
try:
    conn = oracledb.connect(user='system', password='Oratoria_7', dsn='localhost:1521/XE', mode=oracledb.DEFAULT_AUTH)
    print('OK')
    conn.close()
except Exception as e:
    print(f'ERROR:{e}')
"@

$result = python -c $testScript 2>&1

if ($result -match "^OK") {
    Write-Status "Connexion Python réussie" "OK"
    $success = $true
} else {
    Write-Status "Connexion Python échouée" "ERROR"
    Write-Host "    Erreur : $result" -ForegroundColor Red
    $success = $false
}

# 8. Résumé final
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📊 RÉSUMÉ" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($success) {
    Write-Host "`n[OK] Oracle Database est operationnel !" -ForegroundColor Green
    Write-Host "`nVous pouvez maintenant :" -ForegroundColor Cyan
    Write-Host "  1. Tester la connexion : python test_conn.py"
    Write-Host "  2. Creer les utilisateurs : Voir TESTING_PLAN.md Phase 1.3"
    Write-Host "  3. Importer les donnees : python test_utils\import_to_oracle.py"
} else {
    Write-Host "`n[ERROR] Oracle Database n'est pas accessible" -ForegroundColor Red
    Write-Host "`nActions suggerees :" -ForegroundColor Cyan
    Write-Host "  1. Consulter les logs : Get-Content C:\app\Raphael\product\21c\diag\rdbms\xe\xe\trace\alert_xe.log | Select-Object -Last 30"
    Write-Host "  2. Verifier Event Viewer : eventvwr.msc"
    Write-Host "  3. Relancer les services manuellement via services.msc"
    Write-Host "  4. Consulter : ORACLE_TROUBLESHOOTING.md"
}

Write-Host "`n═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
