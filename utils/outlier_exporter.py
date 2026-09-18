"""
Module d'export des outliers en CSV.

Exporte les détails granulaires des outliers détectés pour analyse ultérieure.
"""
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class OutlierExporter:
    """Exporteur CSV pour les outliers détectés."""
    
    def __init__(self, output_dir: str = "outliers"):
        """
        Initialise l'exporteur.
        
        Args:
            output_dir: Répertoire de sortie pour les fichiers CSV
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire s'il n'existe pas
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_outliers(
        self,
        run_id: str,
        breakpoint_id: str,
        target_date: str,
        check_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Exporte les outliers d'un check dans un fichier CSV.
        
        Args:
            run_id: ID du run (ex: "20260912_115206")
            breakpoint_id: ID du breakpoint (ex: "bp9_dwh_oracle")
            target_date: Date cible (ex: "2026-06-22")
            check_result: Résultat du check outlier_detection avec "outlier_rows"
        
        Returns:
            Chemin du fichier CSV créé, ou None si pas d'outliers
        """
        # Vérifier qu'on a des outliers
        metrics = check_result.get("details", {})
        outlier_rows = metrics.get("outlier_rows", [])
        
        if not outlier_rows:
            self.logger.info("[EXPORT] Aucun outlier à exporter")
            return None
        
        # Nom du fichier CSV
        filename = f"{run_id}_{breakpoint_id}_outliers.csv"
        filepath = self.output_dir / filename
        
        # Préparer les données avec métadonnées
        csv_rows = []
        for outlier in outlier_rows:
            csv_rows.append({
                "run_id": run_id,
                "breakpoint_id": breakpoint_id,
                "target_date": target_date,
                "row_key": outlier.get("row_key", ""),
                "column_name": outlier.get("column_name", ""),
                "column_value": outlier.get("column_value", ""),
                "outlier_type": outlier.get("outlier_type", ""),
                "outlier_reason": outlier.get("outlier_reason", ""),
                "export_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Écrire le fichier CSV
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    "run_id",
                    "breakpoint_id",
                    "target_date",
                    "row_key",
                    "column_name",
                    "column_value",
                    "outlier_type",
                    "outlier_reason",
                    "export_timestamp"
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            self.logger.info(f"[EXPORT] OK - {len(csv_rows)} outliers exportés vers {filepath}")
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"[EXPORT] Erreur lors de l'export CSV : {e}")
            return None
    
    def export_all_outliers(
        self,
        run_id: str,
        target_date: str,
        results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Exporte tous les outliers de tous les breakpoints dans des fichiers CSV séparés.
        
        Args:
            run_id: ID du run
            target_date: Date cible
            results: Liste des résultats de breakpoints
        
        Returns:
            Liste des chemins de fichiers CSV créés
        """
        exported_files = []
        
        for result in results:
            breakpoint_id = result.get("breakpoint_id", "unknown")
            checks = result.get("checks", [])
            
            # Chercher le check outlier_detection_check
            for check in checks:
                if check.get("name") == "outlier_detection_check":
                    filepath = self.export_outliers(
                        run_id=run_id,
                        breakpoint_id=breakpoint_id,
                        target_date=target_date,
                        check_result=check
                    )
                    
                    if filepath:
                        exported_files.append(filepath)
        
        if exported_files:
            self.logger.info(f"[EXPORT] {len(exported_files)} fichier(s) CSV créé(s)")
        else:
            self.logger.info("[EXPORT] Aucun outlier détecté sur ce run")
        
        return exported_files
    
    def cleanup_old_files(self, retention_days: int = 90):
        """
        Supprime les fichiers CSV de plus de X jours.
        
        Args:
            retention_days: Nombre de jours de rétention
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for filepath in self.output_dir.glob("*.csv"):
            # Récupérer la date de modification du fichier
            file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"[CLEANUP] Impossible de supprimer {filepath}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"[CLEANUP] {deleted_count} fichier(s) CSV supprimé(s) (> {retention_days} jours)")


# Fonction utilitaire pour utilisation standalone
def export_outliers_csv(
    run_id: str,
    breakpoint_id: str,
    target_date: str,
    check_result: Dict[str, Any],
    output_dir: str = "outliers"
) -> Optional[str]:
    """
    Fonction helper pour exporter rapidement des outliers.
    
    Args:
        run_id: ID du run
        breakpoint_id: ID du breakpoint
        target_date: Date cible
        check_result: Résultat du check outlier_detection
        output_dir: Répertoire de sortie
    
    Returns:
        Chemin du fichier CSV créé
    """
    exporter = OutlierExporter(output_dir)
    return exporter.export_outliers(run_id, breakpoint_id, target_date, check_result)
