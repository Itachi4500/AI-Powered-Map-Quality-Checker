"""
AI Map Quality Checker - Enhanced Streamlit App
Optimized for performance, clarity, and hackathon impact
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.loader import GeoDataLoader
from src.validator import GeometryValidator
from src.feature_engineering import FeatureEngineer
from src.anomaly_detector import AnomalyDetector
from src.reporter import ErrorReporter
from src.visualizer import MapVisualizer
from config.settings import VALIDATION_RULES, ANOMALY_DETECTION_PARAMS

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Map Quality Checker",
    page_icon="🗺️",
    layout="wide"
)

# =====================================================
# SESSION STATE INIT
# =====================================================

for key in [
    "df", "validated_df", "anomaly_df",
    "features", "errors_df", "report",
    "detector"
]:
    if key not in st.session_state:
        st.session_state[key] = None

# =====================================================
# HEADER
# =====================================================

st.title("🗺️ AI Map Quality Checker")
st.caption("Rule-based validation + ML anomaly detection for geospatial QA")

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.header("⚙ Configuration")

    uploaded_file = st.file_uploader("Upload GeoJSON", type=["geojson", "json"])

    st.subheader("Validation Rules")
    min_area = st.number_input("Min Area", value=float(VALIDATION_RULES["min_area"]))
    max_area = st.number_input("Max Area", value=float(VALIDATION_RULES["max_area"]))
    check_self_intersection = st.checkbox("Check Self-Intersection", True)

    st.subheader("ML Settings")
    contamination = st.slider("Anomaly Rate", 0.01, 0.5,
                              ANOMALY_DETECTION_PARAMS["contamination"], 0.01)
    n_estimators = st.slider("Estimators", 50, 200,
                             ANOMALY_DETECTION_PARAMS["n_estimators"], 10)

    run_analysis = st.button("🚀 Run Analysis")

# =====================================================
# DATA LOADING (CACHED)
# =====================================================

@st.cache_data
def load_data(uploaded_file):
    loader = GeoDataLoader()
    success, df, message = loader.load_from_file(uploaded_file)
    return success, df, message


if uploaded_file:
    success, df, message = load_data(uploaded_file)
    if success:
        st.session_state.df = df
        st.success(message)
    else:
        st.error(message)

# =====================================================
# RUN ANALYSIS
# =====================================================

if run_analysis and st.session_state.df is not None:

    with st.spinner("Running validation + ML analysis..."):

        # 1️⃣ Validation
        rules = VALIDATION_RULES.copy()
        rules.update({
            "min_area": min_area,
            "max_area": max_area,
            "self_intersection_check": check_self_intersection
        })

        validator = GeometryValidator(rules)
        validated_df, errors_df = validator.validate_geometry(st.session_state.df)

        st.session_state.validated_df = validated_df
        st.session_state.errors_df = errors_df

        validation_summary = validator.get_validation_summary(validated_df)

        # 2️⃣ Feature Engineering
        engineer = FeatureEngineer()
        features = engineer.extract_features(st.session_state.df)
        st.session_state.features = features

        # 3️⃣ Anomaly Detection
        detector = AnomalyDetector({
            "contamination": contamination,
            "n_estimators": n_estimators,
            "random_state": 42
        })

        success, msg = detector.train(features)

        if success:
            anomaly_df = detector.detect_anomalies(st.session_state.df, features)
            st.session_state.anomaly_df = anomaly_df
            st.session_state.detector = detector
            anomaly_summary = detector.get_anomaly_summary(anomaly_df)
        else:
            st.error(msg)
            anomaly_summary = None

        # 4️⃣ Report
        reporter = ErrorReporter()
        report = reporter.generate_report(
            validated_df,
            errors_df,
            st.session_state.anomaly_df,
            validation_summary,
            anomaly_summary
        )

        st.session_state.report = report

    st.success("✅ Analysis Completed")

# =====================================================
# DASHBOARD TABS
# =====================================================

tabs = st.tabs([
    "📊 Overview",
    "✓ Validation",
    "🤖 Anomaly Detection",
    "🗺 Visualization",
    "📄 Report"
])

# =====================================================
# TAB 1 — OVERVIEW
# =====================================================

with tabs[0]:

    if st.session_state.df is not None:

        total = len(st.session_state.df)
        valid = st.session_state.validated_df["is_valid"].sum() \
            if st.session_state.validated_df is not None else 0

        anomalies = st.session_state.anomaly_df["is_anomaly"].sum() \
            if st.session_state.anomaly_df is not None else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Features", total)
        col2.metric("Valid Features", valid)
        col3.metric("Anomalies", anomalies)

    else:
        st.info("Upload a dataset to begin.")

# =====================================================
# TAB 2 — VALIDATION
# =====================================================

with tabs[1]:

    if st.session_state.validated_df is not None:

        st.dataframe(st.session_state.errors_df)

        viz = MapVisualizer()
        fig = viz.create_validation_map(st.session_state.validated_df)
        st.plotly_chart(fig, use_container_width=True, key="validation_map_tab2")

    else:
        st.info("Run analysis first.")

# =====================================================
# TAB 3 — ANOMALY DETECTION
# =====================================================

with tabs[2]:

    if st.session_state.anomaly_df is not None:

        st.subheader("Feature Importance")

        detector = st.session_state.detector

        if detector and detector.model:
            importance = detector.get_feature_importance()

            if importance:
                st.bar_chart(pd.Series(importance).sort_values(ascending=False))

        viz = MapVisualizer()
        fig = viz.create_anomaly_map(st.session_state.anomaly_df)
        st.plotly_chart(fig, use_container_width=True, key="anomaly_map_tab3")

    else:
        st.info("Run analysis first.")

# =====================================================
# TAB 4 — VISUALIZATION
# =====================================================

with tabs[3]:

    if st.session_state.validated_df is not None:

        viz = MapVisualizer()

        map_option = st.selectbox(
            "Map View",
            ["Validation", "Anomaly", "Severity Heatmap"]
        )

        if map_option == "Validation":
            fig = viz.create_validation_map(st.session_state.validated_df)
        elif map_option == "Anomaly":
            fig = viz.create_anomaly_map(st.session_state.anomaly_df)
        else:
            fig = viz.create_severity_map(st.session_state.validated_df)

        st.plotly_chart(fig, use_container_width=True, key="visualization_map_tab4")

    else:
        st.info("Run analysis first.")

# =====================================================
# TAB 5 — REPORT
# =====================================================

with tabs[4]:

    if st.session_state.report:

        reporter = ErrorReporter()
        reporter.report_data = st.session_state.report

        st.text(reporter.get_summary_text())

        st.subheader("Recommendations")
        for rec in st.session_state.report["recommendations"]:
            st.info(rec)

        json_str = json.dumps(st.session_state.report, indent=2)
        st.download_button(
            "Download JSON Report",
            data=json_str,
            file_name="quality_report.json",
            mime="application/json"
        )

    else:
        st.info("Run analysis to generate report.")
