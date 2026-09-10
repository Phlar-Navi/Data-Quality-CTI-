"""
Chargeur de configuration YAML pour les breakpoints.
Gère le chargement des fichiers de configuration et la substitution des variables d'environnement.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import re


class ConfigLoader:
    """
    Charge et valide les fichiers de configuration YAML des breakpoints.
    Supporte la substitution de variables d'environnement (${VAR_NAME}).
    """
    
    def __init__(self, config_dir: str = None, breakpoints_dir: str = None):
        """
        Initialise le chargeur de configuration.
        
        Args:
            config_dir: Répertoire contenant le fichier de configuration global (config.yaml)
            breakpoints_dir: Répertoire contenant les fichiers de config par breakpoint
        """
        self.config_dir = Path(config_dir or os.path.join(os.path.dirname(__file__)))
        self.breakpoints_dir = Path(breakpoints_dir or os.path.join(os.path.dirname(__file__), "..", "breakpoints"))
    
    def load_global_config(self, config_filename: str = "config.yaml") -> Dict[str, Any]:
        """
        Charge le fichier de configuration global.
        
        Args:
            config_filename: Nom du fichier de configuration (défaut: "config.yaml")
        
        Returns:
            Dictionnaire de configuration globale
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            yaml.YAMLError: Si le fichier est invalide
        """
        config_path = self.config_dir / config_filename
        
        if not config_path.exists():
            raise FileNotFoundError(f"Fichier de configuration global introuvable : {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Substituer les variables d'environnement
        config = self._substitute_env_vars(config)
        
        return config
    
    def load_breakpoint_config(self, breakpoint_id: str) -> Dict[str, Any]:
        """
        Charge la configuration d'un breakpoint spécifique.
        
        Args:
            breakpoint_id: Identifiant du breakpoint (ex: "bp9_dwh_oracle")
        
        Returns:
            Dictionnaire de configuration du breakpoint
        
        Raises:
            FileNotFoundError: Si le fichier du breakpoint n'existe pas
            yaml.YAMLError: Si le fichier est invalide
        """
        breakpoint_path = self.breakpoints_dir / f"{breakpoint_id}.yaml"
        
        if not breakpoint_path.exists():
            raise FileNotFoundError(f"Configuration du breakpoint '{breakpoint_id}' introuvable : {breakpoint_path}")
        
        with open(breakpoint_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Substituer les variables d'environnement
        config = self._substitute_env_vars(config)
        
        # Valider la structure minimale
        self._validate_breakpoint_config(config, breakpoint_id)
        
        return config
    
    def list_breakpoints(self) -> list[str]:
        """
        Liste tous les breakpoints configurés (fichiers .yaml dans breakpoints/).
        
        Returns:
            Liste des identifiants de breakpoints
        """
        if not self.breakpoints_dir.exists():
            return []
        
        return [f.stem for f in self.breakpoints_dir.glob("*.yaml")]
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Remplace les variables d'environnement ${VAR_NAME} dans la configuration.
        
        Args:
            config: Configuration (dict, list, str, ou autre type)
        
        Returns:
            Configuration avec variables substituées
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Rechercher les patterns ${VAR_NAME}
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                var_value = os.environ.get(var_name)
                if var_value is None:
                    raise ValueError(f"Variable d'environnement '{var_name}' non définie")
                return var_value
            
            return re.sub(pattern, replace_var, config)
        else:
            return config
    
    def _validate_breakpoint_config(self, config: Dict[str, Any], breakpoint_id: str):
        """
        Valide la structure minimale d'une configuration de breakpoint.
        
        Args:
            config: Configuration à valider
            breakpoint_id: Identifiant du breakpoint (pour messages d'erreur)
        
        Raises:
            ValueError: Si la configuration est invalide
        """
        required_fields = ["id", "name", "access", "connector"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Champ obligatoire '{field}' manquant dans la configuration de '{breakpoint_id}'")
        
        # Vérifier que access est valide
        if config["access"] not in ["direct", "inferred"]:
            raise ValueError(f"Valeur 'access' invalide dans '{breakpoint_id}' : attendu 'direct' ou 'inferred', reçu '{config['access']}'")
        
        # Vérifier la structure du connecteur
        if "type" not in config["connector"]:
            raise ValueError(f"Champ 'connector.type' manquant dans la configuration de '{breakpoint_id}'")
        
        # Vérifier la présence de checks
        if "checks" not in config or not isinstance(config["checks"], list):
            raise ValueError(f"Champ 'checks' manquant ou invalide dans la configuration de '{breakpoint_id}' (liste attendue)")
