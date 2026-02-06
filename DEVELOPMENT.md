# 🛠️ Development Guide

## Getting Started with Development

### Setting Up Development Environment

1. **Clone/Navigate to Project**
```bash
cd "d:\Projects\Personal_Projects\German Hackathon\ai-map-quality-checker"
```

2. **Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Development Tools (Optional)**
```bash
pip install black flake8 pytest
```

## 📁 Code Organization

### Module Responsibilities

```
src/
├── loader.py           # Data I/O operations
├── validator.py        # Rule-based checks
├── feature_engineering.py  # Feature extraction
├── anomaly_detector.py     # ML operations
├── reporter.py         # Report generation
└── visualizer.py       # Visualization
```

### Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Loose Coupling**: Modules interact through well-defined interfaces
3. **High Cohesion**: Related functionality grouped together
4. **Dependency Injection**: Configuration passed as parameters

## 🔧 Common Development Tasks

### Adding a New Validation Rule

**File**: `src/validator.py`

```python
# In GeometryValidator.validate_geometry()

# Check N: Your new validation
if your_condition:
    errors.append("Your error message")
    self._add_error(idx, 'your_error_type', 'Detailed message', geom)
```

**Update Configuration**: `config/settings.py`

```python
VALIDATION_RULES = {
    # ... existing rules ...
    'your_new_rule': True,
    'your_threshold': 100
}
```

### Adding a New Geometric Feature

**File**: `src/feature_engineering.py`

```python
class FeatureEngineer:
    def extract_features(self, gdf):
        features = pd.DataFrame()
        # ... existing features ...
        
        # Add your new feature
        features['your_feature'] = self._calculate_your_feature(gdf)
        
        return features
    
    def _calculate_your_feature(self, gdf):
        """Calculate your custom feature"""
        results = []
        for geom in gdf.geometry:
            # Your calculation logic
            value = your_calculation(geom)
            results.append(value)
        return pd.Series(results, index=gdf.index)
```

### Adding a New ML Algorithm

**File**: `src/anomaly_detector.py`

Create a new class or extend existing:

```python
from sklearn.svm import OneClassSVM

class SVMAnomalyDetector:
    def __init__(self, params=None):
        self.params = params or {}
        self.model = OneClassSVM(
            kernel=self.params.get('kernel', 'rbf'),
            nu=self.params.get('nu', 0.1)
        )
        self.scaler = StandardScaler()
    
    # Implement train(), predict(), etc.
```

### Adding a New Visualization

**File**: `src/visualizer.py`

```python
class MapVisualizer:
    def create_your_custom_map(self, gdf):
        """Create your custom visualization"""
        fig = go.Figure()
        
        # Your visualization logic
        
        self._update_map_layout(fig, gdf, "Your Title")
        return fig
```

**Update App**: `app.py`

```python
# In the Visualization tab
map_type = st.selectbox(
    "Select map view",
    ["Validation Results", "Anomaly Detection", "Combined Analysis", "Your Custom View"]
)

if map_type == "Your Custom View":
    fig = viz.create_your_custom_map(st.session_state.gdf)
    st.plotly_chart(fig, use_container_width=True)
```

### Adding a New Report Section

**File**: `src/reporter.py`

```python
class ErrorReporter:
    def generate_report(self, ...):
        report = {
            # ... existing sections ...
            'your_section': self._analyze_your_aspect(gdf)
        }
        return report
    
    def _analyze_your_aspect(self, gdf):
        """Analyze your custom aspect"""
        return {
            'metric1': value1,
            'metric2': value2
        }
```

## 🧪 Testing

### Manual Testing

1. **Test with Sample Data**
```bash
streamlit run app.py
# Use "Use sample data" checkbox
# Select "Invalid" to test validation
```

2. **Test with Custom Data**
- Create test GeoJSON files
- Upload and run analysis
- Verify results

### Unit Testing (Future Enhancement)

Create `tests/` directory:

