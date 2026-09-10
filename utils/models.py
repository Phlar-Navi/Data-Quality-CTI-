"""
Modèles de données pour le système de monitoring.
Définit les structures communes utilisées par tous les composants.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class CheckStatus(Enum):
    """Statut d'un check individuel."""
    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"


class CheckConfidence(Enum):
    """Niveau de confiance d'un check (direct vs déduit)."""
    DIRECT = "direct"      # Mesuré directement à la source
    INFERRED = "inferred"  # Déduit via une trace/proxy


class BreakpointStatus(Enum):
    """Statut macro d'un breakpoint (pour affichage dashboard)."""
    NORMAL = "normal"                    # 10/10
    ANORMAL_DEGRADE = "anormal_degrade"  # 6-9/10
    ANORMAL_CRITIQUE = "anormal_critique"  # ≤5/10
    EN_COURS = "en_cours"                # Run en cours d'exécution
    INCONNU = "inconnu"                  # Échec technique ou jamais exécuté


@dataclass
class CheckResult:
    """
    Résultat d'un check individuel.
    Structure normalisée retournée par tous les checks.
    """
    check_name: str
    status: CheckStatus
    confidence: CheckConfidence
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire pour sérialisation."""
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "confidence": self.confidence.value,
            "message": self.message,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class BreakpointResult:
    """
    Résultat consolidé d'un breakpoint (ensemble de checks).
    Utilisé pour calculer le score global et le statut macro.
    """
    breakpoint_id: str
    breakpoint_name: str
    access_type: str  # "direct" ou "inferred"
    target_date: str  # Date des données contrôlées (YYYY-MM-DD)
    run_timestamp: datetime
    run_state: str  # "completed", "in_progress", "failed"
    checks: list[CheckResult] = field(default_factory=list)
    score: Optional[int] = None  # Score sur 10
    score_max: int = 10
    status: Optional[BreakpointStatus] = None
    
    def calculate_score(self, force_zero_on: Optional[list[str]] = None) -> int:
        """
        Calcule le score global du breakpoint.
        
        Args:
            force_zero_on: Liste des noms de checks qui forcent le score à 0 si en échec
        
        Returns:
            Score sur 10
        """
        if not self.checks:
            return 0
        
        # Vérifier les checks à effet immédiat (score forcé à 0)
        if force_zero_on:
            for check in self.checks:
                if check.check_name in force_zero_on and check.status == CheckStatus.FAILURE:
                    return 0
        
        # Calcul pondéré : nombre de checks réussis / checks attendus
        successful = sum(1 for c in self.checks if c.status == CheckStatus.SUCCESS)
        total = len(self.checks)
        
        score = round((successful / total) * 10) if total > 0 else 0
        return score
    
    def determine_status(self) -> BreakpointStatus:
        """
        Détermine le statut macro du breakpoint basé sur le score.
        
        Returns:
            BreakpointStatus
        """
        if self.run_state == "in_progress":
            return BreakpointStatus.EN_COURS
        
        if self.run_state == "failed" or self.score is None:
            return BreakpointStatus.INCONNU
        
        if self.score == 10:
            return BreakpointStatus.NORMAL
        elif 6 <= self.score <= 9:
            return BreakpointStatus.ANORMAL_DEGRADE
        else:  # score ≤ 5
            return BreakpointStatus.ANORMAL_CRITIQUE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire pour sérialisation/API."""
        return {
            "breakpoint_id": self.breakpoint_id,
            "breakpoint_name": self.breakpoint_name,
            "access": self.access_type,
            "target_date": self.target_date,
            "run_timestamp": self.run_timestamp.isoformat(),
            "run_state": self.run_state,
            "score": self.score,
            "score_max": self.score_max,
            "status": self.status.value if self.status else None,
            "checks": [c.to_dict() for c in self.checks]
        }
