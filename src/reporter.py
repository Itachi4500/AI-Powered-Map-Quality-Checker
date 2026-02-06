"""
Error report generation module
"""
import pandas as pd
import geopandas as gpd
from typing import Dict, List
from datetime import datetime
import json


class ErrorReporter:
    """Generates comprehensive error reports"""
    
    def __init__(self):
        self.report_data = {}
        
    def generate_report(self, 
                       validated_gdf: gpd.GeoDataFrame,
                       errors_df: pd.DataFrame,
                       anomaly_gdf: gpd.GeoDataFrame = None,
                       validation_summary: Dict = None,
                       anomaly_summary: Dict = None) -> Dict:
        """
        Generate comprehensive error report
        
        Args:
            validated_gdf: GeoDataFrame with validation results
            errors_df: DataFrame with detailed errors
            anomaly_gdf: GeoDataFrame with anomaly detection results
            validation_summary: Summary of validation results
            anomaly_summary: Summary of anomaly detection results
            
        Returns:
            Dictionary containing the complete report
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_features': len(validated_gdf)
            },
            'validation': {},
            'anomaly_detection': {},
            'combined_issues': {},
            'recommendations': []
        }
        
        # Validation section
        if validation_summary:
            report['validation'] = validation_summary
        
        if not errors_df.empty:
            report['validation']['errors_by_type'] = errors_df['error_type'].value_counts().to_dict()
            report['validation']['top_errors'] = errors_df.head(10).to_dict('records')
        
        # Anomaly detection section
        if anomaly_gdf is not None and anomaly_summary:
            report['anomaly_detection'] = anomaly_summary
            
            if 'is_anomaly' in anomaly_gdf.columns:
                anomalous_features = anomaly_gdf[anomaly_gdf['is_anomaly']]
                if len(anomalous_features) > 0:
                    report['anomaly_detection']['top_anomalies'] = self._get_top_anomalies(anomalous_features)
        
        # Combined issues
        report['combined_issues'] = self._analyze_combined_issues(validated_gdf, anomaly_gdf)
        
        # Recommendations
        report['recommendations'] = self._generate_recommendations(
            validated_gdf, errors_df, anomaly_gdf
        )
        
        self.report_data = report
        return report
    
    def _get_top_anomalies(self, anomalous_gdf: gpd.GeoDataFrame, top_n: int = 10) -> List[Dict]:
        """Get top N anomalies by score"""
        if 'anomaly_score' not in anomalous_gdf.columns:
            return []
        
        # Sort by anomaly score (lower is more anomalous)
        sorted_anomalies = anomalous_gdf.sort_values('anomaly_score').head(top_n)
        
        results = []
        for idx, row in sorted_anomalies.iterrows():
            results.append({
                'feature_id': int(idx),
                'anomaly_score': float(row['anomaly_score']),
                'geometry_type': row.geometry.geom_type,
                'bounds': list(row.geometry.bounds)
            })
        
        return results
    
    def _analyze_combined_issues(self, 
                                 validated_gdf: gpd.GeoDataFrame,
                                 anomaly_gdf: gpd.GeoDataFrame = None) -> Dict:
        """Analyze features with both validation errors and anomalies"""
        combined = {}
        
        if anomaly_gdf is None:
            return combined
        
        # Find features with both validation errors and anomalies
        invalid_features = validated_gdf[~validated_gdf['is_valid']].index
        anomalous_features = anomaly_gdf[anomaly_gdf['is_anomaly']].index
        
        both_issues = invalid_features.intersection(anomalous_features)
        
        combined['features_with_both_issues'] = len(both_issues)
        combined['only_validation_errors'] = len(invalid_features) - len(both_issues)
        combined['only_anomalies'] = len(anomalous_features) - len(both_issues)
        
        if len(both_issues) > 0:
            combined['critical_features'] = both_issues.tolist()[:20]  # Top 20
        
        return combined
    
    def _generate_recommendations(self,
                                 validated_gdf: gpd.GeoDataFrame,
                                 errors_df: pd.DataFrame,
                                 anomaly_gdf: gpd.GeoDataFrame = None) -> List[str]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # Validation recommendations
        if not errors_df.empty:
            error_counts = errors_df['error_type'].value_counts()
            
            if 'geometry_validity' in error_counts.index:
                recommendations.append(
                    f"Fix {error_counts['geometry_validity']} invalid geometries using geometry repair tools"
                )
            
            if 'self_intersection' in error_counts.index:
                recommendations.append(
                    f"Resolve {error_counts['self_intersection']} self-intersecting geometries"
                )
            
            if 'area_too_small' in error_counts.index:
                recommendations.append(
                    f"Review {error_counts['area_too_small']} features with areas below minimum threshold"
                )
            
            if 'coordinate_precision' in error_counts.index:
                recommendations.append(
                    f"Reduce coordinate precision for {error_counts['coordinate_precision']} features"
                )
        
        # Anomaly recommendations
        if anomaly_gdf is not None and 'is_anomaly' in anomaly_gdf.columns:
            anomaly_count = anomaly_gdf['is_anomaly'].sum()
            if anomaly_count > 0:
                recommendations.append(
                    f"Manually review {anomaly_count} anomalous features for data quality issues"
                )
        
        # General recommendations
        invalid_count = (~validated_gdf['is_valid']).sum()
        if invalid_count > len(validated_gdf) * 0.1:
            recommendations.append(
                "High error rate detected (>10%). Consider reviewing data collection process"
            )
        
        if len(recommendations) == 0:
            recommendations.append("Data quality looks good! No major issues detected.")
        
        return recommendations
    
    def export_to_csv(self, filepath: str, validated_gdf: gpd.GeoDataFrame, errors_df: pd.DataFrame):
        """Export error report to CSV"""
        try:
            # Export validation errors
            if not errors_df.empty:
                errors_df.to_csv(filepath.replace('.csv', '_errors.csv'), index=False)
            
            # Export invalid features
            invalid_features = validated_gdf[~validated_gdf['is_valid']].copy()
            if len(invalid_features) > 0:
                # Drop geometry for CSV export
                invalid_features_export = invalid_features.drop(columns=['geometry'])
                invalid_features_export.to_csv(filepath.replace('.csv', '_invalid_features.csv'), index=True)
            
            return True, f"Report exported to {filepath}"
            
        except Exception as e:
            return False, f"Error exporting report: {str(e)}"
    
    def export_to_json(self, filepath: str):
        """Export report to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.report_data, f, indent=2)
            
            return True, f"Report exported to {filepath}"
            
        except Exception as e:
            return False, f"Error exporting report: {str(e)}"
    
    def get_summary_text(self) -> str:
        """Get human-readable summary text"""
        if not self.report_data:
            return "No report data available"
        
        lines = []
        lines.append("=" * 60)
        lines.append("AI MAP QUALITY CHECKER - REPORT SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Generated: {self.report_data['metadata']['generated_at']}")
        lines.append(f"Total Features: {self.report_data['metadata']['total_features']}")
        lines.append("")
        
        # Validation section
        if self.report_data.get('validation'):
            val = self.report_data['validation']
            lines.append("VALIDATION RESULTS:")
            lines.append(f"  Valid: {val.get('valid_features', 0)}")
            lines.append(f"  Invalid: {val.get('invalid_features', 0)}")
            lines.append(f"  Validation Rate: {val.get('validation_rate', '0%')}")
            lines.append(f"  Total Errors: {val.get('total_errors', 0)}")
            lines.append("")
        
        # Anomaly section
        if self.report_data.get('anomaly_detection'):
            anom = self.report_data['anomaly_detection']
            lines.append("ANOMALY DETECTION:")
            lines.append(f"  Anomalies: {anom.get('anomalies_detected', 0)}")
            lines.append(f"  Normal: {anom.get('normal_features', 0)}")
            lines.append(f"  Anomaly Rate: {anom.get('anomaly_rate', '0%')}")
            lines.append("")
        
        # Recommendations
        if self.report_data.get('recommendations'):
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(self.report_data['recommendations'], 1):
                lines.append(f"  {i}. {rec}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
