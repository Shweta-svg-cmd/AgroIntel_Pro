"""
AgroIntel — Universal Agricultural Intelligence Platform
------------------------------------------------------------
Merged app:
  - Login / registration / farm management / machinery / soil / compliance /
    AI copilot (originally built against database.py + ai_service_free.py)
  - Field Intelligence: live NASA POWER / OpenWeather / RVO NL dashboard
    (nasapower.py, openweather.py, rvo.py)

Requires in the same folder:
    map.py, database.py, ai_service_free.py,
    nasapower.py, openweather.py, rvo.py, .env

Run:
    pip install streamlit streamlit-option-menu pandas plotly requests
                python-dotenv deep-translator
    streamlit run map.py
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY', '')
if api_key:
    print("✅ API Key loaded successfully!")
else:
    print("❌ No API Key found in .env")

import database as db
import ai_service_free as ai_service

from nasapower import get_agro_weather_flat, safe_end_date
from openweather import get_weather as get_current_weather
from rvo import get_agri_subsidies

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except Exception:
    TRANSLATE_AVAILABLE = False

try:
    import folium
    from folium.plugins import Fullscreen, MiniMap
    from streamlit_folium import st_folium
    import math
    MAP_AVAILABLE = True
except Exception:
    MAP_AVAILABLE = False


# ==================== SESSION STATE ====================

for key, default in {
    'authenticated': False,
    'username': None,
    'user_id': None,
    'page': 'login',
    'ai_question': '',
    'ask_ai': False,
    'voice_enabled': True,
    'layer': 'orbit',
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="AgroIntel - Universal Agricultural Intelligence Platform",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== THEME ====================

BG = "#0A120D"
PANEL = "#101B14"
PANEL2 = "#16231A"
LINE = "#223326"
ORBIT = "#6E8CE0"
ORBIT_DIM = "#33406B"
ATMOS = "#4FAFD8"
ATMOS_DIM = "#2E4A56"
GRANTS = "#E0A93E"
GRANTS_DIM = "#4A3D22"
TEXT = "#E9EEE7"
MUTED = "#7F9482"
ACCENT = "#8FD14F"
WARN = "#E0965B"
DANGER = "#E0705B"

CHART_SEQUENCE = [ACCENT, ORBIT, ATMOS, GRANTS, WARN, "#B98FE0"]
PLOTLY_FONT = dict(family="IBM Plex Mono, monospace", color=MUTED, size=12)

CROP_COLORS = {
    "Winter Wheat": "#D6B04A",
    "Corn": "#E0A93E",
    "Soybeans": "#8FD14F",
    "Barley": "#C98A45",
    "Potatoes": "#B98FE0",
    "Oats": "#E0965B",
    "Sunflowers": "#F0D24A",
    "Other": "#6E8CE0",
}
DEFAULT_CROP_COLOR = "#7F9482"


def plotly_dark(fig, height=320):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=PLOTLY_FONT,
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=PLOTLY_FONT),
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


# ==================== VOICE OUTPUT FUNCTION ====================

def get_voice_html(text):
    """Generate HTML with voice playback functionality"""
    if not text:
        return ""
    
    escaped_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
    
    return f"""
    <div style="margin-top: 0.5rem; padding: 0.5rem; background: #f0f7f0; border-radius: 8px;">
        <button onclick="speakText()" style="
            background: #2E7D32; 
            color: white; 
            border: none; 
            padding: 0.5rem 1.2rem; 
            border-radius: 20px; 
            cursor: pointer; 
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
        "
        onmouseover="this.style.background='#1B5E20'"
        onmouseout="this.style.background='#2E7D32'">
            🔊 Listen to Response
        </button>
        <span style="color: #888; font-size: 0.8rem; margin-left: 0.8rem;">
            Click to hear the AI response
        </span>
    </div>
    <script>
    function speakText() {{
        var text = {repr(escaped_text)};
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """


# ==================== CSS ====================
def apply_custom_css():
    st.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}

    .stApp {{
        background: radial-gradient(ellipse at top, #0D1A12 0%, {BG} 55%);
        color: {TEXT};
    }}
    #MainMenu, header, footer {{visibility: hidden;}}

    .main-header {{
        background: linear-gradient(135deg, {PANEL} 0%, {PANEL2} 100%);
        border: 1px solid {LINE};
        padding: 1.6rem 2rem;
        border-radius: 14px;
        margin-bottom: 2rem;
    }}
    .main-header h1 {{
        margin: 0; font-size: 2rem; font-weight: 700;
        font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(90deg, #EDF3EA 0%, {ACCENT} 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .main-header p {{ margin: 0.3rem 0 0 0; color: {MUTED}; font-size: 1rem; }}

    .metric-card {{
        background: {PANEL}; border: 1px solid {LINE}; border-left: 4px solid {ACCENT};
        padding: 1.3rem 1.5rem; border-radius: 12px; height: 100%;
        transition: transform 0.15s ease;
    }}
    .metric-card:hover {{ transform: translateY(-2px); border-color: {ACCENT}; }}
    .metric-value {{
        font-family: 'IBM Plex Mono', monospace; font-size: 2.1rem; font-weight: 600;
        color: {TEXT}; margin: 0.3rem 0;
    }}
    .metric-label {{
        font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase;
        letter-spacing: 0.1em; color: {MUTED}; font-weight: 500;
    }}
    .metric-sub {{ font-size: 0.8rem; color: {MUTED}; }}

    .section-title {{
        font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 600;
        color: {TEXT}; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem;
        border-bottom: 2px solid {LINE};
    }}

    .ai-card {{
        background: {PANEL2}; padding: 1.5rem; border-radius: 12px;
        border: 1px solid {ORBIT_DIM}; height: 100%; transition: transform 0.15s ease;
    }}
    .ai-card:hover {{ transform: translateY(-2px); border-color: {ORBIT}; }}
    .ai-card h4 {{ color: {ACCENT}; margin-top: 0; font-family: 'Space Grotesk', sans-serif; }}
    .ai-card .confidence {{
        background: {ORBIT_DIM}; color: {TEXT}; padding: 0.2rem 0.8rem;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }}

    .status-badge {{
        padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }}
    .status-badge.success {{ background: {ORBIT_DIM}; color: {ACCENT}; }}
    .status-badge.warning {{ background: {GRANTS_DIM}; color: {WARN}; }}
    .status-badge.info {{ background: {ATMOS_DIM}; color: {ATMOS}; }}
    .status-badge.danger {{ background: #3A1F1A; color: {DANGER}; }}

    .sidebar-brand {{ text-align: center; padding: 1rem 0; }}
    .sidebar-brand h2 {{
        margin: 0; font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(90deg, #EDF3EA 0%, {ACCENT} 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .sidebar-brand p {{ color: {MUTED}; font-size: 0.8rem; }}

    .field-card {{
        background: {PANEL}; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;
        border: 1px solid {LINE}; display: flex; justify-content: space-between; align-items: center;
    }}
    .field-card .field-name {{ font-weight: 600; color: {TEXT}; }}
    .crop-tag {{
        background: {ORBIT_DIM}; padding: 0.2rem 0.8rem; border-radius: 12px;
        font-size: 0.75rem; color: {ACCENT}; font-family: 'IBM Plex Mono', monospace;
    }}

    .welcome-container {{ text-align: center; padding: 4rem 2rem; }}
    .welcome-container .emoji {{ font-size: 4rem; }}
    .welcome-container h1 {{
        margin: 1rem 0; font-family: 'Space Grotesk', sans-serif; font-size: 2.4rem;
        background: linear-gradient(90deg, #EDF3EA 0%, {ACCENT} 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .welcome-container p {{ font-size: 1.15rem; color: {MUTED}; }}
    .welcome-container .sub-text {{ color: {MUTED}; font-size: 0.9rem; }}

    .data-entry-card {{
        background: {PANEL}; border: 1px solid {LINE}; padding: 1.8rem;
        border-radius: 12px; margin-bottom: 2rem;
    }}
    .data-entry-card h3 {{ color: {TEXT}; margin-top: 0; font-family: 'Space Grotesk', sans-serif; }}

    .api-status {{
        padding: 0.6rem 1rem; border-radius: 8px; margin-bottom: 1rem;
        font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
    }}
    .api-status.connected {{ background: {ORBIT_DIM}; border: 1px solid {ACCENT}; color: {TEXT}; }}
    .api-status.disconnected {{ background: {GRANTS_DIM}; border: 1px solid {WARN}; color: {TEXT}; }}

    div[data-testid="stButton"] > button {{
        width: 100%; border-radius: 10px; border: 1px solid {LINE};
        background: {PANEL}; color: {TEXT}; font-family: 'Space Grotesk', sans-serif;
        font-weight: 600; letter-spacing: 0.02em; padding: 0.7rem 0.9rem;
        transition: all 0.15s ease;
    }}
    div[data-testid="stButton"] > button:hover {{
        border-color: {ACCENT}; color: {ACCENT}; transform: translateY(-1px);
    }}
    div[data-testid="stButton"] > button:focus:not(:active) {{ border-color: {ACCENT}; color: {ACCENT}; }}

    .layer-tag {{
        font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.2em;
        text-transform: uppercase; padding: 0.2rem 0.6rem; border-radius: 999px;
        display: inline-block; margin-bottom: 0.8rem;
    }}
    .tag-orbit {{ background: {ORBIT_DIM}; color: #C3CDF5; }}
    .tag-atmos {{ background: {ATMOS_DIM}; color: #B4E4F5; }}
    .tag-grants {{ background: {GRANTS_DIM}; color: #F5D9A0; }}

    .snap-card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 12px; padding: 1.1rem 1.3rem; }}
    .snap-label {{
        font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; text-transform: uppercase;
        letter-spacing: 0.15em; color: {MUTED};
    }}
    .snap-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 2.1rem; font-weight: 600; color: {TEXT}; }}
    .snap-sub {{ color: {MUTED}; font-size: 0.85rem; }}

    .subsidy-card {{
        background: {PANEL}; border: 1px solid {LINE}; border-radius: 12px;
        padding: 1.1rem 1.3rem; margin-bottom: 0.7rem; transition: border-color 0.15s ease;
    }}
    .subsidy-card:hover {{ border-color: {GRANTS}; }}
    .subsidy-title {{ font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1.05rem; color: {TEXT}; margin-bottom: 0.3rem; }}
    .subsidy-intro {{ color: {MUTED}; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.5rem; }}
    .subsidy-link {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: {GRANTS}; text-decoration: none; }}
    .subsidy-link:hover {{ text-decoration: underline; }}

    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {{
        background: {PANEL2} !important; color: {TEXT} !important; border: 1px solid {LINE} !important;
    }}
    [data-testid="stMetricValue"] {{ font-family: 'IBM Plex Mono', monospace; color: {TEXT}; }}
    [data-testid="stMetricLabel"] {{
        font-family: 'IBM Plex Mono', monospace; color: {MUTED};
        text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.1em;
    }}
    hr {{ border-color: {LINE}; }}

    /* FIX: Remove blank spaces in AI output */
    .ai-card > div {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Voice toggle styling */
    .voice-toggle-container {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem;
        background: {PANEL2};
        border-radius: 8px;
        border: 1px solid {LINE};
        margin-bottom: 1rem;
    }}
    .voice-toggle-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        color: {MUTED};
    }}
    .voice-toggle-status {{
        font-weight: 600;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-size: 0.75rem;
    }}
    .voice-status-on {{
        background: {ORBIT_DIM};
        color: {ACCENT};
    }}
    .voice-status-off {{
        background: {GRANTS_DIM};
        color: {WARN};
    }}
    </style>
    """)

apply_custom_css()
apply_custom_css()

OPTION_MENU_STYLE = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": ACCENT, "font-size": "16px"},
    "nav-link": {"font-size": "14px", "text-align": "left", "color": TEXT, "--hover-color": PANEL2},
    "nav-link-selected": {"background-color": ORBIT_DIM, "color": TEXT},
}


