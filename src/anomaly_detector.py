"""
Enhanced ML-based anomaly detection module
Robust, deployment-safe, and production-ready.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, RobustScaler
import joblib
from typing import Tuple, Optional, Dict
import os
from config.settings import ANOMALY_DETECTION_PARAMS


class AnomalyDetector:
    """
    Detects anomalous geometric features using Isolation Forest.
    Enhanced with robust preprocessing, confidence scoring,
    feature validation, and deployment-safe design.
    """

    def __init__(self, params: dict = None, use_robust_scaling: bool = True):
        self.params = params or ANOMALY_DETECTION_PARAMS
        self.model: Optional[IsolationForest] = None
        self.scaler = RobustScaler() if use_robust_scaling else StandardScaler()
        self.feature_names: Optional[list] = None
        self.is_trained = False

    # ---------------------------------------------------
    # TRAIN
    # ---------------------------------------------------

    def train(self, features: pd.DataFrame) -> Tuple[bool, str]:

        try:
            numeric_features = self._prepare_features(features, training=True)

            if numeric_features.shape[0] < 5:
                return False, "Not enough samples to train anomaly detector"

            self.model = IsolationForest(
                contamination=self.params.get("contamination", 0.1),
                n_estimators=self.params.get("n_estimators", 100),
                max_samples=self.params.get("max_samples", "auto"),
                random_state=self.params.get("random_state", 42),
                n_jobs=-1
            )

            self.model.fit(numeric_features)

            self.is_trained = True

            return True, (
                f"Model trained successfully\n"
                f"Samples: {numeric_features.shape[0]}\n"
                f"Features: {numeric_features.shape[1]}"
            )

        except Exception as e:
            return False, f"Training error: {str(e)}"

    # ---------------------------------------------------
    # PREDICT
    # ---------------------------------------------------

    def predict(self, features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:

        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        numeric_features = self._prepare_features(features, training=False)

        predictions = self.model.predict(numeric_features)
        scores = self.model.score_samples(numeric_features)

        return predictions, scores

    # ---------------------------------------------------
    # DETECT ANOMALIES (GeoDataFrame or DataFrame Safe)
    # ---------------------------------------------------

    def detect_anomalies(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:

        result_df = df.copy()

        predictions, scores = self.predict(features)

        result_df["is_anomaly"] = predictions == -1
        result_df["anomaly_score"] = scores

        # Robust normalization
        result_df["anomaly_score_normalized"] = self._normalize_scores(scores)

        # Confidence Score (inverted normalized)
        result_df["anomaly_confidence"] = 1 - result_df["anomaly_score_normalized"]

        return result_df

    # ---------------------------------------------------
    # FEATURE PREPARATION
    # ---------------------------------------------------

    def _prepare_features(self, features: pd.DataFrame, training=False):

        numeric_features = features.select_dtypes(include=[np.number]).copy()

        if numeric_features.empty:
            raise ValueError("No numeric features available")

        numeric_features = numeric_features.fillna(0)
        numeric_features = numeric_features.replace([np.inf, -np.inf], 0)

        if training:
            self.feature_names = numeric_features.columns.tolist()
            scaled = self.scaler.fit_transform(numeric_features)
        else:
            # Ensure same feature order
            for col in self.feature_names:
                if col not in numeric_features.columns:
                    numeric_features[col] = 0

            numeric_features = numeric_features[self.feature_names]
            scaled = self.scaler.transform(numeric_features)

        return scaled

    # ---------------------------------------------------
    # SCORE NORMALIZATION
    # ---------------------------------------------------

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            return np.full_like(scores, 0.5)

        return (scores - min_score) / (max_score - min_score)

    # ---------------------------------------------------
    # FEATURE IMPORTANCE (Tree-based insight)
    # ---------------------------------------------------

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        if not self.model or not self.feature_names:
            return None

        if hasattr(self.model, "estimators_"):
            # Average feature importance from trees
            importances = np.mean(
                [tree.feature_importances_ for tree in self.model.estimators_],
                axis=0
            )
            return dict(zip(self.feature_names, importances))

        return None

    # ---------------------------------------------------
    # MODEL SAVE / LOAD
    # ---------------------------------------------------

    def save_model(self, filepath: str) -> Tuple[bool, str]:
        try:
            if not self.is_trained:
                return False, "No trained model to save."

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            joblib.dump({
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "params": self.params,
                "version": "1.1"
            }, filepath)

            return True, f"Model saved to {filepath}"

        except Exception as e:
            return False, f"Save error: {str(e)}"

    def load_model(self, filepath: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(filepath):
                return False, f"Model file not found: {filepath}"

            model_data = joblib.load(filepath)

            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data["feature_names"]
            self.params = model_data.get("params", self.params)
            self.is_trained = True

            return True, "Model loaded successfully"

        except Exception as e:
            return False, f"Load error: {str(e)}"

    # ---------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------

    def get_anomaly_summary(self, df: pd.DataFrame) -> dict:

        if "is_anomaly" not in df.columns:
            return {}

        total = len(df)
        anomalies = df["is_anomaly"].sum()
        normal = total - anomalies

        return {
            "total_features": total,
            "anomalies_detected": int(anomalies),
            "normal_features": int(normal),
            "anomaly_rate": f"{(anomalies / total * 100):.2f}%" if total > 0 else "0%",
            "avg_anomaly_score": float(df["anomaly_score"].mean()),
            "avg_confidence": float(df["anomaly_confidence"].mean())
        }
