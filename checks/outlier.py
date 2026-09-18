"""
Check de détection d'outliers (valeurs aberrantes).
Analyse automatique des colonnes numériques et catégorielles.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base import BaseCheck
from utils.models import CheckResult, CheckStatus


class OutlierDetectionCheck(BaseCheck):
    """
    Détecte les valeurs aberrantes (outliers) sur une liste de colonnes.
    
    Paramètres attendus dans params :
        - columns (list[dict]) : Liste des colonnes à analyser
            Exemple:
            [
                {
                    "name": "DUREE_CONVERSATION",
                    "type": "numeric",
                    "method": "iqr",  # "iqr" ou "zscore"
                    "iqr_multiplier": 1.5,  # optionnel, par défaut 1.5
                    "log_sample_size": 10  # Nombre d'outliers à logger
                },
                {
                    "name": "TECHNICAL_RESULT",
                    "type": "categorical",
                    "min_frequency_percent": 0.1  # Seuil en % (valeurs < 0.1% = suspects)
                }
            ]
        
        - fail_threshold_percent (float) : % d'outliers qui déclenche un échec (défaut: 5%)
        - warn_threshold_percent (float) : % d'outliers qui déclenche un warning (défaut: 2%)
    
    Données attendues :
        - DataFrame pandas
    """
    
    name = "outlier_detection_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute la détection d'outliers.
        
        Args:
            data: DataFrame à analyser
        
        Returns:
            CheckResult
        """
        if not isinstance(data, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour OutlierDetectionCheck (DataFrame attendu)"
            )
        
        columns_config = self.params.get("columns", [])
        fail_threshold = self.params.get("fail_threshold_percent", 5.0)
        warn_threshold = self.params.get("warn_threshold_percent", 2.0)
        
        if not columns_config:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune colonne configurée pour la détection d'outliers"
            )
        
        total_rows = len(data)
        if total_rows == 0:
            return self._create_result(
                CheckStatus.WARNING,
                "Dataset vide, impossible d'analyser les outliers"
            )
        
        # Analyser chaque colonne
        all_outliers = {}
        total_outliers = 0
        all_outlier_rows = []  # Collecter TOUS les outliers pour export CSV
        
        for col_config in columns_config:
            col_name = col_config.get("name")
            col_type = col_config.get("type", "numeric")
            
            if col_name not in data.columns:
                all_outliers[col_name] = {
                    "status": "missing",
                    "message": "Colonne manquante"
                }
                continue
            
            # Détecter outliers selon le type
            if col_type == "numeric":
                result = self._detect_numeric_outliers(data, col_config)
            elif col_type == "categorical":
                result = self._detect_categorical_outliers(data, col_config)
            else:
                result = {
                    "status": "error",
                    "message": f"Type '{col_type}' non supporté"
                }
            
            all_outliers[col_name] = result
            total_outliers += result.get("outlier_count", 0)
            
            # Collecter les lignes outliers pour export CSV
            if result.get("outlier_rows") is not None:
                all_outlier_rows.extend(result["outlier_rows"])
        
        # Calcul du taux global d'outliers
        outlier_percent = (total_outliers / total_rows) * 100 if total_rows > 0 else 0
        
        metrics = {
            "total_rows": total_rows,
            "total_outliers": total_outliers,
            "outlier_percent": round(outlier_percent, 2),
            "columns_analyzed": len(columns_config),
            "columns_details": all_outliers,
            "fail_threshold_percent": fail_threshold,
            "warn_threshold_percent": warn_threshold,
            "outlier_rows": all_outlier_rows  # NOUVEAU : Liste complète pour export CSV
        }
        
        # Déterminer le statut
        if outlier_percent >= fail_threshold:
            return self._create_result(
                CheckStatus.FAILURE,
                f"{total_outliers} outliers détectés ({outlier_percent:.2f}%, seuil critique {fail_threshold}%)",
                metrics
            )
        elif outlier_percent >= warn_threshold:
            return self._create_result(
                CheckStatus.WARNING,
                f"{total_outliers} outliers détectés ({outlier_percent:.2f}%, seuil warning {warn_threshold}%)",
                metrics
            )
        else:
            return self._create_result(
                CheckStatus.SUCCESS,
                f"Intégrité OK : {total_outliers} outliers ({outlier_percent:.2f}%, < {warn_threshold}%)",
                metrics
            )
    
    def _detect_numeric_outliers(self, data: pd.DataFrame, col_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détecte les outliers sur une colonne numérique.
        
        Args:
            data: DataFrame
            col_config: Configuration de la colonne
        
        Returns:
            Résultat avec outliers détectés
        """
        col_name = col_config["name"]
        method = col_config.get("method", "iqr")
        log_sample_size = col_config.get("log_sample_size", 10)
        key_column = col_config.get("key_column", None)  # Colonne clé pour identifier les lignes
        
        # Extraire la colonne et nettoyer (retirer NaN)
        col_data = data[col_name].copy()
        
        # Convertir en numérique (au cas où)
        col_data = pd.to_numeric(col_data, errors='coerce')
        
        # Retirer les NaN
        valid_data = col_data.dropna()
        
        if len(valid_data) == 0:
            return {
                "status": "empty",
                "message": "Aucune valeur valide",
                "outlier_count": 0,
                "outlier_rows": []
            }
        
        # Méthode IQR
        if method == "iqr":
            q1 = valid_data.quantile(0.25)
            q3 = valid_data.quantile(0.75)
            iqr = q3 - q1
            multiplier = col_config.get("iqr_multiplier", 1.5)
            
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            
            outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
            outliers = data[outlier_mask]
            
            stats = {
                "method": "iqr",
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "multiplier": multiplier
            }
            
            reason_template = f"IQR: valeur hors bornes [{lower_bound:.2f}, {upper_bound:.2f}]"
        
        # Méthode Z-Score
        elif method == "zscore":
            mean = valid_data.mean()
            std = valid_data.std()
            z_threshold = col_config.get("z_threshold", 3.0)
            
            if std == 0:
                return {
                    "status": "constant",
                    "message": "Colonne constante (écart-type = 0)",
                    "outlier_count": 0,
                    "outlier_rows": []
                }
            
            z_scores = np.abs((col_data - mean) / std)
            outlier_mask = z_scores > z_threshold
            outliers = data[outlier_mask]
            
            stats = {
                "method": "zscore",
                "mean": float(mean),
                "std": float(std),
                "z_threshold": z_threshold
            }
            
            reason_template = f"Z-Score: |z| > {z_threshold}"
        
        else:
            return {
                "status": "error",
                "message": f"Méthode '{method}' non supportée",
                "outlier_count": 0,
                "outlier_rows": []
            }
        
        # Collecter échantillon d'outliers pour log
        outlier_count = len(outliers)
        outlier_sample = outliers[col_name].head(log_sample_size).tolist()
        
        # Collecter TOUS les outliers pour export CSV
        outlier_rows = []
        for idx, row in outliers.iterrows():
            outlier_rows.append({
                "row_key": str(row[key_column]) if key_column and key_column in outliers.columns else str(idx),
                "column_name": col_name,
                "column_value": str(row[col_name]),
                "outlier_type": f"numeric_{method}",
                "outlier_reason": reason_template
            })
        
        return {
            "status": "analyzed",
            "type": "numeric",
            "outlier_count": int(outlier_count),
            "outlier_percent": round((outlier_count / len(data)) * 100, 2),
            "stats": stats,
            "outlier_sample": outlier_sample,
            "outlier_rows": outlier_rows,  # NOUVEAU : Liste complète pour export CSV
            "min_value": float(valid_data.min()),
            "max_value": float(valid_data.max()),
            "mean": float(valid_data.mean()),
            "median": float(valid_data.median())
        }
    
    def _detect_categorical_outliers(self, data: pd.DataFrame, col_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détecte les valeurs rares sur une colonne catégorielle.
        
        Args:
            data: DataFrame
            col_config: Configuration de la colonne
        
        Returns:
            Résultat avec valeurs rares
        """
        col_name = col_config["name"]
        min_freq_percent = col_config.get("min_frequency_percent", 0.1)
        log_sample_size = col_config.get("log_sample_size", 10)
        key_column = col_config.get("key_column", None)  # Colonne clé pour identifier les lignes
        
        # Calculer fréquences
        value_counts = data[col_name].value_counts()
        total_rows = len(data)
        
        # Calculer % pour chaque valeur
        value_freq_percent = (value_counts / total_rows) * 100
        
        # Identifier valeurs rares (< seuil)
        rare_values = value_freq_percent[value_freq_percent < min_freq_percent]
        
        # Compter lignes avec valeurs rares
        outlier_mask = data[col_name].isin(rare_values.index)
        outlier_count = outlier_mask.sum()
        outliers = data[outlier_mask]
        
        # Top valeurs rares
        rare_values_sample = rare_values.head(log_sample_size).to_dict()
        
        # Formater pour log
        rare_values_formatted = {
            str(k): {
                "count": int(value_counts[k]),
                "percent": round(float(v), 4)
            }
            for k, v in rare_values_sample.items()
        }
        
        # Collecter TOUS les outliers pour export CSV
        outlier_rows = []
        for idx, row in outliers.iterrows():
            cat_value = row[col_name]
            cat_freq = value_freq_percent.get(cat_value, 0)
            outlier_rows.append({
                "row_key": str(row[key_column]) if key_column and key_column in outliers.columns else str(idx),
                "column_name": col_name,
                "column_value": str(cat_value),
                "outlier_type": "categorical_rare",
                "outlier_reason": f"Fréquence {cat_freq:.2f}% < seuil {min_freq_percent}%"
            })
        
        return {
            "status": "analyzed",
            "type": "categorical",
            "outlier_count": int(outlier_count),
            "outlier_percent": round((outlier_count / total_rows) * 100, 2),
            "min_frequency_percent": min_freq_percent,
            "rare_values_count": len(rare_values),
            "rare_values": rare_values_formatted,
            "outlier_rows": outlier_rows,  # NOUVEAU : Liste complète pour export CSV
            "unique_values": int(data[col_name].nunique()),
            "most_common": str(value_counts.index[0]),
            "most_common_percent": round((value_counts.iloc[0] / total_rows) * 100, 2)
        }


class DataIntegrityCheck(BaseCheck):
    """
    Check d'intégrité générique : combine plusieurs vérifications.
    
    Paramètres attendus dans params :
        - columns (list[dict]) : Colonnes à analyser (même format que OutlierDetectionCheck)
        - include_outliers (bool) : Inclure détection d'outliers (défaut: True)
        - include_nulls (bool) : Inclure vérification nulls (défaut: True)
        - include_blanks (bool) : Inclure vérification blanks (défaut: True)
    """
    
    name = "data_integrity_check"
    
    def run(self, data, **kwargs) -> CheckResult:
        """
        Exécute le check d'intégrité global.
        
        Args:
            data: DataFrame à analyser
        
        Returns:
            CheckResult
        """
        if not isinstance(data, pd.DataFrame):
            return self._create_result(
                CheckStatus.FAILURE,
                "Données invalides pour DataIntegrityCheck (DataFrame attendu)"
            )
        
        columns_config = self.params.get("columns", [])
        include_outliers = self.params.get("include_outliers", True)
        include_nulls = self.params.get("include_nulls", True)
        include_blanks = self.params.get("include_blanks", True)
        
        if not columns_config:
            return self._create_result(
                CheckStatus.WARNING,
                "Aucune colonne configurée pour l'analyse d'intégrité"
            )
        
        total_rows = len(data)
        issues_summary = {
            "outliers": 0,
            "nulls": 0,
            "blanks": 0
        }
        
        column_details = {}
        
        for col_config in columns_config:
            col_name = col_config.get("name")
            
            if col_name not in data.columns:
                column_details[col_name] = {"status": "missing"}
                continue
            
            col_issues = {}
            
            # 1. Outliers
            if include_outliers:
                outlier_check = OutlierDetectionCheck({"columns": [col_config]})
                outlier_result = outlier_check._detect_numeric_outliers(data, col_config) \
                    if col_config.get("type", "numeric") == "numeric" \
                    else outlier_check._detect_categorical_outliers(data, col_config)
                
                col_issues["outliers"] = outlier_result
                issues_summary["outliers"] += outlier_result.get("outlier_count", 0)
            
            # 2. Nulls
            if include_nulls:
                null_count = int(data[col_name].isna().sum())
                col_issues["nulls"] = {
                    "count": null_count,
                    "percent": round((null_count / total_rows) * 100, 2)
                }
                issues_summary["nulls"] += null_count
            
            # 3. Blanks (chaînes vides)
            if include_blanks and data[col_name].dtype == object:
                blank_count = int(data[col_name].astype(str).str.strip().eq("").sum())
                col_issues["blanks"] = {
                    "count": blank_count,
                    "percent": round((blank_count / total_rows) * 100, 2)
                }
                issues_summary["blanks"] += blank_count
            
            column_details[col_name] = col_issues
        
        # Calcul score global
        total_issues = sum(issues_summary.values())
        issue_percent = (total_issues / (total_rows * len(columns_config))) * 100 if total_rows > 0 else 0
        
        metrics = {
            "total_rows": total_rows,
            "columns_analyzed": len(columns_config),
            "total_issues": total_issues,
            "issue_percent": round(issue_percent, 2),
            "issues_summary": issues_summary,
            "column_details": column_details
        }
        
        # Statut
        if issue_percent >= 5.0:
            return self._create_result(
                CheckStatus.FAILURE,
                f"Intégrité compromise : {total_issues} problèmes ({issue_percent:.2f}%)",
                metrics
            )
        elif issue_percent >= 2.0:
            return self._create_result(
                CheckStatus.WARNING,
                f"Problèmes d'intégrité détectés : {total_issues} ({issue_percent:.2f}%)",
                metrics
            )
        else:
            return self._create_result(
                CheckStatus.SUCCESS,
                f"Intégrité acceptable : {total_issues} problèmes mineurs ({issue_percent:.2f}%)",
                metrics
            )
