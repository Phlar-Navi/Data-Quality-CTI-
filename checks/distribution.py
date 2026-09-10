"""
Check de distribution horaire.
Compare la répartition horaire des données du jour à la baseline historique.
"""
import pandas as pd
import numpy as np
from .base import BaseCheck
from utils.models import CheckResult, CheckStatus


class HourlyDistributionCheck(BaseCheck):
    """
    Vérifie que la distribution horaire du jour est cohérente avec la baseline.
    
    Paramètres attendus dans params :
        - time_column (str) : Nom de la colonne contenant l'heure (datetime ou string)
        - tolerance_percent (float) : Écart toléré par tranche en points de % (ex: 5 pour +/-5%)
        - baseline_days (int) : Nombre de jours de référence pour la baseline
        - excluded_hours (list[int]) : Tranches horaires à exclure (activité nulle normale, ex: [0,1,2,3] pour nuit)
    
    Données attendues :
        - dict avec clés "current_data" (DataFrame du jour) et "baseline_distribution" (dict {heure: pourcentage})
    """
    
    name = "hourly_distribution_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de distribution horaire.
        
        Args:
            data: dict avec current_data (DataFrame) et baseline_distribution (dict)
        
        Returns:
            CheckResult
        """
        if not isinstance(data, dict) or "current_data" not in data:
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour HourlyDistributionCheck",
                {"expected_keys": ["current_data", "baseline_distribution"]}
            )
        
        current_df = data["current_data"]
        baseline = data.get("baseline_distribution", {})
        
        time_column = self.params.get("time_column", "EVENT_TIME")
        tolerance = self.params.get("tolerance_percent", 5.0)
        excluded_hours = self.params.get("excluded_hours", [])
        
        if not isinstance(current_df, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "current_data doit être un DataFrame"
            )
        
        if time_column not in current_df.columns:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Colonne '{time_column}' manquante dans les données"
            )
        
        # Extraire l'heure de la colonne temporelle
        try:
            # Format spécifique Oracle : '2026-06-20_16:10:18'
            current_df[time_column] = pd.to_datetime(
                current_df[time_column], 
                format='%Y-%m-%d_%H:%M:%S',
                errors='coerce'
            )
            current_df["hour"] = current_df[time_column].dt.hour
        except Exception as e:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Impossible de parser la colonne temporelle : {e}"
            )
        
        # Calculer la distribution actuelle (% par heure)
        total_rows = len(current_df)
        if total_rows == 0:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune ligne à analyser (dataset vide)"
            )
        
        current_distribution = current_df["hour"].value_counts(normalize=True).mul(100).to_dict()
        
        # Comparer à la baseline
        anomalies = []
        hour_details = {}
        
        for hour in range(24):
            # Exclure les tranches configurées comme normalement nulles
            if hour in excluded_hours:
                continue
            
            current_pct = current_distribution.get(hour, 0.0)
            baseline_pct = baseline.get(hour, 0.0)
            
            delta = abs(current_pct - baseline_pct)
            
            hour_details[hour] = {
                "current_percent": round(current_pct, 2),
                "baseline_percent": round(baseline_pct, 2),
                "delta_percent": round(delta, 2)
            }
            
            if delta > tolerance:
                anomalies.append({
                    "hour": hour,
                    "current_percent": round(current_pct, 2),
                    "baseline_percent": round(baseline_pct, 2),
                    "delta": round(delta, 2)
                })
        
        metrics = {
            "total_rows": total_rows,
            "tolerance_percent": tolerance,
            "excluded_hours": excluded_hours,
            "anomalies_count": len(anomalies),
            "anomalies": anomalies,
            "hour_details": hour_details
        }
        
        if not anomalies:
            return self._create_result(
                CheckStatus.SUCCESS,
                f"Distribution horaire conforme à la baseline (tolérance +/-{tolerance}%)",
                metrics
            )
        
        # Identifier la pire anomalie
        worst = max(anomalies, key=lambda x: x["delta"])
        
        if len(anomalies) <= 3:
            return self._create_result(
                CheckStatus.WARNING,
                f"{len(anomalies)} tranche(s) hors tolérance (pire : {worst['hour']}h à {worst['current_percent']}% vs {worst['baseline_percent']}%, écart {worst['delta']}%)",
                metrics
            )
        else:
            return self._create_result(
                CheckStatus.FAILURE,
                f"{len(anomalies)} tranches hors tolérance (pire : {worst['hour']}h à {worst['current_percent']}% vs {worst['baseline_percent']}%, écart {worst['delta']}%)",
                metrics
            )
