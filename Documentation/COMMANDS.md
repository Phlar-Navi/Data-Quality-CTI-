# 📋 Commandes utiles - Monitoring CTI

Guide de référence rapide des commandes PowerShell.

---

## 🔧 Installation et configuration

### Installer les dépendances

```powershell
pip install -r requirements.txt
```

### Vérifier l'installation

```powershell
pip list | Select-String "oracledb|pandas|yaml"
```

### Créer le fichier .env

```powershell
cp config\.env.example .env
notepad .env
```

### Vérifier l'environnement complet

```powershell
python check_env.py
```

---

## 🚀 Exécution

### Exécution standard (tous les breakpoints, J-1)

```powershell
python main.py
```

### Exécuter un breakpoint spécifique

```powershell
python main.py --breakpoint bp9_dwh_oracle
```

### Spécifier une date cible

```powershell
# Date spécifique
python main.py --date 2026-09-01

# Hier (J-1)
python main.py --date (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')

# Il y a 7 jours
python main.py --date (Get-Date).AddDays(-7).ToString('yyyy-MM-dd')
```

### Combiner breakpoint et date

```powershell
python main.py --breakpoint bp9_dwh_oracle --date 2026-09-01
```

### Utiliser un fichier de config alternatif

```powershell
python main.py --config config/config_prod.yaml
```

---

## 📊 Consulter les résultats

### Voir les logs du jour

```powershell
Get-Content logs\monitoring_$(Get-Date -Format 'yyyyMMdd').log
```

### Voir les derniers logs

```powershell
Get-Content logs\monitoring_*.log | Select-Object -Last 50
```

### Voir le dernier rapport texte

```powershell
Get-ChildItem logs\text\batch_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

### Voir le dernier résultat JSON

```powershell
Get-Content dashboard_data\latest.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Compter les résultats JSON

```powershell
(Get-ChildItem logs\json\*.json).Count
```

---

## 🔍 Analyse et dépannage

### Vérifier la connexion Oracle (test rapide)

```powershell
python -c "import oracledb; print('oracledb OK')"
```

### Chercher les erreurs dans les logs

```powershell
Get-Content logs\monitoring_*.log | Select-String "ERROR|CRITICAL"
```

### Chercher les checks en échec

```powershell
Get-Content logs\monitoring_*.log | Select-String "Critique|score: 0"
```

### Afficher uniquement les statuts finaux

```powershell
Get-Content logs\monitoring_*.log | Select-String "Statut :"
```

### Trouver les runs avec au moins un échec

```powershell
Get-ChildItem logs\text\batch_*.txt | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "Critique|❌") {
        Write-Host "Échec dans : $($_.Name)"
    }
}
```

---

## 📁 Gestion des fichiers

### Lister tous les breakpoints configurés

```powershell
Get-ChildItem breakpoints\*.yaml | Select-Object Name
```

### Afficher le contenu d'un breakpoint

```powershell
Get-Content breakpoints\bp9_dwh_oracle.yaml
```

### Créer un nouveau breakpoint (copie)

```powershell
cp breakpoints\bp9_dwh_oracle.yaml breakpoints\bp10_nouveau.yaml
notepad breakpoints\bp10_nouveau.yaml
```

### Valider un fichier YAML

```powershell
python -c "import yaml; yaml.safe_load(open('breakpoints/bp9_dwh_oracle.yaml', 'r', encoding='utf-8'))"
```

---

## 🧹 Nettoyage

### Supprimer les logs de plus de 30 jours

```powershell
Get-ChildItem logs\*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
```

### Supprimer tous les logs (ATTENTION)

```powershell
Remove-Item logs\* -Recurse -Force
```

### Supprimer les résultats JSON de plus de 60 jours

```powershell
Get-ChildItem logs\json\*.json | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-60) } | Remove-Item
```

### Nettoyer le cache Python

```powershell
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
```

---

## 📦 Développement

### Lancer en mode DEBUG

Éditer `config/config.yaml` :

```yaml
logging:
  log_level: DEBUG
```

Puis :

```powershell
python main.py
```

### Tester un check individuellement

Créer un script test `test_check.py` :

```python
from checks import MinRowCountCheck
import pandas as pd

check = MinRowCountCheck(params={"min_lines": 1000})
data = pd.DataFrame({"col1": range(1500)})
result = check.run(data)
print(f"Status: {result.status.value}, Score: {result.score}")
```

