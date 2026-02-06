"""
Visualization module using Plotly for interactive maps
"""
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import pandas as pd
from typing import Optional, List
from config.settings import VIZ_SETTINGS


class MapVisualizer:
    """Creates interactive map visualizations using Plotly"""
    
    def __init__(self, settings: dict = None):
        self.settings = settings or VIZ_SETTINGS
        
    def create_validation_map(self, gdf: gpd.GeoDataFrame) -> go.Figure:
        """
        Create map showing validation results
        
        Args:
            gdf: GeoDataFrame with validation results
            
        Returns:
            Plotly figure
        """
        # Ensure we're in WGS84 for plotting
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        # Create figure
        fig = go.Figure()
        
        # Add valid features
        if 'is_valid' in gdf.columns:
            valid_gdf = gdf[gdf['is_valid']]
            invalid_gdf = gdf[~gdf['is_valid']]
            
            # Plot valid features
            if len(valid_gdf) > 0:
                self._add_geometries_to_map(
                    fig, valid_gdf, 
                    color=self.settings['valid_color'],
                    name='Valid Features',
                    opacity=0.6
                )
            
            # Plot invalid features
            if len(invalid_gdf) > 0:
                self._add_geometries_to_map(
                    fig, invalid_gdf,
                    color=self.settings['invalid_color'],
                    name='Invalid Features',
                    opacity=0.8
                )
        else:
            # No validation info, plot all features
            self._add_geometries_to_map(
                fig, gdf,
                color='blue',
                name='Features',
                opacity=0.6
            )
        
        # Update layout
        self._update_map_layout(fig, gdf, "Validation Results")
        
        return fig
    
    def create_anomaly_map(self, gdf: gpd.GeoDataFrame) -> go.Figure:
        """
        Create map showing anomaly detection results
        
        Args:
            gdf: GeoDataFrame with anomaly detection results
            
        Returns:
            Plotly figure
        """
        # Ensure we're in WGS84
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        fig = go.Figure()
        
        if 'is_anomaly' in gdf.columns:
            normal_gdf = gdf[~gdf['is_anomaly']]
            anomaly_gdf = gdf[gdf['is_anomaly']]
            
            # Plot normal features
            if len(normal_gdf) > 0:
                self._add_geometries_to_map(
                    fig, normal_gdf,
                    color=self.settings['valid_color'],
                    name='Normal Features',
                    opacity=0.5
                )
            
            # Plot anomalies
            if len(anomaly_gdf) > 0:
                self._add_geometries_to_map(
                    fig, anomaly_gdf,
                    color=self.settings['anomaly_color'],
                    name='Anomalies',
                    opacity=0.8
                )
        else:
            self._add_geometries_to_map(
                fig, gdf,
                color='blue',
                name='Features',
                opacity=0.6
            )
        
        self._update_map_layout(fig, gdf, "Anomaly Detection Results")
        
        return fig
    
    def create_combined_map(self, gdf: gpd.GeoDataFrame) -> go.Figure:
        """
        Create map showing both validation and anomaly results
        
        Args:
            gdf: GeoDataFrame with both validation and anomaly results
            
        Returns:
            Plotly figure
        """
        # Ensure we're in WGS84
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        fig = go.Figure()
        
        # Categorize features
        if 'is_valid' in gdf.columns and 'is_anomaly' in gdf.columns:
            # Good features (valid and not anomaly)
            good = gdf[gdf['is_valid'] & ~gdf['is_anomaly']]
            # Only validation errors
            only_invalid = gdf[~gdf['is_valid'] & ~gdf['is_anomaly']]
            # Only anomalies
            only_anomaly = gdf[gdf['is_valid'] & gdf['is_anomaly']]
            # Both issues
            both_issues = gdf[~gdf['is_valid'] & gdf['is_anomaly']]
            
            # Plot each category
            if len(good) > 0:
                self._add_geometries_to_map(
                    fig, good,
                    color=self.settings['valid_color'],
                    name='Valid & Normal',
                    opacity=0.4
                )
            
            if len(only_invalid) > 0:
                self._add_geometries_to_map(
                    fig, only_invalid,
                    color=self.settings['invalid_color'],
                    name='Validation Errors',
                    opacity=0.7
                )
            
            if len(only_anomaly) > 0:
                self._add_geometries_to_map(
                    fig, only_anomaly,
                    color=self.settings['anomaly_color'],
                    name='Anomalies',
                    opacity=0.7
                )
            
            if len(both_issues) > 0:
                self._add_geometries_to_map(
                    fig, both_issues,
                    color='#FF00FF',  # Magenta for critical
                    name='Critical (Both Issues)',
                    opacity=0.9
                )
        else:
            self._add_geometries_to_map(
                fig, gdf,
                color='blue',
                name='Features',
                opacity=0.6
            )
        
        self._update_map_layout(fig, gdf, "Combined Quality Analysis")
        
        return fig
    
    def _add_geometries_to_map(self, fig: go.Figure, gdf: gpd.GeoDataFrame, 
                               color: str, name: str, opacity: float = 0.6):
        """Add geometries to map figure"""
        for idx, row in gdf.iterrows():
            geom = row.geometry
            
            # Get hover text
            hover_text = self._create_hover_text(row, idx)
            
            # Handle different geometry types
            if geom.geom_type == 'Polygon':
                self._add_polygon(fig, geom, color, name, hover_text, opacity)
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    self._add_polygon(fig, poly, color, name, hover_text, opacity)
            elif geom.geom_type == 'LineString':
                self._add_linestring(fig, geom, color, name, hover_text, opacity)
            elif geom.geom_type == 'Point':
                self._add_point(fig, geom, color, name, hover_text)
    
    def _add_polygon(self, fig: go.Figure, polygon, color: str, 
                     name: str, hover_text: str, opacity: float):
        """Add polygon to figure"""
        x, y = polygon.exterior.xy
        
        fig.add_trace(go.Scattermapbox(
            lon=list(x),
            lat=list(y),
            mode='lines',
            fill='toself',
            fillcolor=color,
            line=dict(color=color, width=2),
            opacity=opacity,
            name=name,
            text=hover_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    def _add_linestring(self, fig: go.Figure, linestring, color: str,
                       name: str, hover_text: str, opacity: float):
        """Add linestring to figure"""
        x, y = linestring.xy
        
        fig.add_trace(go.Scattermapbox(
            lon=list(x),
            lat=list(y),
            mode='lines',
            line=dict(color=color, width=3),
            opacity=opacity,
            name=name,
            text=hover_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    def _add_point(self, fig: go.Figure, point, color: str,
                   name: str, hover_text: str):
        """Add point to figure"""
        fig.add_trace(go.Scattermapbox(
            lon=[point.x],
            lat=[point.y],
            mode='markers',
            marker=dict(size=10, color=color),
            name=name,
            text=hover_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    def _create_hover_text(self, row, idx) -> str:
        """Create hover text for feature"""
        lines = [f"<b>Feature ID: {idx}</b>"]
        
        # Add validation info
        if 'is_valid' in row.index:
            status = "✓ Valid" if row['is_valid'] else "✗ Invalid"
            lines.append(f"Validation: {status}")
        
        if 'validation_errors' in row.index and row['validation_errors']:
            lines.append(f"Errors: {row['validation_errors']}")
        
        # Add anomaly info
        if 'is_anomaly' in row.index:
            status = "⚠ Anomaly" if row['is_anomaly'] else "Normal"
            lines.append(f"Anomaly: {status}")
        
        if 'anomaly_score' in row.index:
            lines.append(f"Score: {row['anomaly_score']:.4f}")
        
        # Add geometry info
        lines.append(f"Type: {row.geometry.geom_type}")
        
        if hasattr(row.geometry, 'area'):
            lines.append(f"Area: {row.geometry.area:.2f}")
        
        return "<br>".join(lines)
    
    def _update_map_layout(self, fig: go.Figure, gdf: gpd.GeoDataFrame, title: str):
        """Update map layout with proper centering and zoom"""
        # Calculate center
        bounds = gdf.total_bounds
        center_lon = (bounds[0] + bounds[2]) / 2
        center_lat = (bounds[1] + bounds[3]) / 2
        
        # Calculate zoom level based on bounds
        lon_range = bounds[2] - bounds[0]
        lat_range = bounds[3] - bounds[1]
        max_range = max(lon_range, lat_range)
        
        # Rough zoom calculation
        if max_range > 10:
            zoom = 5
        elif max_range > 1:
            zoom = 8
        elif max_range > 0.1:
            zoom = 11
        else:
            zoom = 13
        
        fig.update_layout(
            title=title,
            mapbox=dict(
                style=self.settings['map_style'],
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            showlegend=True,
            height=600,
            margin=dict(l=0, r=0, t=30, b=0)
        )
    
    def create_feature_distribution_chart(self, features: pd.DataFrame) -> go.Figure:
        """Create distribution charts for extracted features"""
        # Select numeric columns
        numeric_cols = features.select_dtypes(include=['number']).columns[:6]  # Top 6 features
        
        fig = go.Figure()
        
        for col in numeric_cols:
            fig.add_trace(go.Box(
                y=features[col],
                name=col,
                boxmean='sd'
            ))
        
        fig.update_layout(
            title="Feature Distributions",
            yaxis_title="Value",
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_error_breakdown_chart(self, errors_df: pd.DataFrame) -> go.Figure:
        """Create pie chart of error types"""
        if errors_df.empty:
            return go.Figure()
        
        error_counts = errors_df['error_type'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=error_counts.index,
            values=error_counts.values,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Error Type Distribution",
            height=400
        )
        
        return fig
