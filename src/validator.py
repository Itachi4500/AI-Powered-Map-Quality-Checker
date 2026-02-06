"""
Rule-based validation module for geometric features
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.validation import explain_validity
from typing import Dict, List, Tuple
from config.settings import VALIDATION_RULES


class GeometryValidator:
    """Validates geometric features using rule-based checks"""
    
    def __init__(self, rules: Dict = None):
        self.rules = rules or VALIDATION_RULES
        self.errors = []
        
    def validate_geometry(self, gdf: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
        """
        Validate all geometries in GeoDataFrame
        
        Args:
            gdf: GeoDataFrame to validate
            
        Returns:
            Tuple of (validated GeoDataFrame with error flags, DataFrame of errors)
        """
        self.errors = []
        validated_gdf = gdf.copy()
        
        # Initialize validation columns
        validated_gdf['is_valid'] = True
        validated_gdf['validation_errors'] = ''
        validated_gdf['error_count'] = 0
        
        for idx, row in validated_gdf.iterrows():
            geom = row.geometry
            errors = []
            
            # Check 1: Geometry validity
            if not geom.is_valid:
                error_msg = explain_validity(geom)
                errors.append(f"Invalid geometry: {error_msg}")
                self._add_error(idx, 'geometry_validity', error_msg, geom)
            
            # Check 2: Self-intersection (for polygons)
            if self.rules.get('self_intersection_check', True):
                if isinstance(geom, (Polygon, MultiPolygon)):
                    if not geom.is_simple:
                        errors.append("Self-intersecting geometry")
                        self._add_error(idx, 'self_intersection', 'Geometry intersects itself', geom)
            
            # Check 3: Area constraints (for polygons)
            if isinstance(geom, (Polygon, MultiPolygon)):
                area = geom.area
                min_area = self.rules.get('min_area', 0)
                max_area = self.rules.get('max_area', float('inf'))
                
                if area < min_area:
                    errors.append(f"Area too small: {area:.2f} < {min_area}")
                    self._add_error(idx, 'area_too_small', f"Area {area:.2f} below minimum {min_area}", geom)
                
                if area > max_area:
                    errors.append(f"Area too large: {area:.2f} > {max_area}")
                    self._add_error(idx, 'area_too_large', f"Area {area:.2f} exceeds maximum {max_area}", geom)
            
            # Check 4: Perimeter constraints (for polygons)
            if isinstance(geom, (Polygon, MultiPolygon)):
                perimeter = geom.length
                min_perimeter = self.rules.get('min_perimeter', 0)
                
                if perimeter < min_perimeter:
                    errors.append(f"Perimeter too small: {perimeter:.2f} < {min_perimeter}")
                    self._add_error(idx, 'perimeter_too_small', f"Perimeter {perimeter:.2f} below minimum", geom)
            
            # Check 5: Empty geometry
            if geom.is_empty:
                errors.append("Empty geometry")
                self._add_error(idx, 'empty_geometry', 'Geometry is empty', geom)
            
            # Check 6: Coordinate precision
            if self._check_coordinate_precision(geom):
                errors.append("Excessive coordinate precision")
                self._add_error(idx, 'coordinate_precision', 'Coordinates have excessive precision', geom)
            
            # Update validation results
            if errors:
                validated_gdf.at[idx, 'is_valid'] = False
                validated_gdf.at[idx, 'validation_errors'] = '; '.join(errors)
                validated_gdf.at[idx, 'error_count'] = len(errors)
        
        # Create errors DataFrame
        errors_df = pd.DataFrame(self.errors)
        
        return validated_gdf, errors_df
    
    def _add_error(self, feature_id: int, error_type: str, message: str, geometry):
        """Add an error to the errors list"""
        self.errors.append({
            'feature_id': feature_id,
            'error_type': error_type,
            'message': message,
            'geometry_type': geometry.geom_type,
            'bounds': list(geometry.bounds) if hasattr(geometry, 'bounds') else None
        })
    
    def _check_coordinate_precision(self, geom) -> bool:
        """Check if coordinates have excessive precision"""
        max_precision = self.rules.get('coordinate_precision', 6)
        
        try:
            coords = list(geom.coords) if hasattr(geom, 'coords') else []
            
            # For polygons, get exterior coordinates
            if isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
            elif isinstance(geom, MultiPolygon):
                coords = []
                for poly in geom.geoms:
                    coords.extend(list(poly.exterior.coords))
            
            for coord in coords:
                for value in coord:
                    # Count decimal places
                    str_value = str(value)
                    if '.' in str_value:
                        decimal_places = len(str_value.split('.')[1])
                        if decimal_places > max_precision:
                            return True
            
            return False
            
        except Exception:
            return False
    
    def get_validation_summary(self, validated_gdf: gpd.GeoDataFrame) -> Dict:
        """Get summary of validation results"""
        total = len(validated_gdf)
        valid = validated_gdf['is_valid'].sum()
        invalid = total - valid
        
        error_types = {}
        for error in self.errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_features': total,
            'valid_features': int(valid),
            'invalid_features': int(invalid),
            'validation_rate': f"{(valid/total*100):.2f}%" if total > 0 else "0%",
            'error_types': error_types,
            'total_errors': len(self.errors)
        }
