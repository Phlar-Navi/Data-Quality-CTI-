"""
Package des connecteurs.
Expose les classes de connecteurs disponibles.
"""
from .base import BaseConnector
from .oracle_connector import OracleConnector

__all__ = ["BaseConnector", "OracleConnector"]
