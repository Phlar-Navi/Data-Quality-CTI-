# 🔌 Guide : Connexion Oracle Database (standalone)

**Objectif** : Utiliser uniquement la partie connexion Oracle du script de monitoring, sans tout le reste.

---

## 📦 Fichiers nécessaires

### **Fichiers à copier** (4 fichiers minimum)

```
ton_nouveau_projet/
├── connectors/
│   ├── base.py                       # ✅ OBLIGATOIRE - Classe de base abstraite
│   └── oracle_connector.py           # ✅ OBLIGATOIRE - Classe de connexion Oracle
├── config/
│   └── .env                          # ✅ OBLIGATOIRE - Credentials DB
└── mon_script.py                     # ✅ TON SCRIPT - Utilise la connexion
```

**Optionnel** (pour une meilleure organisation) :
- `config/config.yaml` - Si tu veux centraliser la config
- `utils/config_loader.py` - Pour charger config.yaml

---

## 📋 Fichiers détaillés

### **1. `connectors/base.py`**

**Localisation** : `Code/connectors/base.py`

**Rôle** : Classe abstraite de base pour tous les connecteurs (interface)

**Contenu** : Copier tel quel, pas besoin de modification

**Note** : Nécessaire car `oracle_connector.py` hérite de `BaseConnector`

---

### **2. `connectors/oracle_connector.py`**

**Localisation** : `Code/connectors/oracle_connector.py`

**Rôle** : Classe Python qui gère la connexion à Oracle (hérite de BaseConnector)

**Contenu** : Copier tel quel, pas besoin de modification

**Dépendances** :
```python
import oracledb
import pandas as pd
from .base import BaseConnector
```

---

### **3. `config/.env`**

**Localisation** : `Code/config/.env` (⚠️ NE JAMAIS COMMITER SUR GIT)

**Rôle** : Contient les credentials de connexion Oracle

**Exemple de contenu** :
```bash
# Connexion Oracle DWH
DWH_DSN=hostname:1521/XEPDB1
DWH_READONLY_USER=monitoring_user
DWH_READONLY_PASSWORD=VotreMotDePasse123!
DWH_TABLE_NAME=CTI_SCHEMA.CALLS
```

**⚠️ Important** : Adapter les valeurs à votre environnement !

---

### **4. `mon_script.py` (ton nouveau script)**

**Rôle** : Ton script qui va utiliser la connexion Oracle

---

## 🚀 Installation

### **Étape 1 : Installer les dépendances Python**

```bash
# Créer un environnement virtuel (optionnel mais recommandé)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les packages nécessaires
pip install oracledb pandas python-dotenv
```

**Versions recommandées** :
- `oracledb >= 2.4.1` (remplace cx_Oracle)
- `pandas >= 2.2.3`
- `python-dotenv >= 1.2.1`

---

### **Étape 2 : Copier les fichiers**

```bash
# Structure minimale
mkdir connectors
mkdir config

# Copier depuis le projet de monitoring
copy "Code\connectors\base.py" "connectors\"
copy "Code\connectors\oracle_connector.py" "connectors\"
copy "Code\config\.env" "config\"

# ⚠️ ÉDITER config\.env avec VOS credentials
notepad config\.env
```

---

## 💻 Utilisation - Exemples de code

### **Exemple 1 : Connexion simple + requête SQL**

```python
# mon_script.py
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

# 1. Charger les credentials depuis .env
load_dotenv("config/.env")

# 2. Créer la connexion
connector = OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
)

# 3. Tester la connexion
if connector.test_connection():
    print("✅ Connexion OK !")
else:
    print("❌ Échec de connexion")
    exit(1)

# 4. Exécuter une requête SQL
query = """
    SELECT 
        CONNID,
        STARTTIME,
        DURATION
    FROM CTI_SCHEMA.CALLS
    WHERE TRUNC(STARTTIME) = TO_DATE('2026-06-22', 'YYYY-MM-DD')
    AND ROWNUM <= 100
"""

# 5. Récupérer les résultats dans un DataFrame pandas
df = connector.fetch_dataframe(query)

print(f"Nombre de lignes : {len(df)}")
print(df.head())

# 6. Fermer la connexion
connector.close()
```

**Résultat** :
```
✅ Connexion OK !
Nombre de lignes : 100
         CONNID           STARTTIME  DURATION
0  6d03957c5ff2c1  2026-06-22 08:30:15       265
1  6d03957c5ff039  2026-06-22 08:31:42        41
...
```

---

### **Exemple 2 : Requête avec paramètres dynamiques**

