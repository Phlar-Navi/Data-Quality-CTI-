"""
Classe de base pour tous les connecteurs.
Définit le contrat que tout connecteur doit respecter.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """
    Connecteur abstrait pour l'accès aux sources de données.
    Chaque type de source (Oracle, SFTP, API...) implémente cette interface.
    """
    
    def __init__(self, **kwargs):
        """
        Initialise le connecteur avec les paramètres fournis.
        Les paramètres spécifiques dépendent du type de connecteur.
        """
        self.params = kwargs
        self._connection = None
    
    @abstractmethod
    def connect(self) -> None:
        """
        Établit la connexion à la source de données.
        Doit être implémenté par chaque connecteur concret.
        
        Raises:
            ConnectionError: Si la connexion échoue
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Ferme proprement la connexion à la source de données.
        Doit être implémenté par chaque connecteur concret.
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion est active.
        
        Returns:
            True si connecté, False sinon
        """
        pass
    
    def __enter__(self):
        """Support du context manager (with statement)."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme la connexion à la sortie du context manager."""
        self.disconnect()
        return False  # Ne supprime pas les exceptions
