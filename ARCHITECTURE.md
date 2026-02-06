# 🏗️ Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     STREAMLIT WEB APP                        │
│                        (app.py)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DATA LOADING (loader.py)                                 │
│     ├─ GeoJSON parsing                                       │
│     ├─ GeoDataFrame conversion                               │
│     └─ CRS validation                                        │
│                                                               │
│  2. RULE-BASED VALIDATION (validator.py)                     │
│     ├─ Geometry validity check                               │
│     ├─ Self-intersection detection                           │
│     ├─ Area/perimeter constraints                            │
│     ├─ Coordinate precision check                            │
│     └─ Error collection                                      │
│                                                               │
│  3. FEATURE ENGINEERING (feature_engineering.py)             │
│     ├─ Area & perimeter extraction                           │
│     ├─ Complexity calculation                                │
│     ├─ Compactness & convexity                               │
│     ├─ Aspect ratio & elongation                             │
│     └─ Vertex & hole counting                                │
│                                                               │
│  4. ANOMALY DETECTION (anomaly_detector.py)                  │
│     ├─ Feature scaling                                       │
│     ├─ Isolation Forest training                             │
│     ├─ Anomaly prediction                                    │
│     └─ Score normalization                                   │
│                                                               │
│  5. VISUALIZATION (visualizer.py)                            │
│     ├─ Plotly map creation                                   │
│     ├─ Color-coded features                                  │
│     ├─ Interactive charts                                    │
│     └─ Multi-view support                                    │
│                                                               │
│  6. REPORTING (reporter.py)                                  │
│     ├─ Summary generation                                    │
│     ├─ Recommendation engine                                 │
│     ├─ Export to JSON/CSV                                    │
│     └─ Combined analysis                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
GeoJSON File
    │
    ▼
[LOADER] → GeoDataFrame
    │
    ├─────────────────┬─────────────────┐
    ▼                 ▼                 ▼
[VALIDATOR]    [FEATURE ENG]      [ORIGINAL]
    │                 │                 │
    ▼                 ▼                 │
Validation      Feature Matrix         │
Results              │                 │
    │                ▼                 │
    │         [ANOMALY DETECTOR]       │
    │                │                 │
    │                ▼                 │
    │         Anomaly Results          │
    │                │                 │
    └────────────────┴─────────────────┘
                     │
                     ▼
              [REPORTER]
                     │
                     ├──────────┬──────────┐
                     ▼          ▼          ▼
              [VISUALIZER]  JSON Export  CSV Export
                     │
                     ▼
            Interactive Maps
```

## Component Details

### 1. GeoDataLoader
- **Input**: GeoJSON file or path
- **Output**: GeoDataFrame
- **Key Functions**:
  - `load_from_file()`: Load from uploaded file
  - `load_from_path()`: Load from file path
  - `get_summary()`: Data statistics

### 2. GeometryValidator
- **Input**: GeoDataFrame
- **Output**: Validated GeoDataFrame + Error DataFrame
- **Validation Rules**:
  - Geometry validity (Shapely validation)
  - Self-intersection (is_simple check)
  - Area constraints (min/max thresholds)
  - Perimeter constraints
  - Coordinate precision

### 3. FeatureEngineer
- **Input**: GeoDataFrame
- **Output**: Feature DataFrame
- **Extracted Features**:
  - Basic: area, perimeter
  - Derived: complexity, compactness, convexity
  - Shape: aspect_ratio, elongation
  - Structural: num_vertices, num_holes

### 4. AnomalyDetector
- **Algorithm**: Isolation Forest
- **Input**: Feature DataFrame
- **Output**: Anomaly predictions + scores
- **Process**:
  1. Feature scaling (StandardScaler)
  2. Model training (IsolationForest)
  3. Prediction (-1 = anomaly, 1 = normal)
  4. Score normalization

### 5. MapVisualizer
- **Library**: Plotly
- **Map Types**:
  - Validation results map
  - Anomaly detection map
  - Combined analysis map
- **Charts**:
  - Feature distributions (box plots)
  - Error breakdown (pie chart)

### 6. ErrorReporter
- **Input**: All analysis results
- **Output**: Comprehensive report
- **Sections**:
  - Metadata & summary
  - Validation results
  - Anomaly detection results
  - Combined issues
  - Recommendations

## Configuration

All settings are centralized in `config/settings.py`:

- **VALIDATION_RULES**: Thresholds and checks
- **ANOMALY_DETECTION_PARAMS**: ML model parameters
- **VIZ_SETTINGS**: Map and chart styling
- **FEATURE_PARAMS**: Feature extraction options

## Technology Stack

- **Frontend**: Streamlit
- **Geospatial**: GeoPandas, Shapely
- **ML**: Scikit-learn (Isolation Forest)
- **Visualization**: Plotly
- **Data Processing**: Pandas, NumPy

## Performance Considerations

- **Streaming**: Large files processed in chunks
- **Caching**: Streamlit session state for results
- **Optimization**: Vectorized operations with NumPy
- **Scalability**: Designed for datasets up to 10K features

## Extension Points

1. **New Validators**: Add to `validator.py`
2. **New Features**: Add to `feature_engineering.py`
3. **New ML Models**: Extend `anomaly_detector.py`
4. **New Visualizations**: Add to `visualizer.py`
5. **Custom Reports**: Extend `reporter.py`
