"""DocFinder Frontend - Main App."""
import os
import re
import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration - Use localhost since backend and frontend are in same container
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="DocFinder - Intelligent Document Comparison",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7F8C8D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #ECF0F1;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .success-box {
        background-color: #D5F4E6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #27AE60;
    }
    .error-box {
        background-color: #FADBD8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #E74C3C;
    }
    .stButton>button {
        width: 100%;
        background-color: #3498DB;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2980B9;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables - only if not already set."""
    # Only initialize if not already in session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'is_guest' not in st.session_state:
        st.session_state.is_guest = False
    if 'reg_step' not in st.session_state:
        st.session_state.reg_step = 1


def api_request(method, endpoint, data=None, files=None, use_form=False):
    """Make API request with error handling.
    
    Args:
        method: HTTP method (GET, POST)
        endpoint: API endpoint path
        data: Request body data (dict)
        files: File data for multipart uploads
        use_form: If True, send data as form fields instead of JSON
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, timeout=60)
            elif use_form:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = requests.post(url, headers=headers, data=data, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Please login again")
            st.session_state.token = None
            st.session_state.logged_in = False
            return None
        else:
            try:
                error = response.json().get("detail", "Unknown error")
            except:
                error = f"HTTP {response.status_code}"
            st.error(f"Error: {error}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


def login_page():
    """Display login/register page with optional login."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<p class="main-header">📄 DocFinder</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Intelligent Document Difference Finder</p>', unsafe_allow_html=True)
        
        # Show option to skip login
        st.info("💡 **No account needed!** You can use DocFinder without logging in. Your comparisons won't be saved.")
        
        # Guest button - uses JavaScript to redirect
        st.markdown("""
        <script>
        function goGuest() {
            window.location.href = window.location.pathname + '?guest=true';
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Create a link that acts as a button
        st.markdown('<a href="?guest=true"><button style="width:100%;padding:0.75rem 2rem;background-color:#6C757D;color:white;border:none;border-radius:0.5rem;font-weight:bold;cursor:pointer;">🚀 Continue as Guest</button></a>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "🔑 Demo"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter username", key="login_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
                
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
                if submitted:
                    if username and password:
                        result = api_request("POST", "/api/login", {"username": username, "password": password})
                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = username
                            st.session_state.is_admin = result["is_admin"]
                            st.session_state.logged_in = True
                            st.session_state.user_id = result.get("user_id")
                            st.session_state.is_guest = False
                            st.success("Login successful!")
                            st.rerun()
                    else:
                        st.warning("Please fill in all fields")
        
        with tab2:
            if st.session_state.reg_step == 1:
                st.markdown("**Step 1:** Enter your details")
                with st.form("register_form_1"):
                    new_username = st.text_input("Username", placeholder="Choose username", key="reg_user_input")
                    new_email = st.text_input("Email", placeholder="Enter email (OTP will be sent)", key="reg_email_input")
                    new_password = st.text_input("Password", type="password", placeholder="Choose password", key="reg_pass_input")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm_input")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        send_otp = st.form_submit_button("📧 Send OTP", use_container_width=True)
                    with col_b:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                    
                    if cancel:
                        st.session_state.reg_step = 1
                        st.rerun()
                    
                    if send_otp:
                        if new_username and new_email and new_password:
                            if new_password != confirm_password:
                                st.error("Passwords don't match")
                            elif len(new_password) < 6:
                                st.error("Password must be at least 6 characters")
                            elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', new_email):
                                st.error("Please enter a valid email address")
                            else:
                                # Check if username is available
                                result = api_request("POST", "/api/auth/send-otp", {"email": new_email})
                                if result:
                                    st.session_state.reg_username = new_username
                                    st.session_state.reg_email = new_email
                                    st.session_state.reg_password = new_password
                                    st.session_state.reg_step = 2
                                    st.success("✅ OTP sent! Check your email (or console logs for development).")
                                    st.rerun()
                        else:
                            st.warning("Please fill in all fields")
            
            elif st.session_state.reg_step == 2:
                st.markdown("**Step 2:** Enter OTP")
                st.info(f"📧 OTP sent to: `{st.session_state.reg_email}`")
                st.info("💡 **Check your email inbox (and spam folder)** for the verification code!")
                
                with st.form("register_form_2"):
                    otp = st.text_input("Enter 6-digit OTP", placeholder="123456", max_chars=6, key="otp_input")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        verify = st.form_submit_button("✅ Verify & Register", use_container_width=True)
                    with col_b:
                        back = st.form_submit_button("← Back", use_container_width=True)
                    
                    if back:
                        st.session_state.reg_step = 1
                        st.rerun()
                    
                    if verify:
                        if otp and len(otp) == 6:
                            result = api_request("POST", "/api/auth/verify-otp", {
                                "email": st.session_state.reg_email,
                                "otp": otp,
                                "username": st.session_state.reg_username,
                                "password": st.session_state.reg_password
                            })
                            if result:
                                st.session_state.token = result["access_token"]
                                st.session_state.user = st.session_state.reg_username
                                st.session_state.is_admin = result["is_admin"]
                                st.session_state.logged_in = True
                                st.session_state.user_id = result.get("user_id")
                                st.session_state.is_guest = False
                                # Clear registration state
                                for key in ['reg_step', 'reg_email', 'reg_username', 'reg_password']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.success("🎉 Registration successful!")
                                st.rerun()
                        else:
                            st.error("Please enter a valid 6-digit OTP")
        
        with tab3:
            st.markdown("**Quick Demo Access**")
            st.warning("This logs you in as the admin user for testing purposes.")
            
            # Demo login link
            st.markdown('<a href="?demo_login=true"><button style="width:100%;padding:0.75rem 2rem;background-color:#3498DB;color:white;border:none;border-radius:0.5rem;font-weight:bold;cursor:pointer;">🔑 Login as Demo Admin</button></a>', unsafe_allow_html=True)


def sidebar_menu():
    """Render sidebar menu."""
    with st.sidebar:
        st.markdown("### 📄 DocFinder")
        
        if st.session_state.logged_in:
            st.markdown(f"**Welcome, {st.session_state.user}!**")
            if st.session_state.is_admin:
                st.markdown("🛡️ Admin")
        
        st.markdown("---")
        
        menu_options = ["🏠 Home", "📝 Compare", "📊 History"]
        if st.session_state.is_admin:
            menu_options.append("⚙️ Admin")
        
        # Set default index based on URL param for all users
        page_param = st.query_params.get("page", "Home")
        if page_param == "Compare":
            default_index = 1
        elif page_param == "History":
            default_index = 2
        elif page_param == "Admin":
            default_index = 3
        else:
            default_index = 0
        
        choice = st.radio("Menu", menu_options, index=default_index)
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.is_admin = False
            st.session_state.logged_in = False
            st.rerun()
        
        return choice


def home_page():
    """Display home page."""
    st.markdown('<p class="main-header">📄 DocFinder</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent Document Comparison Platform</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 Compare Documents")
        st.write("Compare TXT, PDF, Excel, and CSV files with AI-powered analysis")
        st.markdown("""
        - Character/Word/Sentence/Paragraph comparison
        - Semantic analysis with AI
        - Visual diff highlighting
        """)
    
    with col2:
        st.markdown("### 🤖 AI Features")
        st.write("Advanced AI-powered document analysis")
        st.markdown("""
        - Semantic similarity detection
        - Paraphrase identification
        - Change importance classification
        """)
    
    with col3:
        st.markdown("### 📊 Reports")
        st.write("Generate comprehensive comparison reports")
        st.markdown("""
        - PDF reports
        - Excel reports
        - Similarity scores
        """)
    
    st.markdown("---")
    
    if st.session_state.logged_in:
        st.markdown("### 🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Start New Comparison", use_container_width=True):
                st.session_state.page = "Compare"
                st.rerun()
        with col2:
            if st.button("View History", use_container_width=True):
                st.session_state.page = "History"
                st.rerun()
        with col3:
            if st.button("View Statistics", use_container_width=True):
                st.session_state.page = "Admin"
                st.rerun()
    else:
        st.info("👈 Please login to start comparing documents")


def compare_page():
    """Display comparison page."""
    st.markdown("## 📝 Document Comparison")
    
    # Use radio buttons for simple tab switching
    comparison_type = st.radio(
        "Select Comparison Type",
        ["📄 Text", "📕 PDF", "📊 Excel", "📋 CSV"],
        horizontal=True,
        index=0,
        key="comparison_type_radio"
    )
    
    # Only render the active comparison form
    if comparison_type == "📄 Text":
        render_text_comparison()
    elif comparison_type == "📕 PDF":
        render_pdf_comparison()
    elif comparison_type == "📊 Excel":
        render_excel_comparison()
    elif comparison_type == "📋 CSV":
        render_csv_comparison()


def render_text_comparison():
    """Render text comparison form with preprocessing options."""
    st.markdown("### Text Comparison")
    
    # Initialize session state for results
    if "comparison_result" not in st.session_state:
        st.session_state.comparison_result = None

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Text**")
        st.text_area("Enter original text", height=300, key="text1")
    
    with col2:
        st.markdown("**Modified Text**")
        st.text_area("Enter modified text", height=300, key="text2")
    
    # Comparison options
    with st.expander("⚙️ Comparison Options", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            level = st.selectbox(
                "Comparison Level",
                ["word", "sentence", "paragraph", "character"],
                help="Select the granularity of comparison"
            )
            to_lowercase = st.checkbox("Convert to lowercase", value=False)
        with col_b:
            sort_lines = st.checkbox("Sort lines alphabetically", value=False)
            replace_line_breaks = st.checkbox("Replace line breaks with spaces", value=False)
            remove_extra_spaces = st.checkbox("Remove extra whitespace", value=False)
    
    if st.button("🔍 Compare Text", type="primary", use_container_width=True):
        # Read from session_state directly
        text1 = st.session_state.get("text1", "")
        text2 = st.session_state.get("text2", "")
        
        if text1 and text2:
            with st.spinner("Comparing texts..."):
                result = api_request("POST", "/api/compare/text", data={
                    "text1": text1,
                    "text2": text2,
                    "level": level,
                    "to_lowercase": str(to_lowercase).lower(),
                    "sort_lines": str(sort_lines).lower(),
                    "replace_line_breaks": str(replace_line_breaks).lower(),
                    "remove_extra_spaces": str(remove_extra_spaces).lower()
                }, use_form=True)
                
                if result and "results" in result:
                    st.session_state.comparison_result = result["results"]
                    st.rerun()
                elif result is None:
                    st.error("API connection failed")
        else:
            st.warning("Please enter both texts")
    
    # Display results if available (always check on every render)
    if st.session_state.comparison_result:
        st.markdown("---")
        col_clear, _ = st.columns([1, 5])
        with col_clear:
            if st.button("🗑️ Clear Results"):
                st.session_state.comparison_result = None
                st.rerun()
        
        st.markdown("## 📊 Comparison Results")
        
        results = st.session_state.comparison_result
        score = results.get("similarity_score", 0)
        
        # Score display with color
        if score >= 0.8:
            score_color = "🟢"
        elif score >= 0.5:
            score_color = "🟡"
        else:
            score_color = "🔴"
        
        st.markdown(f"**Similarity Score:** {score_color} **{score * 100:.1f}%**")
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("✅ Additions", results.get('total_additions', 0))
        with col_stat2:
            st.metric("❌ Deletions", results.get('total_deletions', 0))
        with col_stat3:
            st.metric("🔄 Modifications", results.get('total_modifications', 0))
        
        # Visual Diff View - Side by Side
        st.markdown("### 📝 Visual Difference View")
        
        # Generate unified diff for visual display
        text1 = st.session_state.get("text1", "")
        text2 = st.session_state.get("text2", "")
        
        import difflib
        d = difflib.unified_diff(text1.splitlines(keepends=True), text2.splitlines(keepends=True), lineterm='')
        diff_lines = list(d)
        
        if diff_lines:
            diff_text = ''.join(diff_lines)
            
            # Display with color coding using HTML
            html_diff = []
            for line in diff_lines:
                if line.startswith('+') and not line.startswith('+++'):
                    html_diff.append(f'<span style="background-color: #90EE90; color: green;">{line}</span>')
                elif line.startswith('-') and not line.startswith('---'):
                    html_diff.append(f'<span style="background-color: #FFB6C1; color: red;">{line}</span>')
                elif line.startswith('@@'):
                    html_diff.append(f'<span style="color: blue; font-weight: bold;">{line}</span>')
            
            st.markdown("**Legend:** 🟢 Green = Added | 🔴 Red = Deleted", unsafe_allow_html=True)
            st.markdown('<br>'.join(html_diff), unsafe_allow_html=True)
        else:
            st.info("No differences found - texts are identical!")
        
        # Detailed Changes Section
        st.markdown("---")
        st.markdown("### 📋 Detailed Changes")
        
        tab1, tab2, tab3 = st.tabs(["✅ Additions", "❌ Deletions", "🔄 Modifications"])
        
        with tab1:
            if results.get("additions"):
                st.markdown(f"**Total: {len(results['additions'])} additions**")
                for i, add in enumerate(results["additions"][:20], 1):
                    word = add.get('word', add) if isinstance(add, dict) else add
                    pos = add.get('position', 'N/A') if isinstance(add, dict) else 'N/A'
                    st.markdown(f"  {i}. <span style='color: green;'>+ {word}</span> *(pos: {pos})*", unsafe_allow_html=True)
                if len(results['additions']) > 20:
                    st.info(f"Showing 20 of {len(results['additions'])} additions")
            else:
                st.info("No additions found")
        
        with tab2:
            if results.get("deletions"):
                st.markdown(f"**Total: {len(results['deletions'])} deletions**")
                for i, dele in enumerate(results["deletions"][:20], 1):
                    word = dele.get('word', dele) if isinstance(dele, dict) else dele
                    pos = dele.get('position', 'N/A') if isinstance(dele, dict) else 'N/A'
                    st.markdown(f"  {i}. <span style='color: red;'>- {word}</span> *(pos: {pos})*", unsafe_allow_html=True)
                if len(results['deletions']) > 20:
                    st.info(f"Showing 20 of {len(results['deletions'])} deletions")
            else:
                st.info("No deletions found")
        
        with tab3:
            if results.get("modifications"):
                st.markdown(f"**Total: {len(results['modifications'])} modifications**")
                for i, mod in enumerate(results["modifications"][:20], 1):
                    orig = mod.get('original', '')
                    modified = mod.get('modified', '')
                    st.markdown(f"  {i}. <span style='color: red;'>{orig}</span> → <span style='color: green;'>{modified}</span>", unsafe_allow_html=True)
                if len(results['modifications']) > 20:
                    st.info(f"Showing 20 of {len(results['modifications'])} modifications")
            else:
                st.info("No modifications found (use 'word' level for modifications)")
        
        # Case Changes Detection
        st.markdown("---")
        st.markdown("### 🔤 Case Changes (Uppercase/Lowercase)")
        
        case_changes = []
        if results.get("additions") and results.get("deletions"):
            additions_words = [a.get('word', a) if isinstance(a, dict) else a for a in results['additions']]
            deletions_words = [d.get('word', d) if isinstance(d, dict) else d for d in results['deletions']]
            
            # Find case-only differences
            for del_word in deletions_words:
                for add_word in additions_words:
                    if del_word.lower() == add_word.lower() and del_word != add_word:
                        case_changes.append({
                            "from": del_word,
                            "to": add_word,
                            "type": "uppercase" if add_word.isupper() else "lowercase"
                        })
        
        if case_changes:
            for change in case_changes[:10]:
                if change['type'] == 'uppercase':
                    st.markdown(f"  🔠 `{change['from']}` → `{change['to']}`")
                else:
                    st.markdown(f"  🔡 `{change['from']}` → `{change['to']}`")
        else:
            st.info("No case changes detected")
        
        # AI Analysis
        if results.get("ai_analysis"):
            st.markdown("---")
            ai = results["ai_analysis"]
            st.markdown("### 🤖 AI Analysis")
            st.write(f"**Semantic Similarity:** {ai.get('similarity_percentage', 'N/A')}%")


def render_pdf_comparison():
    """Render PDF comparison form."""
    st.markdown("### PDF Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original PDF**")
        file1 = st.file_uploader("Upload original PDF", type=["pdf"], key="pdf1")
    
    with col2:
        st.markdown("**Modified PDF**")
        file2 = st.file_uploader("Upload modified PDF", type=["pdf"], key="pdf2")
    
    use_ocr = st.checkbox("Use OCR for scanned PDFs", help="Enable if PDFs contain scanned images")
    
    if st.button("🔍 Compare PDFs", type="primary"):
        if file1 and file2:
            with st.spinner("Comparing PDFs..."):
                files = {
                    "file1": (file1.name, file1.getvalue(), "application/pdf"),
                    "file2": (file2.name, file2.getvalue(), "application/pdf"),
                    "use_ocr": (None, str(use_ocr).lower())
                }
                result = api_request("POST", "/api/compare/pdf", files=files)
                
                if result:
                    render_comparison_results(result["results"])
        else:
            st.warning("Please upload both PDF files")


def render_excel_comparison():
    """Render Excel comparison form."""
    st.markdown("### Excel Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Excel**")
        file1 = st.file_uploader("Upload original Excel", type=["xlsx", "xls"], key="excel1")
    
    with col2:
        st.markdown("**Modified Excel**")
        file2 = st.file_uploader("Upload modified Excel", type=["xlsx", "xls"], key="excel2")
    
    if st.button("🔍 Compare Excel", type="primary"):
        if file1 and file2:
            with st.spinner("Comparing Excel files..."):
                files = {
                    "file1": (file1.name, file1.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    "file2": (file2.name, file2.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                }
                result = api_request("POST", "/api/compare/excel", files=files)
                
                if result:
                    render_comparison_results(result["results"])
        else:
            st.warning("Please upload both Excel files")


def render_csv_comparison():
    """Render CSV comparison form."""
    st.markdown("### CSV Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original CSV**")
        file1 = st.file_uploader("Upload original CSV", type=["csv"], key="csv1")
    
    with col2:
        st.markdown("**Modified CSV**")
        file2 = st.file_uploader("Upload modified CSV", type=["csv"], key="csv2")
    
    if st.button("🔍 Compare CSV", type="primary"):
        if file1 and file2:
            with st.spinner("Comparing CSV files..."):
                files = {
                    "file1": (file1.name, file1.getvalue(), "text/csv"),
                    "file2": (file2.name, file2.getvalue(), "text/csv")
                }
                result = api_request("POST", "/api/compare/csv", files=files)
                
                if result:
                    render_comparison_results(result["results"])
        else:
            st.warning("Please upload both CSV files")


def render_comparison_results(results):
    """Render comparison results."""
    st.markdown("---")
    st.markdown("## 📊 Comparison Results")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = results.get("similarity_score", 0)
        st.metric("Similarity Score", f"{score * 100:.1f}%")
    
    with col2:
        st.metric("Additions", results.get("total_additions", 0))
    
    with col3:
        st.metric("Deletions", results.get("total_deletions", 0))
    
    with col4:
        comp_type = results.get("type", "N/A").upper()
        st.metric("Type", comp_type)
    
    # AI Analysis
    if "ai_analysis" in results and results["ai_analysis"]:
        ai = results["ai_analysis"]
        st.markdown("### 🤖 AI Analysis")
        
        if "similarity_percentage" in ai:
            st.write(f"**Semantic Similarity:** {ai['similarity_percentage']}%")
        
        if ai.get("is_semantically_similar"):
            st.success("Texts are semantically similar")
        elif ai.get("paraphrase_detected"):
            st.warning("Paraphrasing detected")
    
    # Detailed results
    if "additions" in results and results["additions"]:
        st.markdown("### ✅ Additions")
        additions = results["additions"][:20]
        for add in additions:
            if isinstance(add, dict):
                st.markdown(f"<span style='color:green'>+ {add.get('word', str(add))}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:green'>+ {add}</span>", unsafe_allow_html=True)
    
    if "deletions" in results and results["deletions"]:
        st.markdown("### ❌ Deletions")
        deletions = results["deletions"][:20]
        for dele in deletions:
            if isinstance(dele, dict):
                st.markdown(f"<span style='color:red'>- {dele.get('word', str(dele))}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red'>- {dele}</span>", unsafe_allow_html=True)
    
    if "modifications" in results and results["modifications"]:
        st.markdown("### 🔄 Modifications")
        for mod in results["modifications"][:10]:
            st.write(f"• {mod.get('original', 'N/A')} → {mod.get('modified', 'N/A')}")


def history_page():
    """Display comparison history."""
    st.markdown("## 📊 Comparison History")
    
    history = api_request("GET", "/api/history")
    
    if history:
        for item in history[:20]:
            with st.expander(f"📄 {item['file1_name']} vs {item['file2_name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Similarity:** {item['similarity_score'] * 100:.1f}%")
                    st.write(f"**Status:** {item['status']}")
                with col2:
                    st.write(f"**Date:** {item['created_at'][:10] if item['created_at'] else 'N/A'}")
    else:
        st.info("No comparison history found")


def admin_page():
    """Display admin page."""
    if not st.session_state.is_admin:
        st.error("Admin access required")
        return
    
    st.markdown("## ⚙️ Admin Dashboard")
    
    stats = api_request("GET", "/api/admin/stats")
    
    if stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", stats.get("total_users", 0))
        with col2:
            st.metric("Active Users", stats.get("active_users", 0))
        with col3:
            st.metric("Total Comparisons", stats.get("total_comparisons", 0))
    
    st.markdown("### 👥 Users")
    users = api_request("GET", "/api/admin/users")
    
    if users:
        for user in users:
            with st.expander(f"👤 {user['username']} ({user['email']})"):
                st.write(f"**Admin:** {'Yes' if user['is_admin'] else 'No'}")
                st.write(f"**Active:** {'Yes' if user['is_active'] else 'No'}")
                st.write(f"**Last Login:** {user['last_login'][:10] if user['last_login'] else 'Never'}")


def main():
    """Main application entry point."""
    import os
    init_session_state()
    
    # Check for auto-login parameter ONLY if not already logged in
    query_params = st.query_params
    
    if not st.session_state.get("logged_in", False):
        # Handle guest mode via URL parameter
        if query_params.get("guest") == "true":
            st.session_state.logged_in = True
            st.session_state.user = "Guest"
            st.session_state.is_admin = False
            st.session_state.token = None
            st.session_state.is_guest = True
            # Keep page param
            page = query_params.get("page", "Home")
            query_params.clear()
            query_params["guest"] = "true"
            query_params["page"] = page
            st.rerun()
        
        if query_params.get("demo_login") == "true":
            result = api_request("POST", "/api/login", {"username": "admin", "password": "admin123"})
            if result:
                st.session_state.token = result["access_token"]
                st.session_state.user = "admin"
                st.session_state.is_admin = result["is_admin"]
                st.session_state.logged_in = True
                st.session_state.user_id = result.get("user_id")
                st.session_state.is_guest = False
                # Preserve page param and redirect
                page = query_params.get("page", "Home")
                query_params.clear()
                query_params["page"] = page
                st.rerun()
        
        # Not logged in, show login page
        login_page()
    else:
        # Already logged in - render the app
        # Get current page from query params or default to Home
        page_from_url = query_params.get("page", "Home")
        
        # Render sidebar menu to set initial value
        choice = sidebar_menu()
        
        # Get page from URL if set (for guest mode deep linking)
        page_from_url = query_params.get("page", None)
        
        # Determine page name based on sidebar choice OR URL param (for deep linking)
        # Use sidebar choice if user clicked a menu item, otherwise use URL param
        if "Home" in choice:
            page_name = "Home"
        elif "Compare" in choice:
            page_name = "Compare"
        elif "History" in choice:
            page_name = "History"
        elif "Admin" in choice:
            page_name = "Admin"
        else:
            # Default: use URL param if available
            page_name = query_params.get("page", "Home")
        
        # Update query param
        query_params["page"] = page_name
        
        # Render the page based on choice, not URL
        if page_name == "Home":
            home_page()
        elif page_name == "Compare":
            compare_page()
        elif page_name == "History":
            history_page()
        elif page_name == "Admin":
            admin_page()


if __name__ == "__main__":
    main()

import os