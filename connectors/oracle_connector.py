"""
Connecteur Oracle pour le Datawarehouse CTI.
Connexion en lecture seule uniquement (sécurité).
"""
import oracledb
import pandas as pd
from typing import Optional
from .base import BaseConnector


class OracleConnector(BaseConnector):
    """
    Connecteur Oracle avec accès en lecture seule.
    
    Sécurité :
    - Refuse toute requête non-SELECT
    - Ne doit jamais avoir de permissions INSERT/UPDATE/DELETE
    - Le compte utilisé doit être limité à GRANT SELECT uniquement
    
    Usage :
        with OracleConnector(dsn="...", user="...", password="...") as conn:
            df = conn.query("SELECT * FROM table WHERE date = :date", {"date": "2026-09-02"})
    """
    
    def __init__(self, dsn: str, user: str, password: str, **kwargs):
        """
        Initialise le connecteur Oracle.
        
        Args:
            dsn: Data Source Name (ex: "host:port/service_name")
            user: Nom d'utilisateur (recommandé : compte en lecture seule)
            password: Mot de passe
            **kwargs: Paramètres additionnels pour oracledb.connect()
        """
        super().__init__(dsn=dsn, user=user, password=password, **kwargs)
        self._connection: Optional[oracledb.Connection] = None
    
    def connect(self) -> None:
        """
        Établit la connexion à la base Oracle.
        
        Raises:
            ConnectionError: Si la connexion échoue
        """
        try:
            self._connection = oracledb.connect(
                user=self.params["user"],
                password=self.params["password"],
                dsn=self.params["dsn"]
            )
        except oracledb.Error as e:
            raise ConnectionError(f"Échec de connexion Oracle : {e}")
    
    def disconnect(self) -> None:
        """Ferme la connexion Oracle proprement."""
        if self._connection:
            try:
                self._connection.close()
            except oracledb.Error:
                pass  # Ignorer les erreurs de fermeture
            finally:
                self._connection = None
    
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion est active.
        
        Returns:
            True si connecté, False sinon
        """
        return self._connection is not None
    
    def query(self, sql: str, params: dict = None) -> pd.DataFrame:
        """
        Exécute une requête SELECT et retourne un DataFrame.
        
        Args:
            sql: Requête SQL (doit commencer par SELECT)
            params: Paramètres de la requête (optionnel, pour :param dans la requête)
        
        Returns:
            DataFrame pandas avec les résultats
        
        Raises:
            ValueError: Si la requête n'est pas un SELECT (sécurité)
            ConnectionError: Si pas de connexion active
            oracledb.Error: En cas d'erreur SQL
        
        Exemples:
            >>> df = conn.query("SELECT * FROM table WHERE date = :date", {"date": "2026-09-02"})
            >>> count = conn.query("SELECT COUNT(*) as cnt FROM table WHERE date = :date", {"date": "2026-09-02"})
        """
        if not self.is_connected():
            raise ConnectionError("Aucune connexion Oracle active. Appelez connect() d'abord.")
        
        # Sécurité : refuser toute requête non-SELECT
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            raise ValueError(
                "OracleConnector est en lecture seule : seules les requêtes SELECT sont autorisées. "
                f"Requête reçue : {sql[:50]}..."
            )
        
        try:
            df = pd.read_sql(sql, self._connection, params=params or {})
            return df
        except oracledb.Error as e:
            raise oracledb.Error(f"Erreur lors de l'exécution de la requête : {e}")
    
    def execute_scalar(self, sql: str, params: dict = None) -> any:
        """
        Exécute une requête SELECT qui retourne une seule valeur (ex: COUNT, MAX).
        
        Args:
            sql: Requête SQL retournant une seule ligne/colonne
            params: Paramètres de la requête (optionnel)
        
        Returns:
            La valeur scalaire retournée (int, str, date, etc.)
        
        Exemple:
            >>> count = conn.execute_scalar("SELECT COUNT(*) FROM table WHERE date = :date", {"date": "2026-09-02"})
        """
        df = self.query(sql, params)
        if df.empty:
            return None
        return df.iloc[0, 0]  # Première ligne, première colonne
    
    def get_table_columns(self, table_name: str, schema: str = None) -> list[str]:
        """
        Récupère la liste des colonnes d'une table/vue.
        
        Args:
            table_name: Nom de la table
            schema: Nom du schéma (optionnel, utilise le schéma de l'utilisateur si omis)
        
        Returns:
            Liste des noms de colonnes
        
        Exemple:
            >>> cols = conn.get_table_columns("CTI_EVENTS", schema="DWH")
        """
        if schema:
            sql = """
                SELECT column_name 
                FROM all_tab_columns 
                WHERE table_name = :table_name 
                  AND owner = :schema
                ORDER BY column_id
            """
            params = {"table_name": table_name.upper(), "schema": schema.upper()}
        else:
            sql = """
                SELECT column_name 
                FROM user_tab_columns 
                WHERE table_name = :table_name
                ORDER BY column_id
            """
            params = {"table_name": table_name.upper()}
        
        df = self.query(sql, params)
        return df["COLUMN_NAME"].tolist() if not df.empty else []
