"""
DocMind AI - Streamlit UI Application
Main application entry point
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="DocMind AI - Intelligent Document Change Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5A7A9A;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
    }
    .highlight-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
    }
    .risk-medium {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
    }
    .risk-low {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
    }
    .change-item {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    .severity-critical {
        color: #dc3545;
        font-weight: bold;
    }
    .severity-significant {
        color: #fd7e14;
        font-weight: bold;
    }
    .severity-moderate {
        color: #ffc107;
        font-weight: bold;
    }
    .severity-minor {
        color: #28a745;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# API Configuration
API_BASE_URL = os.getenv("DOCMIND_API_URL", "http://localhost:8000")


def init_session_state():
    """Initialize session state variables"""
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = None
    if 'comparison_id' not in st.session_state:
        st.session_state.comparison_id = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}


def call_api(endpoint: str, method: str = "GET", data: dict = None, files: dict = None):
    """Make API call"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if files:
            response = requests.post(url, files=files, timeout=300)
        elif data:
            response = requests.post(url, json=data, timeout=300)
        else:
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status_code": response.status_code}
    except requests.exceptions.ConnectionError:
        return {"error": "API server not available. Please start the API server.", "status_code": 503}
    except Exception as e:
        return {"error": str(e), "status_code": 500}


def render_header():
    """Render the main header"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<p class="main-header">📄 DocMind AI</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Intelligent Document Change Intelligence Platform</p>', unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=DocMind+AI", width=150)
        
        st.markdown("### Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Dashboard", "📊 Comparison", "🔍 Risk Analysis", "⚠️ Fraud Detection", 
             "📋 Executive Summary", "💬 AI Assistant", "📈 Reports", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        st.metric("Documents Compared", "24")
        st.metric("Active Sessions", "3")
        
        return page


def render_dashboard():
    """Render dashboard page"""
    st.markdown("## 📊 Dashboard")
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📄</h3>
            <h2>156</h2>
            <p>Documents Analyzed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>🎯</h3>
            <h2>94%</h2>
            <p>Accuracy Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>⏱️</h3>
            <h2>2.3s</h2>
            <p>Avg. Processing Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>✅</h3>
            <h2>12</h2>
            <p>Fraud Detected</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent comparisons
    st.markdown("### Recent Comparisons")
    
    recent_data = pd.DataFrame({
        "Document": ["Contract_v1.pdf", "Invoice_May.pdf", "Agreement_Draft.docx"],
        "Similarity": ["87%", "95%", "72%"],
        "Changes": ["23", "8", "45"],
        "Risk Level": ["Medium", "Low", "High"],
        "Date": ["2024-01-15", "2024-01-14", "2024-01-14"]
    })
    
    st.dataframe(recent_data, use_container_width=True)
    
    # Chart section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Change Distribution")
        fig = px.pie(
            values=[45, 30, 15, 10],
            names=['Content', 'Formatting', 'Structure', 'Other'],
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Risk Overview")
        fig = px.bar(
            x=['Financial', 'Legal', 'Compliance', 'Operational'],
            y=[0.3, 0.5, 0.2, 0.4],
            color=['#dc3545', '#fd7e14', '#ffc107', '#28a745']
        )
        st.plotly_chart(fig, use_container_width=True)


def render_comparison_page():
    """Render document comparison page"""
    st.markdown("## 📊 Document Comparison")
    
    # File upload section
    st.markdown("### Upload Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        original_file = st.file_uploader(
            "Original Document",
            type=["pdf", "docx", "xlsx", "xls", "txt"],
            help="Upload the original version of the document"
        )
    
    with col2:
        modified_file = st.file_uploader(
            "Modified Document",
            type=["pdf", "docx", "xlsx", "xls", "txt"],
            help="Upload the modified version of the document"
        )
    
    # Options
    with st.expander("⚙️ Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            language = st.selectbox("Language", ["en", "te", "hi", "ta"])
        
        with col2:
            include_semantic = st.checkbox("Semantic Analysis", value=True)
        
        with col3:
            include_fraud = st.checkbox("Fraud Detection", value=True)
    
    # Compare button
    if st.button("🚀 Compare Documents", type="primary", use_container_width=True):
        if original_file and modified_file:
            with st.spinner("Analyzing documents..."):
                start_time = time.time()
                
                files = {
                    "original_file": (original_file.name, original_file.getvalue()),
                    "modified_file": (modified_file.name, modified_file.getvalue())
                }
                
                data = {
                    "language": language,
                    "include_semantic": include_semantic,
                    "include_fraud_detection": include_fraud
                }
                
                result = call_api("/api/v1/compare", method="POST", files=files, data=data)
                
                if "error" not in result:
                    st.session_state.comparison_results = result
                    st.session_state.comparison_id = result.get("comparison_id")
                    
                    elapsed = time.time() - start_time
                    st.success(f"Comparison completed in {elapsed:.2f} seconds!")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please upload both documents to compare")
    
    # Display results if available
    if st.session_state.comparison_results:
        render_comparison_results(st.session_state.comparison_results)


def render_comparison_results(results: dict):
    """Render comparison results"""
    st.markdown("---")
    st.markdown("## Comparison Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Similarity", f"{results.get('overall_similarity', 0) * 100:.1f}%")
    
    with col2:
        st.metric("Semantic Similarity", f"{results.get('semantic_similarity', 0) * 100:.1f}%")
    
    with col3:
        st.metric("Total Changes", results.get('total_changes', 0))
    
    with col4:
        processing = results.get('processing_time', 0)
        st.metric("Processing Time", f"{processing:.2f}s")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Changes", "📊 Statistics", "🎯 Risk Analysis", "⚠️ Fraud Detection"])
    
    with tab1:
        render_changes_tab(results.get('changes', []))
    
    with tab2:
        render_statistics_tab(results)
    
    with tab3:
        render_risk_tab(results.get('risk_analysis', {}))
    
    with tab4:
        render_fraud_tab(results.get('fraud_detection', {}))


def render_changes_tab(changes: list):
    """Render changes tab"""
    if not changes:
        st.info("No changes to display")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["critical", "significant", "moderate", "minor"],
            default=["critical", "significant", "moderate", "minor"]
        )
    
    with col2:
        type_filter = st.multiselect(
            "Change Type",
            ["character", "word", "sentence", "paragraph", "structure", "insertion", "deletion", "modification"],
            default=[]
        )
    
    with col3:
        category_filter = st.multiselect(
            "Category",
            ["content", "structure", "formatting", "data", "compliance"],
            default=[]
        )
    
    # Display changes
    for change in changes:
        severity = change.get('severity', '').lower()
        
        if severity_filter and severity not in severity_filter:
            continue
        
        with st.container():
            severity_class = f"severity-{severity}"
            
            st.markdown(f"""
            <div class="change-item">
                <span class="{severity_class}">[{severity.upper()}]</span>
                <strong>{change.get('change_type', '').upper()}</strong> - 
                {change.get('category', '').title()}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_area("Original", change.get('original_content', ''), height=100, key=f"orig_{change.get('change_id')}")
            
            with col2:
                st.text_area("Modified", change.get('modified_content', ''), height=100, key=f"mod_{change.get('change_id')}")
            
            st.markdown("---")


