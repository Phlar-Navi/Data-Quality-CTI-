"""
Runner pour l'exécution des checks d'un breakpoint.
Orchestre l'exécution, agrège les résultats, calcule le score global.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd

from .models import BreakpointResult, CheckResult, BreakpointStatus
from connectors import OracleConnector
from checks import (
    MinRowCountCheck,
    BaselineComparisonCheck,
    SchemaConformityCheck,
    DuplicateKeyCheck,
    NullRateCheck,
    HourlyDistributionCheck
)


# Registre des checks disponibles (mapping type -> classe)
CHECK_REGISTRY = {
    "min_row_count_check": MinRowCountCheck,
    "baseline_comparison_check": BaselineComparisonCheck,
    "schema_conformity_check": SchemaConformityCheck,
    "duplicate_key_check": DuplicateKeyCheck,
    "null_rate_check": NullRateCheck,
    "hourly_distribution_check": HourlyDistributionCheck
}

# Registre des connecteurs disponibles
CONNECTOR_REGISTRY = {
    "oracle": OracleConnector
}


class BreakpointRunner:
    """
    Exécute tous les checks configurés pour un breakpoint et agrège les résultats.
    """
    
    def __init__(self, breakpoint_config: Dict[str, Any]):
        """
        Initialise le runner avec la configuration d'un breakpoint.
        
        Args:
            breakpoint_config: Configuration YAML chargée du breakpoint
        """
        self.config = breakpoint_config
        self.breakpoint_id = breakpoint_config["id"]
        self.breakpoint_name = breakpoint_config["name"]
        self.access_type = breakpoint_config["access"]
    
    def run(self, target_date: str = None) -> BreakpointResult:
        """
        Exécute tous les checks du breakpoint pour une date donnée.
        
        Args:
            target_date: Date des données à contrôler (YYYY-MM-DD)
                        Si None, utilise check_offset_days de la config
        
        Returns:
            BreakpointResult avec tous les checks exécutés et le score calculé
        """
        # Déterminer la date cible
        if target_date is None:
            offset_days = self.config.get("schedule", {}).get("check_offset_days", 1)
            target_date = (datetime.now().date() - timedelta(days=offset_days)).isoformat()
        
        # Initialiser le résultat
        result = BreakpointResult(
            breakpoint_id=self.breakpoint_id,
            breakpoint_name=self.breakpoint_name,
            access_type=self.access_type,
            target_date=target_date,
            run_timestamp=datetime.now(),
            run_state="in_progress"
        )
        
        try:
            # Récupérer les données depuis la source
            data = self._fetch_data(target_date)
            
            # Exécuter les checks
            check_configs = self.config.get("checks", [])
            force_zero_checks = []
            
            for check_config in check_configs:
                check_type = check_config["type"]
                check_params = check_config.get("params", {})
                force_zero = check_config.get("force_zero_on_failure", False)
                
                # Instancier le check
                check_class = CHECK_REGISTRY.get(check_type)
                if not check_class:
                    # Check non reconnu, loguer un warning mais continuer
                    print(f"[WARN]  Check '{check_type}' non reconnu, ignoré")
                    continue
                
                check = check_class(params=check_params)
                
                # Préparer les données selon le type de check
                check_data = self._prepare_check_data(check_type, data, target_date)
                
                # Exécuter le check
                check_result = check.run(check_data)
                result.checks.append(check_result)
                
                # Mémoriser si ce check doit forcer le score à 0 en cas d'échec
                if force_zero:
                    force_zero_checks.append(check.name)
            
            # Calculer le score global
            result.score = result.calculate_score(force_zero_on=force_zero_checks)
            result.status = result.determine_status()
            result.run_state = "completed"
            
        except Exception as e:
            # En cas d'erreur technique, marquer comme échec
            result.run_state = "failed"
            result.status = BreakpointStatus.INCONNU
            print(f"[ECHEC] Erreur lors de l'exécution du breakpoint '{self.breakpoint_id}' : {e}")
            raise
        
        return result
    
    def _fetch_data(self, target_date: str) -> pd.DataFrame:
        """
        Récupère les données depuis la source (via le connecteur configuré).
        
        Args:
            target_date: Date des données à récupérer (YYYY-MM-DD)
        
        Returns:
            DataFrame avec les données du jour
        """
        connector_config = self.config["connector"]
        connector_type = connector_config["type"]
        connector_params = connector_config.get("params", {})
        
        connector_class = CONNECTOR_REGISTRY.get(connector_type)
        if not connector_class:
            raise ValueError(f"Connecteur '{connector_type}' non reconnu")
        
        # Connexion et récupération des données
        with connector_class(**connector_params) as conn:
            data_source = self.config.get("data_source", {})
            table = data_source.get("table")
            date_column = data_source.get("date_column", "EVENT_DATE")
            
            if not table:
                raise ValueError(f"Champ 'data_source.table' manquant dans la config de '{self.breakpoint_id}'")
            
            # Requête de base
            query = f"""
                SELECT * 
                FROM {table}
                WHERE {date_column} = TO_DATE(:target_date, 'YYYY-MM-DD')
            """
            
            df = conn.query(query, params={"target_date": target_date})
        
        return df
    
    def _prepare_check_data(self, check_type: str, data: pd.DataFrame, target_date: str) -> Any:
        """
        Prépare les données spécifiques pour chaque type de check.
        
        Args:
            check_type: Type du check
            data: DataFrame source
            target_date: Date cible
        
        Returns:
            Données formatées pour le check
        """
        # La plupart des checks reçoivent directement le DataFrame
        if check_type in ["min_row_count_check", "schema_conformity_check", 
                          "duplicate_key_check", "null_rate_check"]:
            return data
        
        # Baseline comparison : besoin de calculer la baseline historique
        if check_type == "baseline_comparison_check":
            current_count = len(data)
            baseline_avg = self._calculate_baseline(target_date)
            return {
                "current_count": current_count,
                "baseline_avg": baseline_avg
            }
        
        # Hourly distribution : besoin de la baseline de distribution horaire
        if check_type == "hourly_distribution_check":
            baseline_distribution = self._calculate_hourly_baseline(target_date)
            return {
                "current_data": data,
                "baseline_distribution": baseline_distribution
            }
        
        # Par défaut, retourner le DataFrame brut
        return data
    
    def _calculate_baseline(self, target_date: str) -> float:
        """
        Calcule la baseline historique (moyenne des N derniers jours).
        
        Args:
            target_date: Date cible (YYYY-MM-DD)
        
        Returns:
            Moyenne du nombre de lignes des N derniers jours
        """
        connector_config = self.config["connector"]
        connector_type = connector_config["type"]
        connector_params = connector_config.get("params", {})
        
        connector_class = CONNECTOR_REGISTRY[connector_type]
        
        data_source = self.config.get("data_source", {})
        table = data_source["table"]
        date_column = data_source.get("date_column", "EVENT_DATE")
        
        # Récupérer le nombre de jours de baseline depuis la config du check
        baseline_days = 14  # Valeur par défaut
        for check_config in self.config.get("checks", []):
            if check_config["type"] == "baseline_comparison_check":
                baseline_days = check_config.get("params", {}).get("baseline_days", 14)
                break
        
        # Calculer la plage de dates (exclure les weekends pour "jours ouvrés")
        # Simplifié : prendre baseline_days × 1.5 pour compenser les weekends
        lookback_days = int(baseline_days * 1.5)
        
        with connector_class(**connector_params) as conn:
            query = f"""
                SELECT AVG(daily_count) as avg_count
                FROM (
                    SELECT {date_column}, COUNT(*) as daily_count
                    FROM {table}
                    WHERE {date_column} BETWEEN 
                        TO_DATE(:target_date, 'YYYY-MM-DD') - {lookback_days}
                        AND TO_DATE(:target_date, 'YYYY-MM-DD') - 1
                    GROUP BY {date_column}
                    ORDER BY {date_column} DESC
                    FETCH FIRST {baseline_days} ROWS ONLY
                )
            """
            avg_count = conn.execute_scalar(query, params={"target_date": target_date})
        
        return float(avg_count) if avg_count else 0.0
    
    def _calculate_hourly_baseline(self, target_date: str) -> Dict[int, float]:
        """
        Calcule la distribution horaire de référence (% par heure sur N jours).
        
        Args:
            target_date: Date cible (YYYY-MM-DD)
        
        Returns:
            Dict {heure: pourcentage} de 0 à 23
        """
        connector_config = self.config["connector"]
        connector_type = connector_config["type"]
        connector_params = connector_config.get("params", {})
        
        connector_class = CONNECTOR_REGISTRY[connector_type]
        
        data_source = self.config.get("data_source", {})
        table = data_source["table"]
        date_column = data_source.get("date_column", "EVENT_DATE")
        
        # Récupérer la colonne temporelle et le nombre de jours
        time_column = "EVENT_TIME"
        baseline_days = 14
        for check_config in self.config.get("checks", []):
            if check_config["type"] == "hourly_distribution_check":
                params = check_config.get("params", {})
                time_column = params.get("time_column", "EVENT_TIME")
                baseline_days = params.get("baseline_days", 14)
                break
        
        lookback_days = int(baseline_days * 1.5)
        
        with connector_class(**connector_params) as conn:
            query = f"""
                SELECT 
                    EVENT_HOUR as hour,
                    COUNT(*) as count
                FROM {table}
                WHERE {date_column} BETWEEN 
                    TO_DATE(:target_date, 'YYYY-MM-DD') - {lookback_days}
                    AND TO_DATE(:target_date, 'YYYY-MM-DD') - 1
                GROUP BY EVENT_HOUR
            """
            df = conn.query(query, params={"target_date": target_date})
        
        if df.empty:
            return {}
        
        # Calculer les pourcentages
        total_count = df["COUNT"].sum()
        baseline = {}
        for _, row in df.iterrows():
            hour = int(row["HOUR"])
            pct = (row["COUNT"] / total_count) * 100
            baseline[hour] = round(pct, 2)
        
        return baseline
