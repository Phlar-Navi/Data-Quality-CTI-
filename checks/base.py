"""
Classe de base pour tous les checks.
Définit le contrat que tout check doit respecter.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from utils.models import CheckResult, CheckStatus, CheckConfidence


class BaseCheck(ABC):
    """
    Check abstrait pour les vérifications de qualité/volumétrie/statut.
    Chaque type de vérification implémente cette interface.
    """
    
    # Nom du check (à surcharger dans les classes concrètes)
    name: str = "unnamed_check"
    
    # Niveau de confiance par défaut (peut être surchargé)
    default_confidence: CheckConfidence = CheckConfidence.DIRECT
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialise le check avec ses paramètres de configuration.
        
        Args:
            params: Dictionnaire de paramètres (seuils, colonnes, etc.)
        """
        self.params = params or {}
    
    @abstractmethod
    def run(self, data: Any, **kwargs) -> CheckResult:
        """
        Exécute le check sur les données fournies.
        
        Args:
            data: Données à vérifier (DataFrame, dict, etc. selon le check)
            **kwargs: Paramètres additionnels contextuels
        
        Returns:
            CheckResult: Résultat structuré du check
        
        Cette méthode doit être implémentée par chaque check concret.
        """
        pass
    
    def _create_result(
        self,
        status: CheckStatus,
        message: str,
        metrics: Dict[str, Any] = None,
        confidence: CheckConfidence = None
    ) -> CheckResult:
        """
        Méthode utilitaire pour créer un CheckResult.
        
        Args:
            status: Statut du check (SUCCESS, WARNING, FAILURE)
            message: Message descriptif du résultat
            metrics: Métriques additionnelles (optionnel)
            confidence: Niveau de confiance (optionnel, utilise default_confidence sinon)
        
        Returns:
            CheckResult
        """
        return CheckResult(
            check_name=self.name,
            status=status,
            confidence=confidence or self.default_confidence,
            message=message,
            metrics=metrics or {}
        )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"
