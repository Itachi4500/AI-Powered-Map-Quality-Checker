"""
Data loading module for GeoJSON files
"""
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from typing import Dict, List, Tuple, Optional
import streamlit as st


class GeoDataLoader:
    """Handles loading and parsing of GeoJSON data"""
    
    def __init__(self):
        self.data = None
        self.gdf = None
        
    def load_from_file(self, uploaded_file) -> Tuple[bool, Optional[gpd.GeoDataFrame], str]:
        """
        Load GeoJSON from uploaded file
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (success, GeoDataFrame, message)
        """
        try:
            # Read the file content
            content = uploaded_file.read()
            geojson_data = json.loads(content)
            
            # Validate basic GeoJSON structure
            if 'type' not in geojson_data:
                return False, None, "Invalid GeoJSON: Missing 'type' field"
            
            if geojson_data['type'] not in ['FeatureCollection', 'Feature']:
                return False, None, f"Unsupported GeoJSON type: {geojson_data['type']}"
            
            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(geojson_data['features'] if geojson_data['type'] == 'FeatureCollection' else [geojson_data])
            
            # Ensure CRS is set (default to WGS84)
            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            
            self.gdf = gdf
            self.data = geojson_data
            
            return True, gdf, f"Successfully loaded {len(gdf)} features"
            
        except json.JSONDecodeError as e:
            return False, None, f"JSON parsing error: {str(e)}"
        except Exception as e:
            return False, None, f"Error loading GeoJSON: {str(e)}"
    
    def load_from_path(self, file_path: str) -> Tuple[bool, Optional[gpd.GeoDataFrame], str]:
        """
        Load GeoJSON from file path
        
        Args:
            file_path: Path to GeoJSON file
            
        Returns:
            Tuple of (success, GeoDataFrame, message)
        """
        try:
            gdf = gpd.read_file(file_path)
            
            # Ensure CRS is set
            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            
            self.gdf = gdf
            
            return True, gdf, f"Successfully loaded {len(gdf)} features from {file_path}"
            
        except Exception as e:
            return False, None, f"Error loading file: {str(e)}"
    
    def get_summary(self) -> Dict:
        """Get summary statistics of loaded data"""
        if self.gdf is None:
            return {}
        
        summary = {
            'total_features': len(self.gdf),
            'geometry_types': self.gdf.geometry.type.value_counts().to_dict(),
            'crs': str(self.gdf.crs),
            'bounds': self.gdf.total_bounds.tolist(),
            'columns': list(self.gdf.columns)
        }
        
        return summary
    
    def get_feature_properties(self) -> List[str]:
        """Get list of property names from features"""
        if self.gdf is None:
            return []
        
        # Exclude geometry column
        return [col for col in self.gdf.columns if col != 'geometry']
