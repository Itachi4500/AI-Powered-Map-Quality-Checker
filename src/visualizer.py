"""
Enhanced Interactive Map Visualization Module
Optimized, scalable, and production-ready
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional
from config.settings import VIZ_SETTINGS


class MapVisualizer:
    """
    Creates interactive Plotly Mapbox visualizations
    with performance optimizations and severity mapping.
    """

    def __init__(self, settings: dict = None):
        self.settings = settings or VIZ_SETTINGS

    # =====================================================
    # VALIDATION MAP
    # =====================================================

    def create_validation_map(self, df: pd.DataFrame) -> go.Figure:

        fig = go.Figure()

        if "is_valid" in df.columns:
            valid = df[df["is_valid"]]
            invalid = df[~df["is_valid"]]

            if not valid.empty:
                self._add_layer(fig, valid, self.settings["valid_color"],
                                "Valid Features", 0.4)

            if not invalid.empty:
                self._add_layer(fig, invalid, self.settings["invalid_color"],
                                "Invalid Features", 0.8)

        else:
            self._add_layer(fig, df, "blue", "Features", 0.6)

        self._update_layout(fig, df, "Validation Results")
        return fig

    # =====================================================
    # ANOMALY MAP
    # =====================================================

    def create_anomaly_map(self, df: pd.DataFrame) -> go.Figure:

        fig = go.Figure()

        if "is_anomaly" in df.columns:
            normal = df[~df["is_anomaly"]]
            anomaly = df[df["is_anomaly"]]

            if not normal.empty:
                self._add_layer(fig, normal, self.settings["valid_color"],
                                "Normal Features", 0.4)

            if not anomaly.empty:
                self._add_layer(fig, anomaly, self.settings["anomaly_color"],
                                "Anomalies", 0.9)

        else:
            self._add_layer(fig, df, "blue", "Features", 0.6)

        self._update_layout(fig, df, "Anomaly Detection")
        return fig

    # =====================================================
    # SEVERITY HEAT MAP (NEW 🔥)
    # =====================================================

    def create_severity_map(self, df: pd.DataFrame) -> go.Figure:
        """
        Color by severity_score if available
        """

        fig = go.Figure()

        if "severity_score" in df.columns:

            max_severity = df["severity_score"].max() or 1

            for idx, row in df.iterrows():
                geom = row.geometry
                severity = row["severity_score"] / max_severity

                color = f"rgba(255, 0, 0, {severity})"

                self._add_single_geometry(fig, geom, color,
                                          f"Severity {row['severity_score']}",
                                          opacity=0.8)

        else:
            self._add_layer(fig, df, "blue", "Features", 0.6)

        self._update_layout(fig, df, "Severity Heat Map")
        return fig

    # =====================================================
    # CORE GEOMETRY RENDERING
    # =====================================================

    def _add_layer(self, fig, df, color, name, opacity):

        for idx, row in df.iterrows():
            geom = row.geometry
            hover_text = self._hover_text(row, idx)
            self._add_single_geometry(fig, geom, color, hover_text, opacity, name)

    def _add_single_geometry(self, fig, geom, color, hover_text,
                             opacity=0.6, name="Feature"):

        if geom is None:
            return

        if geom.geom_type == "Polygon":
            x, y = geom.exterior.xy
            fig.add_trace(go.Scattermapbox(
                lon=list(x),
                lat=list(y),
                mode="lines",
                fill="toself",
                fillcolor=color,
                line=dict(color=color, width=2),
                opacity=opacity,
                text=hover_text,
                hoverinfo="text",
                name=name,
                showlegend=False
            ))

        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                self._add_single_geometry(fig, poly, color, hover_text,
                                          opacity, name)

        elif geom.geom_type == "LineString":
            x, y = geom.xy
            fig.add_trace(go.Scattermapbox(
                lon=list(x),
                lat=list(y),
                mode="lines",
                line=dict(color=color, width=3),
                opacity=opacity,
                text=hover_text,
                hoverinfo="text",
                name=name,
                showlegend=False
            ))

        elif geom.geom_type == "Point":
            fig.add_trace(go.Scattermapbox(
                lon=[geom.x],
                lat=[geom.y],
                mode="markers",
                marker=dict(size=8, color=color),
                text=hover_text,
                hoverinfo="text",
                name=name,
                showlegend=False
            ))

    # =====================================================
    # HOVER TEXT
    # =====================================================

    def _hover_text(self, row, idx):

        lines = [f"<b>ID:</b> {idx}"]

        if "is_valid" in row:
            lines.append(f"Validation: {'✓ Valid' if row['is_valid'] else '✗ Invalid'}")

        if "is_anomaly" in row:
            lines.append(f"Anomaly: {'⚠ Yes' if row['is_anomaly'] else 'No'}")

        if "anomaly_score" in row:
            lines.append(f"Score: {row['anomaly_score']:.4f}")

        if "severity_score" in row:
            lines.append(f"Severity: {row['severity_score']}")

        lines.append(f"Type: {row.geometry.geom_type}")

        return "<br>".join(lines)

    # =====================================================
    # SMART MAP LAYOUT
    # =====================================================

    def _update_layout(self, fig, df, title):

        bounds = self._calculate_bounds(df)

        center_lon = (bounds[0] + bounds[2]) / 2
        center_lat = (bounds[1] + bounds[3]) / 2

        zoom = self._calculate_zoom(bounds)

        fig.update_layout(
            title=title,
            mapbox=dict(
                style=self.settings.get("map_style", "carto-positron"),
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=True
        )

    # =====================================================
    # SAFE BOUNDS (No GeoPandas dependency)
    # =====================================================

    def _calculate_bounds(self, df):

        minx, miny, maxx, maxy = [], [], [], []

        for geom in df["geometry"]:
            try:
                b = geom.bounds
                minx.append(b[0])
                miny.append(b[1])
                maxx.append(b[2])
                maxy.append(b[3])
            except:
                continue

        if not minx:
            return [0, 0, 0, 0]

        return [min(minx), min(miny), max(maxx), max(maxy)]

    # =====================================================
    # SMART ZOOM
    # =====================================================

    def _calculate_zoom(self, bounds):

        lon_range = bounds[2] - bounds[0]
        lat_range = bounds[3] - bounds[1]
        max_range = max(lon_range, lat_range)

        if max_range > 20:
            return 4
        elif max_range > 5:
            return 6
        elif max_range > 1:
            return 9
        elif max_range > 0.1:
            return 12
        else:
            return 14