# ==================== REGISTRATION PAGE ====================

def show_registration():
    st.html("""
        <div class="main-header">
            <h1>📝 Create Your Account</h1>
            <p>Join AgroIntel and start managing your farm intelligently</p>
        </div>
    """)

    with st.form("registration_form"):
        st.markdown("### 👤 Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username *", placeholder="Choose a unique username", autocomplete="username")
            full_name = st.text_input("Full Name *", placeholder="John Doe", autocomplete="name")
            email = st.text_input("Email *", placeholder="john@example.com", autocomplete="email")
            phone = st.text_input("Phone Number", placeholder="+1 234 567 8900", autocomplete="tel")
        with col2:
            password = st.text_input("Password *", type="password", placeholder="Minimum 6 characters", autocomplete="new-password")
            confirm_password = st.text_input("Confirm Password *", type="password", autocomplete="new-password")

        st.markdown("---")
        st.markdown("### 📍 Address Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            address = st.text_area("Address", placeholder="Street address", height=80)
        with col2:
            city = st.text_input("City", placeholder="Your city", autocomplete="address-level2")
            state = st.text_input("State/Province", placeholder="Your state", autocomplete="address-level1")
        with col3:
            postal_code = st.text_input("Postal Code", placeholder="12345", autocomplete="postal-code")
            country = st.text_input("Country", placeholder="Your country", autocomplete="country")

        st.markdown("---")
        st.markdown("### 🚜 Farm Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            farm_name = st.text_input("Farm Name", placeholder="Sunset Farm", autocomplete="off")
        with col2:
            farm_size = st.number_input("Farm Size (acres)", min_value=0.0, step=1.0)
        with col3:
            farm_type = st.selectbox("Farm Type", ["Select...", "Crop", "Livestock", "Mixed", "Organic", "Dairy", "Poultry", "Other"])

        st.markdown("---")
        st.markdown("*Required fields")
        submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)

        if submitted:
            errors = []
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters")
            if not full_name:
                errors.append("Full name is required")
            if not email or '@' not in email:
                errors.append("Invalid email address")
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters")
            if password != confirm_password:
                errors.append("Passwords do not match")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                success, message = db.create_user(
                    username=username, password=password, email=email, phone=phone,
                    full_name=full_name, address=address, city=city, state=state,
                    country=country, postal_code=postal_code, farm_name=farm_name,
                    farm_size=farm_size, farm_type=farm_type
                )
                if success:
                    st.success("✅ Account created successfully! Please login.")
                    st.balloons()
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f"❌ {message}")


# ==================== PROFILE PAGE ====================

