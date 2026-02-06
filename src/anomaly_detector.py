"""
ML-based anomaly detection module
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Tuple, Optional
from config.settings import ANOMALY_DETECTION_PARAMS
import os


class AnomalyDetector:
    """Detects anomalous geometric features using Isolation Forest"""
    
    def __init__(self, params: dict = None):
        self.params = params or ANOMALY_DETECTION_PARAMS
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        
    def train(self, features: pd.DataFrame) -> Tuple[bool, str]:
        """
        Train the anomaly detection model
        
        Args:
            features: DataFrame with extracted features
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Remove any non-numeric columns
            numeric_features = features.select_dtypes(include=[np.number])
            
            if numeric_features.empty:
                return False, "No numeric features found for training"
            
            # Handle missing values
            numeric_features = numeric_features.fillna(0)
            
            # Handle infinite values
            numeric_features = numeric_features.replace([np.inf, -np.inf], 0)
            
            # Store feature names
            self.feature_names = numeric_features.columns.tolist()
            
            # Scale features
            scaled_features = self.scaler.fit_transform(numeric_features)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=self.params.get('contamination', 0.1),
                n_estimators=self.params.get('n_estimators', 100),
                max_samples=self.params.get('max_samples', 'auto'),
                random_state=self.params.get('random_state', 42),
                n_jobs=-1
            )
            
            self.model.fit(scaled_features)
            
            return True, f"Model trained successfully on {len(numeric_features)} samples with {len(self.feature_names)} features"
            
        except Exception as e:
            return False, f"Error training model: {str(e)}"
    
    def predict(self, features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies in features
        
        Args:
            features: DataFrame with extracted features
            
        Returns:
            Tuple of (predictions, anomaly_scores)
            predictions: -1 for anomalies, 1 for normal
            anomaly_scores: Lower scores indicate more anomalous
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Select only numeric features
        numeric_features = features.select_dtypes(include=[np.number])
        
        # Ensure we have the same features as training
        if self.feature_names:
            missing_features = set(self.feature_names) - set(numeric_features.columns)
            if missing_features:
                for feat in missing_features:
                    numeric_features[feat] = 0
            numeric_features = numeric_features[self.feature_names]
        
        # Handle missing and infinite values
        numeric_features = numeric_features.fillna(0)
        numeric_features = numeric_features.replace([np.inf, -np.inf], 0)
        
        # Scale features
        scaled_features = self.scaler.transform(numeric_features)
        
        # Predict
        predictions = self.model.predict(scaled_features)
        anomaly_scores = self.model.score_samples(scaled_features)
        
        return predictions, anomaly_scores
    
    def detect_anomalies(self, gdf: gpd.GeoDataFrame, features: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Detect anomalies and add results to GeoDataFrame
        
        Args:
            gdf: Original GeoDataFrame
            features: Extracted features DataFrame
            
        Returns:
            GeoDataFrame with anomaly predictions
        """
        result_gdf = gdf.copy()
        
        # Get predictions
        predictions, scores = self.predict(features)
        
        # Add to GeoDataFrame
        result_gdf['is_anomaly'] = predictions == -1
        result_gdf['anomaly_score'] = scores
        
        # Normalize scores to 0-1 range for easier interpretation
        min_score = scores.min()
        max_score = scores.max()
        if max_score > min_score:
            result_gdf['anomaly_score_normalized'] = (scores - min_score) / (max_score - min_score)
        else:
            result_gdf['anomaly_score_normalized'] = 0.5
        
        return result_gdf
    
    def save_model(self, filepath: str) -> Tuple[bool, str]:
        """
        Save trained model to file
        
        Args:
            filepath: Path to save model
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.model is None:
                return False, "No model to save. Train the model first."
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'params': self.params
            }
            
            joblib.dump(model_data, filepath)
            return True, f"Model saved to {filepath}"
            
        except Exception as e:
            return False, f"Error saving model: {str(e)}"
    
    def load_model(self, filepath: str) -> Tuple[bool, str]:
        """
        Load trained model from file
        
        Args:
            filepath: Path to load model from
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(filepath):
                return False, f"Model file not found: {filepath}"
            
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.params = model_data.get('params', self.params)
            
            return True, f"Model loaded from {filepath}"
            
        except Exception as e:
            return False, f"Error loading model: {str(e)}"
    
    def get_anomaly_summary(self, gdf: gpd.GeoDataFrame) -> dict:
        """Get summary of anomaly detection results"""
        if 'is_anomaly' not in gdf.columns:
            return {}
        
        total = len(gdf)
        anomalies = gdf['is_anomaly'].sum()
        normal = total - anomalies
        
        return {
            'total_features': total,
            'anomalies_detected': int(anomalies),
            'normal_features': int(normal),
            'anomaly_rate': f"{(anomalies/total*100):.2f}%" if total > 0 else "0%",
            'avg_anomaly_score': float(gdf['anomaly_score'].mean()) if 'anomaly_score' in gdf.columns else 0
        }
