"""
Module de logging SQLite pour le monitoring CTI.

Stocke les résultats de chaque run dans une base de données SQLite
pour historisation, analyse de tendances et dashboard.

Schema:
    - runs: Run global (1 par exécution de main.py)
    - breakpoint_results: Résultats par breakpoint
    - check_results: Résultats détaillés par check
    - metrics_history: Métriques clés pour trending

Usage:
    from utils.sqlite_logger import SQLiteLogger
    
    logger = SQLiteLogger("data/monitoring.db")
    run_id = logger.log_run(target_date="2026-06-22", ...)
    logger.log_breakpoint_result(run_id, breakpoint_result)
    logger.log_check_result(run_id, breakpoint_id, check_result)
    logger.close()
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class SQLiteLogger:
    """Logger SQLite pour stockage des résultats de monitoring."""
    
    def __init__(self, db_path: str = "data/monitoring.db"):
        """
        Initialise le logger SQLite.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire data si nécessaire
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Créer la connexion
        self.connection = None
        self._connect()
        
        # Initialiser le schema
        self._init_schema()
    
    def _connect(self):
        """Établit la connexion à la base de données."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Activer les foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Activer WAL mode pour meilleures performances
            self.connection.execute("PRAGMA journal_mode = WAL")
            
            self.logger.info(f"[DB] Connexion SQLite établie : {self.db_path}")
        except Exception as e:
            self.logger.error(f"[DB] Erreur connexion SQLite : {e}")
            raise
    
    def _init_schema(self):
        """Crée les tables si elles n'existent pas."""
        try:
            cursor = self.connection.cursor()
            
            # Table runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    run_date TEXT NOT NULL,
                    target_date TEXT,
                    total_breakpoints INTEGER,
                    average_score REAL,
                    status_summary TEXT,
                    execution_time_sec REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_run_id ON runs(run_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_run_date ON runs(run_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_target_date ON runs(target_date)
            """)
            
            # Table breakpoint_results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS breakpoint_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    breakpoint_id TEXT NOT NULL,
                    breakpoint_name TEXT NOT NULL,
                    access_type TEXT,
                    target_date TEXT,
                    run_timestamp TEXT,
                    status TEXT,
                    score INTEGER,
                    total_checks INTEGER,
                    checks_passed INTEGER,
                    checks_warned INTEGER,
                    checks_failed INTEGER,
                    execution_time_sec REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bp_run_id ON breakpoint_results(run_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bp_breakpoint_id ON breakpoint_results(breakpoint_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bp_target_date ON breakpoint_results(target_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bp_score ON breakpoint_results(score)
            """)
            
            # Table check_results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS check_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    breakpoint_id TEXT NOT NULL,
                    check_name TEXT NOT NULL,
                    check_type TEXT,
                    status TEXT NOT NULL,
                    confidence TEXT,
                    message TEXT,
                    metrics TEXT,
                    timestamp TEXT,
                    execution_time_sec REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_run_id ON check_results(run_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_breakpoint_id ON check_results(breakpoint_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_name ON check_results(check_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_status ON check_results(status)
            """)
            
            # Table metrics_history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    breakpoint_id TEXT NOT NULL,
                    target_date TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_unit TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics_history(run_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_breakpoint_id ON metrics_history(breakpoint_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_target_date ON metrics_history(target_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics_history(metric_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_composite 
                ON metrics_history(breakpoint_id, metric_name, target_date)
            """)
            
            self.connection.commit()
            self.logger.info("[DB] Schéma SQLite initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur initialisation schéma : {e}")
            raise
    
    def log_run(
        self,
        run_id: str,
        run_date: str,
        target_date: Optional[str] = None,
        total_breakpoints: int = 0,
        average_score: float = 0.0,
        status_summary: Dict[str, int] = None,
        execution_time_sec: float = 0.0
    ) -> str:
        """
        Log un run global.
        
        Args:
            run_id: ID unique du run (timestamp)
            run_date: Date/heure ISO du run
            target_date: Date cible analysée (None = date du jour)
            total_breakpoints: Nombre de breakpoints exécutés
            average_score: Score moyen
            status_summary: Dict avec compteurs par statut
            execution_time_sec: Durée totale
        
        Returns:
            run_id
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO runs (
                    run_id, run_date, target_date, total_breakpoints,
                    average_score, status_summary, execution_time_sec
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                run_date,
                target_date,
                total_breakpoints,
                average_score,
                json.dumps(status_summary) if status_summary else None,
                execution_time_sec
            ))
            
            self.connection.commit()
            self.logger.debug(f"[DB] Run loggé : {run_id}")
            return run_id
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur log run : {e}")
            self.connection.rollback()
            raise
    
    def log_breakpoint_result(
        self,
        run_id: str,
        breakpoint_result: Dict[str, Any]
    ) -> int:
        """
        Log le résultat d'un breakpoint.
        
        Args:
            run_id: ID du run parent
            breakpoint_result: Dict avec résultat du breakpoint
        
        Returns:
            ID de la ligne insérée
        """
        try:
            cursor = self.connection.cursor()
            
            # Compter les checks par statut
            checks = breakpoint_result.get("checks", [])
            checks_passed = sum(1 for c in checks if c.get("status") == "success")
            checks_warned = sum(1 for c in checks if c.get("status") == "warning")
            checks_failed = sum(1 for c in checks if c.get("status") in ["failure", "error"])
            
            cursor.execute("""
                INSERT INTO breakpoint_results (
                    run_id, breakpoint_id, breakpoint_name, access_type,
                    target_date, run_timestamp, status, score,
                    total_checks, checks_passed, checks_warned, checks_failed,
                    execution_time_sec
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                breakpoint_result.get("breakpoint_id"),
                breakpoint_result.get("breakpoint_name"),
                breakpoint_result.get("access_type"),
                breakpoint_result.get("target_date"),
                breakpoint_result.get("run_timestamp"),
                breakpoint_result.get("status"),
                breakpoint_result.get("score"),
                len(checks),
                checks_passed,
                checks_warned,
                checks_failed,
                None  # execution_time_sec - peut être ajouté plus tard
            ))
            
            self.connection.commit()
            
            bp_id = breakpoint_result.get("breakpoint_id")
            self.logger.debug(f"[DB] Breakpoint loggé : {bp_id}")
            
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur log breakpoint : {e}")
            self.connection.rollback()
            raise
    
    def log_check_result(
        self,
        run_id: str,
        breakpoint_id: str,
        check_result: Dict[str, Any]
    ) -> int:
        """
        Log le résultat d'un check individuel.
        
        Args:
            run_id: ID du run parent
            breakpoint_id: ID du breakpoint parent
            check_result: Dict avec résultat du check
        
        Returns:
            ID de la ligne insérée
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO check_results (
                    run_id, breakpoint_id, check_name, check_type,
                    status, confidence, message, metrics, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                breakpoint_id,
                check_result.get("name"),
                check_result.get("type"),
                check_result.get("status"),
                check_result.get("confidence"),
                check_result.get("message"),
                json.dumps(check_result.get("metrics", {})),
                check_result.get("timestamp")
            ))
            
            self.connection.commit()
            self.logger.debug(f"[DB] Check loggé : {check_result.get('name')}")
            
            return cursor.lastrowid
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur log check : {e}")
            self.connection.rollback()
            raise
    
    def log_metrics(
        self,
        run_id: str,
        breakpoint_id: str,
        target_date: str,
        metrics: List[Dict[str, Any]]
    ):
        """
        Log une liste de métriques pour trending.
        
        Args:
            run_id: ID du run
            breakpoint_id: ID du breakpoint
            target_date: Date des données analysées
            metrics: Liste de dicts avec {name, value, unit, metadata}
        
        Example:
            metrics = [
                {"name": "row_count", "value": 15049, "unit": "rows"},
                {"name": "duplicate_percent", "value": 1.89, "unit": "percent"}
            ]
        """
        try:
            cursor = self.connection.cursor()
            
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO metrics_history (
                        run_id, breakpoint_id, target_date,
                        metric_name, metric_value, metric_unit, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    breakpoint_id,
                    target_date,
                    metric.get("name"),
                    metric.get("value"),
                    metric.get("unit"),
                    json.dumps(metric.get("metadata", {}))
                ))
            
            self.connection.commit()
            self.logger.debug(f"[DB] {len(metrics)} métriques loggées pour {breakpoint_id}")
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur log metrics : {e}")
            self.connection.rollback()
            raise
    
    def log_full_run(
        self,
        run_data: Dict[str, Any],
        breakpoints_results: List[Dict[str, Any]]
    ):
        """
        Log un run complet avec tous ses breakpoints et checks (transaction).
        
        Args:
            run_data: Dict avec données du run global
            breakpoints_results: Liste de dicts avec résultats des breakpoints
        """
        try:
            # Démarrer transaction
            cursor = self.connection.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. Log le run global
            run_id = run_data.get("run_timestamp")
            self.log_run(
                run_id=run_id,
                run_date=run_data.get("run_date"),
                target_date=run_data.get("target_date"),
                total_breakpoints=len(breakpoints_results),
                average_score=sum(bp.get("score", 0) for bp in breakpoints_results) / len(breakpoints_results) if breakpoints_results else 0,
                status_summary=self._compute_status_summary(breakpoints_results)
            )
            
            # 2. Log chaque breakpoint
            for bp_result in breakpoints_results:
                self.log_breakpoint_result(run_id, bp_result)
                
                # 3. Log chaque check du breakpoint
                breakpoint_id = bp_result.get("breakpoint_id")
                for check in bp_result.get("checks", []):
                    self.log_check_result(run_id, breakpoint_id, check)
                
                # 4. Extraire et log les métriques clés
                metrics = self._extract_metrics(bp_result)
                if metrics:
                    self.log_metrics(
                        run_id,
                        breakpoint_id,
                        bp_result.get("target_date"),
                        metrics
                    )
            
            # Commit transaction
            self.connection.commit()
            self.logger.info(f"[DB] Run complet loggé : {run_id} ({len(breakpoints_results)} breakpoints)")
            
        except Exception as e:
            self.logger.error(f"[DB] Erreur log run complet : {e}")
            self.connection.rollback()
            raise
    
    def _compute_status_summary(self, breakpoints_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calcule le résumé des statuts."""
        summary = {}
        for bp in breakpoints_results:
            status = bp.get("status", "unknown")
            summary[status] = summary.get(status, 0) + 1
        return summary
    
    def _extract_metrics(self, breakpoint_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrait les métriques clés d'un résultat de breakpoint.
        
        Returns:
            Liste de métriques {name, value, unit}
        """
        metrics = []
        
        # Score global
        metrics.append({
            "name": "score",
            "value": breakpoint_result.get("score"),
            "unit": "points"
        })
        
        # Parcourir les checks pour extraire métriques
        for check in breakpoint_result.get("checks", []):
            check_metrics = check.get("metrics", {})
            check_name = check.get("name", "unknown")
            
            # row_count
            if "row_count" in check_metrics:
                metrics.append({
                    "name": "row_count",
                    "value": check_metrics["row_count"],
                    "unit": "rows",
                    "metadata": {"source_check": check_name}
                })
            
            # duplicate_count / duplicate_percentage
            if "duplicate_rows" in check_metrics:
                metrics.append({
                    "name": "duplicate_count",
                    "value": check_metrics["duplicate_rows"],
                    "unit": "rows",
                    "metadata": {"source_check": check_name}
                })
            if "duplicate_percentage" in check_metrics:
                metrics.append({
                    "name": "duplicate_percent",
                    "value": check_metrics["duplicate_percentage"],
                    "unit": "percent",
                    "metadata": {"source_check": check_name}
                })
            
            # outlier_count / outlier_percent
            if "total_outliers" in check_metrics:
                metrics.append({
                    "name": "outlier_count",
                    "value": check_metrics["total_outliers"],
                    "unit": "rows",
                    "metadata": {"source_check": check_name}
                })
            if "outlier_percent" in check_metrics:
                metrics.append({
                    "name": "outlier_percent",
                    "value": check_metrics["outlier_percent"],
                    "unit": "percent",
                    "metadata": {"source_check": check_name}
                })
            
            # baseline_delta_percent
            if "delta_percent" in check_metrics:
                metrics.append({
                    "name": "baseline_delta_percent",
                    "value": check_metrics["delta_percent"],
                    "unit": "percent",
                    "metadata": {"source_check": check_name}
                })
            
            # null_rate_max
            if "field_results" in check_metrics:
                null_rates = [
                    field.get("null_rate", 0)
                    for field in check_metrics["field_results"].values()
                ]
                if null_rates:
                    metrics.append({
                        "name": "null_rate_max",
                        "value": max(null_rates),
                        "unit": "percent",
                        "metadata": {"source_check": check_name}
                    })
        
        return metrics
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Exécute une requête SELECT et retourne les résultats.
        
        Args:
            sql: Requête SQL
            params: Paramètres de la requête (tuple)
        
        Returns:
            Liste de dicts (lignes)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"[DB] Erreur query : {e}")
            raise
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les N derniers runs."""
        return self.query("""
            SELECT * FROM runs
            ORDER BY run_date DESC
            LIMIT ?
        """, (limit,))
    
    def get_breakpoint_history(
        self,
        breakpoint_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Retourne l'historique d'un breakpoint."""
        return self.query("""
            SELECT * FROM breakpoint_results
            WHERE breakpoint_id = ?
            ORDER BY target_date DESC
            LIMIT ?
        """, (breakpoint_id, limit))
    
    def get_metric_trend(
        self,
        breakpoint_id: str,
        metric_name: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Retourne l'évolution d'une métrique."""
        return self.query("""
            SELECT target_date, metric_value, metric_unit
            FROM metrics_history
            WHERE breakpoint_id = ? AND metric_name = ?
            ORDER BY target_date DESC
            LIMIT ?
        """, (breakpoint_id, metric_name, limit))
    
    def close(self):
        """Ferme la connexion."""
        if self.connection:
            self.connection.close()
            self.logger.info("[DB] Connexion SQLite fermée")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Fonction helper pour usage simple
def log_monitoring_run(
    run_data: Dict[str, Any],
    breakpoints_results: List[Dict[str, Any]],
    db_path: str = "data/monitoring.db"
):
    """
    Fonction helper pour logger un run complet en une seule fois.
    
    Args:
        run_data: Dict avec données du run global
        breakpoints_results: Liste de résultats des breakpoints
        db_path: Chemin vers la DB SQLite
    
    Example:
        log_monitoring_run(
            run_data={"run_timestamp": "20260912_070705", ...},
            breakpoints_results=[bp1_result, bp2_result, ...]
        )
    """
    with SQLiteLogger(db_path) as logger:
        logger.log_full_run(run_data, breakpoints_results)