Exécuter :

```powershell
python test_check.py
```

### Lister tous les checks disponibles

```powershell
python -c "from utils.breakpoint_runner import CHECK_REGISTRY; print('\n'.join(CHECK_REGISTRY.keys()))"
```

### Afficher la structure du projet

```powershell
tree /F /A
```

---

## 🔄 Automatisation

### Créer un script d'exécution quotidienne

Créer `run_daily.ps1` :

```powershell
# run_daily.ps1
$ErrorActionPreference = "Stop"

cd "C:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"

Write-Host "Démarrage monitoring CTI - $(Get-Date)"
python main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Monitoring terminé avec succès"
} else {
    Write-Host "❌ Monitoring terminé avec des erreurs"
    exit 1
}
```

### Planifier avec Task Scheduler (PowerShell)

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code\run_daily.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName "Monitoring CTI" -Action $action -Trigger $trigger -Principal $principal
```

### Voir les tâches planifiées

```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "*Monitoring*" }
```

---

## 📊 Statistiques

### Nombre total de runs

```powershell
(Get-ChildItem logs\json\batch_*.json).Count
```

### Taille totale des logs

```powershell
$totalSize = (Get-ChildItem logs -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Taille totale : $([math]::Round($totalSize, 2)) MB"
```

### Moyenne des scores (derniers 10 runs)

```powershell
Get-ChildItem logs\json\batch_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object {
    $json = Get-Content $_.FullName | ConvertFrom-Json
    $scores = $json.breakpoints | ForEach-Object { $_.score }
    $avg = ($scores | Measure-Object -Average).Average
    Write-Host "$($_.Name): Score moyen = $([math]::Round($avg, 1))/10"
}
```

---

## 🆘 Dépannage

### Test connexion Oracle complet

```powershell
python -c "
import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

dsn = os.getenv('DWH_DSN')
user = os.getenv('DWH_READONLY_USER')
password = os.getenv('DWH_READONLY_PASSWORD')

print(f'DSN: {dsn}')
print(f'User: {user}')

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    print('✅ Connexion OK')
    conn.close()
except Exception as e:
    print(f'❌ Erreur: {e}')
"
```

### Afficher les variables d'environnement

```powershell
Get-Content .env
```

### Réinstaller toutes les dépendances

```powershell
pip uninstall -y oracledb pandas pyyaml python-dotenv
pip install -r requirements.txt
```

### Vérifier la syntaxe Python d'un fichier

```powershell
python -m py_compile main.py
```

---

## 📤 Export et partage

### Créer une archive du projet (sans logs/cache)

```powershell
$exclude = @('logs', 'dashboard_data', '__pycache__', '.env', '*.pyc')
$files = Get-ChildItem -Recurse | Where-Object {
    $item = $_
    -not ($exclude | Where-Object { $item.FullName -like "*$_*" })
}
Compress-Archive -Path $files -DestinationPath "monitoring_cti_backup_$(Get-Date -Format 'yyyyMMdd').zip"
```

### Exporter les résultats du dernier run en CSV

```powershell
$json = Get-Content dashboard_data\latest.json | ConvertFrom-Json
$json.breakpoints | Select-Object breakpoint_name, status, score, target_date | Export-Csv -Path "export_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

---

## 🔐 Sécurité

### Vérifier que .env n'est pas tracké par Git

```powershell
git check-ignore .env
# Doit retourner : .env
```

### Chiffrer le fichier .env (Windows)

```powershell
# Nécessite EFS (Encrypting File System)
cipher /e .env
```

---

## 💡 Raccourcis utiles

### Alias PowerShell à ajouter au profil

Éditer le profil :

```powershell
notepad $PROFILE
```

Ajouter :

```powershell
# Monitoring CTI
function Run-Monitoring {
    cd "C:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code"
    python main.py $args
}

Set-Alias monitoring Run-Monitoring

function Show-MonitoringLogs {
    Get-Content "C:\Users\Raphael\PROJETS\OCM\Monitoring CTI\Code\logs\monitoring_$(Get-Date -Format 'yyyyMMdd').log" | Select-Object -Last 50
}

Set-Alias mlogs Show-MonitoringLogs
```

Recharger :

```powershell
. $PROFILE
```

Utiliser :

```powershell
monitoring --date 2026-09-01
mlogs
```

---

**Astuce** : Ajoutez ce fichier à vos favoris pour un accès rapide aux commandes !
