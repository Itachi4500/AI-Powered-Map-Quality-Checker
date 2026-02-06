"""
AI Map Quality Checker - Streamlit Application
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.loader import GeoDataLoader
from src.validator import GeometryValidator
from src.feature_engineering import FeatureEngineer
from src.anomaly_detector import AnomalyDetector
from src.reporter import ErrorReporter
from src.visualizer import MapVisualizer
from config.settings import MAPBOX_TOKEN, VALIDATION_RULES, ANOMALY_DETECTION_PARAMS

# Page configuration
st.set_page_config(
    page_title="AI Map Quality Checker",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'gdf' not in st.session_state:
    st.session_state.gdf = None
if 'validated_gdf' not in st.session_state:
    st.session_state.validated_gdf = None
if 'anomaly_gdf' not in st.session_state:
    st.session_state.anomaly_gdf = None
if 'features' not in st.session_state:
    st.session_state.features = None
if 'errors_df' not in st.session_state:
    st.session_state.errors_df = None
if 'report' not in st.session_state:
    st.session_state.report = None

# Header
st.markdown('<h1 class="main-header">🗺️ AI Map Quality Checker</h1>', unsafe_allow_html=True)
st.markdown("### Validate and analyze GeoJSON data with AI-powered quality checks")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # File upload
    st.subheader("📁 Data Input")
    uploaded_file = st.file_uploader("Upload GeoJSON file", type=['geojson', 'json'])
    
    # Sample data option
    use_sample = st.checkbox("Use sample data")
    sample_type = st.selectbox("Sample type", ["Valid", "Invalid"]) if use_sample else None
    
    st.divider()
    
    # Validation settings
    st.subheader("✓ Validation Rules")
    min_area = st.number_input("Minimum area", value=float(VALIDATION_RULES['min_area']), min_value=0.0)
    max_area = st.number_input("Maximum area", value=float(VALIDATION_RULES['max_area']), min_value=0.0)
    check_self_intersection = st.checkbox("Check self-intersection", value=True)
    
    st.divider()
    
    # ML settings
    st.subheader("🤖 ML Settings")
    contamination = st.slider("Expected anomaly rate", 0.01, 0.5, 
                             ANOMALY_DETECTION_PARAMS['contamination'], 0.01)
    n_estimators = st.slider("Number of estimators", 50, 200, 
                            ANOMALY_DETECTION_PARAMS['n_estimators'], 10)
    
    st.divider()
    
    # Actions
    st.subheader("🚀 Actions")
    run_analysis = st.button("🔍 Run Analysis", use_container_width=True)
    
    if st.session_state.report:
        export_format = st.selectbox("Export format", ["JSON", "CSV"])
        if st.button("📥 Export Report", use_container_width=True):
            st.session_state.export_requested = True

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "✓ Validation", 
    "🤖 Anomaly Detection", 
    "🗺️ Visualization", 
    "📄 Report"
])

# Load data
loader = GeoDataLoader()
data_loaded = False

if uploaded_file:
    success, gdf, message = loader.load_from_file(uploaded_file)
    if success:
        st.session_state.gdf = gdf
        data_loaded = True
    else:
        st.error(f"Error loading file: {message}")
elif use_sample:
    sample_path = Path(__file__).parent / "data" / f"sample_{sample_type.lower()}.geojson"
    if sample_path.exists():
        success, gdf, message = loader.load_from_path(str(sample_path))
        if success:
            st.session_state.gdf = gdf
            data_loaded = True
    else:
        st.warning(f"Sample file not found: {sample_path}")

# Run analysis
if run_analysis and st.session_state.gdf is not None:
    with st.spinner("🔄 Running analysis..."):
        # Update validation rules
        custom_rules = VALIDATION_RULES.copy()
        custom_rules['min_area'] = min_area
        custom_rules['max_area'] = max_area
        custom_rules['self_intersection_check'] = check_self_intersection
        
        # 1. Validation
        validator = GeometryValidator(custom_rules)
        validated_gdf, errors_df = validator.validate_geometry(st.session_state.gdf)
        st.session_state.validated_gdf = validated_gdf
        st.session_state.errors_df = errors_df
        validation_summary = validator.get_validation_summary(validated_gdf)
        
        # 2. Feature Engineering
        engineer = FeatureEngineer()
        features = engineer.extract_features(st.session_state.gdf)
        st.session_state.features = features
        
        # 3. Anomaly Detection
        detector = AnomalyDetector({
            'contamination': contamination,
            'n_estimators': n_estimators,
            'max_samples': 'auto',
            'random_state': 42
        })
        
        # Train and predict
        train_success, train_msg = detector.train(features)
        if train_success:
            anomaly_gdf = detector.detect_anomalies(st.session_state.gdf, features)
            st.session_state.anomaly_gdf = anomaly_gdf
            anomaly_summary = detector.get_anomaly_summary(anomaly_gdf)
            
            # Save model
            model_path = Path(__file__).parent / "models" / "isolation_forest.pkl"
            detector.save_model(str(model_path))
        else:
            st.error(f"ML training failed: {train_msg}")
            anomaly_summary = None
        
        # 4. Generate Report
        reporter = ErrorReporter()
        report = reporter.generate_report(
            validated_gdf,
            errors_df,
            st.session_state.anomaly_gdf,
            validation_summary,
            anomaly_summary
        )
        st.session_state.report = report
        
    st.success("✅ Analysis complete!")

# Tab 1: Overview
with tab1:
    st.header("📊 Data Overview")
    
    if st.session_state.gdf is not None:
        summary = loader.get_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Features", summary['total_features'])
        
        with col2:
            if st.session_state.validated_gdf is not None:
                valid_count = st.session_state.validated_gdf['is_valid'].sum()
                st.metric("Valid Features", valid_count)
        
        with col3:
            if st.session_state.anomaly_gdf is not None:
                anomaly_count = st.session_state.anomaly_gdf['is_anomaly'].sum()
                st.metric("Anomalies Detected", anomaly_count)
        
        with col4:
            st.metric("CRS", summary['crs'])
        
        st.divider()
        
        # Geometry types
        st.subheader("Geometry Types")
        geom_types_df = pd.DataFrame(
            list(summary['geometry_types'].items()),
            columns=['Type', 'Count']
        )
        st.dataframe(geom_types_df, use_container_width=True)
        
        # Bounds
        st.subheader("Spatial Bounds")
        bounds_df = pd.DataFrame({
            'Min X': [summary['bounds'][0]],
            'Min Y': [summary['bounds'][1]],
            'Max X': [summary['bounds'][2]],
            'Max Y': [summary['bounds'][3]]
        })
        st.dataframe(bounds_df, use_container_width=True)
        
        # Properties
        st.subheader("Feature Properties")
        properties = loader.get_feature_properties()
        if properties:
            st.write(", ".join(properties))
        else:
            st.info("No additional properties found")
    else:
        st.info("👆 Upload a GeoJSON file or select sample data to begin")

# Tab 2: Validation
with tab2:
    st.header("✓ Validation Results")
    
    if st.session_state.validated_gdf is not None:
        validator = GeometryValidator()
        summary = validator.get_validation_summary(st.session_state.validated_gdf)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Valid Features", summary['valid_features'], 
                     delta=f"{summary['validation_rate']}")
        
        with col2:
            st.metric("Invalid Features", summary['invalid_features'])
        
        with col3:
            st.metric("Total Errors", summary['total_errors'])
        
        st.divider()
        
        # Error breakdown
        if summary['error_types']:
            st.subheader("Error Type Breakdown")
            error_df = pd.DataFrame(
                list(summary['error_types'].items()),
                columns=['Error Type', 'Count']
            ).sort_values('Count', ascending=False)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.dataframe(error_df, use_container_width=True)
            
            with col2:
                if st.session_state.errors_df is not None and not st.session_state.errors_df.empty:
                    viz = MapVisualizer()
                    fig = viz.create_error_breakdown_chart(st.session_state.errors_df)
                    st.plotly_chart(fig, use_container_width=True)
        
        # Detailed errors
        if st.session_state.errors_df is not None and not st.session_state.errors_df.empty:
            st.subheader("Detailed Errors")
            st.dataframe(st.session_state.errors_df, use_container_width=True)
    else:
        st.info("Run analysis to see validation results")

# Tab 3: Anomaly Detection
with tab3:
    st.header("🤖 Anomaly Detection Results")
    
    if st.session_state.anomaly_gdf is not None:
        detector = AnomalyDetector()
        summary = detector.get_anomaly_summary(st.session_state.anomaly_gdf)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Normal Features", summary['normal_features'])
        
        with col2:
            st.metric("Anomalies", summary['anomalies_detected'],
                     delta=f"{summary['anomaly_rate']}")
        
        with col3:
            st.metric("Avg Anomaly Score", f"{summary['avg_anomaly_score']:.4f}")
        
        st.divider()
        
        # Feature distributions
        if st.session_state.features is not None:
            st.subheader("Feature Distributions")
            viz = MapVisualizer()
            fig = viz.create_feature_distribution_chart(st.session_state.features)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top anomalies
        st.subheader("Top Anomalies")
        anomalies = st.session_state.anomaly_gdf[st.session_state.anomaly_gdf['is_anomaly']]
        if len(anomalies) > 0:
            top_anomalies = anomalies.nsmallest(10, 'anomaly_score')
            display_cols = ['anomaly_score', 'anomaly_score_normalized']
            if 'is_valid' in top_anomalies.columns:
                display_cols.append('is_valid')
            st.dataframe(
                top_anomalies[display_cols].reset_index(),
                use_container_width=True
            )
        else:
            st.success("No anomalies detected!")
    else:
        st.info("Run analysis to see anomaly detection results")

# Tab 4: Visualization
with tab4:
    st.header("🗺️ Interactive Map")
    
    if st.session_state.gdf is not None:
        viz = MapVisualizer()
        
        # Map type selector
        map_type = st.selectbox(
            "Select map view",
            ["Validation Results", "Anomaly Detection", "Combined Analysis"]
        )
        
        # Create appropriate map
        if map_type == "Validation Results" and st.session_state.validated_gdf is not None:
            fig = viz.create_validation_map(st.session_state.validated_gdf)
            st.plotly_chart(fig, use_container_width=True)
        
        elif map_type == "Anomaly Detection" and st.session_state.anomaly_gdf is not None:
            fig = viz.create_anomaly_map(st.session_state.anomaly_gdf)
            st.plotly_chart(fig, use_container_width=True)
        
        elif map_type == "Combined Analysis":
            if st.session_state.validated_gdf is not None and st.session_state.anomaly_gdf is not None:
                # Merge validation and anomaly results
                combined_gdf = st.session_state.validated_gdf.copy()
                combined_gdf['is_anomaly'] = st.session_state.anomaly_gdf['is_anomaly']
                combined_gdf['anomaly_score'] = st.session_state.anomaly_gdf['anomaly_score']
                
                fig = viz.create_combined_map(combined_gdf)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Run analysis to see combined results")
        else:
            st.info("Run analysis to see map visualization")
    else:
        st.info("Upload data to see visualization")

# Tab 5: Report
with tab5:
    st.header("📄 Quality Report")
    
    if st.session_state.report:
        reporter = ErrorReporter()
        reporter.report_data = st.session_state.report
        
        # Display summary
        st.text(reporter.get_summary_text())
        
        st.divider()
        
        # Recommendations
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(st.session_state.report['recommendations'], 1):
            st.info(f"{i}. {rec}")
        
        # Export options
        st.divider()
        st.subheader("📥 Export Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export as JSON", use_container_width=True):
                import json
                json_str = json.dumps(st.session_state.report, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="quality_report.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Export as CSV", use_container_width=True):
                if st.session_state.errors_df is not None:
                    csv = st.session_state.errors_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="validation_errors.csv",
                        mime="text/csv"
                    )
    else:
        st.info("Run analysis to generate report")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>🗺️ AI Map Quality Checker | Built with Streamlit & Scikit-learn</p>
    <p>Upload GeoJSON data to validate geometry and detect anomalies using AI</p>
</div>
""", unsafe_allow_html=True)