```python
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

# Connexion
connector = OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
)

# Paramètres dynamiques
date_debut = "2026-06-01"
date_fin = "2026-06-30"
duree_min = 300  # 5 minutes

# Requête SQL avec paramètres
query = f"""
    SELECT 
        CONNID,
        STARTTIME,
        DURATION,
        ORIGDNIS,
        DESTDNIS
    FROM {os.getenv('DWH_TABLE_NAME')}
    WHERE TRUNC(STARTTIME) BETWEEN TO_DATE('{date_debut}', 'YYYY-MM-DD') 
                               AND TO_DATE('{date_fin}', 'YYYY-MM-DD')
      AND DURATION >= {duree_min}
    ORDER BY DURATION DESC
"""

# Exécution
df = connector.fetch_dataframe(query)

print(f"Appels longs (>= {duree_min}s) : {len(df)}")
print(f"Durée moyenne : {df['DURATION'].mean():.1f}s")
print(f"Durée max : {df['DURATION'].max()}s")

# Export CSV
df.to_csv("appels_longs.csv", index=False, sep=";")
print("✅ Export CSV : appels_longs.csv")

connector.close()
```

---

### **Exemple 3 : Context manager (fermeture automatique)**

```python
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

# Utiliser 'with' pour fermeture automatique
with OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
) as connector:
    
    # Requête simple
    query = "SELECT COUNT(*) as nb_appels FROM CTI_SCHEMA.CALLS"
    df = connector.fetch_dataframe(query)
    
    print(f"Nombre total d'appels : {df['NB_APPELS'].iloc[0]}")

# Connexion fermée automatiquement ici
print("✅ Connexion fermée")
```

---

### **Exemple 4 : Traitement par batch (gros volumes)**

```python
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector
import pandas as pd

load_dotenv("config/.env")

connector = OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
)

# Traiter les données mois par mois
mois = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]

all_data = []

for mois_cible in mois:
    print(f"Extraction {mois_cible}...")
    
    query = f"""
        SELECT CONNID, STARTTIME, DURATION
        FROM CTI_SCHEMA.CALLS
        WHERE TO_CHAR(STARTTIME, 'YYYY-MM') = '{mois_cible}'
    """
    
    df_mois = connector.fetch_dataframe(query)
    all_data.append(df_mois)
    
    print(f"  → {len(df_mois)} lignes extraites")

# Fusionner tous les mois
df_complet = pd.concat(all_data, ignore_index=True)

print(f"\n✅ Total : {len(df_complet)} lignes sur {len(mois)} mois")

# Export consolidé
df_complet.to_csv("donnees_semestriel.csv", index=False, sep=";")

connector.close()
```

---

### **Exemple 5 : Gestion des erreurs**

```python
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

try:
    # Connexion
    connector = OracleConnector(
        dsn=os.getenv("DWH_DSN"),
        user=os.getenv("DWH_READONLY_USER"),
        password=os.getenv("DWH_READONLY_PASSWORD")
    )
    
    # Test connexion
    if not connector.test_connection():
        raise ConnectionError("Impossible de se connecter à Oracle")
    
    # Requête SQL
    query = "SELECT * FROM MA_TABLE_QUI_EXISTE_PAS"
    df = connector.fetch_dataframe(query)
    
    print(df.head())

except ConnectionError as e:
    print(f"❌ Erreur de connexion : {e}")
    print("Vérifier les credentials dans config/.env")

except Exception as e:
    print(f"❌ Erreur SQL : {e}")
    print("Vérifier la requête SQL")

finally:
    # Toujours fermer la connexion
    if 'connector' in locals():
        connector.close()
        print("Connexion fermée")
```

---

## 🔧 API de `OracleConnector`

### **Constructeur**

```python
OracleConnector(dsn: str, user: str, password: str)
```

**Paramètres** :
- `dsn` : Data Source Name (ex: "hostname:1521/XEPDB1")
- `user` : Nom d'utilisateur Oracle
- `password` : Mot de passe

---

### **Méthodes principales**

#### **`test_connection() -> bool`**

Teste si la connexion fonctionne.

```python
if connector.test_connection():
    print("Connexion OK")
```

---

#### **`fetch_dataframe(query: str) -> pd.DataFrame`**

Exécute une requête SQL et retourne un DataFrame pandas.

```python
df = connector.fetch_dataframe("SELECT * FROM ma_table")
```

**Retour** : `pandas.DataFrame`

---

#### **`execute_query(query: str) -> List[tuple]`**

Exécute une requête SQL et retourne une liste de tuples.

```python
rows = connector.execute_query("SELECT col1, col2 FROM ma_table")
for row in rows:
    print(row[0], row[1])
```

**Retour** : `List[tuple]`

---

#### **`close()`**

Ferme la connexion Oracle.

```python
connector.close()
```

---

#### **Context manager (avec `with`)**

Permet une fermeture automatique.

```python
with OracleConnector(dsn, user, pwd) as connector:
    df = connector.fetch_dataframe("SELECT ...")
# Connexion fermée automatiquement
```

---

## 🛠️ Troubleshooting

### **Problème 1 : "ModuleNotFoundError: No module named 'oracledb'"**

**Solution** :
```bash
pip install oracledb
```

---

### **Problème 2 : "DPI-1047: Cannot locate a 64-bit Oracle Client library"**

**Cause** : Oracle Instant Client manquant

