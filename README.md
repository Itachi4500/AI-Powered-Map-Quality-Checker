# 🗺️ AI Map Quality Checker

An intelligent GeoJSON validation and quality assessment tool powered by machine learning. This application combines rule-based validation with AI-driven anomaly detection to ensure the highest quality of geographic data.

## ✨ Features

### 🔍 Rule-Based Validation
- **Geometry Validity**: Checks for invalid geometries and provides detailed error messages
- **Self-Intersection Detection**: Identifies polygons that intersect themselves
- **Area & Perimeter Constraints**: Validates features against configurable thresholds
- **Coordinate Precision**: Detects excessive coordinate precision
- **Empty Geometry Detection**: Identifies and flags empty geometries

### 🤖 AI-Powered Anomaly Detection
- **Isolation Forest Algorithm**: Detects unusual geometric patterns
- **Feature Engineering**: Extracts 10+ geometric features including:
  - Area, perimeter, complexity
  - Compactness, convexity, aspect ratio
  - Vertex count, hole count, elongation
- **Anomaly Scoring**: Provides normalized scores for each feature
- **Model Persistence**: Save and load trained models

### 📊 Interactive Visualization
- **Plotly Maps**: Interactive map visualization with hover information
- **Multiple Views**: Validation results, anomaly detection, and combined analysis
- **Color-Coded Features**: Easy identification of issues
- **Statistical Charts**: Feature distributions and error breakdowns

### 📄 Comprehensive Reporting
- **Detailed Error Reports**: Complete breakdown of all validation errors
- **Anomaly Analysis**: Top anomalies with scores and locations
- **Combined Issue Detection**: Identifies features with multiple problems
- **Actionable Recommendations**: Specific suggestions for data improvement
- **Export Options**: JSON and CSV export formats

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or navigate to the project directory**
```bash
cd ai-map-quality-checker
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure settings (optional)**
Edit `config/settings.py` to customize:
- Validation rules (min/max area, perimeter thresholds)
- ML model parameters (contamination rate, estimators)
- Visualization settings (colors, map style)

## 🎯 Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Interface

1. **Upload Data**
   - Click "Browse files" in the sidebar
   - Select a GeoJSON file
   - Or use the sample data checkbox for testing

2. **Configure Settings**
   - Adjust validation rules (min/max area, etc.)
   - Set ML parameters (anomaly rate, estimators)

3. **Run Analysis**
   - Click "🔍 Run Analysis" button
   - Wait for processing to complete

4. **Explore Results**
   - **Overview Tab**: Data summary and statistics
   - **Validation Tab**: Rule-based validation results
   - **Anomaly Detection Tab**: ML-based anomaly findings
   - **Visualization Tab**: Interactive maps
   - **Report Tab**: Comprehensive quality report

5. **Export Results**
   - Navigate to the Report tab
   - Choose JSON or CSV format
   - Click export button

## 📁 Project Structure

```
ai-map-quality-checker/
│
├── app.py                        # Streamlit entry point
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── config/
│   └── settings.py               # Configuration settings
│
├── data/
│   ├── sample_valid.geojson      # Sample valid data
│   └── sample_invalid.geojson    # Sample invalid data
│
├── src/
│   ├── __init__.py
│   ├── loader.py                 # GeoJSON data loading
│   ├── validator.py              # Rule-based validation
│   ├── feature_engineering.py    # Geometric feature extraction
│   ├── anomaly_detector.py       # ML anomaly detection
│   ├── reporter.py               # Report generation
│   └── visualizer.py             # Map visualization
│
└── models/
    └── isolation_forest.pkl      # Trained ML model (generated)
```

## 🔧 Configuration

### Validation Rules

Edit `config/settings.py` to customize validation rules:

```python
VALIDATION_RULES = {
    'min_area': 10,                    # Minimum area in square meters
    'max_area': 1000000,               # Maximum area in square meters
    'min_perimeter': 10,               # Minimum perimeter in meters
    'complexity_threshold': 0.5,       # Complexity ratio threshold
    'self_intersection_check': True,   # Enable self-intersection check
    'coordinate_precision': 6          # Max decimal places
}
```

### ML Parameters

Adjust anomaly detection sensitivity:

```python
ANOMALY_DETECTION_PARAMS = {
    'contamination': 0.1,    # Expected proportion of outliers (10%)
    'n_estimators': 100,     # Number of trees in forest
    'max_samples': 'auto',   # Samples per tree
    'random_state': 42       # Reproducibility seed
}
```

## 📊 Sample Data

The project includes two sample GeoJSON files:

- **sample_valid.geojson**: Clean data with valid geometries
- **sample_invalid.geojson**: Data with various validation errors for testing

## 🛠️ Development

### Adding New Validation Rules

1. Edit `src/validator.py`
2. Add new check in `validate_geometry()` method
3. Update `VALIDATION_RULES` in `config/settings.py`

### Adding New Features

1. Edit `src/feature_engineering.py`
2. Add new feature extraction method
3. Update `extract_features()` to include new feature

### Customizing Visualization

1. Edit `src/visualizer.py`
2. Modify color schemes in `config/settings.py`
3. Add new chart types as needed

## 📈 Performance

- **Validation**: ~1000 features/second
- **Feature Extraction**: ~500 features/second
- **ML Training**: Depends on dataset size and parameters
- **Visualization**: Optimized for datasets up to 10,000 features

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional validation rules
- More ML algorithms (One-Class SVM, Local Outlier Factor)
- Advanced visualization options
- Batch processing capabilities
- API endpoints for integration

## 📝 License

This project is open source and available for use in hackathons and educational purposes.

## 🙏 Acknowledgments

- **Streamlit**: For the amazing web framework
- **Scikit-learn**: For ML algorithms
- **GeoPandas**: For geospatial data handling
- **Plotly**: For interactive visualizations
- **Shapely**: For geometric operations

## 📧 Support

For issues, questions, or suggestions, please create an issue in the project repository.

---

**Built with ❤️ for the German Hackathon**

🗺️ Ensuring map data quality through AI and automation
