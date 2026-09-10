# Script simple pour verifier et demarrer Oracle
Write-Host "==============================================="
Write-Host " VERIFICATION ORACLE DATABASE"
Write-Host "==============================================="

# 1. Lister les services Oracle
Write-Host "`n[1] Services Oracle..."
$services = Get-Service | Where-Object {$_.Name -like "*Oracle*"}

if ($services.Count -eq 0) {
    Write-Host "[ERROR] Aucun service Oracle trouve" -ForegroundColor Red
    exit 1
}

$services | Format-Table Name, Status, DisplayName -AutoSize

# 2. Identifier et demarrer les services critiques
$serviceXE = Get-Service | Where-Object {$_.Name -like "*ServiceXE*"} | Select-Object -First 1
$listener = Get-Service | Where-Object {$_.DisplayName -like "*TNSListener*"} | Select-Object -First 1

Write-Host "`n[2] Demarrage des services..."

if ($serviceXE -and $serviceXE.Status -ne "Running") {
    Write-Host "Demarrage de $($serviceXE.Name)..." -ForegroundColor Yellow
    Start-Service $serviceXE.Name
}

Write-Host "Attente 15 secondes..."
Start-Sleep -Seconds 15

if ($listener -and $listener.Status -ne "Running") {
    Write-Host "Demarrage de $($listener.Name)..." -ForegroundColor Yellow
    Start-Service $listener.Name
}

# 3. Test port 1521
Write-Host "`n[3] Test port 1521..."
$portTest = Test-NetConnection -ComputerName localhost -Port 1521 -WarningAction SilentlyContinue

if ($portTest.TcpTestSucceeded) {
    Write-Host "[OK] Port 1521 accessible" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Port 1521 inaccessible" -ForegroundColor Red
}

# 4. Test connexion Python
Write-Host "`n[4] Test connexion Python..."
$testResult = python -c "import oracledb; conn = oracledb.connect(user='system', password='Oratoria_7', dsn='localhost:1521/XE'); print('OK'); conn.close()" 2>&1

if ($testResult -match "OK") {
    Write-Host "[OK] Connexion reussie" -ForegroundColor Green
    Write-Host "`nProchaines etapes:"
    Write-Host "  1. Creer les utilisateurs (voir TESTING_PLAN.md)"
    Write-Host "  2. Importer les donnees"
} else {
    Write-Host "[ERROR] Connexion echouee" -ForegroundColor Red
    Write-Host "Erreur: $testResult"
}

Write-Host "`n==============================================="