def show_profile():
    user = db.get_user_by_id(st.session_state.user_id)
    if not user:
        st.error("User not found")
        return

    st.html(f"""
        <div class="main-header">
            <h1>👤 My Profile</h1>
            <p>Welcome back, {user['full_name']}!</p>
        </div>
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.html('<div class="data-entry-card"><h3>👤 Personal Information</h3>')
        st.write(f"**Full Name:** {user['full_name']}")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Phone:** {user['phone'] or 'Not set'}")
        st.html("</div>")
    with col2:
        st.html('<div class="data-entry-card"><h3>📍 Address Information</h3>')
        st.write(f"**Address:** {user['address'] or 'Not set'}")
        st.write(f"**City:** {user['city'] or 'Not set'}")
        st.write(f"**State:** {user['state'] or 'Not set'}")
        st.write(f"**Country:** {user['country'] or 'Not set'}")
        st.write(f"**Postal Code:** {user['postal_code'] or 'Not set'}")
        st.html("</div>")

    col1, _ = st.columns(2)
    with col1:
        st.html('<div class="data-entry-card"><h3>🚜 Farm Information</h3>')
        st.write(f"**Farm Name:** {user['farm_name'] or 'Not set'}")
        st.write(f"**Farm Size:** {user['farm_size'] or 0} acres")
        st.write(f"**Farm Type:** {user['farm_type'] or 'Not set'}")
        st.html("</div>")


# ==================== DASHBOARD PAGE ====================

def show_dashboard(data):
    st.html(f"""
        <div class="main-header">
            <h1>🌾 AgroIntel Dashboard</h1>
            <p>Welcome back! Here's your farm overview for {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.html(f"""<div class="metric-card"><div class="metric-label">🌱 Total Acres</div>
            <div class="metric-value">{data['total_acres']:,.0f}</div>
            <div class="metric-sub">acres under cultivation</div></div>""")
    with col2:
        st.html(f"""<div class="metric-card"><div class="metric-label">📊 Average Yield</div>
            <div class="metric-value">{data['avg_yield']} t/ha</div>
            <div class="metric-sub">across all fields</div></div>""")
    with col3:
        st.html(f"""<div class="metric-card"><div class="metric-label">🚜 Active Machinery</div>
            <div class="metric-value">{data['active_machinery']}/{data['total_machinery']}</div>
            <div class="metric-sub">units operational</div></div>""")
    with col4:
        st.html(f"""<div class="metric-card"><div class="metric-label">📋 Compliance Score</div>
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-sub">overall compliance rating</div></div>""")

    if data['fields']:
        col1, col2 = st.columns(2)
        with col1:
            st.html('<div class="section-title">📊 Yield by Field</div>')
            df_fields = pd.DataFrame(data['fields'])
            fig = px.bar(df_fields, x='name', y='yield', color='crop', text='yield',
                         color_discrete_sequence=CHART_SEQUENCE)
            fig.update_traces(texttemplate='%{text:.1f} t/ha', textposition='outside')
            fig.update_layout(xaxis_title='', yaxis_title='Yield (t/ha)')
            st.plotly_chart(plotly_dark(fig, height=350), use_container_width=True)
        with col2:
            st.html('<div class="section-title">🌾 Crop Distribution</div>')
            df_fields = pd.DataFrame(data['fields'])
            fig = px.pie(df_fields, values='acres', names='crop', color_discrete_sequence=CHART_SEQUENCE)
            st.plotly_chart(plotly_dark(fig, height=350), use_container_width=True)
    else:
        st.info("No field data available. Add your first field in Farm Management!")

    if data['ai_recommendations']:
        st.html('<div class="section-title">🤖 AI-Powered Insights</div>')
        cols = st.columns(min(3, len(data['ai_recommendations'])))
        for idx, recommendation in enumerate(data['ai_recommendations'][:3]):
            with cols[idx % 3]:
                st.html(f"""
                    <div class="ai-card">
                        <h4>{recommendation['title']}</h4>
                        <p><strong>{recommendation['field']}</strong></p>
                        <p>{recommendation['recommendation']}</p>
                        <span class="confidence">ROI: {recommendation['roi']}</span>
                        <span class="confidence" style="margin-left:0.5rem;">Confidence: {recommendation['confidence']}%</span>
                    </div>
                """)


# ==================== FARM MANAGEMENT PAGE ====================

def show_farm_management(data):
    st.html('<div class="main-header"><h1>🚜 Farm Management</h1></div>')

    with st.expander("➕ Add New Field", expanded=False):
        with st.form("add_field_form"):
            st.markdown("### 🌱 Add New Field")
            col1, col2 = st.columns(2)
            with col1:
                field_id = st.text_input("Field ID *", placeholder="e.g., F6", autocomplete="off")
                field_name = st.text_input("Field Name *", placeholder="e.g., South Field", autocomplete="off")
                crop_type = st.selectbox("Crop Type", ["Winter Wheat", "Corn", "Soybeans", "Barley", "Potatoes", "Oats", "Sunflowers", "Other"])
                acres = st.number_input("Acres *", min_value=0.0, step=0.5)
            with col2:
                yield_tons = st.number_input("Yield (tons/ha)", min_value=0.0, step=0.1)
                soil_health = st.slider("Soil Health Score", 0, 100, 75)
                planting_date = st.date_input("Planting Date")
                harvest_date = st.date_input("Harvest Date")

            submitted = st.form_submit_button("🌱 Add Field", use_container_width=True)
            if submitted:
                if field_id and field_name and acres > 0:
                    success, message = db.add_field(
                        st.session_state.user_id, field_id, field_name, crop_type, acres,
                        yield_tons, soil_health,
                        planting_date.strftime('%Y-%m-%d') if planting_date else None,
                        harvest_date.strftime('%Y-%m-%d') if harvest_date else None
                    )
                    if success:
                        st.success(f"✅ Field '{field_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")

    st.html('<div class="section-title">📋 Your Fields</div>')
    if data['fields']:
        df_fields = pd.DataFrame(data['fields'])
        st.dataframe(df_fields, use_container_width=True)

        st.markdown("### 🗑️ Delete Field")
        field_to_delete = st.selectbox("Select field to delete",
                                        options=[f"{f['name']} ({f['id']})" for f in data['fields']],
                                        key="delete_field_select")
        if st.button("🗑️ Delete Selected Field"):
            field_id = field_to_delete.split('(')[-1].replace(')', '')
            if db.delete_field(st.session_state.user_id, field_id):
                st.success("✅ Field deleted successfully!")
                st.rerun()
    else:
        st.info("No fields added yet. Use the 'Add New Field' section above!")


# ==================== MACHINERY PAGE ====================