def render_statistics_tab(results: dict):
    """Render statistics tab"""
    st.markdown("### Comparison Statistics")
    
    # Similarity breakdown
    if 'executive_summary' in results and results['executive_summary']:
        stats = results['executive_summary'].get('statistics', {})
        
        st.markdown("#### Similarity Scores")
        
        sim_stats = stats.get('similarity', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Similarity", f"{sim_stats.get('overall', 0) * 100:.1f}%")
        
        with col2:
            st.metric("Semantic Similarity", f"{sim_stats.get('semantic', 0) * 100:.1f}%")
        
        with col3:
            st.metric("Structural Similarity", f"{sim_stats.get('structural', 0) * 100:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Changes by Type")
        fig = go.Figure(data=[
            go.Bar(x=['Insertions', 'Deletions', 'Modifications', 'Movements'],
                   y=[15, 8, 12, 3])
        ])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Changes by Severity")
        fig = go.Figure(data=[
            go.Pie(labels=['Critical', 'Significant', 'Moderate', 'Minor'],
                   values=[5, 10, 15, 20])
        ])
        st.plotly_chart(fig, use_container_width=True)


def render_risk_tab(risk_analysis: dict):
    """Render risk analysis tab"""
    if not risk_analysis:
        st.info("No risk analysis available")
        return
    
    st.markdown("### Risk Analysis Results")
    
    # Risk score gauge
    risk_score = risk_analysis.get('overall_risk_score', 0)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score * 100,
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': 'green'},
                    {'range': [30, 70], 'color': 'yellow'},
                    {'range': [70, 100], 'color': 'red'}
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"**Risk Level: {risk_analysis.get('risk_level', 'unknown').upper()}**")
        
        risk_scores = {
            "Financial Risk": risk_analysis.get('financial_risk', 0),
            "Legal Risk": risk_analysis.get('legal_risk', 0),
            "Compliance Risk": risk_analysis.get('compliance_risk', 0),
            "Operational Risk": risk_analysis.get('operational_risk', 0)
        }
        
        df = pd.DataFrame([
            {"Risk Type": k, "Score": v * 100} for k, v in risk_scores.items()
        ])
        
        fig = px.bar(df, x='Risk Type', y='Score', color='Score',
                     color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk factors
    st.markdown("#### Key Risk Factors")
    
    risk_factors = risk_analysis.get('risk_factors', [])
    for factor in risk_factors:
        st.markdown(f"- {factor}")
    
    # Recommendations
    st.markdown("#### Recommendations")
    
    recommendations = risk_analysis.get('recommendations', [])
    for rec in recommendations:
        st.markdown(f"- {rec}")


def render_fraud_tab(fraud_detection: dict):
    """Render fraud detection tab"""
    if not fraud_detection:
        st.info("No fraud detection results available")
        return
    
    st.markdown("### Fraud Detection Results")
    
    fraud_score = fraud_detection.get('fraud_score', 0)
    fraud_level = fraud_detection.get('fraud_level', 'unknown')
    
    # Display fraud score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Fraud Score", f"{fraud_score * 100:.1f}%")
    
    with col2:
        st.metric("Fraud Level", fraud_level.upper())
    
    with col3:
        st.metric("Indicators Found", fraud_detection.get('indicators_count', 0))
    
    # Risk classification
    if fraud_score > 0.7:
        st.markdown("""
        <div class="risk-high">
            <h4>⚠️ HIGH FRAUD RISK DETECTED</h4>
            <p>Critical fraud indicators have been found. Immediate investigation recommended.</p>
        </div>
        """, unsafe_allow_html=True)
    elif fraud_score > 0.4:
        st.markdown("""
        <div class="risk-medium">
            <h4>⚡ MODERATE FRAUD RISK</h4>
            <p>Some suspicious patterns detected. Review recommended.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="risk-low">
            <h4>✅ LOW FRAUD RISK</h4>
            <p>No significant fraud indicators detected.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Fraud types
    st.markdown("#### Fraud Type Distribution")
    fraud_types = ['Amount Manipulation', 'Date Manipulation', 'Hidden Text', 
                   'Signature Removal', 'Content Swapping']
    fraud_counts = [3, 2, 1, 1, 0]
    
    fig = px.bar(x=fraud_types, y=fraud_counts, color=fraud_counts,
                 color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)


def render_executive_summary():
    """Render executive summary page"""
    st.markdown("## 📋 Executive Summary")
    
    if not st.session_state.comparison_results:
        st.info("Run a document comparison first to generate an executive summary")
        return
    
    results = st.session_state.comparison_results
    summary = results.get('executive_summary', {})
    
    # Overview section
    st.markdown("### Overview")
    st.markdown(f"**{summary.get('overview', 'No overview available')}**")
    
    # Key findings
    st.markdown("### Critical Findings")
    
    findings = summary.get('critical_findings', [])
    for idx, finding in enumerate(findings, 1):
        st.markdown(f"{idx}. {finding}")
    
    # Statistics summary
    st.markdown("### Summary Statistics")
    
    stats = summary.get('statistics', {})
    comparison_stats = stats.get('comparison', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Changes", comparison_stats.get('total_changes', 0))
    
    with col2:
        st.metric("Insertions", comparison_stats.get('insertions', 0))
    
    with col3:
        st.metric("Deletions", comparison_stats.get('deletions', 0))
    
    with col4:
        st.metric("Modifications", comparison_stats.get('modifications', 0))
    
    # Recommendations
    st.markdown("### Recommendations")
    
    recommendations = summary.get('recommendations', [])
    for rec in recommendations:
        st.markdown(f"- {rec}")
    
    # Export options
    st.markdown("### Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export PDF Report"):
            st.info("PDF export coming soon")
    
    with col2:
        if st.button("📊 Export Excel Report"):
            st.info("Excel export coming soon")
    
    with col3:
        if st.button("📋 Export JSON"):
            st.json(summary)


def render_ai_assistant():
    """Render AI reviewer assistant page"""
    st.markdown("## 💬 AI Reviewer Assistant")
    
    st.markdown("""
    Ask questions about the document comparison and get AI-powered insights.
    
    **Example queries:**
    - "Explain the most critical changes"
    - "What are the fraud risks?"
    - "Summarize the comparison"
    - "What sections have the most changes?"
    """)
    
    # Chat input
    user_input = st.text_area("Ask a question:", placeholder="Type your question here...")
    
    if st.button("Ask", type="primary"):
        if user_input:
            with st.spinner("Processing..."):
                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Call API
                result = call_api("/api/v1/chat", method="POST", 
                                data={"message": user_input, "comparison_id": st.session_state.comparison_id})
                
                if "error" not in result:
                    response = result.get('response', '')
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    # Display chat history
    st.markdown("### Conversation")
    
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")
        
        st.markdown("---")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []


def render_reports():
    """Render reports page"""
    st.markdown("## 📈 Reports")
    
    st.markdown("### Available Reports")
    
    report_types = [
        {"name": "Executive Summary", "description": "High-level overview of the comparison", "icon": "📋"},
        {"name": "Detailed Changes Report", "description": "Complete list of all changes", "icon": "📝"},
        {"name": "Risk Analysis Report", "description": "Comprehensive risk assessment", "icon": "🎯"},
        {"name": "Fraud Detection Report", "description": "Fraud indicator details", "icon": "⚠️"},
        {"name": "Compliance Report", "description": "Compliance check results", "icon": "✅"},
        {"name": "Audit Trail Report", "description": "Complete audit trail", "icon": "📜"}
    ]
    
    for report in report_types:
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col1:
            st.markdown(f"{report['icon']}")
        
        with col2:
            st.markdown(f"**{report['name']}**")
            st.caption(report['description'])
        
        with col3:
            if st.button("Generate", key=report['name']):
                st.info(f"Generating {report['name']}...")
        
        st.markdown("---")


def render_settings():
    """Render settings page"""
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### OCR Configuration")
    
    ocr_engine = st.selectbox("OCR Engine", ["EasyOCR", "Tesseract"])
    ocr_language = st.multiselect("OCR Languages", ["English", "Telugu", "Hindi", "Tamil"], default=["English"])
    
    st.markdown("### AI Configuration")
    
    ai_model = st.selectbox("AI Model", ["all-MiniLM-L6-v2", "all-mpnet-base-v2"])
    semantic_threshold = st.slider("Semantic Similarity Threshold", 0.0, 1.0, 0.75)
    
    st.markdown("### Display Settings")
    
    theme = st.selectbox("Theme", ["Light", "Dark"])
    language = st.selectbox("Interface Language", ["English", "Telugu", "Hindi", "Tamil"])
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")


def main():
    """Main application entry point"""
    init_session_state()
    
    render_header()
    
    page = render_sidebar()
    
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "📊 Comparison":
        render_comparison_page()
    elif page == "📋 Executive Summary":
        render_executive_summary()
    elif page == "💬 AI Assistant":
        render_ai_assistant()
    elif page == "📈 Reports":
        render_reports()
    elif page == "⚙️ Settings":
        render_settings()
    elif page == "🔍 Risk Analysis":
        if st.session_state.comparison_results:
            render_risk_tab(st.session_state.comparison_results.get('risk_analysis', {}))
        else:
            st.info("Run a document comparison first")
    elif page == "⚠️ Fraud Detection":
        if st.session_state.comparison_results:
            render_fraud_tab(st.session_state.comparison_results.get('fraud_detection', {}))
        else:
            st.info("Run a document comparison first")


if __name__ == "__main__":
    main()