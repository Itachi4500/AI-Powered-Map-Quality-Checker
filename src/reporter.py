"""
Enhanced Error Report Generator
Executive-ready, ML-aware, deployment-safe
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json


class ErrorReporter:
    """
    Generates intelligent, explainable QA reports
    with severity scoring and risk assessment.
    """

    def __init__(self):
        self.report_data = {}

    # ---------------------------------------------------
    # MAIN REPORT GENERATOR
    # ---------------------------------------------------

    def generate_report(
        self,
        validated_df: pd.DataFrame,
        errors_df: pd.DataFrame,
        anomaly_df: Optional[pd.DataFrame] = None,
        validation_summary: Optional[Dict] = None,
        anomaly_summary: Optional[Dict] = None
    ) -> Dict:

        total_features = len(validated_df)

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_features": total_features,
                "report_version": "2.0"
            },
            "executive_summary": {},
            "validation": validation_summary or {},
            "anomaly_detection": anomaly_summary or {},
            "combined_issues": {},
            "risk_assessment": {},
            "recommendations": []
        }

        # Validation error details
        if errors_df is not None and not errors_df.empty:
            report["validation"]["errors_by_type"] = (
                errors_df["error_type"].value_counts().to_dict()
                if "error_type" in errors_df.columns else {}
            )

            report["validation"]["top_errors"] = errors_df.head(10).to_dict("records")

        # Top anomalies
        if anomaly_df is not None and "is_anomaly" in anomaly_df.columns:
            anomalous = anomaly_df[anomaly_df["is_anomaly"]]
            report["anomaly_detection"]["top_anomalies"] = self._get_top_anomalies(anomalous)

        # Combined issue analysis
        report["combined_issues"] = self._analyze_combined(validated_df, anomaly_df)

        # Risk scoring
        risk_score = self._calculate_risk_score(
            validated_df, errors_df, anomaly_df
        )

        report["risk_assessment"] = {
            "risk_score": risk_score,
            "severity_level": self._severity_label(risk_score)
        }

        # Data Quality Index
        report["executive_summary"] = self._generate_executive_summary(
            validated_df, errors_df, anomaly_df, risk_score
        )

        # Recommendations
        report["recommendations"] = self._generate_recommendations(
            validated_df, errors_df, anomaly_df
        )

        self.report_data = report
        return report

    # ---------------------------------------------------
    # TOP ANOMALIES
    # ---------------------------------------------------

    def _get_top_anomalies(self, df: pd.DataFrame, top_n=10) -> List[Dict]:

        if df.empty or "anomaly_score" not in df.columns:
            return []

        df_sorted = df.sort_values("anomaly_score").head(top_n)

        results = []
        for idx, row in df_sorted.iterrows():
            bounds = row.geometry.bounds if "geometry" in df.columns else None

            results.append({
                "feature_id": int(idx),
                "anomaly_score": float(row["anomaly_score"]),
                "confidence": float(row.get("anomaly_confidence", 0)),
                "geometry_type": row.get("geometry_type", "Unknown"),
                "bounds": list(bounds) if bounds else None
            })

        return results

    # ---------------------------------------------------
    # COMBINED ISSUES
    # ---------------------------------------------------

    def _analyze_combined(self, validated_df, anomaly_df):

        combined = {}

        if anomaly_df is None:
            return combined

        invalid = validated_df[~validated_df["is_valid"]].index \
            if "is_valid" in validated_df.columns else []

        anomalous = anomaly_df[anomaly_df["is_anomaly"]].index \
            if "is_anomaly" in anomaly_df.columns else []

        both = set(invalid).intersection(set(anomalous))

        combined["features_with_both_issues"] = len(both)
        combined["only_validation_errors"] = len(invalid) - len(both)
        combined["only_anomalies"] = len(anomalous) - len(both)

        return combined

    # ---------------------------------------------------
    # RISK SCORE
    # ---------------------------------------------------

    def _calculate_risk_score(self, validated_df, errors_df, anomaly_df):

        total = len(validated_df)
        if total == 0:
            return 0

        invalid_count = (
            (~validated_df["is_valid"]).sum()
            if "is_valid" in validated_df.columns else 0
        )

        anomaly_count = (
            anomaly_df["is_anomaly"].sum()
            if anomaly_df is not None and "is_anomaly" in anomaly_df.columns else 0
        )

        error_weight = 0.6
        anomaly_weight = 0.4

        score = (
            (invalid_count / total) * 100 * error_weight +
            (anomaly_count / total) * 100 * anomaly_weight
        )

        return round(min(score, 100), 2)

    def _severity_label(self, score):

        if score < 10:
            return "Low"
        elif score < 30:
            return "Moderate"
        elif score < 60:
            return "High"
        else:
            return "Critical"

    # ---------------------------------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------------------------------

    def _generate_executive_summary(self, validated_df, errors_df, anomaly_df, risk_score):

        total = len(validated_df)

        valid_count = (
            validated_df["is_valid"].sum()
            if "is_valid" in validated_df.columns else total
        )

        anomaly_count = (
            anomaly_df["is_anomaly"].sum()
            if anomaly_df is not None and "is_anomaly" in anomaly_df.columns else 0
        )

        data_quality_index = round((valid_count / total) * 100, 2) if total > 0 else 0

        return {
            "data_quality_index": data_quality_index,
            "valid_features": int(valid_count),
            "invalid_features": int(total - valid_count),
            "anomalies_detected": int(anomaly_count),
            "overall_risk_score": risk_score
        }

    # ---------------------------------------------------
    # RECOMMENDATIONS
    # ---------------------------------------------------

    def _generate_recommendations(self, validated_df, errors_df, anomaly_df):

        recs = []

        if errors_df is not None and not errors_df.empty:
            recs.append("Review invalid geometries and apply automated repair where possible.")

        if anomaly_df is not None and "is_anomaly" in anomaly_df.columns:
            anomaly_count = anomaly_df["is_anomaly"].sum()
            if anomaly_count > 0:
                recs.append("Manually inspect anomalous features identified by AI model.")

        invalid_count = (
            (~validated_df["is_valid"]).sum()
            if "is_valid" in validated_df.columns else 0
        )

        if len(validated_df) > 0 and invalid_count / len(validated_df) > 0.1:
            recs.append("High validation failure rate detected. Investigate data collection workflow.")

        if not recs:
            recs.append("No major data quality issues detected.")

        return recs

    # ---------------------------------------------------
    # EXPORT
    # ---------------------------------------------------

    def export_to_json(self, filepath: str):

        try:
            with open(filepath, "w") as f:
                json.dump(self.report_data, f, indent=2)

            return True, f"Report exported to {filepath}"

        except Exception as e:
            return False, f"Export error: {str(e)}"

    # ---------------------------------------------------
    # HUMAN SUMMARY
    # ---------------------------------------------------

    def get_summary_text(self):

        if not self.report_data:
            return "No report generated."

        summary = self.report_data["executive_summary"]
        risk = self.report_data["risk_assessment"]

        lines = [
            "=" * 60,
            "AI MAP QUALITY CHECKER - EXECUTIVE SUMMARY",
            "=" * 60,
            f"Generated: {self.report_data['metadata']['generated_at']}",
            f"Total Features: {self.report_data['metadata']['total_features']}",
            "",
            f"Data Quality Index: {summary.get('data_quality_index', 0)}%",
            f"Invalid Features: {summary.get('invalid_features', 0)}",
            f"Anomalies Detected: {summary.get('anomalies_detected', 0)}",
            "",
            f"Overall Risk Score: {risk.get('risk_score', 0)}",
            f"Severity Level: {risk.get('severity_level', 'Unknown')}",
            "=" * 60
        ]

        return "\n".join(lines)