def show_machinery(data):
    st.html('<div class="main-header"><h1>⚙️ Machinery Management</h1></div>')

    with st.expander("➕ Add New Machinery", expanded=False):
        with st.form("add_machinery_form"):
            st.markdown("### 🚜 Add New Machinery")
            col1, col2 = st.columns(2)
            with col1:
                machine_id = st.text_input("Machine ID *", placeholder="e.g., M5", autocomplete="off")
                machine_name = st.text_input("Machine Name *", placeholder="e.g., John Deere 6120", autocomplete="off")
                machine_type = st.selectbox("Machine Type", ["Tractor", "Combine", "Sprayer", "Plow", "Drill", "Harvester", "Other"])
                operating_hours = st.number_input("Operating Hours", min_value=0, step=1)
            with col2:
                fuel_level = st.slider("Fuel Level (%)", 0, 100, 50)
                status = st.selectbox("Status", ["Active", "Maintenance", "Idle", "Broken"])
                last_maintenance = st.date_input("Last Maintenance Date")
                next_maintenance = st.date_input("Next Maintenance Date")

            submitted = st.form_submit_button("🚜 Add Machinery", use_container_width=True)
            if submitted:
                if machine_id and machine_name:
                    success, message = db.add_machinery(
                        st.session_state.user_id, machine_id, machine_name, machine_type,
                        operating_hours, fuel_level, status,
                        last_maintenance.strftime('%Y-%m-%d') if last_maintenance else None,
                        next_maintenance.strftime('%Y-%m-%d') if next_maintenance else None
                    )
                    if success:
                        st.success(f"✅ Machinery '{machine_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")

    st.html('<div class="section-title">📋 Your Machinery</div>')
    if data['machinery']:
        df_machinery = pd.DataFrame(data['machinery'])
        st.dataframe(df_machinery, use_container_width=True)

        st.markdown("### 🗑️ Delete Machinery")
        machine_to_delete = st.selectbox("Select machinery to delete",
                                          options=[f"{m['name']} ({m['id']})" for m in data['machinery']],
                                          key="delete_machine_select")
        if st.button("🗑️ Delete Selected Machinery"):
            machine_id = machine_to_delete.split('(')[-1].replace(')', '')
            if db.delete_machinery(st.session_state.user_id, machine_id):
                st.success("✅ Machinery deleted successfully!")
                st.rerun()
    else:
        st.info("No machinery added yet. Use the 'Add New Machinery' section above!")


# ==================== SOIL ANALYSIS PAGE ====================

def show_soil_analysis(data):
    st.html('<div class="main-header"><h1>🧪 Soil Analysis</h1></div>')

    with st.expander("➕ Add Soil Analysis", expanded=False):
        with st.form("add_soil_form"):
            st.markdown("### 🧪 Add New Soil Analysis")
            col1, col2 = st.columns(2)
            with col1:
                field_options = [f['id'] for f in data['fields']] if data['fields'] else []
                if field_options:
                    field_id = st.selectbox("Field ID", options=field_options)
                    ph = st.slider("pH Level", 0.0, 14.0, 6.5, 0.1)
                    nitrogen = st.number_input("Nitrogen (mg/kg)", min_value=0.0, step=0.1)
                else:
                    st.warning("Please add fields first before adding soil analysis!")
                    field_id = None
                    ph = 6.5
                    nitrogen = 0.0
            with col2:
                phosphorus = st.number_input("Phosphorus (mg/kg)", min_value=0.0, step=0.1)
                potassium = st.number_input("Potassium (mg/kg)", min_value=0.0, step=0.1)
                organic_matter = st.slider("Organic Matter (%)", 0.0, 10.0, 3.0, 0.1)

            submitted = st.form_submit_button("🧪 Add Soil Analysis", use_container_width=True)
            if submitted and field_options:
                success = db.add_soil_analysis(st.session_state.user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter)
                if success:
                    st.success("✅ Soil analysis added successfully!")
                    st.rerun()
            elif submitted and not field_options:
                st.error("❌ Please add a field first!")

    st.html('<div class="section-title">📋 Soil Analysis Data</div>')
    if data['soil']:
        st.dataframe(pd.DataFrame(data['soil']), use_container_width=True)
    else:
        st.info("No soil analysis data available. Add some using the section above!")


# ==================== FARM WEATHER LOG PAGE ====================

def show_weather(data):
    st.html('<div class="main-header"><h1>🌤️ Farm Weather Log</h1><p>Historical weather logged for your farm records</p></div>')

    if data['weather'] and len(data['weather']) > 0:
        latest = data['weather'][-1]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌡️ Temperature", f"{latest['temperature']}°C")
        with col2:
            st.metric("💧 Humidity", f"{latest['humidity']}%")
        with col3:
            st.metric("🌧️ Rainfall", f"{latest['rainfall']} mm")
        with col4:
            st.metric("💨 Wind", f"{latest['wind_speed']} km/h")

        df_weather = pd.DataFrame(data['weather'])
        fig = px.line(df_weather, x='date', y=['temperature', 'humidity', 'rainfall', 'wind_speed'],
                      title='Weather Trends (30 Days)', color_discrete_sequence=CHART_SEQUENCE)
        st.plotly_chart(plotly_dark(fig, height=400), use_container_width=True)
    else:
        st.info("No weather data available")

    st.info("💡 Looking for **live** satellite and current-conditions data instead of logged history? Check the **🛰️ Field Intelligence** tab.")


# ==================== COMPLIANCE PAGE ====================

def show_compliance(data):
    st.html('<div class="main-header"><h1>📋 Compliance & Reporting</h1></div>')
    st.html(f"""
        <div class="metric-card">
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-label">Overall Compliance Score</div>
        </div>
    """)

    if data['compliance']:
        st.dataframe(pd.DataFrame(data['compliance']), use_container_width=True)
    else:
        st.info("No compliance data available")


# ==================== AI COPILOT PAGE (FULLY FIXED) ====================

