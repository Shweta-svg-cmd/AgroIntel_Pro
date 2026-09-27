"""
AgroIntel — Universal Agricultural Intelligence Platform
------------------------------------------------------------
Merged app:
  - Login / registration / farm management / machinery / soil / compliance /
    AI copilot (originally built against database.py + ai_service_free.py)
  - Field Intelligence: live NASA POWER / OpenWeather / RVO NL dashboard
    (nasapower.py, openweather.py, rvo.py)
  - Ground layer: live John Deere Operations Center data, scoped to the
    APIs actually approved for this app (Organizations, Equipment,
    Machine Locations, Machine Hours Of Operation, Machine Alerts,
    Machine Device State Report, Map Layers, ISO 15143-3). Fields, Farms,
    Boundaries, Users, Assets, Files, and Product are NOT approved and are
    not called here.

Requires in the same folder:
    app_jd.py, database.py, ai_service_free.py,
    nasapower.py, openweather.py, rvo.py, johndeere.py, .env

Run:
    pip install streamlit streamlit-option-menu pandas plotly requests
                python-dotenv deep-translator
    streamlit run app_jd.py
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re
import html
from dotenv import load_dotenv

load_dotenv()

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
    'layer': 'orbit',
    'copilot_messages': [],
    'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
    'ai_suggestions': None,
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
MUTED = "#A8B6A5"
ACCENT = "#8FD14F"
WARN = "#E0965B"
DANGER = "#E0705B"
DEERE = "#E0A93E"
DEERE_DIM = "#4A3A26"

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
    .tag-deere {{ background: {DEERE_DIM}; color: #F0C793; }}
    .tag-soil {{ background: #4A3320; color: #E8B98A; }}
    .tag-cropmon {{ background: #1E4A2A; color: #A9E8BC; }}
    .tag-sat {{ background: #2A2A4A; color: #C3C3F5; }}
    .tag-farmos {{ background: #1E4A44; color: #A9E8DC; }}

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

    .field-guide-hero {{ position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:1.5rem;
        min-height:205px;padding:2.1rem 2.3rem;margin:.2rem 0 1.2rem;border-radius:22px;
        color:{TEXT};background:radial-gradient(ellipse at 85% 120%,rgba(143,209,79,.2),transparent 38%),
        linear-gradient(120deg,#101D15 0%,#173321 56%,#23452B 100%);border:1px solid #304834;box-shadow:0 18px 44px rgba(0,0,0,.22); }}
    .field-guide-hero .hero-copy {{ position:relative;z-index:1;max-width:700px; }}
    .field-guide-hero .eyebrow {{ color:{ACCENT};font:700 .7rem 'IBM Plex Mono',monospace;letter-spacing:.15em;margin-bottom:.75rem; }}
    .field-guide-hero h1 {{ color:#F4F8F0!important;font:700 2.4rem 'Space Grotesk',sans-serif!important;line-height:1.06;margin:0 0 .65rem!important; }}
    .field-guide-hero p {{ color:#A9BDA9;font-size:.98rem;line-height:1.55;margin:0;max-width:620px; }}
    .hero-orbit {{ z-index:1;flex:0 0 112px;width:112px;height:112px;border-radius:50%;display:grid;place-items:center;color:#E9FFD4;font-size:2.1rem;
        background:linear-gradient(145deg,rgba(143,209,79,.2),rgba(143,209,79,.04));border:1px solid #526A43;box-shadow:inset 0 0 25px rgba(143,209,79,.08); }}
    .guide-stat {{ min-height:117px;padding:1rem 1.1rem;border-radius:15px;background:linear-gradient(145deg,{PANEL2},{PANEL});border:1px solid {LINE};box-shadow:0 6px 18px rgba(0,0,0,.12); }}
    .guide-stat .icon {{ font-size:1.22rem; }} .guide-stat .value {{ font:700 1.65rem 'IBM Plex Mono',monospace;color:{TEXT};margin:.35rem 0 .1rem; }}
    .guide-stat .label {{ color:#C1D1BF;font-size:.84rem;font-weight:700; }} .guide-stat .hint {{ color:{MUTED};font-size:.68rem;margin-top:.1rem; }}
    .guide-coverage {{ padding:1rem 1.15rem;border-radius:15px;background:{PANEL};border:1px solid {LINE}; }}
    .guide-coverage-top {{ display:flex;justify-content:space-between;gap:.8rem;color:#A9BCA9;font-size:.78rem;margin-bottom:.42rem; }}
    .guide-track {{ height:7px;border-radius:9px;background:#26362A;overflow:hidden;margin-bottom:.85rem; }}
    .guide-track:last-child {{ margin-bottom:0; }} .guide-track span {{ display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,#659C46,{ACCENT}); }}
    .guide-cta {{ padding:1rem 1.2rem;border-radius:15px;background:linear-gradient(120deg,#18271B,#1C2F1F);border:1px solid #344A32; }}
    .guide-cta strong {{ color:#E6F2DC;font-size:1rem; }} .guide-cta p {{ color:{MUTED};font-size:.78rem;margin:.28rem 0 0; }}
    .plan-section-label {{ margin:1.5rem 0 .6rem;color:#DAE8D4;font:700 1.12rem 'Space Grotesk',sans-serif; }}
    .plan-card {{ padding:.95rem 1.1rem;margin:.55rem 0;border-radius:14px;background:{PANEL};border:1px solid {LINE};box-shadow:0 7px 20px rgba(0,0,0,.11); }}
    .plan-card.action {{ border-left:3px solid {ACCENT}; }} .plan-card.caution {{ border-left:3px solid {GRANTS};background:#1D1A14; }} .plan-card.gap {{ border-left:3px solid {ATMOS};background:#111B1F; }}
    .plan-card-head {{ display:flex;justify-content:space-between;margin-bottom:.5rem; }} .plan-step {{ color:{MUTED};font:600 .65rem 'IBM Plex Mono',monospace;letter-spacing:.1em; }}
    .plan-priority {{ padding:.18rem .55rem;border-radius:99px;background:#263923;color:{ACCENT};font:600 .64rem 'IBM Plex Mono',monospace; }}
    .plan-card.caution .plan-priority {{ background:{GRANTS_DIM};color:#F0CB87; }} .plan-card.gap .plan-priority {{ background:{ATMOS_DIM};color:#9BD8EF; }}
    .plan-copy {{ color:#BDCCBC;font-size:.87rem;line-height:1.65; }} .plan-copy p {{ margin:.35rem 0; }} .plan-copy ul {{ padding-left:1.1rem;margin:.3rem 0; }}
    .ai-answer-shell {{ padding:.95rem 1rem;border-radius:16px;background:linear-gradient(145deg,{PANEL2},{PANEL});border:1px solid {LINE};margin:.7rem 0; }}
    .ai-answer-head {{ display:flex;align-items:center;gap:.7rem;padding:.1rem .1rem .8rem;border-bottom:1px solid {LINE};margin-bottom:.75rem; }}
    .ai-answer-icon {{ width:38px;height:38px;flex:0 0 38px;border-radius:12px;display:grid;place-items:center;color:#EBFFD7;background:linear-gradient(145deg,#345F35,#779F46);font-size:1.1rem; }}
    .ai-answer-title {{ color:#E6F0E2;font-size:.96rem;font-weight:800; }} .ai-answer-subtitle {{ color:{MUTED};font-size:.7rem;margin-top:.15rem; }}
    .ai-answer-provider {{ margin-left:auto;padding:.25rem .55rem;border:1px solid #354638;border-radius:99px;color:#AFC39F;background:#172219;font:600 .62rem 'IBM Plex Mono',monospace; }}
    .ai-answer-summary {{ padding:.8rem .95rem;margin:.4rem 0 .7rem;border-radius:12px;background:#18251A;border-left:3px solid {ACCENT};color:#D2E2CA;font-size:.9rem;line-height:1.65; }}
    .ai-answer-section-title {{ color:#BDD1B7;font-size:.8rem;font-weight:800;margin:.85rem .1rem .38rem; }}
    .ai-answer-step {{ display:flex;gap:.7rem;align-items:flex-start;padding:.7rem .8rem;margin:.4rem 0;border-radius:12px;background:#111B14;border:1px solid #29372B; }}
    .ai-answer-step-num {{ width:24px;height:24px;flex:0 0 24px;display:grid;place-items:center;border-radius:8px;background:#293B25;color:{ACCENT};font:700 .7rem 'IBM Plex Mono',monospace; }}
    .ai-answer-copy {{ min-width:0;flex:1;color:#B9C9B7;font-size:.83rem;line-height:1.6; }} .ai-answer-copy p {{ margin:.1rem 0 .35rem; }} .ai-answer-copy ul {{ padding-left:1.05rem;margin:.25rem 0; }}

    /* Apply the dark palette to Streamlit's native surfaces and their text. */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"] {{ background:#0E1711!important; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] label {{ color:#E1EADF!important; }}
    [data-testid="stSidebar"] .sidebar-brand h2 {{ background:none!important;-webkit-text-fill-color:#EAF2E6!important;color:#EAF2E6!important; }}
    [data-testid="stSidebar"] .sidebar-brand p {{ color:#A8B6A5!important; }}
    [data-testid="stSidebar"] button, [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button span {{ color:#E1EADF!important;-webkit-text-fill-color:#E1EADF!important; }}
    [data-testid="stSidebar"] hr {{ border-color:#28372B!important; }}
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] li,
    .stApp [data-testid="stMarkdownContainer"] blockquote {{ color:#DCE7D9; }}
    .stApp a {{ color:#A9D779; }} .stApp a:hover {{ color:#D3F1AA; }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{ color:#E9EEE7; }}
    .stApp label, .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] {{ color:#DCE7D9!important; }}
    .stApp [data-testid="stButton"] button,
    .stApp .stButton > button,
    .stApp button[kind="secondary"] {{ color:#E4EDE1!important;-webkit-text-fill-color:#E4EDE1!important; }}
    .stApp [data-testid="stButton"] button *, .stApp .stButton > button * {{ color:#E4EDE1!important;-webkit-text-fill-color:#E4EDE1!important; }}
    .stApp [data-testid="stButton"] button[kind="primary"],
    .stApp .stButton > button[kind="primary"] {{ color:#F7FFF2!important;-webkit-text-fill-color:#F7FFF2!important; }}
    .stApp [data-testid="stButton"] button[kind="primary"] *, .stApp .stButton > button[kind="primary"] * {{ color:#F7FFF2!important;-webkit-text-fill-color:#F7FFF2!important; }}
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{ color:#A8B6A5!important; }}
    [data-testid="stChatMessage"] {{ background:#142017!important;border:1px solid #304033!important;border-radius:14px!important; }}
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {{ color:#E1EADF!important; }}
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{ background:#0A120D!important; }}
    .ai-answer-title {{ color:#F0F7EB!important; }} .ai-answer-subtitle {{ color:#A9BBA6!important; }}
    .ai-answer-provider {{ color:#D2E6C8!important; }} .ai-answer-summary {{ color:#E0EBDD!important; }}
    .ai-answer-section-title {{ color:#D1E3C9!important; }} .ai-answer-copy {{ color:#D0DDCD!important; }}
    .ai-answer-copy p, .ai-answer-copy li {{ color:#D0DDCD!important; }}
    [data-testid="stSidebar"] a.nav-link, [data-testid="stSidebar"] a.nav-link span {{ color:#E1EADF!important;-webkit-text-fill-color:#E1EADF!important; }}
    [data-testid="stSidebar"] a.nav-link-selected, [data-testid="stSidebar"] a.nav-link-selected span {{ color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important; }}
    [data-testid="stSidebar"] button, [data-testid="stSidebar"] button * {{ color:#E1EADF!important;-webkit-text-fill-color:#E1EADF!important; }}
    .stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div,
    .stApp [data-testid="stChatInput"] textarea {{ background:#142017!important;color:#E9EEE7!important;-webkit-text-fill-color:#E9EEE7!important;caret-color:{ACCENT}!important; }}
    .stApp [data-baseweb="select"] *, .stApp [data-testid="stSelectbox"] *,
    .stApp [data-testid="stMultiSelect"] * {{ color:#E9EEE7!important; }}
    .stApp input::placeholder, .stApp textarea::placeholder,
    .stApp [data-testid="stChatInput"] textarea::placeholder {{ color:#A8B6A5!important;-webkit-text-fill-color:#A8B6A5!important;opacity:1!important; }}
    .stApp [data-testid="stChatInput"] button {{ color:#E4F0DC!important; }}
    .stApp [data-testid="stChatInput"] button svg {{ fill:#E4F0DC!important; }}
    .stApp [data-baseweb="popover"], .stApp [data-baseweb="menu"], .stApp [role="listbox"], .stApp [role="option"] {{ background:#142017!important;color:#E9EEE7!important; }}
    .stApp [role="option"] *, .stApp [role="listbox"] * {{ color:#E9EEE7!important; }}
    .stApp [data-testid="stDataFrame"], .stApp [data-testid="stTable"] {{ color:#E0E9DD!important; }}
    .stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricDelta"] {{ color:#B8C7B4!important; }}
    .stApp [data-testid="stAlert"] p {{ color:#E9EEE7!important; }}
    .stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary p {{ color:#DFE9DB!important; }}
    .stApp [data-testid="stTabs"] button {{ color:#B9C8B7!important; }}
    .stApp [data-testid="stTabs"] button[aria-selected="true"] {{ color:#E5F4D9!important; }}
    </style>
    """)


