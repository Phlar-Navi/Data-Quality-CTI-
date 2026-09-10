"""
Checks de qualité des données.
Vérifie la conformité de schéma, les doublons, les valeurs manquantes.
"""
import pandas as pd
import numpy as np
from .base import BaseCheck
from utils.models import CheckResult, CheckStatus


class SchemaConformityCheck(BaseCheck):
    """
    Vérifie la présence des colonnes obligatoires dans les données.
    
    Paramètres attendus dans params :
        - mandatory_columns (list[str]) : Liste des colonnes obligatoires
    
    Données attendues :
        - DataFrame pandas
    """
    
    name = "schema_conformity_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de conformité de schéma.
        
        Args:
            data: DataFrame à vérifier
        
        Returns:
            CheckResult
        """
        if not isinstance(data, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour SchemaConformityCheck (DataFrame attendu)"
            )
        
        mandatory_columns = self.params.get("mandatory_columns", [])
        
        if not mandatory_columns:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune colonne obligatoire définie dans la configuration"
            )
        
        actual_columns = set(data.columns)
        expected_columns = set(mandatory_columns)
        
        missing_columns = expected_columns - actual_columns
        
        metrics = {
            "expected_columns": len(expected_columns),
            "found_columns": len(actual_columns),
            "missing_columns": list(missing_columns) if missing_columns else []
        }
        
        if missing_columns:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Colonnes manquantes : {', '.join(sorted(missing_columns))}",
                metrics
            )
        
        return self._create_result(
            CheckStatus.SUCCESS,
            f"Toutes les colonnes obligatoires présentes ({len(expected_columns)}/{len(expected_columns)})",
            metrics
        )


class DuplicateKeyCheck(BaseCheck):
    """
    Détecte les doublons sur la/les clé(s) primaire(s).
    
    Paramètres attendus dans params :
        - primary_keys (list[str]) : Liste des colonnes formant la clé primaire
        - tolerance (int) : Nombre de doublons toléré (par défaut 0)
    
    Données attendues :
        - DataFrame pandas
    """
    
    name = "duplicate_key_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de détection de doublons.
        
        Args:
            data: DataFrame à vérifier
        
        Returns:
            CheckResult
        """
        if not isinstance(data, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour DuplicateKeyCheck (DataFrame attendu)"
            )
        
        primary_keys = self.params.get("primary_keys", [])
        tolerance = self.params.get("tolerance", 0)
        
        if not primary_keys:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune clé primaire définie dans la configuration"
            )
        
        # Vérifier que les colonnes existent
        missing_keys = [k for k in primary_keys if k not in data.columns]
        if missing_keys:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Colonnes de clé primaire manquantes : {', '.join(missing_keys)}"
            )
        
        # Nettoyer les valeurs (strip, conversion string)
        subset_data = data[primary_keys].copy()
        for col in primary_keys:
            subset_data[col] = subset_data[col].astype(str).str.strip()
        
        # Détecter les blancs/nulls
        is_blank = subset_data.eq("").any(axis=1) | subset_data.eq("nan").any(axis=1)
        blank_count = int(is_blank.sum())
        
        # Travailler sur les données nettoyées
        clean_data = subset_data[~is_blank]
        
        if clean_data.empty:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune clé primaire valide (toutes vides/nulles)",
                {"blank_keys": blank_count}
            )
        
        # Détecter les doublons
        duplicated_mask = clean_data.duplicated(keep=False)
        duplicate_rows = int(duplicated_mask.sum())
        
        # Compter les clés distinctes dupliquées
        duplicated_keys = clean_data[duplicated_mask].drop_duplicates()
        num_duplicated_keys = len(duplicated_keys)
        
        metrics = {
            "total_rows": len(data),
            "blank_keys": blank_count,
            "clean_rows": len(clean_data),
            "duplicate_rows": duplicate_rows,
            "duplicated_keys_count": num_duplicated_keys,
            "duplicate_percentage": round((duplicate_rows / len(clean_data) * 100), 2) if len(clean_data) > 0 else 0
        }
        
        if duplicate_rows == 0:
            return self._create_result(
                CheckStatus.SUCCESS,
                f"Aucun doublon détecté sur {', '.join(primary_keys)} ({blank_count} clés vides exclues)",
                metrics
            )
        elif duplicate_rows <= tolerance:
            return self._create_result(
                CheckStatus.WARNING,
                f"{duplicate_rows} doublons détectés (dans la tolérance de {tolerance})",
                metrics
            )
        else:
            return self._create_result(
                CheckStatus.FAILURE,
                f"{duplicate_rows} doublons détectés sur {', '.join(primary_keys)} ({num_duplicated_keys} clés distinctes dupliquées, {metrics['duplicate_percentage']}%)",
                metrics
            )


class NullRateCheck(BaseCheck):
    """
    Mesure le taux de valeurs nulles/vides sur un ou plusieurs champs critiques.
    
    Paramètres attendus dans params :
        - critical_fields (list[str]) : Liste des champs critiques à vérifier
        - max_null_rate_percent (float) : Taux de nullité maximal toléré en % (ex: 2.0 pour 2%)
    
    Données attendues :
        - DataFrame pandas
    """
    
    name = "null_rate_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check de taux de nullité.
        
        Args:
            data: DataFrame à vérifier
        
        Returns:
            CheckResult
        """
        if not isinstance(data, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour NullRateCheck (DataFrame attendu)"
            )
        
        critical_fields = self.params.get("critical_fields", [])
        max_null_rate = self.params.get("max_null_rate_percent", 2.0)
        
        if not critical_fields:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucun champ critique défini dans la configuration"
            )
        
        total_rows = len(data)
        if total_rows == 0:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune ligne à vérifier (dataset vide)"
            )
        
        # Calculer le taux de nullité par champ
        field_results = {}
        fields_over_threshold = []
        
        for field in critical_fields:
            if field not in data.columns:
                field_results[field] = {"status": "missing", "null_rate": None}
                continue
            
            # Compter les nulls (NA + chaînes vides après strip)
            null_count = data[field].isna().sum()
            if data[field].dtype == object:  # Si c'est une colonne de type string
                empty_count = data[field].astype(str).str.strip().eq("").sum()
                null_count += empty_count
            
            null_rate = (null_count / total_rows) * 100
            field_results[field] = {
                "null_count": int(null_count),
                "null_rate": round(null_rate, 2)
            }
            
            if null_rate > max_null_rate:
                fields_over_threshold.append(field)
        
        metrics = {
            "total_rows": total_rows,
            "max_null_rate_percent": max_null_rate,
            "field_results": field_results,
            "fields_over_threshold": fields_over_threshold
        }
        
        if fields_over_threshold:
            worst_field = max(field_results.items(), 
                            key=lambda x: x[1].get("null_rate", 0) if isinstance(x[1], dict) else 0)
            return self._create_result(
                CheckStatus.FAILURE,
                f"{len(fields_over_threshold)} champ(s) dépassent le seuil de {max_null_rate}% : {', '.join(fields_over_threshold)} (pire : {worst_field[0]} à {worst_field[1]['null_rate']}%)",
                metrics
            )
        
        avg_null_rate = sum(r.get("null_rate", 0) for r in field_results.values() if isinstance(r, dict)) / len(critical_fields)
        return self._create_result(
            CheckStatus.SUCCESS,
            f"Taux de nullité acceptable sur tous les champs critiques (moy. {avg_null_rate:.2f}%, seuil {max_null_rate}%)",
            metrics
        )