def show_ai_copilot(data):
    st.html("""
        <div class="main-header">
            <h1>🤖 AI Copilot</h1>
            <p>Get predictive, explainable, and actionable guidance for your farm</p>
        </div>
    """)

    groq_key = os.getenv('GROQ_API_KEY', '')
    if groq_key:
        st.html('<div class="api-status connected">🟢 <strong>AI Connected</strong> - Powered by Groq AI (FREE)</div>')
    else:
        st.html('<div class="api-status disconnected">🟡 <strong>AI Disconnected</strong> - Click "Get FREE Groq API Key" below to enable</div>')

    st.html("""
        <div class="ai-card">
            <h4>💬 Ask AgroIntel AI</h4>
            <p>Get predictive, explainable, and actionable guidance for your farm</p>
            <p style="font-size:0.9rem; color:#7F9482; margin-top:0.5rem;">
                💡 Try asking: "What should I plant next season?" or "How is my farm performing?"
            </p>
        </div>
    """)

    # ============================================================
    # VOICE TOGGLE
    # ============================================================
    st.markdown("### 🔊 Voice Settings")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        voice_status = "🔊 ON" if st.session_state.voice_enabled else "🔇 OFF"
        st.caption(f"Voice output: **{voice_status}**")

    with col2:
        if st.button("🔊 Enable Voice", use_container_width=True, key="enable_voice"):
            st.session_state.voice_enabled = True
            st.rerun()

    with col3:
        if st.button("🔇 Disable Voice", use_container_width=True, key="disable_voice"):
            st.session_state.voice_enabled = False
            st.rerun()

    if st.session_state.voice_enabled:
        st.success("✅ Voice output is **ENABLED** - AI responses will be spoken aloud")
    else:
        st.warning("⚠️ Voice output is **DISABLED** - Click 'Enable Voice' to turn it on")

    st.markdown("---")

    # Quick action buttons
    st.markdown("### 🔥 Quick Questions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🌾 Crop Advice", use_container_width=True, key="crop_advice"):
            st.session_state.ai_question = "What crops should I plant next season?"
            st.session_state.ask_ai = True
            st.rerun()
    with col2:
        if st.button("📊 Farm Performance", use_container_width=True, key="farm_performance"):
            st.session_state.ai_question = "How is my farm performing overall?"
            st.session_state.ask_ai = True
            st.rerun()
    with col3:
        if st.button("🚜 Machinery Health", use_container_width=True, key="machinery_health"):
            st.session_state.ai_question = "What maintenance do my machines need?"
            st.session_state.ask_ai = True
            st.rerun()
    with col4:
        if st.button("💰 Profit Optimization", use_container_width=True, key="profit_optimization"):
            st.session_state.ai_question = "How can I increase my farm profits?"
            st.session_state.ask_ai = True
            st.rerun()

    st.markdown("---")

    if not groq_key:
        with st.expander("🔑 Get FREE Groq API Key", expanded=False):
            st.html("""
                ### 🆓 Get Your Free Groq API Key (No Credit Card Required)
                1. Go to <a href="https://console.groq.com/" target="_blank">Groq Console</a>
                2. Sign up with your email (free)
                3. Go to API Keys section
                4. Click "Create API Key"
                5. Copy and paste it below

                🔑 <strong>Pro Tip:</strong> Groq gives you 30 requests per minute for free!
            """)
            api_key = st.text_input("Enter your Groq API Key:", type="password", key="groq_api_key_input", autocomplete="off")
            if st.button("💾 Save API Key", key="save_api_key"):
                if api_key:
                    os.environ['GROQ_API_KEY'] = api_key
                    st.success("✅ API Key saved for this session!")
                    st.rerun()
                else:
                    st.error("❌ Please enter a valid API key")

    # Chat input
    st.markdown("### ✍️ Ask a Question")

    with st.form(key="ai_question_form", clear_on_submit=True):
        user_question = st.text_input(
            "Type your question here:",
            placeholder="e.g., Which field is most profitable? What should I do about low soil nitrogen?",
            key="ai_question_input",
            label_visibility="collapsed",
            autocomplete="off"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("🤖 Ask AI (FREE)", use_container_width=True)

    # Process question
    question_to_process = None

    if st.session_state.get('ask_ai', False):
        question_to_process = st.session_state.get('ai_question', '')
        st.session_state.ask_ai = False

    elif submit_button and user_question:
        question_to_process = user_question

    if question_to_process:
        st.markdown("---")

        with st.spinner("🤔 Analyzing your farm data with AI..."):
            try:
                ai = ai_service.GroqAIService()
                result = ai.get_farm_analysis(question_to_process, data)

                st.markdown("### 🤖 AI Response")

                if result['success']:
                    st.caption(f"⚡ Powered by: {result.get('source', 'Groq AI')} (FREE)")

                    response_text = result['response']

                    # Clean HTML tags and entities out of the AI's raw response
                    cleaned_response = re.sub(r'<[^>]+>', '', response_text)
                    cleaned_response = re.sub(r'\n\s*\n', '\n\n', cleaned_response)
                    cleaned_response = cleaned_response.strip()

                    cleaned_response = cleaned_response.replace('&nbsp;', ' ')
                    cleaned_response = cleaned_response.replace('&amp;', '&')
                    cleaned_response = cleaned_response.replace('&lt;', '<')
                    cleaned_response = cleaned_response.replace('&gt;', '>')

                    st.session_state.ai_response = cleaned_response

                    # FIXED: render markdown content in its own st.markdown() call,
                    # inside a bordered container, instead of embedding it inside
                    # a raw HTML <div> string (which broke on blank lines).
                    with st.container(border=True):
                        st.markdown("#### 💡 AI Analysis")
                        st.markdown(cleaned_response)

                    # Voice output
                    if st.session_state.voice_enabled and cleaned_response:
                        voice_html = get_voice_html(cleaned_response)
                        st.components.v1.html(voice_html, height=70)

                        auto_play_js = f"""
                        <script>
                        (function() {{
                            var text = {repr(cleaned_response)};
                            var utterance = new SpeechSynthesisUtterance(text);
                            utterance.lang = 'en-US';
                            utterance.rate = 0.9;
                            utterance.pitch = 1;
                            utterance.volume = 1;
                            window.speechSynthesis.cancel();
                            window.speechSynthesis.speak(utterance);
                        }})();
                        </script>
                        """
                        st.components.v1.html(auto_play_js, height=0)
                    elif not st.session_state.voice_enabled:
                        st.info("🔇 Voice output is disabled. Click 'Enable Voice' above to hear responses.")

                else:
                    st.warning(f"⚠️ {result.get('error', 'AI error occurred')}")
                    st.info("💡 Using offline analysis...")

                    response_text = result['response']
                    cleaned_response = re.sub(r'<[^>]+>', '', response_text)
                    cleaned_response = re.sub(r'\n\s*\n', '\n\n', cleaned_response)
                    cleaned_response = cleaned_response.strip()

                    with st.container(border=True):
                        st.markdown("#### 💡 Analysis (Offline Mode)")
                        st.markdown(cleaned_response)

                    if st.session_state.voice_enabled and cleaned_response:
                        voice_html = get_voice_html(cleaned_response)
                        st.components.v1.html(voice_html, height=70)

                        auto_play_js = f"""
                        <script>
                        (function() {{
                            var text = {repr(cleaned_response)};
                            var utterance = new SpeechSynthesisUtterance(text);
                            utterance.lang = 'en-US';
                            utterance.rate = 0.9;
                            utterance.pitch = 1;
                            utterance.volume = 1;
                            window.speechSynthesis.cancel();
                            window.speechSynthesis.speak(utterance);
                        }})();
                        </script>
                        """
                        st.components.v1.html(auto_play_js, height=0)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please try again or check your API key.")

        if 'ai_question' in st.session_state:
            st.session_state.ai_question = ''

        show_related_data(question_to_process, data)

def show_related_data(question, data):
    question_lower = question.lower()
    st.markdown("### 📊 Related Data")

    if any(word in question_lower for word in ['crop', 'field', 'yield']):
        if data['fields']:
            st.dataframe(pd.DataFrame(data['fields']), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Acres", f"{data['total_acres']:.0f}")
            with col2:
                st.metric("Avg Yield", f"{data['avg_yield']} t/ha")
        else:
            st.info("No field data available")
    elif any(word in question_lower for word in ['machinery', 'tractor', 'maintenance']):
        if data['machinery']:
            st.dataframe(pd.DataFrame(data['machinery']), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Equipment", len(data['machinery']))
            with col2:
                active = sum(1 for m in data['machinery'] if m['status'] == 'Active')
                st.metric("Active", f"{active}/{len(data['machinery'])}")
        else:
            st.info("No machinery data available")
    elif any(word in question_lower for word in ['soil', 'nutrient', 'fertilizer']):
        if data['soil']:
            st.dataframe(pd.DataFrame(data['soil']), use_container_width=True)
        else:
            st.info("No soil analysis data available")
    elif any(word in question_lower for word in ['weather', 'rain', 'temperature']):
        if data['weather']:
            st.dataframe(pd.DataFrame(data['weather']), use_container_width=True)
        else:
            st.info("No weather data available")


# ==================== FIELD INTELLIGENCE (NASA / OpenWeather / RVO) ====================

def show_field_intelligence():
    st.html("""
        <div class="main-header">
            <h1>🛰️ Field Intelligence</h1>
            <p>Satellite climatology from orbit, live atmosphere overhead, funding on the ground.</p>
        </div>
    """)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛰️  ORBIT — NASA POWER", key="btn_orbit", use_container_width=True):
            st.session_state.layer = "orbit"
    with c2:
        if st.button("☁️  ATMOSPHERE — OpenWeather", key="btn_atmos", use_container_width=True):
            st.session_state.layer = "atmosphere"
    with c3:
        if st.button("🏛️  GRANTS — RVO NL", key="btn_grants", use_container_width=True):
            st.session_state.layer = "grants"

    st.html("<div style='height: 0.6rem'></div>")

    if st.session_state.layer == "orbit":
        _render_orbit()
    elif st.session_state.layer == "atmosphere":
        _render_atmosphere()
    else:
        _render_grants()


def _render_orbit():
    st.html('<span class="layer-tag tag-orbit">Satellite · Reanalysis · Agroclimatology</span>')

    colA, colB, colC, colD = st.columns([1, 1, 1, 1])
    with colA:
        lat = st.number_input("Latitude", value=20.0059, format="%.4f")
    with colB:
        lon = st.number_input("Longitude", value=73.7910, format="%.4f")
    with colC:
        days = st.slider("Days of history", 3, 21, 10)
    with colD:
        st.write("")
        st.write("")
        fetch_clicked = st.button("Read orbit data", key="fetch_orbit", use_container_width=True)

    first_load = "orbit_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Pulling satellite readings..."):
            try:
                end = safe_end_date()
                start = (datetime.strptime(end, "%Y%m%d") - timedelta(days=days - 1)).strftime("%Y%m%d")
                rows = get_agro_weather_flat(lat, lon, start, end)
                st.session_state.orbit_data = rows
            except Exception as e:
                st.error(f"Orbit read failed: {e}")
                return

    rows = st.session_state.get("orbit_data")
    if not rows:
        st.info("Set coordinates and hit **Read orbit data**.")
        return

    df = pd.DataFrame(rows).replace(-999.0, pd.NA)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.dropna(subset=["T2M"])
    if df.empty:
        st.warning("No processed data yet for this window — NASA POWER lags a few days behind real-time. Try a shorter history.")
        return
    latest = df.iloc[-1]

    s1, s2, s3, s4, s5 = st.columns(5)
    for col, label, value, sub in [
        (s1, "Temp (avg)", f"{latest['T2M']:.1f}°C", f"{latest['T2M_MIN']:.0f}° / {latest['T2M_MAX']:.0f}°"),
        (s2, "Rainfall", f"{latest['PRECTOTCORR']:.1f} mm", "last processed day"),
        (s3, "Humidity", f"{latest['RH2M']:.0f}%", "relative, 2m"),
        (s4, "Solar", f"{latest['ALLSKY_SFC_SW_DWN']:.1f}", "kWh/m²/day"),
        (s5, "Root wetness", f"{latest['GWETROOT']:.2f}", "0 dry – 1 sat."),
    ]:
        with col:
            st.html(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value">{value}</div><div class="snap-sub">{sub}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(x=df["date"], y=df["T2M_MAX"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig_temp.add_trace(go.Scatter(x=df["date"], y=df["T2M_MIN"], fill="tonexty", fillcolor="rgba(110,140,224,0.15)",
                                   line=dict(width=0), name="Range", hoverinfo="skip"))
    fig_temp.add_trace(go.Scatter(x=df["date"], y=df["T2M"], line=dict(color=ORBIT, width=3), name="Avg temp",
                                   mode="lines+markers", marker=dict(size=5)))
    fig_temp.update_layout(title=dict(text="Temperature range (°C)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
    st.plotly_chart(plotly_dark(fig_temp), use_container_width=True)

    ct1, ct2 = st.columns(2)
    with ct1:
        fig_rain = go.Figure(go.Bar(x=df["date"], y=df["PRECTOTCORR"], marker_color=ACCENT))
        fig_rain.update_layout(title=dict(text="Rainfall (mm/day)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
        st.plotly_chart(plotly_dark(fig_rain, height=280), use_container_width=True)
    with ct2:
        fig_soil = go.Figure()
        fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETTOP"], name="Surface", line=dict(color=WARN, width=2)))
        fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETROOT"], name="Root zone", line=dict(color=ORBIT, width=2)))
        fig_soil.update_layout(title=dict(text="Soil wetness (0–1)", font=dict(family="Space Grotesk", color=TEXT, size=15)), yaxis_range=[0, 1])
        st.plotly_chart(plotly_dark(fig_soil, height=280), use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


def _render_atmosphere():
    st.html('<span class="layer-tag tag-atmos">Live conditions</span>')

    colA, colB = st.columns([3, 1])
    with colA:
        city = st.text_input("City", value="Nashik", autocomplete="address-level2")
    with colB:
        st.write("")
        st.write("")
        fetch_clicked = st.button("Read atmosphere", key="fetch_atmos", use_container_width=True)

    first_load = "atmos_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Checking overhead conditions..."):
            try:
                data = get_current_weather(city)
                st.session_state.atmos_data = data
            except Exception as e:
                st.error(f"Atmosphere read failed: {e}")
                return

    data = st.session_state.get("atmos_data")
    if not data:
        st.info("Enter a city and hit **Read atmosphere**.")
        return

    main = data.get("main", {})
    wind = data.get("wind", {})
    weather = (data.get("weather") or [{}])[0]
    icon = weather.get("icon", "01d")
    temp = main.get("temp", 0)
    humidity = main.get("humidity", 0)
    wind_speed = wind.get("speed", 0)
    clouds = data.get("clouds", {}).get("all", 0)

    top1, top2 = st.columns([1, 3])
    with top1:
        st.image(f"https://openweathermap.org/img/wn/{icon}@4x.png", width=140)
    with top2:
        st.html(f"""
        <div class="snap-value" style="font-size:3rem">{temp}<span style="font-size:1.3rem;color:{MUTED}">°C</span></div>
        <div class="snap-sub" style="font-size:1rem">{weather.get('description','').title()} · feels like {main.get('feels_like','—')}°C</div>
        <div class="snap-sub">{data.get('name','')}, {data.get('sys',{}).get('country','')}</div>
        """)

    st.html("<div style='height:1rem'></div>")

    m1, m2, m3, m4 = st.columns(4)
    for col, label, value, sub in [
        (m1, "Humidity", f"{humidity}%", "relative"),
        (m2, "Pressure", f"{main.get('pressure','—')}", "hPa"),
        (m3, "Wind", f"{wind_speed}", "m/s"),
        (m4, "Cloud cover", f"{clouds}%", "sky coverage"),
    ]:
        with col:
            st.html(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value">{value}</div><div class="snap-sub">{sub}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    g1, g2 = st.columns(2)
    with g1:
        fig_h = go.Figure(go.Indicator(
            mode="gauge+number", value=humidity,
            title={"text": "Humidity %", "font": {"family": "Space Grotesk", "color": TEXT, "size": 14}},
            number={"font": {"family": "IBM Plex Mono", "color": TEXT}},
            gauge={"axis": {"range": [0, 100], "tickcolor": MUTED}, "bar": {"color": ATMOS}, "bgcolor": PANEL2, "borderwidth": 0},
        ))
        st.plotly_chart(plotly_dark(fig_h, height=260), use_container_width=True)
    with g2:
        fig_c = go.Figure(go.Indicator(
            mode="gauge+number", value=clouds,
            title={"text": "Cloud cover %", "font": {"family": "Space Grotesk", "color": TEXT, "size": 14}},
            number={"font": {"family": "IBM Plex Mono", "color": TEXT}},
            gauge={"axis": {"range": [0, 100], "tickcolor": MUTED}, "bar": {"color": ACCENT}, "bgcolor": PANEL2, "borderwidth": 0},
        ))
        st.plotly_chart(plotly_dark(fig_c, height=260), use_container_width=True)


def _render_grants():
    st.html('<span class="layer-tag tag-grants">Netherlands Enterprise Agency · Open Data</span>')

    colA, colB = st.columns([3, 1])
    with colA:
        st.caption("Dutch government funding schemes open to agricultural businesses — no auth required, pulled live from RVO's open data API.")
    with colB:
        fetch_clicked = st.button("Read grants", key="fetch_grants", use_container_width=True)

    first_load = "grants_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Checking in with RVO..."):
            try:
                items = get_agri_subsidies()
                st.session_state.grants_data = items
            except Exception as e:
                st.error(f"Grants read failed: {e}")
                return

    items = st.session_state.get("grants_data")
    if not items:
        st.info("Hit **Read grants** to pull the latest agricultural funding schemes.")
        return

    s1, s2, s3 = st.columns(3)
    subject_counts = {}
    for item in items:
        for subj in item.get("subjects", []):
            subject_counts[subj] = subject_counts.get(subj, 0) + 1
    top_subject = max(subject_counts, key=subject_counts.get) if subject_counts else "—"

    for col, label, value, sub in [
        (s1, "Schemes found", str(len(items)), "matching agricultural sector"),
        (s2, "Top category", top_subject, f"{subject_counts.get(top_subject, 0)} schemes"),
        (s3, "Source", "RVO.nl", "open data, live"),
    ]:
        with col:
            st.html(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value" style="font-size:1.4rem">{value}</div>
                <div class="snap-sub">{sub}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    if subject_counts:
        sorted_items = sorted(subject_counts.items(), key=lambda x: x[1])
        fig = go.Figure(go.Bar(x=[v for _, v in sorted_items], y=[k for k, _ in sorted_items],
                                orientation="h", marker_color=GRANTS))
        fig.update_layout(title=dict(text="Schemes by category", font=dict(family="Space Grotesk", color=TEXT, size=15)))
        st.plotly_chart(plotly_dark(fig, height=max(220, 40 * len(subject_counts))), use_container_width=True)

    st.html("<div style='height:0.6rem'></div>")

    tcol1, tcol2 = st.columns([3, 1])
    with tcol1:
        search = st.text_input("Filter by keyword", placeholder="e.g. mest, energie, krediet", autocomplete="off")
    with tcol2:
        st.write("")
        if TRANSLATE_AVAILABLE:
            translate_on = st.toggle("🌐 Translate to English", key="translate_grants")
        else:
            translate_on = False
            st.caption("Install `deep-translator` to enable translation.")

    filtered = items
    if search:
        s = search.lower()
        filtered = [i for i in items if s in i["title"].lower() or s in i.get("intro", "").lower()]

    if "translation_cache" not in st.session_state:
        st.session_state.translation_cache = {}

    def translated(item):
        if not translate_on:
            return item["title"], item.get("intro", "")
        cache = st.session_state.translation_cache
        item_id = item["id"]
        if item_id in cache:
            return cache[item_id]["title"], cache[item_id]["intro"]
        try:
            translator = GoogleTranslator(source="nl", target="en")
            title_en = translator.translate(item["title"])
            intro_en = translator.translate(item.get("intro", "")[:400])
            cache[item_id] = {"title": title_en, "intro": intro_en}
            return title_en, intro_en
        except Exception:
            return item["title"], item.get("intro", "")

    if translate_on:
        with st.spinner("Translating..."):
            for item in filtered:
                title, intro = translated(item)
                st.html(f"""<div class="subsidy-card"><div class="subsidy-title">{title}</div>
                    <div class="subsidy-intro">{intro[:220].rsplit(' ', 1)[0]}...</div>
                    <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a></div>""")
    else:
        for item in filtered:
            st.html(f"""<div class="subsidy-card"><div class="subsidy-title">{item['title']}</div>
                <div class="subsidy-intro">{item.get('intro', '')[:220].rsplit(' ', 1)[0]}...</div>
                <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a></div>""")

    if not filtered:
        st.caption("No schemes match that filter.")


# ==================== FARM MAP (Digital Twin) ====================

def _yield_to_color(value, low, high):
    if value is None or high is None or low is None or high <= low:
        return DEFAULT_CROP_COLOR

    t = max(0.0, min(1.0, (value - low) / (high - low)))

    low_rgb = (224, 169, 62)
    high_rgb = (143, 209, 79)

    r = int(low_rgb[0] + (high_rgb[0] - low_rgb[0]) * t)
    g = int(low_rgb[1] + (high_rgb[1] - low_rgb[1]) * t)
    b = int(low_rgb[2] + (high_rgb[2] - low_rgb[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _field_polygon(center_lat, center_lon, acres, aspect=1.15):
    acre_to_m2 = 4046.86
    area_m2 = max(acres, 0.5) * acre_to_m2
    width_m = math.sqrt(area_m2 * aspect)
    height_m = math.sqrt(area_m2 / aspect)

    dlat = (height_m / 2) / 111320
    dlon = (width_m / 2) / (111320 * math.cos(math.radians(center_lat)))

    return [
        [center_lat - dlat, center_lon - dlon],
        [center_lat - dlat, center_lon + dlon],
        [center_lat + dlat, center_lon + dlon],
        [center_lat + dlat, center_lon - dlon],
    ]


def build_field_map(fields, center_lat, center_lon):
    n = len(fields)
    cols = math.ceil(math.sqrt(n)) if n else 1
    spacing_lat = 0.0075
    spacing_lon = 0.0095

    yields = [float(f.get("yield") or 0) for f in fields if f.get("yield")]
    low_yield = min(yields) if yields else None
    high_yield = max(yields) if yields else None

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Labels",
        overlay=True,
        control=True,
        show=True,
    ).add_to(m)

    folium.TileLayer("CartoDB dark_matter", name="Dark", overlay=False, control=True).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Streets", overlay=False, control=True).add_to(m)

    for idx, field in enumerate(fields):
        row, col = divmod(idx, cols)
        offset_lat = (row - (n - 1) / (2 * cols)) * spacing_lat
        offset_lon = (col - (cols - 1) / 2) * spacing_lon
        f_lat = center_lat + offset_lat
        f_lon = center_lon + offset_lon

        crop = field.get("crop", "Other")
        acres = float(field.get("acres", 1) or 1)
        field_yield = float(field.get("yield") or 0) or None
        color = _yield_to_color(field_yield, low_yield, high_yield)

        polygon = _field_polygon(f_lat, f_lon, acres)

        popup_html = f"""
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #16231A;">
            <b style="font-size:13px;">{field.get('name', 'Field')}</b> ({field.get('id', '')})<br>
            Crop: {crop}<br>
            Acres: {acres:.1f}<br>
            <span style="display:inline-block;width:10px;height:10px;background:{color};
                border-radius:2px;margin-right:4px;"></span>
            Yield: {field.get('yield', '—')} t/ha<br>
            Soil health: {field.get('soil_health', '—')}/100
        </div>
        """

        folium.Polygon(
            locations=polygon,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.55,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{field.get('name', 'Field')} — {field.get('yield', '—')} t/ha",
        ).add_to(m)

        folium.Marker(
            location=[f_lat, f_lon],
            icon=folium.DivIcon(html=f"""
                <div style="font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600;
                    color:#FFFFFF; text-shadow: 0 0 3px #000, 0 0 3px #000; text-align:center;
                    white-space:nowrap; transform:translate(-50%,-50%);">
                    {field.get('name', 'Field')}
                </div>
            """),
        ).add_to(m)

    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomleft").add_to(m)
    folium.LayerControl(position="topleft", collapsed=False).add_to(m)

    return m, low_yield, high_yield


def show_farm_map(data):
    st.html("""
        <div class="main-header">
            <h1>🗺️ Farm Map</h1>
            <p>Digital twin view of your fields — parcels sized by acreage, colored by crop.</p>
        </div>
    """)

    if not MAP_AVAILABLE:
        st.warning("Map libraries not installed. Run `pip install folium streamlit-folium` to enable this page.")
        return

    fields = data.get("fields") or []
    if not fields:
        st.info("No fields yet. Add fields in **Farm Management** first, then come back here to see them mapped.")
        return

    colA, colB = st.columns(2)
    with colA:
        center_lat = st.number_input("Farm center latitude", value=20.0059, format="%.4f")
    with colB:
        center_lon = st.number_input("Farm center longitude", value=73.7910, format="%.4f")

    st.caption(
        "⚠️ Field shapes are estimated (sized to match each field's acreage) since exact "
        "boundary coordinates aren't stored yet — not surveyed GPS boundaries. Set your farm's "
        "actual location above to place them correctly on the satellite image. Use the layer "
        "control (top-left) to switch between satellite, streets, and dark view."
    )

    fmap, low_yield, high_yield = build_field_map(fields, center_lat, center_lon)
    st_folium(fmap, use_container_width=True, height=560)

    if low_yield is not None and high_yield is not None:
        st.html(f"""
        <div style="margin-top:0.8rem; display:flex; align-items:center; gap:0.8rem;">
            <span style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:{MUTED};">
                {low_yield:.1f} t/ha
            </span>
            <div style="flex:1; max-width:260px; height:10px; border-radius:5px;
                background: linear-gradient(90deg, {GRANTS} 0%, {ACCENT} 100%);"></div>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:{MUTED};">
                {high_yield:.1f} t/ha
            </span>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:{MUTED};
                margin-left:0.5rem; text-transform:uppercase; letter-spacing:0.1em;">
                Yield (low → high)
            </span>
        </div>
        """)

    yielded_fields = [f for f in fields if f.get("yield")]
    if yielded_fields:
        best = max(yielded_fields, key=lambda f: float(f["yield"]))
        worst = min(yielded_fields, key=lambda f: float(f["yield"]))
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        colB, colW = st.columns(2)
        with colB:
            st.html(f"""<div class="snap-card" style="border-left:4px solid {ACCENT};">
                <div class="snap-label">🏆 Top performer</div>
                <div class="snap-value" style="font-size:1.3rem;">{best['name']}</div>
                <div class="snap-sub">{best['yield']} t/ha · {best.get('crop','—')}</div></div>""")
        with colW:
            st.html(f"""<div class="snap-card" style="border-left:4px solid {GRANTS};">
                <div class="snap-label">⚠️ Needs attention</div>
                <div class="snap-value" style="font-size:1.3rem;">{worst['name']}</div>
                <div class="snap-sub">{worst['yield']} t/ha · {worst.get('crop','—')}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")
    st.html('<div class="section-title">📋 Fields on this map</div>')
    st.dataframe(pd.DataFrame(fields), use_container_width=True)


# ==================== DATA LOADING ====================

def load_user_data(user_id):
    return {
        'fields': db.get_fields(user_id),
        'machinery': db.get_machinery(user_id),
        'weather': db.get_weather(user_id, 30),
        'soil': db.get_soil_analysis(user_id),
        'compliance': db.get_compliance(user_id),
        'ai_recommendations': db.get_ai_recommendations(user_id),
        'total_acres': db.get_total_acres(user_id),
        'avg_yield': db.get_avg_yield(user_id),
        'active_machinery': db.get_active_machinery_count(user_id),
        'total_machinery': db.get_total_machinery_count(user_id),
        'compliance_score': db.get_compliance_score(user_id)
    }


# ==================== MAIN ====================

def main():
    with st.sidebar:
        st.html("""
            <div class="sidebar-brand">
                <div style="font-size:3rem;">🌾</div>
                <h2>AgroIntel</h2>
                <p>Universal Agricultural Intelligence</p>
            </div>
        """)
        st.markdown("---")

        selected = None

        if st.session_state.authenticated:
            user = db.get_user_by_id(st.session_state.user_id)
            if user:
                st.markdown(f"👋 **Welcome, {user['full_name']}**")
            st.markdown("---")

            selected = option_menu(
                "Navigation",
                ["Dashboard", "🗺️ Farm Map", "Farm Management", "Machinery", "Weather",
                 "Soil Analysis", "Compliance", "🛰️ Field Intelligence", "AI Copilot", "👤 My Profile"],
                icons=["house", "geo-alt", "tractor", "gear", "cloud-sun",
                       "droplet", "clipboard-check", "broadcast", "robot", "person"],
                menu_icon="cast",
                default_index=0,
                styles=OPTION_MENU_STYLE,
            )

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.user_id = None
                st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username", autocomplete="username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password", autocomplete="current-password")
                    submitted = st.form_submit_button("Login", use_container_width=True)
                    if submitted:
                        user = db.get_user(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = user['username']
                            st.session_state.user_id = user['id']
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            with tab2:
                st.markdown("### 📝 New User?")
                if st.button("Create Account", use_container_width=True):
                    st.session_state.page = 'register'
                    st.rerun()

    if st.session_state.authenticated:
        if selected == "🛰️ Field Intelligence":
            show_field_intelligence()
            return

        data = load_user_data(st.session_state.user_id)

        if selected == "👤 My Profile":
            show_profile()
        elif selected == "Dashboard":
            show_dashboard(data)
        elif selected == "🗺️ Farm Map":
            show_farm_map(data)
        elif selected == "Farm Management":
            show_farm_management(data)
        elif selected == "Machinery":
            show_machinery(data)
        elif selected == "Weather":
            show_weather(data)
        elif selected == "Soil Analysis":
            show_soil_analysis(data)
        elif selected == "Compliance":
            show_compliance(data)
        elif selected == "AI Copilot":
            show_ai_copilot(data)
    else:
        if st.session_state.page == 'register':
            show_registration()
        else:
            st.html("""
                <div class="welcome-container">
                    <div class="emoji">🌾</div>
                    <h1>Welcome to AgroIntel</h1>
                    <p>Universal Agricultural Intelligence Platform</p>
                    <p class="sub-text">Please login or create an account to access your dashboard.</p>
                </div>
            """)


if __name__ == "__main__":
    main()