apply_custom_css()

OPTION_MENU_STYLE = {
    "container": {"padding": "0!important", "background-color": PANEL, "border-radius": "10px"},
    "icon": {"color": ACCENT, "font-size": "16px"},
    "nav-link": {"font-size": "14px", "text-align": "left", "color": TEXT, "--hover-color": PANEL2},
    "nav-link-selected": {"background-color": ORBIT_DIM, "color": "#FFFFFF"},
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
            username = st.text_input("Username *", placeholder="Choose a unique username")
            full_name = st.text_input("Full Name *", placeholder="John Doe")
            email = st.text_input("Email *", placeholder="john@example.com")
            phone = st.text_input("Phone Number", placeholder="+1 234 567 8900")
        with col2:
            password = st.text_input("Password *", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password *", type="password")

        st.markdown("---")
        st.markdown("### 📍 Address Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            address = st.text_area("Address", placeholder="Street address", height=80)
        with col2:
            city = st.text_input("City", placeholder="Your city")
            state = st.text_input("State/Province", placeholder="Your state")
        with col3:
            postal_code = st.text_input("Postal Code", placeholder="12345")
            country = st.text_input("Country", placeholder="Your country")

        st.markdown("---")
        st.markdown("### 🚜 Farm Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            farm_name = st.text_input("Farm Name", placeholder="Sunset Farm")
        with col2:
            farm_size = st.number_input("Farm Size (acres)", min_value=0.0, step=1.0)
        with col3:
            farm_type = st.selectbox("Farm Type", ["Select...", "Crop", "Livestock", "Mixed", "Organic", "Dairy", "Poultry", "Other"])

        st.markdown("---")
        st.markdown("*Required fields")
        submitted = st.form_submit_button("🚀 Create Account", width='stretch')

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

def show_profile(data):
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
    show_page_ai("My Profile", data, "What farm information should I add to receive more useful guidance?")

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
    show_page_ai("Dashboard", data, "What stands out in my farm overview, and what should I check first?")

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
            st.plotly_chart(plotly_dark(fig, height=350), width='stretch')
        with col2:
            st.html('<div class="section-title">🌾 Crop Distribution</div>')
            df_fields = pd.DataFrame(data['fields'])
            fig = px.pie(df_fields, values='acres', names='crop', color_discrete_sequence=CHART_SEQUENCE)
            st.plotly_chart(plotly_dark(fig, height=350), width='stretch')
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
    show_page_ai("Farm Management", data, "Which fields may need attention based on recorded crop, yield, and soil-health data?")

    with st.expander("➕ Add New Field", expanded=False):
        with st.form("add_field_form"):
            st.markdown("### 🌱 Add New Field")
            col1, col2 = st.columns(2)
            with col1:
                field_id = st.text_input("Field ID *", placeholder="e.g., F6")
                field_name = st.text_input("Field Name *", placeholder="e.g., South Field")
                crop_type = st.selectbox("Crop Type", ["Winter Wheat", "Corn", "Soybeans", "Barley", "Potatoes", "Oats", "Sunflowers", "Other"])
                acres = st.number_input("Acres *", min_value=0.0, step=0.5)
            with col2:
                yield_tons = st.number_input("Yield (tons/ha)", min_value=0.0, step=0.1)
                soil_health = st.slider("Soil Health Score", 0, 100, 75)
                planting_date = st.date_input("Planting Date")
                harvest_date = st.date_input("Harvest Date")

            submitted = st.form_submit_button("🌱 Add Field", width='stretch')
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
        st.dataframe(df_fields, width='stretch')

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
    show_page_ai("Machinery", data, "Which equipment needs attention based on its status, fuel, and recorded hours?")

    with st.expander("➕ Add New Machinery", expanded=False):
        with st.form("add_machinery_form"):
            st.markdown("### 🚜 Add New Machinery")
            col1, col2 = st.columns(2)
            with col1:
                machine_id = st.text_input("Machine ID *", placeholder="e.g., M5")
                machine_name = st.text_input("Machine Name *", placeholder="e.g., John Deere 6120")
                machine_type = st.selectbox("Machine Type", ["Tractor", "Combine", "Sprayer", "Plow", "Drill", "Harvester", "Other"])
                operating_hours = st.number_input("Operating Hours", min_value=0, step=1)
            with col2:
                fuel_level = st.slider("Fuel Level (%)", 0, 100, 50)
                status = st.selectbox("Status", ["Active", "Maintenance", "Idle", "Broken"])
                last_maintenance = st.date_input("Last Maintenance Date")
                next_maintenance = st.date_input("Next Maintenance Date")

            submitted = st.form_submit_button("🚜 Add Machinery", width='stretch')
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
        st.dataframe(df_machinery, width='stretch')

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
    show_page_ai("Soil Analysis", data, "Explain my soil test results and what should be checked before changing inputs.")

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

            submitted = st.form_submit_button("🧪 Add Soil Analysis", width='stretch')
            if submitted and field_options:
                success = db.add_soil_analysis(st.session_state.user_id, field_id, ph, nitrogen, phosphorus, potassium, organic_matter)
                if success:
                    st.success("✅ Soil analysis added successfully!")
                    st.rerun()
            elif submitted and not field_options:
                st.error("❌ Please add a field first!")

    st.html('<div class="section-title">📋 Soil Analysis Data</div>')
    if data['soil']:
        st.dataframe(pd.DataFrame(data['soil']), width='stretch')
    else:
        st.info("No soil analysis data available. Add some using the section above!")


# ==================== FARM WEATHER LOG PAGE ====================

def show_weather(data):
    st.html('<div class="main-header"><h1>🌤️ Farm Weather Log</h1><p>Historical weather logged for your farm records</p></div>')
    show_page_ai("Weather", data, "What do my recent recorded weather observations suggest for planning?")

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
        st.plotly_chart(plotly_dark(fig, height=400), width='stretch')
    else:
        st.info("No weather data available")

    st.info("💡 Looking for **live** satellite and current-conditions data instead of logged history? Check the **🛰️ Field Intelligence** tab.")


# ==================== COMPLIANCE PAGE ====================

def show_compliance(data):
    st.html('<div class="main-header"><h1>📋 Compliance & Reporting</h1></div>')
    show_page_ai("Compliance", data, "Summarize my compliance records and identify any recorded deadlines needing attention.")
    st.html(f"""
        <div class="metric-card">
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-label">Overall Compliance Score</div>
        </div>
    """)

    if data['compliance']:
        st.dataframe(pd.DataFrame(data['compliance']), width='stretch')
    else:
        st.info("No compliance data available")


# ==================== FARM AI ====================

def _farm_ai_service():
    return ai_service.FarmAIService(
        gemini_api_key=st.session_state.get('gemini_api_key') or None,
        groq_api_key=os.getenv('GROQ_API_KEY') or None,
    )


def show_ai_setup():
    provider = _farm_ai_service().provider
    if provider:
        st.caption(f"✦ AI connected: {provider} · Farm records are sent only when you submit an AI request.")
        return
    with st.expander("Connect Gemini AI", expanded=True):
        st.markdown("Create a key in [Google AI Studio](https://aistudio.google.com/app/apikey) and add it here. The key stays in this browser session; use a server secret for deployment.")
        key = st.text_input("Gemini API key", type="password", key="gemini_key_input_jd")
        if st.button("Connect Gemini", key="connect_gemini_jd"):
            if key.strip():
                st.session_state.gemini_api_key = key.strip()
                st.rerun()
            else:
                st.warning("Paste your Gemini API key first.")


def show_page_ai(page_name, data, suggested_question):
    with st.expander(f"✦ Ask AgroIntel about {page_name}"):
        if not _farm_ai_service().provider:
            st.markdown("Connect a key from [Google AI Studio](https://aistudio.google.com/app/apikey) to get personalized answers.")
            page_key = st.text_input("Gemini API key", type="password", key=f"page_gemini_key_{page_name}")
            if st.button("Connect Gemini", key=f"page_connect_gemini_{page_name}") and page_key.strip():
                st.session_state.gemini_api_key = page_key.strip()
                st.rerun()
        st.caption("Grounded in your recorded farm information. Confirm high-impact decisions with local agronomic guidance.")
        question = st.text_area("What would you like to know?", value=suggested_question,
                                key=f"page_ai_question_{page_name}", height=75)
        if st.button("✦ Generate farm insight", key=f"page_ai_submit_{page_name}", type="primary"):
            if not question.strip():
                st.warning("Enter a question first.")
            else:
                with st.spinner("Reviewing your farm records…"):
                    context = dict(data)
                    if page_name == "Field Intelligence":
                        layer = st.session_state.get("layer", "orbit")
                        context["field_intelligence"] = {
                            "active_layer": layer,
                            "observations": st.session_state.get(f"{layer}_data"),
                        }
                    result = _farm_ai_service().get_farm_analysis(question, context, focus=page_name)
                if not result['success']:
                    st.warning(result['error'])
                render_ai_answer(result['response'], result.get('source', 'Farm AI'))


def _safe_ai_markup(text):
    escaped = html.escape(text, quote=True)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
    output, list_open = [], False
    for raw_line in escaped.splitlines():
        line = raw_line.strip()
        bullet = re.match(r"^(?:[-*]|\d+[.)])\s+(.+)$", line)
        if bullet:
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append(f"<li>{bullet.group(1)}</li>")
        else:
            if list_open:
                output.append("</ul>")
                list_open = False
            if line:
                output.append(f"<p>{line}</p>")
    if list_open:
        output.append("</ul>")
    return "".join(output)


def render_ai_answer(answer, source="AgroIntel AI"):
    sections, title, lines, summary = [], "", [], []
    for line in answer.splitlines():
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if heading:
            if title or any(part.strip() for part in lines):
                sections.append((title, lines))
            elif not sections and any(part.strip() for part in summary):
                sections.append(("Details", summary))
                summary = []
            title, lines = heading.group(1), []
        elif title:
            lines.append(line)
        else:
            summary.append(line)
    if title or any(part.strip() for part in lines):
        sections.append((title, lines))
    if not sections and any(part.strip() for part in summary):
        paragraphs = re.split(r"\n\s*\n", "\n".join(summary).strip())
        summary = paragraphs[0].splitlines()
        if len(paragraphs) > 1:
            sections.append(("More detail", "\n\n".join(paragraphs[1:]).splitlines()))
    if not any(part.strip() for part in summary) and sections:
        first_title, first_lines = sections.pop(0)
        summary = [f"**{first_title}**", *first_lines]

    st.html(f'''<div class="ai-answer-shell"><div class="ai-answer-head">
        <div class="ai-answer-icon">✦</div><div><div class="ai-answer-title">Your farm insight</div>
        <div class="ai-answer-subtitle">Personalized guidance based on your recorded data</div></div>
        <span class="ai-answer-provider">{html.escape(str(source))}</span></div></div>''')
    if any(part.strip() for part in summary):
        st.html(f'<div class="ai-answer-summary">{_safe_ai_markup(chr(10).join(summary))}</div>')
    for section_title, section_lines in sections:
        normalized = section_title.lower()
        icon = "🟠" if any(word in normalized for word in ("caution", "avoid", "hold", "risk", "not do")) else (
            "🔎" if any(word in normalized for word in ("evidence", "data", "detail", "monitor")) else "🌱")
        st.html(f'<div class="ai-answer-section-title">{icon} &nbsp;{html.escape(section_title or "Helpful next steps")}</div>')
        cards, current = [], []
        for line in section_lines:
            if re.match(r"^\s*\d+[.)]\s+", line) and current and any(part.strip() for part in current):
                cards.append(current)
                current = [line]
            else:
                current.append(line)
        if current and any(part.strip() for part in current):
            cards.append(current)
        for index, card in enumerate(cards, 1):
            content = "\n".join(card).strip()
            number = re.match(r"^\s*(\d+)[.)]\s+", content)
            if number:
                content = re.sub(r"^\s*\d+[.)]\s+", "", content, count=1)
            st.html(f'<div class="ai-answer-step"><div class="ai-answer-step-num">{number.group(1) if number else "•"}</div><div class="ai-answer-copy">{_safe_ai_markup(content)}</div></div>')


def render_suggestion_plan(markdown_text):
    sections, title, lines = [], "", []
    for line in markdown_text.splitlines():
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if heading:
            if title or any(part.strip() for part in lines):
                sections.append((title, lines))
            title, lines = heading.group(1), []
        else:
            lines.append(line)
    if title or any(part.strip() for part in lines):
        sections.append((title, lines))
    if not sections:
        render_ai_answer(markdown_text, "Farm action plan")
        return
    for section_title, section_lines in sections:
        normalized = section_title.lower()
        card_type = "caution" if any(word in normalized for word in ("hold off", "do not", "avoid")) else (
            "gap" if any(word in normalized for word in ("data", "collect", "missing")) else "action")
        icon = "🟠" if card_type == "caution" else ("🔎" if card_type == "gap" else "🌱")
        st.html(f'<div class="plan-section-label">{icon} &nbsp;{html.escape(section_title or "Farm action plan")}</div>')
        items, current = [], []
        for line in section_lines:
            starts_item = bool(re.match(r"^\s*(?:\d+[.)]|[-*])\s+", line))
            if starts_item and current and any(part.strip() for part in current):
                items.append(current)
                current = [line]
            else:
                current.append(line)
        if current and any(part.strip() for part in current):
            items.append(current)
        if not items:
            items = [section_lines]
        for index, item in enumerate(items, 1):
            content = "\n".join(item).strip()
            number = re.match(r"^\s*(\d+)[.)]\s+", content)
            if number:
                content = re.sub(r"^\s*\d+[.)]\s+", "", content, count=1)
            priority = "CHECK" if card_type == "caution" else ("DATA GAP" if card_type == "gap" else "NEXT STEP")
            step = f"ACTION {number.group(1)}" if number else f"NOTE {index}"
            st.html(f'<div class="plan-card {card_type}"><div class="plan-card-head"><span class="plan-step">{step}</span><span class="plan-priority">{priority}</span></div><div class="plan-copy">{_safe_ai_markup(content)}</div></div>')


def show_ai_suggestions(data):
    st.html("""<div class="field-guide-hero"><div class="hero-copy">
        <div class="eyebrow">AGROINTEL · PERSONAL FARM BRIEF</div><h1>Your farm.<br>Your next move.</h1>
        <p>Practical, prioritized guidance built from your farm records, with the evidence and unknowns made clear.</p></div>
        <div class="hero-orbit">✳</div></div>""")
    show_ai_setup()
    st.html('<div class="suggestion-intro">🛡️ &nbsp;<strong>Advice with guardrails</strong> &nbsp;·&nbsp; Verify field conditions, product labels, and local requirements before high-impact actions.</div>')
    soil_coverage = min(100, round(len(data['soil']) / len(data['fields']) * 100)) if data['fields'] else 0
    weather_coverage = min(100, round(len(data['weather']) / 7 * 100))
    metrics = st.columns(5)
    metric_items = [("🌾", "Fields", len(data['fields']), "Growing areas"),
                    ("📐", "Farm area", f"{data['total_acres']:,.0f}", "Recorded acres"),
                    ("🧪", "Soil tests", len(data['soil']), "Nutrient records"),
                    ("🌦️", "Weather", len(data['weather']), "Recent observations"),
                    ("🚜", "Ready", f"{data['active_machinery']}/{data['total_machinery']}", "Equipment active")]
    for column, (icon, label, value, caption) in zip(metrics, metric_items):
        with column:
            st.html(f'<div class="guide-stat"><div class="icon">{icon}</div><div class="value">{value}</div><div class="label">{label}</div><div class="hint">{caption}</div></div>')
    st.html("<div style='height:.8rem'></div>")
    coverage_col, generate_col = st.columns([1.05, 1])
    with coverage_col:
        st.html(f'''<div class="guide-coverage"><div class="guide-coverage-top"><strong>Farm data coverage</strong><span>More records sharpen guidance</span></div>
            <div class="guide-coverage-top"><span>Fields with soil tests</span><strong>{soil_coverage}%</strong></div><div class="guide-track"><span style="width:{soil_coverage}%"></span></div>
            <div class="guide-coverage-top"><span>Recent weather log</span><strong>{weather_coverage}%</strong></div><div class="guide-track"><span style="width:{weather_coverage}%"></span></div></div>''')
    with generate_col:
        st.html('<div class="guide-cta"><strong>Ready for your farm field guide?</strong><p>Review your latest field, soil, weather, and equipment records.</p></div>')
        st.html("<div style='height:.35rem'></div>")
        if st.button("✦  Generate my action plan", type="primary", width='stretch', key="generate_farm_suggestions"):
            with st.status("Building your farm brief…", expanded=True) as status:
                st.write("Reviewing recorded conditions for useful next steps")
                st.session_state.ai_suggestions = _farm_ai_service().generate_suggestions(data)
                status.update(label="Your farm brief is ready", state="complete", expanded=False)
    if not data['fields']:
        st.warning("Add fields and crop details in Farm Management to get field-specific suggestions.")
    if st.session_state.ai_suggestions:
        result = st.session_state.ai_suggestions
        st.html(f'<div class="plan-section-label" style="margin-top:1.6rem">YOUR FIELD GUIDE <span style="font-size:.7rem;color:{MUTED};font-weight:400">· {datetime.now().strftime("%b %d, %Y")}</span></div>')
        if not result['success']:
            st.warning(result['error'])
        render_suggestion_plan(result['response'])
        st.caption(f"Prepared with {result.get('source', 'Farm AI')} · Refresh records before generating your next plan.")
        st.download_button("⬇ Download action plan", result['response'], file_name="agrointel-farm-action-plan.md", mime="text/markdown")
    else:
        st.html('<div class="snap-card" style="text-align:center;padding:1.6rem;color:#7F9482"><div style="font-size:2rem">🌱</div><strong>Your personalized field guide will appear here</strong><br><span>Generate a plan to see recommendations, cautions, and useful data to collect.</span></div>')
    show_page_ai("AI Suggestions", data, "What is the most important thing I should check on my farm this week?")


# ==================== AI COPILOT PAGE ====================

def show_ai_copilot(data):
    st.html('<div class="main-header"><h1>🤖 AgroIntel AI Copilot</h1><p>Your farm-aware assistant, with evidence and uncertainty made clear.</p></div>')
    show_ai_setup()
    st.caption("Farm records are sent only when you submit a prompt. This chat remains in the current browser session.")
    prompt_cols = st.columns(4)
    prompts = ["Review my farm performance", "What should I check in my soil?", "Which equipment needs attention?", "How should I plan this week?"]
    for column, prompt in zip(prompt_cols, prompts):
        with column:
            if st.button(prompt, key=f"copilot_quick_{prompt}", width='stretch'):
                st.session_state.ai_pending_question = prompt
                st.rerun()
    for message in st.session_state.copilot_messages:
        with st.chat_message(message['role']):
            if message['role'] == 'assistant':
                render_ai_answer(message['content'], _farm_ai_service().provider or "Local analysis")
            else:
                st.markdown(message['content'])
    if not st.session_state.copilot_messages:
        st.info("Ask about your crops, fields, soil tests, recorded weather, machinery, or compliance tasks.")
    question = st.chat_input("Ask about your farm…") or st.session_state.pop('ai_pending_question', None)
    if question:
        history = st.session_state.copilot_messages[-12:]
        st.session_state.copilot_messages.append({'role': 'user', 'content': question})
        with st.spinner("Reviewing your farm records…"):
            result = _farm_ai_service().get_farm_analysis(question, data, history=history)
        if not result['success']:
            st.warning(result['error'])
        st.session_state.copilot_messages.append({'role': 'assistant', 'content': result['response']})
        st.rerun()


def show_related_data(question, data):
    question_lower = question.lower()
    st.markdown("### 📊 Related Data")

    if any(word in question_lower for word in ['crop', 'field', 'yield']):
        if data['fields']:
            st.dataframe(pd.DataFrame(data['fields']), width='stretch')
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Acres", f"{data['total_acres']:.0f}")
            with col2:
                st.metric("Avg Yield", f"{data['avg_yield']} t/ha")
        else:
            st.info("No field data available")
    elif any(word in question_lower for word in ['machinery', 'tractor', 'maintenance']):
        if data['machinery']:
            st.dataframe(pd.DataFrame(data['machinery']), width='stretch')
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
            st.dataframe(pd.DataFrame(data['soil']), width='stretch')
        else:
            st.info("No soil analysis data available")
    elif any(word in question_lower for word in ['weather', 'rain', 'temperature']):
        if data['weather']:
            st.dataframe(pd.DataFrame(data['weather']), width='stretch')
        else:
            st.info("No weather data available")


# ==================== FIELD INTELLIGENCE (NASA / OpenWeather / RVO) ====================

def show_field_intelligence(data):
    st.html("""
        <div class="main-header">
            <h1>🛰️ Field Intelligence</h1>
            <p>Satellite climatology from orbit, live atmosphere overhead, funding on the ground.</p>
        </div>
    """)
    show_page_ai("Field Intelligence", data, "How can I use the satellite, live-weather, and farm records shown here to plan field checks?")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🛰️  ORBIT — NASA POWER", key="btn_orbit", width='stretch'):
            st.session_state.layer = "orbit"
    with c2:
        if st.button("☁️  ATMOSPHERE — OpenWeather", key="btn_atmos", width='stretch'):
            st.session_state.layer = "atmosphere"
    with c3:
        if st.button("🏛️  GRANTS — RVO NL", key="btn_grants", width='stretch'):
            st.session_state.layer = "grants"
    with c4:
        if st.button("🚜  GROUND — John Deere", key="btn_deere", width='stretch'):
            st.session_state.layer = "deere"

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        if st.button("🧱  SOIL — SoilGrids", key="btn_soilgrids", width='stretch'):
            st.session_state.layer = "soilgrids"
    with c6:
        if st.button("🌿  CROP MONITOR — Agro API", key="btn_agromon", width='stretch'):
            st.session_state.layer = "agromonitoring"
    with c7:
        if st.button("🛱  SATELLITE — Copernicus", key="btn_copernicus", width='stretch'):
            st.session_state.layer = "copernicus"
    with c8:
        if st.button("🐄  FARM RECORDS — farmOS", key="btn_farmos", width='stretch'):
            st.session_state.layer = "farmos"

    st.html("<div style='height: 0.6rem'></div>")

    if st.session_state.layer == "orbit":
        _render_orbit()
    elif st.session_state.layer == "atmosphere":
        _render_atmosphere()
    elif st.session_state.layer == "grants":
        _render_grants()
    elif st.session_state.layer == "deere":
        _render_deere()
    elif st.session_state.layer == "soilgrids":
        _render_soilgrids()
    elif st.session_state.layer == "agromonitoring":
        _render_agromonitoring()
    elif st.session_state.layer == "copernicus":
        _render_copernicus()
    else:
        _render_farmos()


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
        fetch_clicked = st.button("Read orbit data", key="fetch_orbit", width='stretch')

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
    st.plotly_chart(plotly_dark(fig_temp), width='stretch')

    ct1, ct2 = st.columns(2)
    with ct1:
        fig_rain = go.Figure(go.Bar(x=df["date"], y=df["PRECTOTCORR"], marker_color=ACCENT))
        fig_rain.update_layout(title=dict(text="Rainfall (mm/day)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
        st.plotly_chart(plotly_dark(fig_rain, height=280), width='stretch')
    with ct2:
        fig_soil = go.Figure()
        fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETTOP"], name="Surface", line=dict(color=WARN, width=2)))
        fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETROOT"], name="Root zone", line=dict(color=ORBIT, width=2)))
        fig_soil.update_layout(title=dict(text="Soil wetness (0–1)", font=dict(family="Space Grotesk", color=TEXT, size=15)), yaxis_range=[0, 1])
        st.plotly_chart(plotly_dark(fig_soil, height=280), width='stretch')

    with st.expander("Raw data"):
        st.dataframe(df, width='stretch')


def _render_atmosphere():
    st.html('<span class="layer-tag tag-atmos">Live conditions</span>')

    colA, colB = st.columns([3, 1])
    with colA:
        city = st.text_input("City", value="Nashik")
    with colB:
        st.write("")
        st.write("")
        fetch_clicked = st.button("Read atmosphere", key="fetch_atmos", width='stretch')

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
        st.plotly_chart(plotly_dark(fig_h, height=260), width='stretch')
    with g2:
        fig_c = go.Figure(go.Indicator(
            mode="gauge+number", value=clouds,
            title={"text": "Cloud cover %", "font": {"family": "Space Grotesk", "color": TEXT, "size": 14}},
            number={"font": {"family": "IBM Plex Mono", "color": TEXT}},
            gauge={"axis": {"range": [0, 100], "tickcolor": MUTED}, "bar": {"color": ACCENT}, "bgcolor": PANEL2, "borderwidth": 0},
        ))
        st.plotly_chart(plotly_dark(fig_c, height=260), width='stretch')


def _render_grants():
    st.html('<span class="layer-tag tag-grants">Netherlands Enterprise Agency · Open Data</span>')

    colA, colB = st.columns([3, 1])
    with colA:
        st.caption("Dutch government funding schemes open to agricultural businesses — no auth required, pulled live from RVO's open data API.")
    with colB:
        fetch_clicked = st.button("Read grants", key="fetch_grants", width='stretch')

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
        st.plotly_chart(plotly_dark(fig, height=max(220, 40 * len(subject_counts))), width='stretch')

    st.html("<div style='height:0.6rem'></div>")

    tcol1, tcol2 = st.columns([3, 1])
    with tcol1:
        search = st.text_input("Filter by keyword", placeholder="e.g. mest, energie, krediet")
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


# ---------------------------------------------------------------------------
# GROUND — John Deere
#
# Scoped to APPROVED APIs only:
#   Organizations, Equipment, Machine Locations, Machine Hours Of Operation,
#   Machine Alerts, Machine Device State Report, Map Layers, ISO 15143-3.
# Fields / Farms / Boundaries / Users / Assets / Files / Product are NOT
# approved for this app registration and are never called here.
# ---------------------------------------------------------------------------

def _render_deere():
    st.html('<span class="layer-tag tag-deere">Operations Center · Live Connection</span>')

    try:
        from johndeere import (
            get_valid_access_token,
            get_organizations,
            get_equipment,
            get_machine_related,
            get_engine_hours,
            get_aemp_fleet,
            summarize_aemp_equipment,
            get_map_layers,
        )
        deere_available = True
    except Exception as e:
        st.warning(f"johndeere.py not available yet ({e}) — copy the updated johndeere.py into this folder to enable this layer.")
        deere_available = False

    if not deere_available:
        return

    st.caption(
        "Scoped to your approved John Deere APIs: Organizations, Equipment, Machine "
        "Locations, Hours of Operation, Machine Alerts, Device State Reports, Map "
        "Layers, and ISO 15143-3. Fields / Farms / Boundaries / Assets / Files / "
        "Product aren't authorized for this app and aren't called here."
    )

    fetch_clicked = st.button("Read ground data", key="fetch_deere", width='stretch')
    first_load = "deere_data" not in st.session_state

    if fetch_clicked or first_load:
        with st.status("Connecting to John Deere...", expanded=True) as status:
            try:
                st.write("🔑 Getting access token...")
                token = get_valid_access_token()

                if not token:
                    st.write("❌ No valid token found.")
                    status.update(label="Not connected", state="error", expanded=True)
                    st.session_state.deere_error = "no_token"
                    st.session_state.deere_data = None
                    return

                st.write("✅ Token acquired.")
                st.write("🏢 Fetching organizations...")
                orgs = get_organizations(token)
                org_values = orgs.get("values", [])
                if not org_values:
                    st.write("❌ No organizations returned on this account at all.")
                    status.update(label="No organizations", state="error", expanded=True)
                    st.session_state.deere_data = None
                    return

                for o in org_values:
                    st.write(f"　→ found org: **{o.get('name','—')}** (id={o.get('id','—')}, type={o.get('type','—')})")

                # Prefer an org literally named AgroIntel if there's more than
                # one on this account — get_organizations()[0] isn't
                # guaranteed to be the one you granted consent to.
                org = next((o for o in org_values if o.get("name", "").strip().lower() == "agrointel"), org_values[0])
                st.write(f"✅ Using organization: **{org.get('name', '—')}** (id={org.get('id')})")

                st.write("🚜 Fetching equipment...")
                machines, equipment_error, equipment_connect_url = [], None, None
                try:
                    equipment = get_equipment(token, org["id"], org=org)
                    machines = equipment.get("values", []) if equipment else []
                    st.write(f"✅ Equipment: {len(machines)} record(s)")
                except Exception as e:
                    equipment_error = str(e)
                    equipment_connect_url = getattr(e, "manage_connection_url", None)
                    st.write(f"🔒 Equipment: not available ({type(e).__name__})")
                    if equipment_connect_url:
                        st.write(f"　→ Grant consent for this org here: {equipment_connect_url}")

                st.write("🛰️ Fetching ISO 15143-3 (AEMP) fleet snapshot...")
                aemp_fleet, aemp_error, aemp_connect_url = [], None, None
                try:
                    aemp_fleet = get_aemp_fleet(token, org["id"], org=org)
                    st.write(f"　→ ✅ AEMP Fleet: {len(aemp_fleet)} equipment record(s)")
                except Exception as e:
                    aemp_error = str(e)
                    aemp_connect_url = getattr(e, "manage_connection_url", None)
                    st.write(f"　→ 🔒 AEMP Fleet: not available ({type(e).__name__})")

                st.write("🗺️ Trying Map Layers...")
                map_layers, map_layers_error = None, None
                try:
                    map_layers = get_map_layers(token, org)
                    st.write("　→ ✅ Map Layers available" if map_layers else "　→ ⚪ Map Layers: no matching link on this org")
                except Exception as e:
                    map_layers_error = str(e)
                    st.write(f"　→ 🔒 Map Layers: not available ({type(e).__name__})")

                st.session_state.deere_data = {
                    "org": org,
                    "machines": machines,
                    "equipment_error": equipment_error,
                    "equipment_connect_url": equipment_connect_url,
                    "aemp_fleet": aemp_fleet,
                    "aemp_error": aemp_error,
                    "aemp_connect_url": aemp_connect_url,
                    "map_layers": map_layers,
                    "map_layers_error": map_layers_error,
                }
                st.session_state.deere_error = None
                status.update(label="Done", state="complete", expanded=False)

            except Exception as e:
                st.write(f"❌ Failed: {e}")
                status.update(label="Failed", state="error", expanded=True)
                st.session_state.deere_data = None
                return

    if st.session_state.get("deere_error") == "no_token":
        st.warning(
            "Not connected yet. Run `python johndeere.py` once in a terminal, "
            "complete the browser login, then come back and hit **Read ground data** again."
        )
        return

    data = st.session_state.get("deere_data")
    if not data:
        st.info("Hit **Read ground data** to pull your live John Deere data.")
        return

    org = data["org"]
    machines = data["machines"]

    st.html(f"""
    <div class="snap-card" style="border-left:4px solid {DEERE};">
        <div class="snap-label">🚜 Connected Organization</div>
        <div class="snap-value" style="font-size:1.8rem;">{org.get('name', '—')}</div>
        <div class="snap-sub">Live from John Deere Operations Center via OAuth2</div>
    </div>
    """)

    st.html("<div style='height:1rem'></div>")

    connect_url = data.get("equipment_connect_url") or data.get("aemp_connect_url")
    if connect_url:
        st.warning(
            "🔒 This organization hasn't granted your app consent to share its data yet "
            "(this is separate from your app being approved for the API itself — it's a "
            "per-organization step). Open the link below, log in as the org, and check the "
            "data categories (Equipment, Machine Locations, Hours of Operation, etc.) to "
            "share with this app, then come back and hit **Read ground data** again.\n\n"
            f"👉 {connect_url}"
        )

    o1, o2, o3 = st.columns(3)
    for col, label, value, sub in [
        (o1, "Organization ID", str(org.get("id", "—")), "unique Deere org identifier"),
        (o2, "Equipment on record", str(len(machines)), "via Equipment API"),
        (o3, "AEMP fleet records", str(len(data.get("aemp_fleet") or [])), "ISO 15143-3 snapshot"),
    ]:
        with col:
            st.html(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value" style="font-size:1.4rem">{value}</div>
                <div class="snap-sub">{sub}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    tab_equip, tab_fleet, tab_machine, tab_layers = st.tabs(
        ["📋 Equipment", "🛰️ ISO 15143-3 Fleet", "📡 Per-Machine Data", "🗺️ Map Layers"]
    )

    # --- Equipment (Equipment API) -----------------------------------------
    with tab_equip:
        if machines:
            st.dataframe(pd.json_normalize(machines), width='stretch')
        elif data.get("equipment_error"):
            st.caption(f"ℹ️ {data['equipment_error']}")
        else:
            st.caption("No equipment records returned for this organization.")

    # --- ISO 15143-3 (AEMP) fleet snapshot ----------------------------------
    with tab_fleet:
        aemp_fleet = data.get("aemp_fleet") or []
        if aemp_fleet:
            rows = []
            for equip in aemp_fleet:
                s = summarize_aemp_equipment(equip)
                loc = s.get("location") or {}
                rows.append({
                    "Make": s.get("make") or "—",
                    "Model": s.get("model") or "—",
                    "VIN / Serial": s.get("vin") or "—",
                    "Last lat": loc.get("lat") or loc.get("latitude") or "—",
                    "Last lon": loc.get("lon") or loc.get("longitude") or "—",
                })
            st.dataframe(pd.DataFrame(rows), width='stretch')

            # Plot last-known locations if we have coordinates and folium is available
            if MAP_AVAILABLE:
                pins = []
                for equip in aemp_fleet:
                    s = summarize_aemp_equipment(equip)
                    loc = s.get("location") or {}
                    lat_val = loc.get("lat") or loc.get("latitude")
                    lon_val = loc.get("lon") or loc.get("longitude")
                    try:
                        if lat_val is not None and lon_val is not None:
                            pins.append((float(lat_val), float(lon_val), s.get("model") or "Machine"))
                    except (TypeError, ValueError):
                        continue
                if pins:
                    st.markdown("#### Last known positions")
                    center_lat = sum(p[0] for p in pins) / len(pins)
                    center_lon = sum(p[1] for p in pins) / len(pins)
                    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=13)
                    for lat_val, lon_val, label in pins:
                        folium.Marker(
                            location=[lat_val, lon_val],
                            tooltip=label,
                            icon=folium.Icon(color="orange", icon="cog", prefix="fa"),
                        ).add_to(fmap)
                    st_folium(fmap, width='stretch', height=380)

            with st.expander("Raw AEMP records (exact field names your sandbox reports)"):
                st.json(aemp_fleet)
        elif data.get("aemp_error"):
            st.caption(f"ℹ️ ISO 15143-3 fleet snapshot wasn't available: {data['aemp_error']}")
        else:
            st.caption("No ISO 15143-3 fleet data returned for this organization yet.")

    # --- Per-machine: Engine Hours (confirmed endpoint) + best-effort links --
    with tab_machine:
        if not machines:
            st.caption("No equipment to inspect.")
        else:
            names = [f"{m.get('name', 'Machine')} ({m.get('id', '')})" for m in machines]
            picked = st.selectbox("Choose a machine", options=names, key="deere_machine_pick")
            machine = machines[names.index(picked)]

            token = get_valid_access_token()

            st.markdown("#### ⏱️ Engine hours")
            try:
                hours_data = get_engine_hours(token, machine["id"], last_known=True)
                values = (hours_data or {}).get("values") or []
                if values:
                    latest = values[0]
                    reading = latest.get("reading", {})
                    st.html(f"""<div class="snap-card"><div class="snap-label">Last known engine hours</div>
                        <div class="snap-value">{reading.get('valueAsDouble', '—')}</div>
                        <div class="snap-sub">as of {latest.get('reportTime', '—')} · source {latest.get('source', '—')}</div></div>""")
                else:
                    st.caption("No engine hours reported for this machine yet.")
            except Exception as e:
                st.caption(f"🔒 Engine hours not available for this machine ({type(e).__name__}).")

            st.html("<div style='height:1rem'></div>")
            st.markdown("#### 📡 Other linked resources on this machine")
            st.caption(
                "These are fetched by following the machine's own HATEOAS links. The exact "
                "`rel` name for each resource can vary by sandbox account, so a few likely "
                "candidates are tried per resource — see 'Links available on this machine' "
                "below if a resource comes back empty and you want to wire up the real rel name."
            )

            candidates = {
                "📍 Locations": ["locationHistory", "locations", "breadcrumbs"],
                "🕓 Hours of operation": ["hoursOfOperation", "hoursOfOperations"],
                "🚨 Alerts": ["alerts", "machineAlerts"],
                "📶 Device state report": ["deviceStateReports", "deviceState", "lastKnownDeviceState"],
            }

            for label, rels in candidates.items():
                found, found_rel = None, None
                for rel in rels:
                    try:
                        result = get_machine_related(token, machine, rel)
                    except Exception:
                        result = None
                    if result:
                        found, found_rel = result, rel
                        break

                with st.expander(label):
                    if found:
                        st.caption(f"via link rel `{found_rel}`")
                        values = found.get("values", found) if isinstance(found, dict) else found
                        if isinstance(values, list):
                            st.dataframe(pd.json_normalize(values), width='stretch')
                        else:
                            st.json(found)
                    else:
                        st.caption(
                            f"Not returned via rel candidates {rels} — either no data reported "
                            f"yet, or this sandbox uses a different rel name. Check the raw links "
                            f"below to find it."
                        )

            with st.expander("🔗 Links available on this machine (raw)"):
                links = machine.get("links", [])
                if links:
                    st.dataframe(pd.DataFrame(links), width='stretch')
                else:
                    st.caption("This machine record has no `links` array.")

    # --- Map Layers (best-effort, org-level) --------------------------------
    with tab_layers:
        map_layers = data.get("map_layers")
        if map_layers:
            st.json(map_layers)
        elif data.get("map_layers_error"):
            st.caption(f"ℹ️ Map Layers wasn't available: {data['map_layers_error']}")
        else:
            st.caption(
                "No Map Layers link found on this organization in the sandbox. Map Layers "
                "is typically field-scoped in Operations Center, so it may need a field "
                "context this app doesn't have access to."
            )


# ---------------------------------------------------------------------------
# SOIL — SoilGrids (ISRIC)
# ---------------------------------------------------------------------------

def _render_soilgrids():
    st.html('<span class="layer-tag tag-soil">ISRIC · Global Soil Property Maps · Public, no key needed</span>')

    try:
        from soilgrids import get_soil_properties, get_soil_classification, STANDARD_DEPTHS
        available = True
    except Exception as e:
        st.warning(f"soilgrids.py not available yet ({e}) — copy it into this folder to enable this layer.")
        available = False
    if not available:
        return

    colA, colB, colC, colD = st.columns([1, 1, 1, 1])
    with colA:
        lat = st.number_input("Latitude", value=20.0059, format="%.4f", key="soilgrids_lat")
    with colB:
        lon = st.number_input("Longitude", value=73.7910, format="%.4f", key="soilgrids_lon")
    with colC:
        depth = st.selectbox("Depth", STANDARD_DEPTHS, index=0, key="soilgrids_depth")
    with colD:
        st.write("")
        st.write("")
        fetch_clicked = st.button("Read soil data", key="fetch_soilgrids", width='stretch')

    first_load = "soilgrids_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Querying global soil maps..."):
            try:
                props = get_soil_properties(lat, lon, depths=[depth])
                classification = get_soil_classification(lat, lon)
                st.session_state.soilgrids_data = {"props": props, "classification": classification}
            except Exception as e:
                st.error(f"SoilGrids read failed: {e}")
                return

    data = st.session_state.get("soilgrids_data")
    if not data:
        st.info("Set coordinates and hit **Read soil data**.")
        return

    props = data["props"]
    classification = data["classification"]

    cols = st.columns(4)
    for i, row in enumerate(props):
        with cols[i % 4]:
            value_display = f"{row['value']:.2f}" if row["value"] is not None else "—"
            st.html(f"""<div class="snap-card"><div class="snap-label">{row['property']}</div>
                <div class="snap-value" style="font-size:1.5rem">{value_display}</div>
                <div class="snap-sub">{row['unit']} · {row['depth']}</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    if classification.get("classes"):
        st.html('<div class="section-title">🗺️ Likely soil classification (WRB)</div>')
        top = classification.get("top_class", "—")
        st.caption(f"Most likely: **{top}**")
        sorted_classes = sorted(classification["classes"], key=lambda c: c["probability"])
        fig = go.Figure(go.Bar(
            x=[c["probability"] for c in sorted_classes],
            y=[c["name"] for c in sorted_classes],
            orientation="h", marker_color=WARN,
        ))
        fig.update_layout(title=dict(text="Class probability (%)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
        st.plotly_chart(plotly_dark(fig, height=max(220, 40 * len(sorted_classes))), width='stretch')

    with st.expander("Raw data"):
        st.json(data)


# ---------------------------------------------------------------------------
# CROP MONITOR — Agromonitoring (Agro API)
# ---------------------------------------------------------------------------

def _render_agromonitoring():
    st.html('<span class="layer-tag tag-cropmon">Agro API · Field polygons, soil, UV, NDVI</span>')

    try:
        import agromonitoring as agro
        available = True
    except Exception as e:
        st.warning(f"agromonitoring.py not available yet ({e}) — copy it into this folder to enable this layer.")
        available = False
    if not available:
        return

    if not agro.API_KEY:
        st.warning(
            "AGROMONITORING_API_KEY isn't set. Get a free key at "
            "[agromonitoring.com](https://agromonitoring.com/) (separate signup from "
            "regular OpenWeather) and add it to your .env file."
        )
        return

    st.caption(
        "This API is scoped to a registered field polygon rather than a raw lat/lon. "
        "Enter a center point + rough size below to create a small rectangular test "
        "polygon, or paste an existing polygon id if you already made one."
    )

    colA, colB, colC = st.columns(3)
    with colA:
        center_lat = st.number_input("Field center latitude", value=20.0059, format="%.4f", key="agro_lat")
    with colB:
        center_lon = st.number_input("Field center longitude", value=73.7910, format="%.4f", key="agro_lon")
    with colC:
        size_deg = st.slider("Rough field size (degrees)", 0.001, 0.02, 0.005, key="agro_size")

    existing_id = st.text_input("Or paste an existing polygon id (optional)", key="agro_existing_id")

    if st.button("Create / use polygon", key="agro_create_poly", width='stretch'):
        with st.spinner("Registering field polygon..."):
            try:
                if existing_id.strip():
                    st.session_state.agro_polygon_id = existing_id.strip()
                else:
                    d = size_deg / 2
                    coords = [[
                        [center_lon - d, center_lat - d],
                        [center_lon + d, center_lat - d],
                        [center_lon + d, center_lat + d],
                        [center_lon - d, center_lat + d],
                        [center_lon - d, center_lat - d],
                    ]]
                    polygon = agro.create_polygon("AgroIntel field", coords)
                    st.session_state.agro_polygon_id = polygon["id"]
                st.success(f"Using polygon id: {st.session_state.agro_polygon_id}")
            except Exception as e:
                st.error(f"Polygon setup failed: {e}")
                return

    poly_id = st.session_state.get("agro_polygon_id")
    if not poly_id:
        st.info("Create or paste a polygon id above, then hit **Create / use polygon**.")
        return

    fetch_clicked = st.button("Read crop monitor data", key="fetch_agro", width='stretch')
    first_load = "agro_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Reading soil, UV and vegetation data..."):
            try:
                soil = agro.get_current_soil(poly_id)
                uvi = agro.get_current_uvi(poly_id)
                st.session_state.agro_data = {"soil": soil, "uvi": uvi}
            except Exception as e:
                st.error(f"Crop monitor read failed: {e}")
                return

    data = st.session_state.get("agro_data")
    if not data:
        st.info("Hit **Read crop monitor data**.")
        return

    soil, uvi = data["soil"], data["uvi"]
    s1, s2, s3 = st.columns(3)
    with s1:
        surface_c = soil.get("t0", 0) - 273.15 if soil.get("t0") else None
        st.html(f"""<div class="snap-card"><div class="snap-label">Surface temp</div>
            <div class="snap-value">{f'{surface_c:.1f}°C' if surface_c is not None else '—'}</div>
            <div class="snap-sub">at ground level</div></div>""")
    with s2:
        temp10_c = soil.get("t10", 0) - 273.15 if soil.get("t10") else None
        st.html(f"""<div class="snap-card"><div class="snap-label">Temp @ 10cm</div>
            <div class="snap-value">{f'{temp10_c:.1f}°C' if temp10_c is not None else '—'}</div>
            <div class="snap-sub">root-zone depth</div></div>""")
    with s3:
        st.html(f"""<div class="snap-card"><div class="snap-label">Soil moisture</div>
            <div class="snap-value">{soil.get('moisture', '—')}</div>
            <div class="snap-sub">m³/m³ · UV index {uvi.get('uvi', '—')}</div></div>""")

    st.html("<div style='height:1rem'></div>")
    st.caption(
        "🌿 NDVI (vegetation health) needs history over a date range and a satellite "
        "pass to already exist for this polygon — use `agromonitoring.get_ndvi_history()` "
        "directly with a start/end date once this polygon has a few weeks of coverage."
    )

    with st.expander("Raw data"):
        st.json(data)


# ---------------------------------------------------------------------------
# SATELLITE — Copernicus Data Space Ecosystem
# ---------------------------------------------------------------------------

def _render_copernicus():
    st.html('<span class="layer-tag tag-sat">Copernicus Data Space · Sentinel imagery search · Public search, no key needed</span>')

    try:
        import copernicus as cds
        available = True
    except Exception as e:
        st.warning(f"copernicus.py not available yet ({e}) — copy it into this folder to enable this layer.")
        available = False
    if not available:
        return

    st.caption(
        "Searching the Sentinel catalogue needs no login — only downloading an actual "
        "product file would need COPERNICUS_USERNAME/PASSWORD in .env, which this page "
        "doesn't do (product archives can be multiple GB)."
    )

    colA, colB = st.columns(2)
    with colA:
        collection = st.selectbox("Collection", ["SENTINEL-2", "SENTINEL-1", "SENTINEL-3"], key="cds_collection")
    with colB:
        cloud_max = st.slider("Max cloud cover %", 0, 100, 30, key="cds_cloud") if collection == "SENTINEL-2" else None

    colC, colD = st.columns(2)
    with colC:
        center_lat = st.number_input("Area center latitude", value=20.0059, format="%.4f", key="cds_lat")
    with colD:
        center_lon = st.number_input("Area center longitude", value=73.7910, format="%.4f", key="cds_lon")

    colE, colF = st.columns(2)
    today = datetime.now()
    with colE:
        start = st.date_input("From", value=today - timedelta(days=30), key="cds_start")
    with colF:
        end = st.date_input("To", value=today, key="cds_end")

    fetch_clicked = st.button("Search Sentinel catalogue", key="fetch_cds", width='stretch')
    if fetch_clicked:
        with st.spinner("Searching Copernicus catalogue..."):
            try:
                d = 0.05
                results = cds.search_products(
                    collection=collection,
                    start_date=start.strftime("%Y-%m-%dT00:00:00.000Z"),
                    end_date=end.strftime("%Y-%m-%dT23:59:59.000Z"),
                    bbox=(center_lon - d, center_lat - d, center_lon + d, center_lat + d),
                    product_type="S2MSI2A" if collection == "SENTINEL-2" else None,
                    cloud_cover_max=cloud_max,
                    top=20,
                )
                st.session_state.cds_results = results
            except Exception as e:
                st.error(f"Copernicus search failed: {e}")
                return

    results = st.session_state.get("cds_results")
    if not results:
        st.info("Set an area and date range, then hit **Search Sentinel catalogue**.")
        return

    st.html(f"""<div class="snap-card"><div class="snap-label">Products found</div>
        <div class="snap-value" style="font-size:1.6rem">{len(results)}</div>
        <div class="snap-sub">{collection} over selected area/date range</div></div>""")

    st.html("<div style='height:1rem'></div>")
    rows = [{
        "Name": r.get("Name"),
        "Sensed": (r.get("ContentDate") or {}).get("Start"),
        "Size (MB)": round((r.get("ContentLength") or 0) / 1_000_000, 1),
        "Id": r.get("Id"),
    } for r in results]
    st.dataframe(pd.DataFrame(rows), width='stretch')

    with st.expander("Raw first result"):
        st.json(results[0] if results else {})


# ---------------------------------------------------------------------------
# FARM RECORDS — farmOS
# ---------------------------------------------------------------------------

def _render_farmos():
    st.html('<span class="layer-tag tag-farmos">farmOS · Self-hosted farm record-keeping</span>')

    try:
        import farmos as fos
        available = True
    except Exception as e:
        st.warning(f"farmos.py not available yet ({e}) — copy it into this folder to enable this layer.")
        available = False
    if not available:
        return

    if not fos.FARMOS_URL:
        st.info(
            "farmOS isn't a shared public API — it's software you (or someone) has to "
            "self-host or run via farmOS.net first. Once you have an instance running, "
            "set these in your `.env` file to enable this layer:\n\n"
            "```\nFARMOS_URL=https://yourfarm.farmos.net\n"
            "FARMOS_CLIENT_ID=farm\nFARMOS_CLIENT_SECRET=\n"
            "FARMOS_USERNAME=...\nFARMOS_PASSWORD=...\n```"
        )
        return

    fetch_clicked = st.button("Read farmOS data", key="fetch_farmos", width='stretch')
    first_load = "farmos_data" not in st.session_state
    if fetch_clicked or first_load:
        with st.spinner("Logging into farmOS..."):
            try:
                tokens = fos.get_access_token()
                token = tokens["access_token"]
                fields = fos.get_areas(token)
                logs = fos.get_logs(token, bundle="observation")
                st.session_state.farmos_data = {"fields": fields, "logs": logs}
            except Exception as e:
                st.error(f"farmOS read failed: {e}")
                return

    data = st.session_state.get("farmos_data")
    if not data:
        st.info("Hit **Read farmOS data**.")
        return

    fields, logs = data["fields"], data["logs"]

    s1, s2 = st.columns(2)
    with s1:
        st.html(f"""<div class="snap-card"><div class="snap-label">Fields (land assets)</div>
            <div class="snap-value" style="font-size:1.6rem">{len(fields)}</div>
            <div class="snap-sub">from asset/land</div></div>""")
    with s2:
        st.html(f"""<div class="snap-card"><div class="snap-label">Observation logs</div>
            <div class="snap-value" style="font-size:1.6rem">{len(logs)}</div>
            <div class="snap-sub">from log/observation</div></div>""")

    st.html("<div style='height:1.2rem'></div>")

    tab1, tab2 = st.tabs(["📋 Fields", "📝 Observations"])
    with tab1:
        if fields:
            st.dataframe(pd.DataFrame([{"Name": f["name"], "Status": f["status"], "ID": f["id"]} for f in fields]), width='stretch')
        else:
            st.caption("No land assets found on this farmOS instance.")
    with tab2:
        if logs:
            st.dataframe(pd.DataFrame([{"Name": l["name"], "Status": l["status"], "ID": l["id"]} for l in logs]), width='stretch')
        else:
            st.caption("No observation logs found on this farmOS instance.")


# ==================== FARM MAP (Digital Twin) ====================

def _yield_to_color(value, low, high):
    """
    Interpolates between amber (low yield) and green (high yield),
    matching the app's GRANTS -> ACCENT theme colors.
    Returns a hex string. Falls back to muted gray if value/range is invalid.
    """
    if value is None or high is None or low is None or high <= low:
        return DEFAULT_CROP_COLOR

    t = max(0.0, min(1.0, (value - low) / (high - low)))

    low_rgb = (224, 169, 62)   # GRANTS (amber) — low yield
    high_rgb = (143, 209, 79)  # ACCENT (green) — high yield

    r = int(low_rgb[0] + (high_rgb[0] - low_rgb[0]) * t)
    g = int(low_rgb[1] + (high_rgb[1] - low_rgb[1]) * t)
    b = int(low_rgb[2] + (high_rgb[2] - low_rgb[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _field_polygon(center_lat, center_lon, acres, aspect=1.15):
    """
    Build a simple rectangular polygon centered at (center_lat, center_lon),
    sized so its area roughly matches `acres`. Used when we don't have a
    real surveyed boundary for the field yet.
    """
    acre_to_m2 = 4046.86
    area_m2 = max(acres, 0.5) * acre_to_m2
    width_m = math.sqrt(area_m2 * aspect)
    height_m = math.sqrt(area_m2 / aspect)

    # meters -> degrees (rough, fine at field scale)
    dlat = (height_m / 2) / 111320
    dlon = (width_m / 2) / (111320 * math.cos(math.radians(center_lat)))

    return [
        [center_lat - dlat, center_lon - dlon],
        [center_lat - dlat, center_lon + dlon],
        [center_lat + dlat, center_lon + dlon],
        [center_lat + dlat, center_lon - dlon],
    ]


def build_field_map(fields, center_lat, center_lon):
    """
    Lays fields out in a grid around (center_lat, center_lon), sized by
    acreage, colored by yield (amber = low, green = high). Real satellite
    imagery base layer with optional street/dark toggles.

    Swap in real boundary coordinates per field (e.g. field['boundary'])
    once you have surveyed/GPS data — the polygon call is the only thing
    that needs to change.
    """
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

    # Real satellite imagery as the default base layer
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

        # field name label directly on the map
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
    show_page_ai("Farm Map", data, "Which mapped fields should I inspect first based on acreage and recorded yield?")

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
    st_folium(fmap, width='stretch', height=560)

    # yield gradient legend
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

    # best / worst yield callouts
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
    st.dataframe(pd.DataFrame(fields), width='stretch')


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
                 "Soil Analysis", "Compliance", "🛰️ Field Intelligence", "AI Suggestions", "AI Copilot", "👤 My Profile"],
                icons=["house", "geo-alt", "tractor", "gear", "cloud-sun",
                       "droplet", "clipboard-check", "broadcast", "lightbulb", "robot", "person"],
                menu_icon="cast",
                default_index=0,
                styles=OPTION_MENU_STYLE,
            )

            st.markdown("---")
            if st.button("🚪 Logout", width='stretch'):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.user_id = None
                st.session_state.copilot_messages = []
                st.session_state.ai_suggestions = None
                st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Login", width='stretch')
                    if submitted:
                        user = db.get_user(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = user['username']
                            st.session_state.user_id = user['id']
                            st.session_state.copilot_messages = []
                            st.session_state.ai_suggestions = None
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            with tab2:
                st.markdown("### 📝 New User?")
                if st.button("Create Account", width='stretch'):
                    st.session_state.page = 'register'
                    st.rerun()

    if st.session_state.authenticated:
        if selected == "🛰️ Field Intelligence":
            data = load_user_data(st.session_state.user_id)
            show_field_intelligence(data)
            return

        data = load_user_data(st.session_state.user_id)

        if selected == "👤 My Profile":
            show_profile(data)
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
        elif selected == "AI Suggestions":
            show_ai_suggestions(data)
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
