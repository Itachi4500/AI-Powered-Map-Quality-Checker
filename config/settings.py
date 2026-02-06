"""
Centralized Configuration Settings
AI Map Quality Checker
Deployment-safe, environment-aware
"""

import os

# =====================================================
# OPTIONAL .env SUPPORT (SAFE IMPORT)
# =====================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed — safe to ignore (Streamlit Cloud)
    pass


# =====================================================
# ENVIRONMENT FLAGS
# =====================================================

ENVIRONMENT = os.getenv("APP_ENV", "production")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# =====================================================
# MAPBOX CONFIGURATION
# =====================================================

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

# If no token provided, fallback to public style
DEFAULT_MAP_STYLE = "carto-positron" if not MAPBOX_TOKEN else "mapbox://styles/mapbox/streets-v11"


# =====================================================
# ANOMALY DETECTION PARAMETERS
# =====================================================

ANOMALY_DETECTION_PARAMS = {
    "contamination": float(os.getenv("ANOMALY_CONTAMINATION", 0.1)),
    "n_estimators": int(os.getenv("ANOMALY_ESTIMATORS", 100)),
    "max_samples": "auto",
    "random_state": 42
}


# =====================================================
# VALIDATION RULES
# =====================================================

VALIDATION_RULES = {
    "min_area": float(os.getenv("MIN_AREA", 10)),
    "max_area": float(os.getenv("MAX_AREA", 1_000_000)),
    "min_perimeter": float(os.getenv("MIN_PERIMETER", 10)),
    "self_intersection_check": True,
    "coordinate_precision": int(os.getenv("COORD_PRECISION", 6)),
}


# =====================================================
# FEATURE ENGINEERING PARAMETERS
# =====================================================

FEATURE_PARAMS = {
    "use_area": True,
    "use_perimeter": True,
    "use_complexity": True,
    "use_compactness": True,
    "use_convexity": True,
    "use_aspect_ratio": True,
}


# =====================================================
# VISUALIZATION SETTINGS
# =====================================================

VIZ_SETTINGS = {
    "default_zoom": 12,
    "default_center": [51.1657, 10.4515],  # Germany center
    "valid_color": "#00CC96",
    "invalid_color": "#EF553B",
    "anomaly_color": "#FFA15A",
    "critical_color": "#FF00FF",
    "map_style": DEFAULT_MAP_STYLE,
}


# =====================================================
# REPORT SETTINGS
# =====================================================

REPORT_SETTINGS = {
    "max_errors_display": 100,
    "export_format": "json",
    "include_screenshots": False,
    "report_version": "2.0"
}
