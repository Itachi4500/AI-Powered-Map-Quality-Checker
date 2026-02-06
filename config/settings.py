"""
Configuration settings for the AI Map Quality Checker
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mapbox Configuration
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN', 'your_mapbox_token_here')

# Model Parameters
ANOMALY_DETECTION_PARAMS = {
    'contamination': 0.1,  # Expected proportion of outliers
    'n_estimators': 100,
    'max_samples': 'auto',
    'random_state': 42
}

# Validation Rules
VALIDATION_RULES = {
    'min_area': 10,  # Minimum area in square meters
    'max_area': 1000000,  # Maximum area in square meters
    'min_perimeter': 10,  # Minimum perimeter in meters
    'complexity_threshold': 0.5,  # Complexity ratio threshold
    'self_intersection_check': True,
    'coordinate_precision': 6  # Decimal places for coordinates
}

# Feature Engineering Parameters
FEATURE_PARAMS = {
    'use_area': True,
    'use_perimeter': True,
    'use_complexity': True,
    'use_compactness': True,
    'use_convexity': True,
    'use_aspect_ratio': True
}

# Visualization Settings
VIZ_SETTINGS = {
    'default_zoom': 12,
    'default_center': [51.1657, 10.4515],  # Germany center
    'valid_color': '#00FF00',
    'invalid_color': '#FF0000',
    'anomaly_color': '#FFA500',
    'map_style': 'open-street-map'
}

# Report Settings
REPORT_SETTINGS = {
    'max_errors_display': 100,
    'export_format': 'csv',
    'include_screenshots': False
}
