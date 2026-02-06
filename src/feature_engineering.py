"""
Feature engineering module for extracting geometric features
"""
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from typing import List
from config.settings import FEATURE_PARAMS


class FeatureEngineer:
    """Extracts geometric features for ML analysis"""
    
    def __init__(self, params: dict = None):
        self.params = params or FEATURE_PARAMS
        
    def extract_features(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Extract geometric features from GeoDataFrame
        
        Args:
            gdf: GeoDataFrame to extract features from
            
        Returns:
            DataFrame with extracted features
        """
        features = pd.DataFrame()
        
        # Basic geometric properties
        if self.params.get('use_area', True):
            features['area'] = gdf.geometry.area
        
        if self.params.get('use_perimeter', True):
            features['perimeter'] = gdf.geometry.length
        
        # Derived features
        if self.params.get('use_complexity', True):
            features['complexity'] = self._calculate_complexity(gdf)
        
        if self.params.get('use_compactness', True):
            features['compactness'] = self._calculate_compactness(gdf)
        
        if self.params.get('use_convexity', True):
            features['convexity'] = self._calculate_convexity(gdf)
        
        if self.params.get('use_aspect_ratio', True):
            features['aspect_ratio'] = self._calculate_aspect_ratio(gdf)
        
        # Additional features
        features['num_vertices'] = self._count_vertices(gdf)
        features['num_holes'] = self._count_holes(gdf)
        features['bbox_area'] = self._calculate_bbox_area(gdf)
        features['elongation'] = self._calculate_elongation(gdf)
        
        return features
    
    def _calculate_complexity(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate geometric complexity (perimeter^2 / area)"""
        area = gdf.geometry.area
        perimeter = gdf.geometry.length
        
        # Avoid division by zero
        complexity = np.where(area > 0, (perimeter ** 2) / area, 0)
        return pd.Series(complexity, index=gdf.index)
    
    def _calculate_compactness(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate compactness (4π * area / perimeter^2)"""
        area = gdf.geometry.area
        perimeter = gdf.geometry.length
        
        # Avoid division by zero
        compactness = np.where(perimeter > 0, (4 * np.pi * area) / (perimeter ** 2), 0)
        return pd.Series(compactness, index=gdf.index)
    
    def _calculate_convexity(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate convexity (area / convex_hull_area)"""
        convexity = []
        
        for geom in gdf.geometry:
            if isinstance(geom, (Polygon, MultiPolygon)):
                try:
                    convex_hull = geom.convex_hull
                    if convex_hull.area > 0:
                        convexity.append(geom.area / convex_hull.area)
                    else:
                        convexity.append(0)
                except:
                    convexity.append(0)
            else:
                convexity.append(0)
        
        return pd.Series(convexity, index=gdf.index)
    
    def _calculate_aspect_ratio(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate aspect ratio from bounding box"""
        aspect_ratios = []
        
        for geom in gdf.geometry:
            try:
                minx, miny, maxx, maxy = geom.bounds
                width = maxx - minx
                height = maxy - miny
                
                if height > 0:
                    aspect_ratios.append(width / height)
                else:
                    aspect_ratios.append(0)
            except:
                aspect_ratios.append(0)
        
        return pd.Series(aspect_ratios, index=gdf.index)
    
    def _count_vertices(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Count number of vertices in geometry"""
        vertex_counts = []
        
        for geom in gdf.geometry:
            try:
                if isinstance(geom, Point):
                    vertex_counts.append(1)
                elif isinstance(geom, LineString):
                    vertex_counts.append(len(geom.coords))
                elif isinstance(geom, Polygon):
                    vertex_counts.append(len(geom.exterior.coords))
                elif isinstance(geom, MultiPolygon):
                    total = sum(len(poly.exterior.coords) for poly in geom.geoms)
                    vertex_counts.append(total)
                else:
                    vertex_counts.append(0)
            except:
                vertex_counts.append(0)
        
        return pd.Series(vertex_counts, index=gdf.index)
    
    def _count_holes(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Count number of interior holes in polygons"""
        hole_counts = []
        
        for geom in gdf.geometry:
            try:
                if isinstance(geom, Polygon):
                    hole_counts.append(len(geom.interiors))
                elif isinstance(geom, MultiPolygon):
                    total = sum(len(poly.interiors) for poly in geom.geoms)
                    hole_counts.append(total)
                else:
                    hole_counts.append(0)
            except:
                hole_counts.append(0)
        
        return pd.Series(hole_counts, index=gdf.index)
    
    def _calculate_bbox_area(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate bounding box area"""
        bbox_areas = []
        
        for geom in gdf.geometry:
            try:
                minx, miny, maxx, maxy = geom.bounds
                bbox_areas.append((maxx - minx) * (maxy - miny))
            except:
                bbox_areas.append(0)
        
        return pd.Series(bbox_areas, index=gdf.index)
    
    def _calculate_elongation(self, gdf: gpd.GeoDataFrame) -> pd.Series:
        """Calculate elongation (ratio of area to bounding box area)"""
        area = gdf.geometry.area
        bbox_area = self._calculate_bbox_area(gdf)
        
        elongation = np.where(bbox_area > 0, area / bbox_area, 0)
        return pd.Series(elongation, index=gdf.index)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names that will be extracted"""
        features = []
        
        if self.params.get('use_area', True):
            features.append('area')
        if self.params.get('use_perimeter', True):
            features.append('perimeter')
        if self.params.get('use_complexity', True):
            features.append('complexity')
        if self.params.get('use_compactness', True):
            features.append('compactness')
        if self.params.get('use_convexity', True):
            features.append('convexity')
        if self.params.get('use_aspect_ratio', True):
            features.append('aspect_ratio')
        
        features.extend(['num_vertices', 'num_holes', 'bbox_area', 'elongation'])
        
        return features
