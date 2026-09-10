"""
Script de vérification de l'environnement.
Vérifie que toutes les dépendances et configurations sont en place.
"""
import sys
from pathlib import Path


def check_python_version():
    """Vérifie la version de Python."""
    print("🐍 Vérification de la version Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"   ❌ Python 3.8+ requis (version actuelle : {version.major}.{version.minor}.{version.micro})")
        return False
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Vérifie les dépendances Python."""
    print("\n📦 Vérification des dépendances...")
    required = {
        "oracledb": "Connecteur Oracle",
        "pandas": "Manipulation de données",
        "yaml": "Configuration YAML (PyYAML)"
    }
    
    all_ok = True
    for module, description in required.items():
        try:
            __import__(module)
            print(f"   ✅ {module:15} ({description})")
        except ImportError:
            print(f"   ❌ {module:15} MANQUANT ({description})")
            all_ok = False
    
    if not all_ok:
        print("\n   💡 Installer les dépendances : pip install -r requirements.txt")
    
    return all_ok


def check_config_files():
    """Vérifie la présence des fichiers de configuration."""
    print("\n⚙️  Vérification des fichiers de configuration...")
    
    base_path = Path(__file__).parent
    
    files_to_check = {
        "config/config.yaml": "Configuration globale",
        "config/.env.example": "Template credentials (OK si .env existe)",
        ".env": "Credentials Oracle (REQUIS)",
        "breakpoints/bp9_dwh_oracle.yaml": "Config breakpoint BP9"
    }
    
    all_ok = True
    for file_path, description in files_to_check.items():
        full_path = base_path / file_path
        if full_path.exists():
            print(f"   ✅ {file_path:35} ({description})")
        else:
            if file_path == ".env":
                print(f"   ❌ {file_path:35} MANQUANT ({description})")
                print(f"      💡 Créer depuis : cp config/.env.example .env")
                all_ok = False
            elif file_path == "config/.env.example":
                # Acceptable si .env existe
                if not (base_path / ".env").exists():
                    print(f"   ⚠️  {file_path:35} MANQUANT ({description})")
            else:
                print(f"   ❌ {file_path:35} MANQUANT ({description})")
                all_ok = False
    
    return all_ok


def check_directories():
    """Vérifie la présence des répertoires requis."""
    print("\n📁 Vérification de la structure des répertoires...")
    
    base_path = Path(__file__).parent
    
    directories = [
        "connectors",
        "checks",
        "config",
        "utils",
        "breakpoints",
        "logs",
        "dashboard_data"
    ]
    
    all_ok = True
    for dir_name in directories:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ MANQUANT (sera créé automatiquement)")
            # Créer les répertoires manquants (sauf logs et dashboard_data qui seront créés au runtime)
            if dir_name not in ["logs", "dashboard_data"]:
                all_ok = False
    
    return all_ok


def check_env_variables():
    """Vérifie les variables d'environnement critiques."""
    print("\n🔑 Vérification des variables d'environnement...")
    
    base_path = Path(__file__).parent
    env_file = base_path / ".env"
    
    if not env_file.exists():
        print("   ⚠️  Fichier .env non trouvé, impossible de vérifier les variables")
        return False
    
    required_vars = [
        "DWH_DSN",
        "DWH_READONLY_USER",
        "DWH_READONLY_PASSWORD",
        "DWH_TABLE_NAME"
    ]
    
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    all_ok = True
    for var in required_vars:
        if f"{var}=" in content:
            # Vérifier que la variable n'est pas vide
            lines = [line for line in content.split("\n") if line.startswith(f"{var}=")]
            if lines:
                value = lines[0].split("=", 1)[1].strip()
                if value and not value.startswith("your_") and not value.startswith("votre_"):
                    print(f"   ✅ {var:25} (définie)")
                else:
                    print(f"   ⚠️  {var:25} (à configurer)")
                    all_ok = False
            else:
                print(f"   ❌ {var:25} MANQUANT")
                all_ok = False
        else:
            print(f"   ❌ {var:25} MANQUANT")
            all_ok = False
    
    return all_ok


def main():
    """Point d'entrée principal."""
    print("="*60)
    print("🔍 VÉRIFICATION DE L'ENVIRONNEMENT - MONITORING CTI")
    print("="*60)
    
    checks = [
        ("Python", check_python_version()),
        ("Dépendances", check_dependencies()),
        ("Répertoires", check_directories()),
        ("Fichiers config", check_config_files()),
        ("Variables env", check_env_variables())
    ]
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Environnement prêt ! Vous pouvez lancer : python main.py")
    else:
        print("❌ Certaines vérifications ont échoué. Corrigez les erreurs ci-dessus.")
    print("="*60)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
