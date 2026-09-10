"""
Logger des résultats de checks.
Sauvegarde les résultats au format JSON et texte pour l'historique et le dashboard.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .models import BreakpointResult, CheckResult


class CheckResultLogger:
    """
    Gère la persistance des résultats de monitoring.
    Supporte JSON (pour le dashboard) et TXT (pour lecture humaine).
    """
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialise le logger de résultats.
        
        Args:
            log_dir: Répertoire de stockage des logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Créer les sous-répertoires
        self.json_dir = self.log_dir / "json"
        self.text_dir = self.log_dir / "text"
        self.json_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)
    
    def log_result(self, result: BreakpointResult, format: str = "both"):
        """
        Sauvegarde un résultat de breakpoint.
        
        Args:
            result: Résultat à sauvegarder
            format: Format de sauvegarde ("json", "text", "both")
        """
        timestamp = result.run_timestamp.strftime("%Y%m%d_%H%M%S")
        base_filename = f"{result.breakpoint_id}_{timestamp}"
        
        if format in ["json", "both"]:
            self._save_json(result, base_filename)
        
        if format in ["text", "both"]:
            self._save_text(result, base_filename)
    
    def log_batch(self, results: List[BreakpointResult], format: str = "both"):
        """
        Sauvegarde un lot de résultats (tous les breakpoints d'un run).
        
        Args:
            results: Liste des résultats
            format: Format de sauvegarde ("json", "text", "both")
        """
        if not results:
            return
        
        timestamp = results[0].run_timestamp.strftime("%Y%m%d_%H%M%S")
        
        if format in ["json", "both"]:
            self._save_batch_json(results, timestamp)
        
        if format in ["text", "both"]:
            self._save_batch_text(results, timestamp)
    
    def _save_json(self, result: BreakpointResult, filename: str):
        """
        Sauvegarde un résultat au format JSON.
        
        Args:
            result: Résultat à sauvegarder
            filename: Nom de fichier (sans extension)
        """
        filepath = self.json_dir / f"{filename}.json"
        
        data = self._serialize_result(result)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_batch_json(self, results: List[BreakpointResult], timestamp: str):
        """
        Sauvegarde un lot de résultats au format JSON.
        
        Args:
            results: Liste des résultats
            timestamp: Timestamp du run
        """
        filepath = self.json_dir / f"batch_{timestamp}.json"
        
        data = {
            "run_timestamp": timestamp,
            "run_date": results[0].run_timestamp.isoformat(),
            "breakpoints_count": len(results),
            "breakpoints": [self._serialize_result(r) for r in results]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_text(self, result: BreakpointResult, filename: str):
        """
        Sauvegarde un résultat au format texte lisible.
        
        Args:
            result: Résultat à sauvegarder
            filename: Nom de fichier (sans extension)
        """
        filepath = self.text_dir / f"{filename}.txt"
        
        lines = self._format_result_text(result)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    def _save_batch_text(self, results: List[BreakpointResult], timestamp: str):
        """
        Sauvegarde un lot de résultats au format texte lisible.
        
        Args:
            results: Liste des résultats
            timestamp: Timestamp du run
        """
        filepath = self.text_dir / f"batch_{timestamp}.txt"
        
        lines = []
        lines.append("="*80)
        lines.append(f"MONITORING CTI - RAPPORT D'EXÉCUTION")
        lines.append("="*80)
        lines.append(f"Date d'exécution : {results[0].run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Nombre de breakpoints : {len(results)}")
        lines.append("")
        
        # Résumé global
        status_counts = {}
        total_score = 0
        for result in results:
            status = result.status.value if hasattr(result.status, 'value') else str(result.status)
            status_counts[status] = status_counts.get(status, 0) + 1
            total_score += result.score
        
        avg_score = total_score / len(results) if results else 0
        
        lines.append("RÉSUMÉ GLOBAL")
        lines.append("-" * 80)
        for status, count in status_counts.items():
            lines.append(f"  {status:15} : {count}")
        lines.append(f"\n  Score moyen     : {avg_score:.1f}/10")
        lines.append("")
        
        # Détail par breakpoint
        lines.append("="*80)
        lines.append("DÉTAIL PAR BREAKPOINT")
        lines.append("="*80)
        lines.append("")
        
        for result in results:
            lines.extend(self._format_result_text(result))
            lines.append("")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    def _serialize_result(self, result: BreakpointResult) -> Dict[str, Any]:
        """
        Sérialise un BreakpointResult en dictionnaire.
        
        Args:
            result: Résultat à sérialiser
        
        Returns:
            Dictionnaire sérialisé
        """
        return {
            "breakpoint_id": result.breakpoint_id,
            "breakpoint_name": result.breakpoint_name,
            "access_type": result.access_type,
            "target_date": result.target_date,
            "run_timestamp": result.run_timestamp.isoformat(),
            "run_state": result.run_state,
            "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
            "score": result.score,
            "checks": [
                {
                    "name": check.check_name,
                    "status": check.status.value,
                    "confidence": check.confidence.value,
                    "message": check.message,
                    "metrics": check.metrics,
                    "timestamp": check.timestamp.isoformat()
                }
                for check in result.checks
            ]
        }
    
    def _format_result_text(self, result: BreakpointResult) -> List[str]:
        """
        Formate un résultat en lignes de texte lisibles.
        
        Args:
            result: Résultat à formater
        
        Returns:
            Liste de lignes de texte
        """
        lines = []
        
        # En-tête
        lines.append("-" * 80)
        lines.append(f"BREAKPOINT : {result.breakpoint_name} ({result.breakpoint_id})")
        lines.append("-" * 80)
        
        # Métadonnées
        status_str = result.status.value if hasattr(result.status, 'value') else str(result.status)
        lines.append(f"Statut          : {status_str}")
        lines.append(f"Score global    : {result.score}/10")
        lines.append(f"Type d'accès    : {result.access_type}")
        lines.append(f"Date cible      : {result.target_date}")
        lines.append(f"Exécuté à       : {result.run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"État            : {result.run_state}")
        lines.append("")
        
        # Checks
        lines.append(f"CHECKS ({len(result.checks)}) :")
        lines.append("")
        
        for i, check in enumerate(result.checks, 1):
            lines.append(f"  [{i}] {check.check_name}")
            lines.append(f"      Statut     : {check.status.value}")
            lines.append(f"      Confiance  : {check.confidence.value}")
            
            if check.message:
                lines.append(f"      Message    : {check.message}")
            
            if check.metrics:
                lines.append(f"      Métriques  :")
                for key, value in check.metrics.items():
                    # Formater selon le type de valeur
                    if isinstance(value, dict):
                        lines.append(f"        {key}:")
                        for sub_key, sub_value in value.items():
                            lines.append(f"          {sub_key}: {sub_value}")
                    elif isinstance(value, list):
                        lines.append(f"        {key}: {len(value)} éléments")
                    else:
                        lines.append(f"        {key}: {value}")
            
            lines.append("")
        
        return lines
    
    def get_history(self, breakpoint_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des résultats.
        
        Args:
            breakpoint_id: ID du breakpoint (None = tous)
            limit: Nombre de résultats à retourner
        
        Returns:
            Liste des résultats historiques
        """
        history = []
        
        # Parcourir les fichiers JSON
        json_files = sorted(self.json_dir.glob("*.json"), reverse=True)
        
        for json_file in json_files:
            # Ignorer les fichiers batch
            if json_file.name.startswith("batch_"):
                continue
            
            # Filtrer par breakpoint_id si spécifié
            if breakpoint_id and not json_file.name.startswith(breakpoint_id):
                continue
            
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                history.append(data)
            
            if len(history) >= limit:
                break
        
        return history
    
    def cleanup_old_logs(self, retention_days: int = 30):
        """
        Nettoie les anciens logs.
        
        Args:
            retention_days: Nombre de jours à conserver
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for log_file in self.json_dir.glob("*.json"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                log_file.unlink()
        
        for log_file in self.text_dir.glob("*.txt"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                log_file.unlink()
