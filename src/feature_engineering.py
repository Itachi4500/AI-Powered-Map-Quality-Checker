"""
Enhanced Feature Engineering Module
Robust, scalable, and ML-ready geometric feature extractor
"""

import numpy as np
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.ops import unary_union
from typing import List, Optional
from config.settings import FEATURE_PARAMS


class FeatureEngineer:
    """
    Extract geometric and topological features
    for anomaly detection and QA validation.
    """

    def __init__(self, params: dict = None):
        self.params = params or FEATURE_PARAMS

    # ---------------------------------------------------
    # MAIN EXTRACTION
    # ---------------------------------------------------

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:

        if "geometry" not in df.columns:
            raise ValueError("Input DataFrame must contain 'geometry' column")

        features = pd.DataFrame(index=df.index)

        geometries = df["geometry"]

        # Basic metrics
        if self.params.get("use_area", True):
            features["area"] = geometries.apply(lambda g: g.area if g else 0)

        if self.params.get("use_perimeter", True):
            features["perimeter"] = geometries.apply(lambda g: g.length if g else 0)

        # Derived features
        if self.params.get("use_complexity", True):
            features["complexity"] = self._complexity(features)

        if self.params.get("use_compactness", True):
            features["compactness"] = self._compactness(features)

        if self.params.get("use_convexity", True):
            features["convexity"] = geometries.apply(self._convexity)

        if self.params.get("use_aspect_ratio", True):
            features["aspect_ratio"] = geometries.apply(self._aspect_ratio)

        # Advanced geometric features
        features["num_vertices"] = geometries.apply(self._count_vertices)
        features["num_holes"] = geometries.apply(self._count_holes)
        features["bbox_area"] = geometries.apply(self._bbox_area)
        features["elongation"] = self._elongation(features)
        features["bbox_perimeter_ratio"] = self._bbox_perimeter_ratio(geometries)

        # Shape irregularity (new high-impact feature)
        features["irregularity_index"] = self._irregularity(features)

        # Clean numeric stability
        features = features.replace([np.inf, -np.inf], 0)
        features = features.fillna(0)

        return features

    # ---------------------------------------------------
    # BASIC DERIVED FEATURES
    # ---------------------------------------------------

    def _complexity(self, features):
        area = features.get("area", 0)
        perimeter = features.get("perimeter", 0)
        return np.where(area > 0, (perimeter ** 2) / area, 0)

    def _compactness(self, features):
        area = features.get("area", 0)
        perimeter = features.get("perimeter", 0)
        return np.where(perimeter > 0, (4 * np.pi * area) / (perimeter ** 2), 0)

    def _convexity(self, geom):
        if isinstance(geom, (Polygon, MultiPolygon)):
            try:
                hull = geom.convex_hull
                return geom.area / hull.area if hull.area > 0 else 0
            except:
                return 0
        return 0

    def _aspect_ratio(self, geom):
        try:
            minx, miny, maxx, maxy = geom.bounds
            width = maxx - minx
            height = maxy - miny
            return width / height if height > 0 else 0
        except:
            return 0

    # ---------------------------------------------------
    # ADVANCED FEATURES
    # ---------------------------------------------------

    def _count_vertices(self, geom):
        try:
            if isinstance(geom, Point):
                return 1
            elif isinstance(geom, LineString):
                return len(geom.coords)
            elif isinstance(geom, Polygon):
                return len(geom.exterior.coords)
            elif isinstance(geom, MultiPolygon):
                return sum(len(poly.exterior.coords) for poly in geom.geoms)
            return 0
        except:
            return 0

    def _count_holes(self, geom):
        try:
            if isinstance(geom, Polygon):
                return len(geom.interiors)
            elif isinstance(geom, MultiPolygon):
                return sum(len(poly.interiors) for poly in geom.geoms)
            return 0
        except:
            return 0

    def _bbox_area(self, geom):
        try:
            minx, miny, maxx, maxy = geom.bounds
            return (maxx - minx) * (maxy - miny)
        except:
            return 0

    def _elongation(self, features):
        area = features.get("area", 0)
        bbox_area = features.get("bbox_area", 0)
        return np.where(bbox_area > 0, area / bbox_area, 0)

    def _bbox_perimeter_ratio(self, geometries):
        ratios = []
        for geom in geometries:
            try:
                minx, miny, maxx, maxy = geom.bounds
                bbox_perim = 2 * ((maxx - minx) + (maxy - miny))
                ratios.append(geom.length / bbox_perim if bbox_perim > 0 else 0)
            except:
                ratios.append(0)
        return ratios

    def _irregularity(self, features):
        """
        Measures deviation from circularity & convexity combined.
        High values → irregular shapes.
        """
        compactness = features.get("compactness", 0)
        convexity = features.get("convexity", 0)
        return (1 - compactness) + (1 - convexity)

    # ---------------------------------------------------
    # FEATURE NAMES
    # ---------------------------------------------------

    def get_feature_names(self) -> List[str]:
        return [
            "area",
            "perimeter",
            "complexity",
            "compactness",
            "convexity",
            "aspect_ratio",
            "num_vertices",
            "num_holes",
            "bbox_area",
            "elongation",
            "bbox_perimeter_ratio",
            "irregularity_index"
        ]
