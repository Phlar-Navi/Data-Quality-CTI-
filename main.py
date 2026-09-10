"""
Runner principal du système de monitoring CTI.
Charge la configuration, exécute les breakpoints, et exporte les résultats.
"""
import sys
import os
import logging
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import argparse

# Supprimer le warning SQLAlchemy de pandas
warnings.filterwarnings('ignore', message='.*SQLAlchemy connectable.*')

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigLoader
from utils import BreakpointRunner, BreakpointResult, CheckResultLogger


def setup_logging(config: dict) -> logging.Logger:
    """
    Configure le système de logging.
    
    Args:
        config: Configuration globale
    
    Returns:
        Logger configuré
    """
    log_config = config.get("logging", {})
    log_dir = Path(log_config.get("log_dir", "./logs"))
    log_dir.mkdir(exist_ok=True, parents=True)
    
    log_level = getattr(logging, log_config.get("log_level", "INFO"))
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    date_format = log_config.get("date_format", "%Y-%m-%d %H:%M:%S")
    
    # Configuration du logger racine
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_dir / f"monitoring_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("monitoring")


def load_breakpoints(config: dict, config_loader: ConfigLoader) -> List[dict]:
    """
    Charge les breakpoints à exécuter selon la configuration.
    
    Args:
        config: Configuration globale
        config_loader: Instance de ConfigLoader
    
    Returns:
        Liste des configurations de breakpoints
    """
    execution_config = config.get("execution", {})
    mode = execution_config.get("mode", "all")
    
    breakpoints_dir = Path(__file__).parent / "breakpoints"
    
    if mode == "single":
        # Charger uniquement les breakpoints ciblés
        target_ids = execution_config.get("target_breakpoints", [])
        breakpoints = []
        for bp_id in target_ids:
            bp_config = config_loader.load_breakpoint_config(bp_id)
            if bp_config:
                breakpoints.append(bp_config)
        return breakpoints
    
    else:  # mode == "all"
        # Charger tous les fichiers YAML du répertoire breakpoints/
        breakpoints = []
        for yaml_file in breakpoints_dir.glob("*.yaml"):
            bp_id = yaml_file.stem
            bp_config = config_loader.load_breakpoint_config(bp_id)
            if bp_config:
                breakpoints.append(bp_config)
        return breakpoints