```python
# tests/test_validator.py
import pytest
from src.validator import GeometryValidator

def test_valid_polygon():
    # Your test code
    pass

def test_invalid_polygon():
    # Your test code
    pass
```

Run tests:
```bash
pytest tests/
```

## 🎨 UI Customization

### Changing Colors

**File**: `config/settings.py`

```python
VIZ_SETTINGS = {
    'valid_color': '#00FF00',      # Change to your color
    'invalid_color': '#FF0000',    # Change to your color
    'anomaly_color': '#FFA500',    # Change to your color
}
```

### Modifying Layout

**File**: `app.py`

```python
# Change page config
st.set_page_config(
    page_title="Your Title",
    page_icon="🎯",
    layout="wide"
)

# Modify CSS
st.markdown("""
<style>
    .your-custom-class {
        /* Your styles */
    }
</style>
""", unsafe_allow_html=True)
```

### Adding New Tabs

**File**: `app.py`

```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", 
    "✓ Validation", 
    "🤖 Anomaly Detection", 
    "🗺️ Visualization", 
    "📄 Report",
    "🆕 Your New Tab"  # Add here
])

# ... existing tabs ...

with tab6:
    st.header("Your New Tab")
    # Your content
```

## 📊 Performance Optimization

### Caching Results

Use Streamlit caching:

```python
@st.cache_data
def expensive_computation(data):
    # Your expensive operation
    return result
```

### Vectorization

Use NumPy/Pandas vectorized operations:

```python
# ❌ Slow - Loop
results = []
for geom in gdf.geometry:
    results.append(geom.area)

# ✅ Fast - Vectorized
results = gdf.geometry.area
```

### Batch Processing

Process large datasets in chunks:

```python
chunk_size = 1000
for i in range(0, len(gdf), chunk_size):
    chunk = gdf.iloc[i:i+chunk_size]
    process_chunk(chunk)
```

## 🐛 Debugging Tips

### Enable Debug Mode

```bash
streamlit run app.py --logger.level=debug
```

### Print Debugging

```python
import streamlit as st

st.write("Debug:", variable)
st.json(data_dict)
st.dataframe(df)
```

### Error Handling

Add try-except blocks:

```python
try:
    result = risky_operation()
except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
```

## 📦 Deployment

### Local Deployment

```bash
streamlit run app.py --server.port 8501
```

### Streamlit Cloud

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy from repository

### Docker (Future)

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 🔐 Security Considerations

1. **Input Validation**: Always validate uploaded files
2. **File Size Limits**: Set maximum file sizes
3. **Environment Variables**: Use `.env` for secrets
4. **Error Messages**: Don't expose sensitive information

## 📚 Additional Resources

### Streamlit
- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Gallery](https://streamlit.io/gallery)

### GeoPandas
- [GeoPandas Documentation](https://geopandas.org)
- [Shapely Manual](https://shapely.readthedocs.io)

### Scikit-learn
- [Scikit-learn Documentation](https://scikit-learn.org)
- [Isolation Forest Guide](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

### Plotly
- [Plotly Documentation](https://plotly.com/python/)
- [Plotly Maps](https://plotly.com/python/maps/)

## 🤝 Contributing Guidelines

1. **Code Style**: Follow PEP 8
2. **Documentation**: Add docstrings to functions
3. **Comments**: Explain complex logic
4. **Testing**: Test your changes
5. **Commit Messages**: Be descriptive

## 💡 Ideas for Enhancement

### Short Term
- [ ] Add more validation rules
- [ ] Implement One-Class SVM
- [ ] Add batch file processing
- [ ] Create unit tests
- [ ] Add logging

### Medium Term
- [ ] REST API endpoints
- [ ] Database integration
- [ ] User authentication
- [ ] Advanced reporting templates
- [ ] Multi-language support

### Long Term
- [ ] Cloud deployment
- [ ] Real-time collaboration
- [ ] Version control for datasets
- [ ] Integration with GIS platforms
- [ ] Mobile app

---

Happy coding! 🚀
