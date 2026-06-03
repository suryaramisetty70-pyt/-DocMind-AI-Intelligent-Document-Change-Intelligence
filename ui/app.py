"""
DocMind AI - PRO UI v3.0
Next-Level Document Intelligence Platform
"""
import streamlit as st
import requests

st.set_page_config(page_title="DocMind AI PRO", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
:root { --neon-blue: #00f0ff; --neon-purple: #bf00ff; --neon-pink: #ff00ff; --neon-green: #00ff88; }
html, body { color: #fff; background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%) !important; font-family: 'Rajdhani', sans-serif; }
@keyframes neon { 0%, 100% { filter: drop-shadow(0 0 15px var(--neon-blue)); } 50% { filter: drop-shadow(0 0 40px var(--neon-purple)); } }
.futuristic-header h1 { font-family: 'Orbitron', monospace; font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #00f0ff, #bf00ff, #ff00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: neon 3s ease-in-out infinite; }
.futuristic-card { background: rgba(30,30,50,0.95); border: 1px solid rgba(0,240,255,0.3); border-radius: 20px; padding: 25px; }
.neon-border { box-shadow: 0 0 30px rgba(0,240,255,0.2); }
.metric-card { background: linear-gradient(145deg, #1a1a2e, #0f0f1a); border-radius: 15px; padding: 20px; text-align: center; }
.metric-card .value { font-family: 'Orbitron', monospace; font-size: 2.5rem; color: #fff; }
.metric-card .label { color: #888; text-transform: uppercase; font-size: 0.85rem; }
.change-item { background: rgba(30,30,50,0.9); border-left: 4px solid #00f0ff; border-radius: 10px; padding: 20px; margin: 12px 0; }
.change-item.high-risk { border-left-color: #ff4444; }
.risk-badge { padding: 5px 15px; border-radius: 50px; font-weight: bold; text-transform: uppercase; }
.risk-high { background: #ff4444; color: #fff; }
.risk-medium { background: #ffaa00; color: #000; }
.risk-low { background: #00ff88; color: #000; }
.recommendation { background: rgba(30,30,50,0.9); border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 4px solid; }
.recommendation.urgent { border-left-color: #ff0000; }
.recommendation.high { border-left-color: #ffaa00; }
.recommendation.info { border-left-color: #888; }
.fraud-alert { background: rgba(60,30,30,0.95); border: 1px solid #ff4444; border-radius: 10px; padding: 15px; margin: 10px 0; }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, #00f0ff, #bf00ff) !important; color: #fff !important; }
</style>""", unsafe_allow_html=True)

if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = None

API_BASE_URL = "http://127.0.0.1:8002"

def call_api(endpoint, files=None):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        return requests.post(url, files=files, timeout=300).json()
    except Exception as e:
        return {"error": f"Server error: {str(e)}"}

st.markdown("<div class='futuristic-header' style='text-align:center;padding:30px;'><h1>🧠 DocMind AI PRO</h1><p style='color:#888;'>v3.0 - Next Level Intelligence</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎛️ Navigation")
    page = st.radio("", ["🚀 Dashboard", "🎯 Risk", "⚠️ Fraud", "📋 Recs"])

col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='futuristic-card neon-border'><h3 style='color:#00f0ff;'>📄 Original</h3></div>", unsafe_allow_html=True)
    original_file = st.file_uploader("Upload", type=["txt"], key="orig")
with col2:
    st.markdown("<div class='futuristic-card neon-border'><h3 style='color:#ff00ff;'>📝 Modified</h3></div>", unsafe_allow_html=True)
    modified_file = st.file_uploader("Upload", type=["txt"], key="mod")

if st.button("🚀 COMPARE", use_container_width=True):
    if original_file and modified_file:
        with st.spinner("🔮 AI analyzing..."):
            files = {"original_file": (original_file.name, original_file.getvalue()), "modified_file": (modified_file.name, modified_file.getvalue())}
            result = call_api("/api/v1/compare", files=files)
            if "error" not in result:
                st.session_state.comparison_results = result
                st.success("✨ Done!")
                st.rerun()
            else:
                st.error(result["error"])
    else:
        st.warning("Upload both files!")

if st.session_state.comparison_results:
    r = st.session_state.comparison_results
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='value'>{r.get('similarity', 0)}%</div><div class='label'>Similarity</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='value'>{r.get('total_changes', 0)}</div><div class='label'>Changes</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='value' style='color:#00ff88;'>{r.get('insertions', 0)}</div><div class='label'>Added</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><div class='value' style='color:#ff4444;'>{r.get('deletions', 0)}</div><div class='label'>Removed</div></div>", unsafe_allow_html=True)
    
    risk = r.get("risk_analysis", {})
    st.markdown(f"<div class='futuristic-card' style='text-align:center;'><h3>Risk: <span class='risk-badge risk-{risk.get('level', 'low').lower()}'>{risk.get('emoji', '')} {risk.get('level', 'LOW')}</span></h3><h2 style='font-size:3rem;color:#00f0ff;'>{risk.get('score', 0)}%</h2></div>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📝 Changes", "🎯 Risk", "⚠️ Fraud", "📋 Recs", "📊 Stats"])
    with tabs[0]:
        for i, c in enumerate(r.get("changes", [])[:15]):
            high_class = " high-risk" if c.get("severity") == "HIGH" else ""
            st.markdown(f"<div class='change-item{high_class}'><h4>#{i+1} {c.get('type','').upper()}</h4><p style='color:#ffaaaa;'>- {c.get('original_content','')}</p><p style='color:#aaffaa;'>+ {c.get('modified_content','')}</p><p style='color:#888;'>💬 {c.get('ai_explanation','')}</p></div>", unsafe_allow_html=True)
    with tabs[1]:
        for f in risk.get("factors", []):
            st.markdown(f"<p>• {f}</p>", unsafe_allow_html=True)
        st.markdown(f"<p>Total Risk Score: {risk.get('score', 0)}%</p>", unsafe_allow_html=True)
    with tabs[2]:
        fraud = r.get("fraud_detection", {})
        if fraud.get("total_alerts", 0) > 0:
            for a in fraud.get("alerts", []):
                st.markdown(f"<div class='fraud-alert'><h4>⚠️ {a.get('message','')}</h4><p>Type: {a.get('type','')} | Severity: {a.get('severity','')}</p></div>", unsafe_allow_html=True)
        else:
            st.success("✅ No fraud detected!")
    with tabs[3]:
        for rec in r.get("recommendations", []):
            prio_class = rec.get("priority", "info").lower()
            st.markdown(f"<div class='recommendation {prio_class}'><h4>[{rec.get('priority', '')}] {rec.get('title', '')}</h4><p>{rec.get('description', '')}</p><p>➡️ {rec.get('action', '')}</p></div>", unsafe_allow_html=True)
    with tabs[4]:
        st.json(r)