def run_breakpoint(bp_config: dict, target_date: Optional[str], logger: logging.Logger) -> BreakpointResult:
    """
    Exécute un breakpoint et retourne le résultat.
    
    Args:
        bp_config: Configuration du breakpoint
        target_date: Date cible (YYYY-MM-DD) ou None pour utiliser check_offset_days
        logger: Logger
    
    Returns:
        Résultat de l'exécution
    """
    bp_id = bp_config["id"]
    bp_name = bp_config["name"]
    
    logger.info(f"===================================================")
    logger.info(f"[RECHERCHE] Exécution du breakpoint : {bp_name} ({bp_id})")
    logger.info(f"===================================================")
    
    try:
        runner = BreakpointRunner(bp_config)
        result = runner.run(target_date=target_date)
        
        # Affichage du résumé
        status_emoji = {
            "Normal": "[OK]",
            "Dégradé": "[WARN]",
            "Critique": "[ECHEC]",
            "En cours": "[REFRESH]",
            "Inconnu": "[INCONNU]"
        }
        emoji = status_emoji.get(result.status.value, "[INCONNU]")
        
        logger.info(f"{emoji} Statut : {result.status.value}")
        logger.info(f"[STATS] Score : {result.score}/10")
        logger.info(f"[DATE] Date cible : {result.target_date}")
        logger.info(f"[HEURE] Exécuté à : {result.run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"")
        
        # Détail des checks
        logger.info(f"[CHECKS] Détail des checks ({len(result.checks)}) :")
        for check in result.checks:
            check_emoji = "[OK]" if check.status.value == "success" else ("[WARN]" if check.status.value == "warning" else "[ECHEC]")
            # CheckResult n'a pas de 'score', seulement un status
            logger.info(f"  {check_emoji} {check.check_name} : {check.status.value}")
            if check.message:
                logger.info(f"      L_ {check.message}")
        
        logger.info(f"")
        return result
        
    except Exception as e:
        logger.error(f"[ECHEC] Échec de l'exécution du breakpoint {bp_id} : {e}", exc_info=True)
        # Créer un résultat d'échec
        result = BreakpointResult(
            breakpoint_id=bp_id,
            breakpoint_name=bp_name,
            access_type=bp_config.get("access", "inconnu"),
            target_date=target_date or datetime.now().date().isoformat(),
            run_timestamp=datetime.now(),
            run_state="failed"
        )
        result.status = "Inconnu"
        return result


def export_results(results: List[BreakpointResult], config: dict, logger: logging.Logger):
    """
    Exporte les résultats au format JSON pour le dashboard.
    
    Args:
        results: Liste des résultats
        config: Configuration globale
        logger: Logger
    """
    dashboard_config = config.get("dashboard", {})
    if not dashboard_config.get("export_enabled", True):
        logger.info("[ENVOI] Export désactivé dans la configuration")
        return
    
    export_dir = Path(dashboard_config.get("export_dir", "./dashboard_data"))
    export_dir.mkdir(exist_ok=True, parents=True)
    
    # Export du run courant
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_file = export_dir / f"run_{timestamp}.json"
    
    # Sérialisation des résultats
    import json
    results_data = []
    for result in results:
        result_dict = {
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
        results_data.append(result_dict)
    
    with open(current_file, "w", encoding="utf-8") as f:
        json.dump({
            "run_timestamp": timestamp,
            "run_date": datetime.now().isoformat(),
            "breakpoints": results_data
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[ENVOI] Résultats exportés : {current_file}")
    
    # Créer/mettre à jour le fichier "latest" pour le dashboard
    latest_file = export_dir / "latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump({
            "run_timestamp": timestamp,
            "run_date": datetime.now().isoformat(),
            "breakpoints": results_data
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[ENVOI] Fichier latest.json mis à jour")


def send_notifications(results: List[BreakpointResult], config: dict, logger: logging.Logger):
    """
    Envoie des notifications si configuré.
    
    Args:
        results: Liste des résultats
        config: Configuration globale
        logger: Logger
    """
    notif_config = config.get("notifications", {})
    if not notif_config.get("enabled", False):
        return
    
    # Filtrer les échecs si send_on_failure_only
    send_on_failure_only = notif_config.get("email", {}).get("send_on_failure_only", True)
    
    if send_on_failure_only:
        failed_results = [r for r in results if r.status.value in ["Critique", "Inconnu"]]
        if not failed_results:
            logger.info("[EMAIL] Aucune alerte critique, notification non envoyée")
            return
        results_to_notify = failed_results
    else:
        results_to_notify = results
    
    logger.info(f"[EMAIL] Envoi de notifications pour {len(results_to_notify)} breakpoint(s)")
    logger.warning("[WARN]  Module de notification non implémenté (TODO: ajouter email/push)")
    # TODO: Implémenter l'envoi d'emails/push selon la config


def main():
    """Point d'entrée principal."""
    # Parse des arguments CLI
    parser = argparse.ArgumentParser(description="Monitoring CTI - Runner principal")
    parser.add_argument(
        "--date",
        type=str,
        help="Date cible au format YYYY-MM-DD (par défaut: J-1 ou check_offset_days de la config)"
    )
    parser.add_argument(
        "--breakpoint",
        type=str,
        help="ID du breakpoint à exécuter (surcharge le mode 'all' de la config)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Chemin vers le fichier de configuration global"
    )
    
    args = parser.parse_args()
    
    # Chargement de la configuration
    config_dir = os.path.dirname(args.config) if args.config else "config"
    config_filename = os.path.basename(args.config) if args.config else "config.yaml"
    config_loader = ConfigLoader(config_dir=config_dir)
    
    # Charger config globale
    global_config = config_loader.load_global_config(config_filename=config_filename)
    
    # Configuration du logging
    logger = setup_logging(global_config)
    logger.info("="*60)
    logger.info("[DEMARRAGE] DÉMARRAGE DU MONITORING CTI")
    logger.info("="*60)
    logger.info(f"[DATE] Date d'exécution : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.date:
        logger.info(f"[DATE] Date cible forcée : {args.date}")
    
    # Chargement des breakpoints
    if args.breakpoint:
        logger.info(f"[CIBLE] Mode single : breakpoint '{args.breakpoint}'")
        global_config["execution"]["mode"] = "single"
        global_config["execution"]["target_breakpoints"] = [args.breakpoint]
    
    breakpoints = load_breakpoints(global_config, config_loader)
    logger.info(f"[PACKAGE] {len(breakpoints)} breakpoint(s) à exécuter")
    logger.info("")
    
    # Exécution des breakpoints
    results = []
    for bp_config in breakpoints:
        result = run_breakpoint(bp_config, target_date=args.date, logger=logger)
        results.append(result)
    
    # Résumé global
    logger.info("="*60)
    logger.info("[STATS] RÉSUMÉ GLOBAL")
    logger.info("="*60)
    
    status_counts = {}
    for result in results:
        status = result.status.value if hasattr(result.status, 'value') else str(result.status)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        logger.info(f"  {status} : {count}")
    
    scores_valides = [r.score for r in results if r.score is not None]
    avg_score = sum(scores_valides) / len(scores_valides) if scores_valides else 0
    logger.info(f"")
    logger.info(f"[SCORE] Score moyen : {avg_score:.1f}/10")
    logger.info("")
    
    # Export des résultats
    export_results(results, global_config, logger)
    
    # Sauvegarde des résultats (logs JSON/TXT)
    log_config = global_config.get("logging", {})
    log_dir = log_config.get("log_dir", "./logs")
    result_logger = CheckResultLogger(log_dir=log_dir)
    result_logger.log_batch(results, format="both")
    logger.info(f"[SAUVEGARDE] Résultats sauvegardés dans {log_dir}")
    
    # Nettoyage des anciens logs
    retention_days = log_config.get("retention_days", 30)
    result_logger.cleanup_old_logs(retention_days=retention_days)
    logger.info("")
    
    # Notifications
    send_notifications(results, global_config, logger)
    
    logger.info("="*60)
    logger.info("[OK] MONITORING TERMINÉ")
    logger.info("="*60)
    
    # Code de sortie (0 si tout est OK, 1 si au moins un breakpoint est critique)
    critical_count = sum(1 for r in results if r.status.value == "Critique")
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
