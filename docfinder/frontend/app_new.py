"""DocFinder Frontend - Professional Redesign."""
import os
import re
import streamlit as st
import requests
import json
from datetime import datetime
import io

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="DocFinder - Compare Documents Instantly",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --primary: #0f172a;
        --secondary: #1e293b;
        --accent: #3b82f6;
        --accent-light: #60a5fa;
        --highlight: #f43f5e;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --border: #e2e8f0;
        --border-light: #f1f5f9;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main App Background */
    .stApp {
        background: var(--bg-secondary);
    }
    
    /* Header Section */
    .hero-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        pointer-events: none;
    }
    
    .hero-header h1 {
        font-size: 3rem;
        font-weight: 800;
        color: white;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    
    .hero-header p {
        font-size: 1.25rem;
        color: rgba(255,255,255,0.7);
        margin: 0;
        font-weight: 400;
    }
    
    /* Card Styles */
    .card {
        background: var(--bg-primary);
        border-radius: 16px;
        border: 1px solid var(--border);
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-light);
    }
    
    .card-icon {
        width: 56px;
        height: 56px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.75rem;
    }
    
    .icon-primary { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
    .icon-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .icon-warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .icon-error { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
    .icon-purple { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    
    .card-subtitle {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0.25rem 0 0 0;
    }
    
    /* Stat Cards */
    .stat-card {
        background: var(--bg-primary);
        border-radius: 14px;
        border: 1px solid var(--border);
        padding: 1.5rem;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1;
    }
    
    .stat-value.success { color: var(--success); }
    .stat-value.warning { color: var(--warning); }
    .stat-value.error { color: var(--error); }
    .stat-value.accent { color: var(--accent); }
    
    .stat-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 0.75rem;
        font-weight: 500;
    }
    
    /* Comparison Type Cards */
    .type-card {
        background: var(--bg-primary);
        border-radius: 16px;
        border: 2px solid var(--border);
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .type-card:hover {
        border-color: var(--accent);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
        transform: translateY(-4px);
    }
    
    .type-card.selected {
        border-color: var(--accent);
        background: linear-gradient(135deg, rgba(59,130,246,0.05) 0%, rgba(59,130,246,0.02) 100%);
    }
    
    .type-card-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .type-card-title {
        font-size: 1.125rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
    }
    
    .type-card-desc {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0;
    }
    
    /* Diff Display */
    .diff-container {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
    }
    
    .diff-line {
        padding: 0.5rem 1rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    
    .diff-line-added {
        background: linear-gradient(90deg, rgba(16,185,129,0.15) 0%, rgba(16,185,129,0.05) 100%);
        border-left: 4px solid var(--success);
    }
    
    .diff-line-removed {
        background: linear-gradient(90deg, rgba(239,68,68,0.15) 0%, rgba(239,68,68,0.05) 100%);
        border-left: 4px solid var(--error);
    }
    
    .diff-line-unchanged {
        background: var(--bg-tertiary);
        border-left: 4px solid var(--border);
        color: var(--text-secondary);
    }
    
    .diff-marker {
        font-weight: 700;
        width: 16px;
        flex-shrink: 0;
    }
    
    .diff-added .diff-marker { color: var(--success); }
    .diff-removed .diff-marker { color: var(--error); }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
        font-size: 1rem !important;
    }
    
    /* Form Elements */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        padding: 0.875rem 1rem !important;
        font-size: 1rem !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-tertiary);
        padding: 6px;
        border-radius: 12px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary) 0%, var(--secondary) 100%) !important;
    }
    
    /* Success/Error boxes */
    .success-box {
        background: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(16,185,129,0.05) 100%);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: #047857;
    }
    
    .error-box {
        background: linear-gradient(135deg, rgba(239,68,68,0.1) 0%, rgba(239,68,68,0.05) 100%);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: #b91c1c;
    }
    
    /* Hide elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.4s ease forwards;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════════

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'logged_in': False,
        'token': None,
        'user': None,
        'is_admin': False,
        'show_auth': True,
        'reg_step': 1,
        'reg_email': '',
        'reg_username': '',
        'reg_password': '',
        'comparison_result': None,
        'selected_comparison': 'text',
        'page': 'home'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ═══════════════════════════════════════════════════════════════════════════════════
# API HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════

def api_request(method, endpoint, data=None, files=None):
    """Make API request to backend."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if files:
        headers = {}
    else:
        headers["Content-Type"] = "application/json"
    
    if st.session_state.get('token') and st.session_state.token not in ['guest', 'demo']:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, timeout=60)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.json() if response.status_code != 204 else {"success": True}
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════

def login_user(username, password):
    """Login user via API."""
    result = api_request("POST", "/api/login", {"username": username, "password": password})
    if result and "access_token" in result:
        st.session_state.token = result["access_token"]
        st.session_state.user = username
        st.session_state.logged_in = True
        st.session_state.is_admin = result.get("is_admin", False)
        st.session_state.show_auth = False
        st.success("Welcome back!")
        st.rerun()
        return True
    elif result and "detail" in result:
        st.error(result["detail"])
    return False

def register_user(email, username, password):
    """Send OTP for registration."""
    result = api_request("POST", "/api/auth/send-otp", {
        "email": email,
        "username": username,
        "password": password
    })
    if result and result.get("message"):
        st.session_state.reg_email = email
        st.session_state.reg_username = username
        st.session_state.reg_password = password
        st.session_state.reg_step = 2
        st.success(f"OTP sent to your email!")
        st.rerun()
    elif result and "detail" in result:
        st.error(result["detail"])

def verify_otp_and_register(otp):
    """Verify OTP and complete registration."""
    result = api_request("POST", "/api/auth/verify-otp", {
        "email": st.session_state.reg_email,
        "otp": otp,
        "username": st.session_state.reg_username,
        "password": st.session_state.reg_password
    })
    if result and "access_token" in result:
        st.session_state.token = result["access_token"]
        st.session_state.user = st.session_state.reg_username
        st.session_state.logged_in = True
        st.session_state.is_admin = result.get("is_admin", False)
        st.session_state.reg_step = 1
        st.session_state.show_auth = False
        st.success("Registration successful! Welcome to DocFinder!")
        st.rerun()
    elif result and "detail" in result:
        st.error(result["detail"])

def logout_user():
    """Logout user."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.show_auth = True
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Render professional sidebar navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 1.75rem; color: white; margin: 0;">📄 DocFinder</h1>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.875rem; margin: 0.5rem 0 0 0;">Document Comparison</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.get('logged_in') or st.session_state.get('token'):
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; margin: 1rem 0; text-align: center;">
                <div style="color: white; font-weight: 600;">👤 {st.session_state.get('user', 'User')}</div>
                <div style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">{'Admin' if st.session_state.get('is_admin') else 'Member'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation buttons
        pages = [
            ("🏠", "Home", "home"),
            ("📝", "Compare", "compare"),
            ("📊", "History", "history"),
        ]
        
        for icon, label, page_key in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()

# ═══════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION MODAL
# ═══════════════════════════════════════════════════════════════════════════════════

def render_auth_modal():
    """Render professional login/register modal."""
    if not st.session_state.show_auth:
        return
    
    # Hero Header
    st.markdown("""
    <div class="hero-header">
        <h1>📄 DocFinder</h1>
        <p>Intelligent Document Comparison Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different auth options
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Guest Mode",
        "🔐 Login",
        "📝 Register",
        "🔑 Demo"
    ])
    
    # Guest Mode
    with tab1:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-icon icon-primary">🚀</div>
                <div>
                    <p class="card-title">Continue as Guest</p>
                    <p class="card-subtitle">Try without account</p>
                </div>
            </div>
            <p style="color: var(--text-secondary);">Access basic features without creating an account. Your data won't be saved.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Continue as Guest →", use_container_width=True):
            st.session_state.token = "guest"
            st.session_state.user = "Guest"
            st.session_state.show_auth = False
            st.rerun()
    
    # Login
    with tab2:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-icon icon-success">🔐</div>
                <div>
                    <p class="card-title">Login to Your Account</p>
                    <p class="card-subtitle">Access your saved comparisons</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            if st.form_submit_button("Login →", use_container_width=True):
                if username and password:
                    login_user(username, password)
                else:
                    st.warning("Please fill in all fields")
    
    # Register
    with tab3:
        if st.session_state.reg_step == 1:
            st.markdown("""
            <div class="card">
                <div class="card-header">
                    <div class="card-icon icon-purple">📧</div>
                    <div>
                        <p class="card-title">Create Account</p>
                        <p class="card-subtitle">Step 1: Enter your details</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("register_step1"):
                email = st.text_input("Email Address", placeholder="your@email.com")
                username = st.text_input("Username", placeholder="Choose a username")
                password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 chars)")
                confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                if st.form_submit_button("📧 Send OTP →", use_container_width=True):
                    if not all([email, username, password, confirm]):
                        st.warning("Please fill in all fields")
                    elif password != confirm:
                        st.error("Passwords do not match!")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters!")
                    else:
                        register_user(email, username, password)
        
        elif st.session_state.reg_step == 2:
            st.markdown("""
            <div class="card">
                <div class="card-header">
                    <div class="card-icon icon-warning">🔢</div>
                    <div>
                        <p class="card-title">Verify Email</p>
                        <p class="card-subtitle">Step 2: Enter the OTP sent to your email</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.success(f"OTP sent to: **{st.session_state.reg_email}**")
            st.info("💡 Check your inbox (and spam folder)")
            
            with st.form("register_step2"):
                otp = st.text_input("Enter 6-digit OTP", placeholder="123456", max_chars=6)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Verify & Register", use_container_width=True):
                        if len(otp) == 6:
                            verify_otp_and_register(otp)
                        else:
                            st.error("Please enter a valid 6-digit OTP")
                with col2:
                    if st.form_submit_button("← Back", use_container_width=True):
                        st.session_state.reg_step = 1
                        st.rerun()
    
    # Demo
    with tab4:
        st.markdown("""
        <div class="card">
            <div class="card-header">
                <div class="card-icon icon-error">🔑</div>
                <div>
                    <p class="card-title">Demo Account</p>
                    <p class="card-subtitle">Try all features instantly</p>
                </div>
            </div>
            <p style="color: var(--text-secondary);">Access DocFinder with demo privileges to explore all features.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Demo Mode →", use_container_width=True):
            st.session_state.token = "demo"
            st.session_state.user = "DemoUser"
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            st.session_state.show_auth = False
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════════════

def render_home():
    """Render home page."""
    st.markdown("""
    <div class="hero-header">
        <h1>📄 DocFinder</h1>
        <p>Compare Documents with Precision & Clarity</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features overview
    st.markdown("### ✨ Features")
    
    col1, col2, col3, col4 = st.columns(4)
    
    features = [
        ("📝", "Text Comparison", "Compare text documents with detailed diff", "icon-primary"),
        ("📕", "PDF Comparison", "Extract and compare PDF content", "icon-error"),
        ("📊", "Excel Comparison", "Compare spreadsheets cell-by-cell", "icon-success"),
        ("📋", "CSV Comparison", "Compare CSV files instantly", "icon-warning"),
    ]
    
    for col, (icon, title, desc, icon_class) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div class="card" style="height: 100%;">
                <div class="card-icon {icon_class}">{icon}</div>
                <p class="card-title" style="margin-top: 1rem;">{title}</p>
                <p class="card-subtitle">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### 📈 Quick Start")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value accent">1</div>
            <div class="stat-label">Select Document Type</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value success">2</div>
            <div class="stat-label">Upload Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value warning">3</div>
            <div class="stat-label">View Results</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🚀 Start Comparing Now →", use_container_width=True):
        st.session_state.page = "compare"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════════
# TEXT COMPARISON PAGE
# ═══════════════════════════════════════════════════════════════════════════════════

def render_text_comparison():
    """Render text comparison page."""
    st.markdown("""
    <div class="card" style="margin-bottom: 2rem;">
        <div class="card-header">
            <div class="card-icon icon-primary">📝</div>
            <div>
                <p class="card-title">Text Comparison</p>
                <p class="card-subtitle">Compare two text documents and see detailed differences</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Text input columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Original Text**")
        text1 = st.text_area("Original", height=300, placeholder="Paste your original text here...")
    
    with col2:
        st.markdown("**📄 Modified Text**")
        text2 = st.text_area("Modified", height=300, placeholder="Paste your modified text here...")
    
    # Options
    with st.expander("⚙️ Comparison Options"):
        col_a, col_b = st.columns(2)
        with col_a:
            level = st.selectbox("Level", ["word", "sentence", "paragraph", "character"])
            to_lowercase = st.checkbox("Case insensitive")
        with col_b:
            sort_lines = st.checkbox("Sort lines")
            remove_spaces = st.checkbox("Remove extra spaces")
    
    # Compare button
    if st.button("🔍 Compare Texts", type="primary", use_container_width=True):
        if text1 and text2:
            with st.spinner("Analyzing differences..."):
                result = api_request("POST", "/api/compare/text", {
                    "text1": text1,
                    "text2": text2,
                    "level": level,
                    "to_lowercase": str(to_lowercase).lower(),
                    "sort_lines": str(sort_lines).lower(),
                    "remove_extra_spaces": str(remove_spaces).lower()
                })
                
                if result and "results" in result:
                    st.session_state.comparison_result = result["results"]
                    st.success("Comparison complete!")
                elif result is None:
                    st.error("Failed to connect to API")
                else:
                    st.error("Comparison failed")
        else:
            st.warning("Please enter both texts")
    
    # Display results
    if st.session_state.comparison_result:
        results = st.session_state.comparison_result
        score = results.get("similarity_score", 0) * 100
        
        st.markdown("---")
        st.markdown("### 📊 Results")
        
        # Score display
        if score >= 80:
            color = "success"
            status = "🟢 Highly Similar"
        elif score >= 50:
            color = "warning"
            status = "🟡 Moderately Similar"
        else:
            color = "error"
            status = "🔴 Different"
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Similarity", f"{score:.1f}%")
        with col2:
            st.metric("Additions", results.get('total_additions', 0))
        with col3:
            st.metric("Deletions", results.get('total_deletions', 0))
        with col4:
            st.metric("Status", status)
        
        # Visual diff
        st.markdown("### 📝 Visual Difference")
        
        import difflib
        d = difflib.unified_diff(text1.splitlines(), text2.splitlines(), lineterm='')
        diff_lines = list(d)
        
        if diff_lines:
            html_lines = []
            for line in diff_lines:
                if line.startswith('+') and not line.startswith('+++'):
                    html_lines.append(f'<div class="diff-line diff-line-added"><span class="diff-marker">+</span>{line[1:]}</div>')
                elif line.startswith('-') and not line.startswith('---'):
                    html_lines.append(f'<div class="diff-line diff-line-removed"><span class="diff-marker">−</span>{line[1:]}</div>')
                elif line.startswith('@@'):
                    html_lines.append(f'<div style="background: #e0e7ff; padding: 0.5rem; font-weight: bold;">{line}</div>')
            
            st.markdown('<div class="diff-container">' + ''.join(html_lines) + '</div>', unsafe_allow_html=True)
        else:
            st.success("Texts are identical!")
        
        # Detailed changes
        st.markdown("### 📋 Detailed Changes")
        
        tab1, tab2, tab3 = st.tabs(["✅ Additions", "❌ Deletions", "🔄 All Changes"])
        
        with tab1:
            if results.get("additions"):
                for item in results["additions"][:10]:
                    word = item.get('word', item) if isinstance(item, dict) else item
                    st.markdown(f"<div class='diff-line diff-line-added'><span class='diff-marker'>+</span>{word}</div>", unsafe_allow_html=True)
            else:
                st.info("No additions found")
        
        with tab2:
            if results.get("deletions"):
                for item in results["deletions"][:10]:
                    word = item.get('word', item) if isinstance(item, dict) else item
                    st.markdown(f"<div class='diff-line diff-line-removed'><span class='diff-marker'>−</span>{word}</div>", unsafe_allow_html=True)
            else:
                st.info("No deletions found")
        
        with tab3:
            st.json(results)
        
        if st.button("🗑️ Clear Results"):
            st.session_state.comparison_result = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════════
# HISTORY PAGE
# ═══════════════════════════════════════════════════════════════════════════════════

def render_history():
    """Render comparison history page."""
    st.markdown("""
    <div class="card" style="margin-bottom: 2rem;">
        <div class="card-header">
            <div class="card-icon icon-success">📊</div>
            <div>
                <p class="card-title">Comparison History</p>
                <p class="card-subtitle">View your past comparisons</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.token in ['guest', None]:
        st.info("Please login to see your history")
        return
    
    result = api_request("GET", "/api/history")
    
    if result and isinstance(result, list):
        if len(result) == 0:
            st.info("No comparisons yet. Start comparing documents!")
        else:
            for item in result:
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.markdown(f"**{item.get('comparison_type', 'N/A').upper()}**")
                    with col2:
                        st.markdown(f"Similarity: {item.get('similarity_score', 'N/A')}")
                    with col3:
                        st.markdown(f"📅 {item.get('created_at', 'N/A')}")
                    st.markdown("---")
    else:
        st.error("Failed to load history")

# ═══════════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    """Main application."""
    render_sidebar()
    
    if st.session_state.show_auth and not st.session_state.logged_in:
        render_auth_modal()
        return
    
    # Page routing
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "compare":
        render_text_comparison()
    elif st.session_state.page == "history":
        render_history()

if __name__ == "__main__":
    main()