**Solution** :
1. Télécharger Oracle Instant Client : https://www.oracle.com/database/technologies/instant-client.html
2. Extraire dans `C:\oracle\instantclient_21_X`
3. Ajouter au PATH :
   ```powershell
   $env:PATH += ";C:\oracle\instantclient_21_X"
   ```

---

### **Problème 3 : "ORA-12154: TNS:could not resolve the connect identifier"**

**Cause** : DSN incorrect dans `.env`

**Solution** : Vérifier le format DSN :
```bash
# Format attendu
DWH_DSN=hostname:1521/XEPDB1

# ❌ Incorrect
DWH_DSN=hostname/XEPDB1  # Manque le port
```

---

### **Problème 4 : "ORA-01017: invalid username/password"**

**Cause** : Credentials incorrects

**Solution** : Vérifier dans `.env` :
```bash
DWH_READONLY_USER=votre_user
DWH_READONLY_PASSWORD=votre_password
```

---

### **Problème 5 : "No .env file found"**

**Cause** : Chemin incorrect ou fichier manquant

**Solution** :
```python
# Vérifier le chemin
import os
print(os.path.exists("config/.env"))  # Doit retourner True

# Si False, créer le fichier
with open("config/.env", "w") as f:
    f.write("DWH_DSN=votre_dsn\n")
    f.write("DWH_READONLY_USER=votre_user\n")
    f.write("DWH_READONLY_PASSWORD=votre_password\n")
```

---

## 📊 Cas d'usage courants

### **1. Export CSV quotidien**

```python
import os
from datetime import datetime
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

# Date du jour
today = datetime.now().strftime("%Y-%m-%d")

with OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
) as connector:
    
    query = f"""
        SELECT * FROM CTI_SCHEMA.CALLS
        WHERE TRUNC(STARTTIME) = TO_DATE('{today}', 'YYYY-MM-DD')
    """
    
    df = connector.fetch_dataframe(query)
    
    filename = f"export_cti_{today}.csv"
    df.to_csv(filename, index=False, sep=";")
    
    print(f"✅ {len(df)} lignes exportées dans {filename}")
```

---

### **2. Calcul d'agrégats**

```python
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

with OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
) as connector:
    
    query = """
        SELECT 
            TO_CHAR(STARTTIME, 'YYYY-MM-DD') as date_appel,
            COUNT(*) as nb_appels,
            AVG(DURATION) as duree_moyenne,
            MAX(DURATION) as duree_max
        FROM CTI_SCHEMA.CALLS
        WHERE STARTTIME > SYSDATE - 30
        GROUP BY TO_CHAR(STARTTIME, 'YYYY-MM-DD')
        ORDER BY date_appel DESC
    """
    
    df = connector.fetch_dataframe(query)
    
    print("Statistiques sur 30 jours :")
    print(df.to_string(index=False))
```

---

### **3. Vérification de volumétrie**

```python
import os
from dotenv import load_dotenv
from connectors.oracle_connector import OracleConnector

load_dotenv("config/.env")

with OracleConnector(
    dsn=os.getenv("DWH_DSN"),
    user=os.getenv("DWH_READONLY_USER"),
    password=os.getenv("DWH_READONLY_PASSWORD")
) as connector:
    
    query = """
        SELECT 
            TO_CHAR(STARTTIME, 'HH24') as heure,
            COUNT(*) as nb_appels
        FROM CTI_SCHEMA.CALLS
        WHERE TRUNC(STARTTIME) = TRUNC(SYSDATE)
        GROUP BY TO_CHAR(STARTTIME, 'HH24')
        ORDER BY heure
    """
    
    df = connector.fetch_dataframe(query)
    
    print("Répartition horaire aujourd'hui :")
    for _, row in df.iterrows():
        print(f"  {row['HEURE']}h : {row['NB_APPELS']} appels")
```

---

## 📚 Ressources

### **Documentation officielle**

- **python-oracledb** : https://python-oracledb.readthedocs.io/
- **pandas** : https://pandas.pydata.org/docs/
- **python-dotenv** : https://pypi.org/project/python-dotenv/

### **Fichiers du projet complet**

Si besoin d'exemples plus avancés, consulter :
- `Code/utils/breakpoint_runner.py` - Utilisation avancée
- `Code/main.py` - Orchestration complète
- `Code/DOCUMENTATION_COMPLETE.md` - Documentation du projet complet

---

## ✅ Checklist de démarrage

```
☐ 1. Installer les packages : pip install oracledb pandas python-dotenv
☐ 2. Copier connectors/base.py
☐ 3. Copier connectors/oracle_connector.py
☐ 4. Créer config/.env avec les credentials
☐ 5. Tester la connexion avec Exemple 1
☐ 6. Adapter les requêtes SQL à vos besoins
☐ 7. Ajouter config/.env dans .gitignore (IMPORTANT !)
```

---

**Bon développement ! 🚀**

Pour toute question, contacter l'équipe Data Engineering.
