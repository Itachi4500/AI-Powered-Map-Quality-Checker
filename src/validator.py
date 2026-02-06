"""
Enhanced Rule-Based Geometry Validator
Enterprise-grade topology validation engine
"""

import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity
from shapely.ops import unary_union
from typing import Dict, Tuple
from config.settings import VALIDATION_RULES


class GeometryValidator:
    """
    Performs advanced rule-based geometry validation
    with severity scoring and topology checks.
    """

    def __init__(self, rules: Dict = None):
        self.rules = rules or VALIDATION_RULES
        self.errors = []

    # ---------------------------------------------------
    # MAIN VALIDATION
    # ---------------------------------------------------

    def validate_geometry(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

        self.errors = []
        validated_df = df.copy()

        validated_df["is_valid"] = True
        validated_df["validation_errors"] = ""
        validated_df["error_count"] = 0
        validated_df["severity_score"] = 0

        # Pre-calculate overlaps if enabled
        overlap_pairs = self._detect_overlaps(validated_df)

        for idx, row in validated_df.iterrows():
            geom = row.geometry
            feature_errors = []
            severity = 0

            if geom is None:
                continue

            # 1️⃣ Geometry validity
            if not geom.is_valid:
                msg = explain_validity(geom)
                feature_errors.append(f"Invalid geometry: {msg}")
                self._add_error(idx, "geometry_validity", msg, geom)
                severity += 3

            # 2️⃣ Self-intersection
            if isinstance(geom, (Polygon, MultiPolygon)) and not geom.is_simple:
                feature_errors.append("Self-intersecting geometry")
                self._add_error(idx, "self_intersection", "Geometry intersects itself", geom)
                severity += 3

            # 3️⃣ Area constraints
            if isinstance(geom, (Polygon, MultiPolygon)):
                area = geom.area
                min_area = self.rules.get("min_area", 0)
                max_area = self.rules.get("max_area", float("inf"))

                if area < min_area:
                    feature_errors.append(f"Area too small: {area:.4f}")
                    self._add_error(idx, "area_too_small", f"Area below minimum", geom)
                    severity += 2

                if area > max_area:
                    feature_errors.append(f"Area too large: {area:.4f}")
                    self._add_error(idx, "area_too_large", f"Area above maximum", geom)
                    severity += 2

                # Sliver detection
                if area > 0 and geom.length / area > 100:
                    feature_errors.append("Sliver polygon detected")
                    self._add_error(idx, "sliver_polygon", "High perimeter-to-area ratio", geom)
                    severity += 2

            # 4️⃣ Overlap detection
            if idx in overlap_pairs:
                feature_errors.append("Overlaps with another feature")
                self._add_error(idx, "overlap", "Feature overlaps another geometry", geom)
                severity += 3

            # 5️⃣ Empty geometry
            if geom.is_empty:
                feature_errors.append("Empty geometry")
                self._add_error(idx, "empty_geometry", "Geometry is empty", geom)
                severity += 3

            # 6️⃣ Coordinate precision
            if self._check_coordinate_precision(geom):
                feature_errors.append("Excessive coordinate precision")
                self._add_error(idx, "coordinate_precision", "Too many decimal places", geom)
                severity += 1

            # Update row
            if feature_errors:
                validated_df.at[idx, "is_valid"] = False
                validated_df.at[idx, "validation_errors"] = "; ".join(feature_errors)
                validated_df.at[idx, "error_count"] = len(feature_errors)
                validated_df.at[idx, "severity_score"] = severity

        errors_df = pd.DataFrame(self.errors)

        return validated_df, errors_df

    # ---------------------------------------------------
    # OVERLAP DETECTION
    # ---------------------------------------------------

    def _detect_overlaps(self, df):

        overlap_indices = set()

        geometries = df.geometry.tolist()

        for i in range(len(geometries)):
            for j in range(i + 1, len(geometries)):
                try:
                    if geometries[i].intersects(geometries[j]) and not geometries[i].touches(geometries[j]):
                        overlap_indices.add(df.index[i])
                        overlap_indices.add(df.index[j])
                except:
                    continue

        return overlap_indices

    # ---------------------------------------------------
    # ERROR RECORDING
    # ---------------------------------------------------

    def _add_error(self, feature_id, error_type, message, geometry):

        self.errors.append({
            "feature_id": feature_id,
            "error_type": error_type,
            "message": message,
            "geometry_type": geometry.geom_type,
            "bounds": list(geometry.bounds) if hasattr(geometry, "bounds") else None
        })

    # ---------------------------------------------------
    # COORDINATE PRECISION CHECK
    # ---------------------------------------------------

    def _check_coordinate_precision(self, geom):

        max_precision = self.rules.get("coordinate_precision", 6)

        try:
            coords = []

            if hasattr(geom, "coords"):
                coords = list(geom.coords)
            elif isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
            elif isinstance(geom, MultiPolygon):
                for poly in geom.geoms:
                    coords.extend(list(poly.exterior.coords))

            for x, y in coords:
                if len(str(x).split(".")[-1]) > max_precision:
                    return True
                if len(str(y).split(".")[-1]) > max_precision:
                    return True

            return False

        except:
            return False

    # ---------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------

    def get_validation_summary(self, validated_df: pd.DataFrame) -> Dict:

        total = len(validated_df)
        valid = validated_df["is_valid"].sum()
        invalid = total - valid

        error_types = {}
        for err in self.errors:
            error_types[err["error_type"]] = error_types.get(err["error_type"], 0) + 1

        avg_severity = (
            validated_df["severity_score"].mean()
            if "severity_score" in validated_df.columns else 0
        )

        return {
            "total_features": total,
            "valid_features": int(valid),
            "invalid_features": int(invalid),
            "validation_rate": f"{(valid/total*100):.2f}%" if total > 0 else "0%",
            "error_types": error_types,
            "total_errors": len(self.errors),
            "average_severity_score": round(float(avg_severity), 2)
        }
