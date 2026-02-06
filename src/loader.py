"""
Enhanced GeoJSON Data Loader
Robust, validation-aware, deployment-safe
"""

import json
import pandas as pd
from shapely.geometry import shape
from shapely.validation import explain_validity
from typing import Dict, List, Tuple, Optional


class GeoDataLoader:
    """
    Handles loading, validation, and parsing of GeoJSON data.
    Works without strict dependency on GeoPandas.
    """

    def __init__(self):
        self.data = None
        self.df = None

    # ---------------------------------------------------
    # LOAD FROM UPLOAD
    # ---------------------------------------------------

    def load_from_file(self, uploaded_file) -> Tuple[bool, Optional[pd.DataFrame], str]:

        try:
            content = uploaded_file.read()

            # Handle bytes vs string
            if isinstance(content, bytes):
                content = content.decode("utf-8")

            geojson_data = json.loads(content)

            return self._parse_geojson(geojson_data)

        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON format: {str(e)}"

        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"

    # ---------------------------------------------------
    # LOAD FROM PATH
    # ---------------------------------------------------

    def load_from_path(self, file_path: str) -> Tuple[bool, Optional[pd.DataFrame], str]:

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            return self._parse_geojson(geojson_data)

        except Exception as e:
            return False, None, f"Error loading file: {str(e)}"

    # ---------------------------------------------------
    # PARSE GEOJSON CORE
    # ---------------------------------------------------

    def _parse_geojson(self, geojson_data) -> Tuple[bool, Optional[pd.DataFrame], str]:

        if "type" not in geojson_data:
            return False, None, "Invalid GeoJSON: Missing 'type' field"

        if geojson_data["type"] == "FeatureCollection":
            features = geojson_data.get("features", [])
        elif geojson_data["type"] == "Feature":
            features = [geojson_data]
        else:
            return False, None, f"Unsupported GeoJSON type: {geojson_data['type']}"

        if not features:
            return False, None, "No features found in GeoJSON"

        records = []
        invalid_geometries = 0

        for feature in features:
            try:
                geom_data = feature.get("geometry")
                if geom_data is None:
                    continue

                geom = shape(geom_data)

                # Validate geometry
                is_valid = geom.is_valid
                validity_reason = None

                if not is_valid:
                    invalid_geometries += 1
                    validity_reason = explain_validity(geom)

                    # Auto-fix attempt
                    geom = geom.buffer(0)

                properties = feature.get("properties", {})

                records.append({
                    "geometry": geom,
                    "geometry_type": geom.geom_type,
                    "is_valid_on_load": is_valid,
                    "validity_issue": validity_reason,
                    **properties
                })

            except Exception as e:
                continue

        if not records:
            return False, None, "No valid geometries parsed"

        df = pd.DataFrame(records)

        self.df = df
        self.data = geojson_data

        message = f"Loaded {len(df)} features"
        if invalid_geometries > 0:
            message += f" ({invalid_geometries} geometries auto-corrected)"

        return True, df, message

    # ---------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------

    def get_summary(self) -> Dict:

        if self.df is None:
            return {}

        bounds = self._calculate_bounds()

        return {
            "total_features": len(self.df),
            "geometry_types": self.df["geometry_type"].value_counts().to_dict(),
            "bounds": bounds,
            "columns": list(self.df.columns),
            "invalid_on_load": int((~self.df["is_valid_on_load"]).sum())
        }

    # ---------------------------------------------------
    # PROPERTY NAMES
    # ---------------------------------------------------

    def get_feature_properties(self) -> List[str]:

        if self.df is None:
            return []

        return [
            col for col in self.df.columns
            if col not in ["geometry", "geometry_type", "is_valid_on_load", "validity_issue"]
        ]

    # ---------------------------------------------------
    # BOUND CALCULATION
    # ---------------------------------------------------

    def _calculate_bounds(self):

        if self.df is None or self.df.empty:
            return [0, 0, 0, 0]

        minx_list, miny_list, maxx_list, maxy_list = [], [], [], []

        for geom in self.df["geometry"]:
            try:
                minx, miny, maxx, maxy = geom.bounds
                minx_list.append(minx)
                miny_list.append(miny)
                maxx_list.append(maxx)
                maxy_list.append(maxy)
            except:
                continue

        if not minx_list:
            return [0, 0, 0, 0]

        return [
            min(minx_list),
            min(miny_list),
            max(maxx_list),
            max(maxy_list)
        ]
