"""
Checks de volumétrie.
Vérifie le volume de données (nombre de lignes) et la comparaison à la baseline historique.
"""
import pandas as pd
from .base import BaseCheck
from utils.models import CheckResult, CheckStatus


class MinRowCountCheck(BaseCheck):
    """
    Vérifie que le nombre de lignes respecte un seuil minimum.
    
    Paramètres attendus dans params :
        - min_lines (int) : Nombre minimum de lignes attendu
    
    Données attendues :
        - DataFrame pandas ou dict avec clé "row_count"
    """
    
    name = "min_row_count_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de volumétrie minimale.
        
        Args:
            data: DataFrame ou dict contenant le nombre de lignes
        
        Returns:
            CheckResult
        """
        min_lines = self.params.get("min_lines", 0)
        
        # Extraire le nombre de lignes
        if isinstance(data, pd.DataFrame):
            row_count = len(data)
        elif isinstance(data, dict) and "row_count" in data:
            row_count = data["row_count"]
        else:
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour MinRowCountCheck",
                {"expected_format": "DataFrame ou dict avec 'row_count'"}
            )
        
        metrics = {
            "row_count": row_count,
            "min_lines": min_lines
        }
        
        # Cas particulier : 0 ligne = échec structurel
        if row_count == 0:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Aucune ligne trouvée (attendu >= {min_lines})",
                metrics
            )
        
        # Vérification du seuil
        if row_count < min_lines:
            return self._create_result(
                CheckStatus.WARNING,
                f"Volumétrie basse : {row_count} lignes (attendu >= {min_lines})",
                metrics
            )
        
        return self._create_result(
            CheckStatus.SUCCESS,
            f"{row_count} lignes, volumétrie OK (>= {min_lines})",
            metrics
        )


class BaselineComparisonCheck(BaseCheck):
    """
    Compare le volume du jour à la baseline historique (moyenne des N derniers jours).
    
    Paramètres attendus dans params :
        - tolerance_percent (float) : Tolérance d'écart en % (ex: 20 pour +/-20%)
        - baseline_days (int) : Nombre de jours de référence pour la baseline (ex: 14)
    
    Données attendues :
        - dict avec clés "current_count" (int) et "baseline_avg" (float)
    """
    
    name = "baseline_comparison_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de comparaison à la baseline.
        
        Args:
            data: dict avec current_count et baseline_avg
        
        Returns:
            CheckResult
        """
        tolerance_percent = self.params.get("tolerance_percent", 20)
        
        if not isinstance(data, dict) or "current_count" not in data or "baseline_avg" not in data:
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour BaselineComparisonCheck",
                {"expected_keys": ["current_count", "baseline_avg"]}
            )
        
        current = data["current_count"]
        baseline = data["baseline_avg"]
        
        if baseline == 0:
            return self._create_result(
                CheckStatus.WARNING,
                "Baseline historique à 0, impossible de comparer",
                {"current_count": current, "baseline_avg": baseline}
            )
        
        # Calcul de l'écart en %
        delta_percent = abs((current - baseline) / baseline) * 100
        
        metrics = {
            "current_count": current,
            "baseline_avg": baseline,
            "delta_percent": round(delta_percent, 2),
            "tolerance_percent": tolerance_percent
        }
        
        if delta_percent <= tolerance_percent:
            return self._create_result(
                CheckStatus.SUCCESS,
                f"Volume dans la tolérance : {current} vs {baseline:.0f} (écart {delta_percent:.1f}%, tolérance +/-{tolerance_percent}%)",
                metrics
            )
        else:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Volume hors tolérance : {current} vs {baseline:.0f} (écart {delta_percent:.1f}%, dépassement de +/-{tolerance_percent}%)",
                metrics
            )
