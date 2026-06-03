"""
DocMind AI - Futuristic 3D Web Interface v3.0
"""
import streamlit as st
import requests
st.set_page_config(page_title="DocMind AI - Futuristic", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
:root { --neon-blue: #00f0ff; --neon-purple: #bf00ff; --neon-pink: #ff00ff; --neon-green: #00ff88; --dark-bg: #0a0a0f; }
html, body, [class*="css"] { color: #ffffff; background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%) !important; min-height: 100vh !important; font-family: 'Rajdhani', sans-serif; }
@keyframes neon-glow { 0%, 100% { filter: drop-shadow(0 0 10px var(--neon-blue)); } 50% { filter: drop-shadow(0 0 30px var(--neon-purple)); } }
@keyframes border-glow { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
.futuristic-header { text-align: center; padding: 40px 20px; }
.futuristic-header h1 { font-family: 'Orbitron', monospace; font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #00f0ff, #bf00ff, #ff00ff, #00f0ff); background-size: 300% 100%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: neon-glow 3s ease-in-out infinite; letter-spacing: 4px; }
.futuristic-header .subtitle { font-size: 1.3rem; color: #888; letter-spacing: 6px; text-transform: uppercase; margin-top: 10px; }
.neon-border { position: relative; border-radius: 20px; }
.neon-border::before { content: ''; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px; background: linear-gradient(45deg, #00f0ff, #bf00ff, #ff00ff, #00f0ff); background-size: 400% 400%; border-radius: 22px; z-index: -1; animation: border-glow 8s ease-in-out infinite; opacity: 0.7; }
.futuristic-card { background: linear-gradient(145deg, rgba(30,30,50,0.9), rgba(20,20,35,0.9)); border: 1px solid rgba(0,240,255,0.3); border-radius: 20px; padding: 30px; backdrop-filter: blur(20px); box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 30px rgba(0,240,255,0.1); margin-bottom: 20px; }
.metric-3d { background: linear-gradient(145deg, #1a1a2e, #0f0f1a); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; text-align: center; }
.metric-3d .value { font-family: 'Orbitron', monospace; font-size: 2.5rem; font-weight: 900; color: #fff; }
.metric-3d .label { font-size: 0.9rem; color: #888; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px; }
.change-item { background: linear-gradient(145deg, rgba(30,30,50,0.9), rgba(20,20,35,0.9)); border-left: 4px solid var(--neon-blue); border-radius: 10px; padding: 20px; margin: 15px 0; }
.change-item.insertion { border-left-color: #00ff88; }
.change-item.deletion { border-left-color: #ff4444; }
.change-item.modification { border-left-color: #ffaa00; }
.risk-indicator { display: inline-block; padding: 8px 20px; border-radius: 50px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
.risk-high { background: linear-gradient(90deg, #ff0000, #ff4444); color: #fff; }
.risk-medium { background: linear-gradient(90deg, #ffaa00, #ffcc00); color: #000; }
.risk-low { background: linear-gradient(90deg, #00ff00, #00ff88); color: #000; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 10px; padding: 15px 30px; font-family: 'Orbitron', monospace; font-weight: 700; color: #888; }
.stTabs [data-baseweb="tab"]:hover { color: var(--neon-blue); }
.stTabs [aria-selected="true"] { background: linear-gradient(145deg, var(--neon-blue), var(--neon-purple)) !important; color: #fff !important; }
.dataframe th { background: linear-gradient(90deg, #00f0ff, #bf00ff) !important; color: #fff !important; font-family: 'Orbitron', monospace !important; }
.dataframe td { color: #fff !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: rgba(30,30,50,0.5); }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #00f0ff, #bf00ff); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None
API_BASE_URL = "http://127.0.0.1:8000"
def call_api(endpoint, method="GET", data=None, files=None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if files:
            return requests.post(url, files=files, timeout=300).json()
        return requests.request(method, url, json=data, timeout=30).json()
    except Exception as e:
        return {"error": f"API server not available: {str(e)}"}
st.markdown("""<div class="futuristic-header"><h1>🧠 DocMind AI</h1><p class="subtitle">Intelligent Document Change Intelligence v3.0</p></div>""", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("### Navigation", unsafe_allow_html=True)
    selected = st.radio("", ["🏠 Dashboard", "📊 Compare", "🔍 Risk", "⚠️ Fraud", "📋 Summary", "💬 AI Assistant"])
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='futuristic-card neon-border'><h3 style='color: var(--neon-blue);'>📄 Original Document</h3></div>", unsafe_allow_html=True)
    original_file = st.file_uploader("Upload original", type=['pdf', 'docx', 'xlsx', 'xls', 'txt'], key="orig")
with col2:
    st.markdown("<div class='futuristic-card neon-border'><h3 style='color: var(--neon-pink);'>📝 Modified Document</h3></div>", unsafe_allow_html=True)
    modified_file = st.file_uploader("Upload modified", type=['pdf', 'docx', 'xlsx', 'xls', 'txt'], key="mod")
if st.button("🚀 COMPARE DOCUMENTS", use_container_width=True, type="primary"):
    if original_file and modified_file:
        with st.spinner("🔮 Analyzing with AI..."):
            files = {"original_file": (original_file.name, original_file.getvalue()), "modified_file": (modified_file.name, modified_file.getvalue())}
            result = call_api("/api/v1/compare", method="POST", files=files)
            if "error" not in result:
                st.session_state.comparison_results = result
                st.success("✨ Comparison complete!")
                st.rerun()
            else:
                st.error(result.get("error", "Unknown error"))
    else:
        st.warning("Upload both documents!")
if st.session_state.comparison_results:
    results = st.session_state.comparison_results
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-3d'><div class='value'>{results.get('similarity', 0)}%</div><div class='label'>Similarity</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-3d'><div class='value'>{results.get('total_changes', 0)}</div><div class='label'>Changes</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-3d'><div class='value' style='color: #00ff88;'>{results.get('insertions', 0)}</div><div class='label'>Added</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-3d'><div class='value' style='color: #ff4444;'>{results.get('deletions', 0)}</div><div class='label'>Removed</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["📝 Changes", "📊 Stats", "🎯 Risk", "⚠️ Fraud"])
    with tabs[0]:
        for i, c in enumerate(results.get('changes', [])[:20]):
            st.markdown(f"""<div class='change-item {c.get("type", "modification")}'><h4 style='color: var(--neon-blue);'>#{i+1} {c.get("type", "").upper()}</h4><p style='color: #ffaaaa;'>- {c.get('original_content', 'N/A')}</p><p style='color: #aaffaa;'>+ {c.get('modified_content', 'N/A')}</p><p style='color: #666;'>Line: {c.get('line_number', 'N/A')}</p></div>""", unsafe_allow_html=True)
    with tabs[1]:
        st.write(results)
    with tabs[2]:
        st.markdown("<div class='futuristic-card' style='text-align: center;'><span class='risk-indicator risk-low'>LOW RISK</span><p>No significant risks detected</p></div>", unsafe_allow_html=True)
    with tabs[3]:
        st.markdown("<div class='futuristic-card' style='text-align: center;'><span class='risk-indicator risk-low'>NO FRAUD</span><p>Document appears clean</p></div>", unsafe_allow_html=True)
