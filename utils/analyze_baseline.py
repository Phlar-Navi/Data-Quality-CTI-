"""
Script d'analyse baseline pour déterminer les seuils d'outliers en production.

Usage:
    python utils/analyze_baseline.py --start-date 2026-05-01 --end-date 2026-06-30
    
Génère un rapport avec :
- Statistiques descriptives (min, max, Q1, Q3, IQR, mean, median)
- Distribution des valeurs catégorielles
- Recommandations de seuils basées sur les données historiques
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.db_connector import OracleConnector
from dotenv import load_dotenv


class BaselineAnalyzer:
    """Analyse les données historiques pour déterminer les seuils optimaux."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db = OracleConnector(db_config)
        
    def analyze_numeric_column(
        self, 
        table_name: str, 
        column_name: str,
        date_column: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Analyse une colonne numérique sur une période donnée.
        
        Returns:
            Dict avec statistiques et recommandations de seuils
        """
        query = f"""
        SELECT {column_name}
        FROM {table_name}
        WHERE {date_column} BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
                                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
          AND {column_name} IS NOT NULL
        """
        
        self.db.connect()
        df = pd.read_sql(query, self.db.connection)
        self.db.disconnect()
        
        if df.empty or df[column_name].std() == 0:
            return {
                "status": "constant_or_empty",
                "message": "Colonne constante ou vide"
            }
        
        values = df[column_name].dropna()
        
        # Statistiques descriptives
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        
        mean = values.mean()
        std = values.std()
        
        # Méthode IQR
        iqr_lower_15 = q1 - 1.5 * iqr
        iqr_upper_15 = q3 + 1.5 * iqr
        outliers_iqr_15 = ((values < iqr_lower_15) | (values > iqr_upper_15)).sum()
        percent_iqr_15 = (outliers_iqr_15 / len(values)) * 100
        
        iqr_lower_20 = q1 - 2.0 * iqr
        iqr_upper_20 = q3 + 2.0 * iqr
        outliers_iqr_20 = ((values < iqr_lower_20) | (values > iqr_upper_20)).sum()
        percent_iqr_20 = (outliers_iqr_20 / len(values)) * 100
        
        iqr_lower_30 = q1 - 3.0 * iqr
        iqr_upper_30 = q3 + 3.0 * iqr
        outliers_iqr_30 = ((values < iqr_lower_30) | (values > iqr_upper_30)).sum()
        percent_iqr_30 = (outliers_iqr_30 / len(values)) * 100
        
        # Méthode Z-Score
        z_scores = np.abs((values - mean) / std)
        outliers_z2 = (z_scores > 2).sum()
        percent_z2 = (outliers_z2 / len(values)) * 100
        
        outliers_z3 = (z_scores > 3).sum()
        percent_z3 = (outliers_z3 / len(values)) * 100
        
        # Recommandation automatique
        if percent_iqr_15 <= 2.0:
            recommended_method = "iqr"
            recommended_multiplier = 1.5
            recommended_percent = percent_iqr_15
        elif percent_iqr_20 <= 2.0:
            recommended_method = "iqr"
            recommended_multiplier = 2.0
            recommended_percent = percent_iqr_20
        elif percent_z3 <= 2.0:
            recommended_method = "zscore"
            recommended_multiplier = 3.0
            recommended_percent = percent_z3
        else:
            recommended_method = "iqr"
            recommended_multiplier = 3.0
            recommended_percent = percent_iqr_30
        
        return {
            "column": column_name,
            "type": "numeric",
            "total_rows": len(values),
            "statistics": {
                "min": float(values.min()),
                "max": float(values.max()),
                "mean": float(mean),
                "median": float(values.median()),
                "std": float(std),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr)
            },
            "outlier_analysis": {
                "iqr_1.5": {
                    "lower_bound": float(iqr_lower_15),
                    "upper_bound": float(iqr_upper_15),
                    "outliers_count": int(outliers_iqr_15),
                    "outliers_percent": round(percent_iqr_15, 2)
                },
                "iqr_2.0": {
                    "lower_bound": float(iqr_lower_20),
                    "upper_bound": float(iqr_upper_20),
                    "outliers_count": int(outliers_iqr_20),
                    "outliers_percent": round(percent_iqr_20, 2)
                },
                "iqr_3.0": {
                    "lower_bound": float(iqr_lower_30),
                    "upper_bound": float(iqr_upper_30),
                    "outliers_count": int(outliers_iqr_30),
                    "outliers_percent": round(percent_iqr_30, 2)
                },
                "zscore_2.0": {
                    "outliers_count": int(outliers_z2),
                    "outliers_percent": round(percent_z2, 2)
                },
                "zscore_3.0": {
                    "outliers_count": int(outliers_z3),
                    "outliers_percent": round(percent_z3, 2)
                }
            },
            "recommendation": {
                "method": recommended_method,
                "multiplier": recommended_multiplier,
                "expected_outliers_percent": round(recommended_percent, 2),
                "reason": f"Méthode {recommended_method.upper()} avec multiplier {recommended_multiplier} génère ~{round(recommended_percent, 2)}% d'outliers (objectif < 2%)"
            }
        }
    
    def analyze_categorical_column(
        self,
        table_name: str,
        column_name: str,
        date_column: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Analyse une colonne catégorielle sur une période donnée.
        
        Returns:
            Dict avec distribution et recommandations de seuil de fréquence
        """
        query = f"""
        SELECT {column_name}, COUNT(*) as freq
        FROM {table_name}
        WHERE {date_column} BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') 
                                AND TO_DATE('{end_date}', 'YYYY-MM-DD')
          AND {column_name} IS NOT NULL
        GROUP BY {column_name}
        ORDER BY freq DESC
        """
        
        self.db.connect()
        df = pd.read_sql(query, self.db.connection)
        self.db.disconnect()
        
        if df.empty:
            return {
                "status": "empty",
                "message": "Aucune donnée"
            }
        
        total = df['freq'].sum()
        df['percent'] = (df['freq'] / total) * 100
        
        # Analyser différents seuils
        thresholds = [0.1, 0.5, 1.0, 2.0, 5.0]
        threshold_analysis = {}
        
        for threshold in thresholds:
            rare_values = df[df['percent'] < threshold]
            rare_count = rare_values['freq'].sum()
            rare_percent = (rare_count / total) * 100
            
            threshold_analysis[f"{threshold}%"] = {
                "rare_values_count": len(rare_values),
                "rare_rows_count": int(rare_count),
                "rare_rows_percent": round(rare_percent, 2)
            }
        
        # Recommandation : choisir le seuil qui génère entre 1% et 3% d'outliers
        recommended_threshold = 0.5
        for threshold in thresholds:
            rare_percent = threshold_analysis[f"{threshold}%"]["rare_rows_percent"]
            if 1.0 <= rare_percent <= 3.0:
                recommended_threshold = threshold
                break
        
        # Distribution des valeurs
        top_10 = df.head(10)[['VALUE' if column_name.upper() == 'VALUE' else column_name, 'freq', 'percent']].to_dict('records')
        
        return {
            "column": column_name,
            "type": "categorical",
            "total_rows": int(total),
            "unique_values": len(df),
            "statistics": {
                "most_common_value": df.iloc[0][column_name],
                "most_common_percent": round(df.iloc[0]['percent'], 2),
                "least_common_value": df.iloc[-1][column_name],
                "least_common_percent": round(df.iloc[-1]['percent'], 2)
            },
            "top_10_values": top_10,
            "threshold_analysis": threshold_analysis,
            "recommendation": {
                "min_frequency_percent": recommended_threshold,
                "expected_outliers_percent": round(
                    threshold_analysis[f"{recommended_threshold}%"]["rare_rows_percent"], 2
                ),
                "reason": f"Seuil {recommended_threshold}% génère ~{round(threshold_analysis[f'{recommended_threshold}%']['rare_rows_percent'], 2)}% d'outliers (objectif 1-3%)"
            }
        }
    
    def generate_yaml_config(self, analyses: List[Dict[str, Any]]) -> str:
        """
        Génère la configuration YAML recommandée basée sur les analyses.
        """
        yaml_lines = [
            "  # Check : Détection d'outliers (seuils basés sur analyse historique)",
            "  - type: outlier_detection_check",
            "    params:",
            "      fail_threshold_percent: 5.0    # Échec si >= 5% d'outliers",
            "      warn_threshold_percent: 2.0    # Warning si >= 2% d'outliers",
            "      ",
            "      columns:"
        ]
        
        for analysis in analyses:
            if analysis.get("status") in ["constant_or_empty", "empty"]:
                yaml_lines.append(f"        # ⚠️ {analysis['column']} : {analysis['message']}")
                continue
            
            if analysis["type"] == "numeric":
                rec = analysis["recommendation"]
                stats = analysis["statistics"]
                yaml_lines.extend([
                    f"        # {analysis['column']} : {stats['min']:.1f} - {stats['max']:.1f} (médiane: {stats['median']:.1f})",
                    f"        - name: {analysis['column']}",
                    f"          type: numeric",
                    f"          method: {rec['method']}",
                ])
                
                if rec['method'] == 'iqr':
                    yaml_lines.append(f"          iqr_multiplier: {rec['multiplier']}")
                else:
                    yaml_lines.append(f"          z_threshold: {rec['multiplier']}")
                
                yaml_lines.append(f"          # Attendu: ~{rec['expected_outliers_percent']}% d'outliers")
                yaml_lines.append("")
            
            elif analysis["type"] == "categorical":
                rec = analysis["recommendation"]
                stats = analysis["statistics"]
                yaml_lines.extend([
                    f"        # {analysis['column']} : {analysis['unique_values']} valeurs uniques (top: {stats['most_common_value']} à {stats['most_common_percent']}%)",
                    f"        - name: {analysis['column']}",
                    f"          type: categorical",
                    f"          min_frequency_percent: {rec['min_frequency_percent']}",
                    f"          # Attendu: ~{rec['expected_outliers_percent']}% d'outliers",
                    ""
                ])
        
        return "\n".join(yaml_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyse baseline pour recommandations de seuils d'outliers"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Date de début (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="Date de fin (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--table",
        default="DWH_CTI_TEST.CDR_EVENTS_V2",
        help="Nom de la table (défaut: DWH_CTI_TEST.CDR_EVENTS_V2)"
    )
    parser.add_argument(
        "--date-column",
        default="FILE_DATE",
        help="Colonne de date (défaut: FILE_DATE)"
    )
    parser.add_argument(
        "--output",
        default="baseline_analysis_report.txt",
        help="Fichier de sortie (défaut: baseline_analysis_report.txt)"
    )
    
    args = parser.parse_args()
    
    # Charger config DB
    load_dotenv("config/.env")
    db_config = {
        "dsn": os.getenv("ORACLE_DSN"),
        "user": os.getenv("ORACLE_USER"),
        "password": os.getenv("ORACLE_PASSWORD")
    }
    
    print(f"🔍 Analyse baseline : {args.start_date} → {args.end_date}")
    print(f"📊 Table : {args.table}")
    print()
    
    analyzer = BaselineAnalyzer(db_config)
    
    # Colonnes à analyser (à adapter selon vos besoins)
    numeric_columns = [
        "DUREE_CONVERSATION",
        "DUREE_FILE",
        "ORIGINAL_FILE_SIZE"
    ]
    
    categorical_columns = [
        "TECHNICAL_RESULT",
        "SEGMENT",
        "UD_SITE_CHOISI"
    ]
    
    analyses = []
    
    # Analyser colonnes numériques
    print("📈 Analyse des colonnes numériques...")
    for col in numeric_columns:
        print(f"   → {col}...", end=" ")
        try:
            result = analyzer.analyze_numeric_column(
                args.table, col, args.date_column, args.start_date, args.end_date
            )
            analyses.append(result)
            if result.get("status"):
                print(f"⚠️ {result['message']}")
            else:
                print(f"✅ {result['recommendation']['method'].upper()} x{result['recommendation']['multiplier']}")
        except Exception as e:
            print(f"❌ Erreur : {e}")
    
    print()
    
    # Analyser colonnes catégorielles
    print("🏷️ Analyse des colonnes catégorielles...")
    for col in categorical_columns:
        print(f"   → {col}...", end=" ")
        try:
            result = analyzer.analyze_categorical_column(
                args.table, col, args.date_column, args.start_date, args.end_date
            )
            analyses.append(result)
            if result.get("status"):
                print(f"⚠️ {result['message']}")
            else:
                print(f"✅ seuil {result['recommendation']['min_frequency_percent']}%")
        except Exception as e:
            print(f"❌ Erreur : {e}")
    
    print()
    print("=" * 80)
    print("📝 RAPPORT D'ANALYSE BASELINE")
    print("=" * 80)
    print()
    
    # Générer le rapport
    report_lines = []
    report_lines.append(f"Période analysée : {args.start_date} → {args.end_date}")
    report_lines.append(f"Table : {args.table}")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    for analysis in analyses:
        if analysis.get("status"):
            report_lines.append(f"⚠️ {analysis.get('column', 'N/A')} : {analysis['message']}")
            report_lines.append("")
            continue
        
        report_lines.append(f"📊 {analysis['column']} ({analysis['type']})")
        report_lines.append("-" * 80)
        
        if analysis['type'] == 'numeric':
            stats = analysis['statistics']
            report_lines.append(f"Min: {stats['min']:.2f} | Max: {stats['max']:.2f} | Moyenne: {stats['mean']:.2f} | Médiane: {stats['median']:.2f}")
            report_lines.append(f"Q1: {stats['q1']:.2f} | Q3: {stats['q3']:.2f} | IQR: {stats['iqr']:.2f}")
            report_lines.append("")
            report_lines.append("Analyse outliers :")
            for method, data in analysis['outlier_analysis'].items():
                if 'lower_bound' in data:
                    report_lines.append(f"  {method:12} : [{data['lower_bound']:8.1f}, {data['upper_bound']:8.1f}] → {data['outliers_count']:5} outliers ({data['outliers_percent']:5.2f}%)")
                else:
                    report_lines.append(f"  {method:12} : {data['outliers_count']:5} outliers ({data['outliers_percent']:5.2f}%)")
            report_lines.append("")
            rec = analysis['recommendation']
            report_lines.append(f"✅ RECOMMANDATION : method={rec['method']}, multiplier={rec['multiplier']}")
            report_lines.append(f"   {rec['reason']}")
        
        elif analysis['type'] == 'categorical':
            stats = analysis['statistics']
            report_lines.append(f"Valeurs uniques : {analysis['unique_values']}")
            report_lines.append(f"Valeur la plus fréquente : {stats['most_common_value']} ({stats['most_common_percent']}%)")
            report_lines.append("")
            report_lines.append("Top 10 valeurs :")
            for item in analysis['top_10_values']:
                val_key = [k for k in item.keys() if k not in ['freq', 'percent']][0]
                report_lines.append(f"  {item[val_key]:30} : {item['freq']:6} ({item['percent']:5.2f}%)")
            report_lines.append("")
            report_lines.append("Analyse par seuil de fréquence :")
            for threshold, data in analysis['threshold_analysis'].items():
                report_lines.append(f"  Seuil {threshold:5} : {data['rare_values_count']:3} valeurs rares → {data['rare_rows_count']:5} lignes ({data['rare_rows_percent']:5.2f}%)")
            report_lines.append("")
            rec = analysis['recommendation']
            report_lines.append(f"✅ RECOMMANDATION : min_frequency_percent={rec['min_frequency_percent']}%")
            report_lines.append(f"   {rec['reason']}")
        
        report_lines.append("")
        report_lines.append("")
    
    # Configuration YAML recommandée
    report_lines.append("=" * 80)
    report_lines.append("🎯 CONFIGURATION YAML RECOMMANDÉE")
    report_lines.append("=" * 80)
    report_lines.append("")
    yaml_config = analyzer.generate_yaml_config(analyses)
    report_lines.append(yaml_config)
    
    # Écrire le rapport
    report_text = "\n".join(report_lines)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print()
    print(f"✅ Rapport sauvegardé : {args.output}")


if __name__ == "__main__":
    main()
