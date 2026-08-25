# """
# AgroIntel — Orbit to Soil
# --------------------------
# Two altitudes of data on one field:
#   ORBIT       -> NASA POWER (satellite/reanalysis agro-climatology)
#   ATMOSPHERE  -> OpenWeather (live conditions)

# Run:
#     pip install streamlit requests python-dotenv pandas plotly
#     streamlit run app.py

# Keep app.py, nasapower.py, openweather.py, and your .env in the same folder.
# """

# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# from datetime import datetime, timedelta

# from nasapower import get_agro_weather_flat, safe_end_date
# from openweather import get_weather
# from rvo import get_agri_subsidies

# try:
#     from deep_translator import GoogleTranslator
#     TRANSLATE_AVAILABLE = True
# except Exception:
#     TRANSLATE_AVAILABLE = False
# from rvo import get_agri_subsidies


# # ---------------------------------------------------------------------------
# # Page config + theme
# # ---------------------------------------------------------------------------

# st.set_page_config(
#     page_title="AgroIntel — Orbit to Soil",
#     page_icon="🛰️",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# BG = "#0A120D"
# PANEL = "#101B14"
# PANEL2 = "#16231A"
# LINE = "#223326"
# ORBIT = "#6E8CE0"
# ORBIT_DIM = "#33406B"
# ATMOS = "#4FAFD8"
# ATMOS_DIM = "#2E4A56"
# GRANTS = "#E0A93E"
# GRANTS_DIM = "#4A3D22"
# TEXT = "#E9EEE7"
# MUTED = "#7F9482"
# ACCENT = "#8FD14F"
# WARN = "#E0965B"

# PLOTLY_FONT = dict(family="IBM Plex Mono, monospace", color=MUTED, size=12)

# st.markdown(f"""
# <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">

# <style>
# html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}

# .stApp {{
#     background: radial-gradient(ellipse at top, #0D1A12 0%, {BG} 55%);
#     color: {TEXT};
# }}
# #MainMenu, header, footer {{visibility: hidden;}}

# .hero {{
#     padding: 2.2rem 0 1rem 0;
#     border-bottom: 1px solid {LINE};
#     margin-bottom: 1.8rem;
# }}
# .hero-eyebrow {{
#     font-family: 'IBM Plex Mono', monospace;
#     color: {ACCENT};
#     letter-spacing: 0.25em;
#     font-size: 0.72rem;
#     text-transform: uppercase;
#     margin-bottom: 0.4rem;
# }}
# .hero-title {{
#     font-family: 'Space Grotesk', sans-serif;
#     font-weight: 700;
#     font-size: 2.6rem;
#     line-height: 1.05;
#     margin: 0;
#     background: linear-gradient(90deg, #EDF3EA 0%, #9FE870 100%);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
# }}
# .hero-sub {{ color: {MUTED}; font-size: 0.98rem; margin-top: 0.5rem; max-width: 620px; }}

# div[data-testid="stButton"] > button {{
#     width: 100%;
#     border-radius: 10px;
#     border: 1px solid {LINE};
#     background: {PANEL};
#     color: {TEXT};
#     font-family: 'Space Grotesk', sans-serif;
#     font-weight: 600;
#     letter-spacing: 0.03em;
#     padding: 0.9rem 0.5rem;
#     transition: all 0.15s ease;
# }}
# div[data-testid="stButton"] > button:hover {{
#     border-color: {ACCENT}; color: {ACCENT}; transform: translateY(-1px);
# }}
# div[data-testid="stButton"] > button:focus:not(:active) {{ border-color: {ACCENT}; color: {ACCENT}; }}

# .layer-tag {{
#     font-family: 'IBM Plex Mono', monospace;
#     font-size: 0.68rem; letter-spacing: 0.2em; text-transform: uppercase;
#     padding: 0.2rem 0.6rem; border-radius: 999px; display: inline-block; margin-bottom: 0.8rem;
# }}
# .tag-orbit {{ background: {ORBIT_DIM}; color: #C3CDF5; }}
# .tag-atmos {{ background: {ATMOS_DIM}; color: #B4E4F5; }}
# .tag-grants {{ background: {GRANTS_DIM}; color: #F5D9A0; }}

# .subsidy-card {{
#     background: {PANEL}; border: 1px solid {LINE}; border-radius: 12px;
#     padding: 1.1rem 1.3rem; margin-bottom: 0.7rem;
#     transition: border-color 0.15s ease;
# }}
# .subsidy-card:hover {{ border-color: {GRANTS}; }}
# .subsidy-title {{
#     font-family: 'Space Grotesk', sans-serif; font-weight: 600;
#     font-size: 1.05rem; color: {TEXT}; margin-bottom: 0.3rem;
# }}
# .subsidy-intro {{ color: {MUTED}; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.5rem; }}
# .subsidy-link {{
#     font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
#     color: {GRANTS}; text-decoration: none; letter-spacing: 0.02em;
# }}
# .subsidy-link:hover {{ text-decoration: underline; }}

# .panel {{
#     background: {PANEL}; border: 1px solid {LINE}; border-radius: 14px;
#     padding: 1.6rem 1.8rem; margin-top: 0.4rem;
# }}

# .snap-card {{
#     background: {PANEL}; border: 1px solid {LINE}; border-radius: 12px;
#     padding: 1.1rem 1.3rem;
# }}
# .snap-label {{
#     font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
#     text-transform: uppercase; letter-spacing: 0.15em; color: {MUTED};
# }}
# .snap-value {{
#     font-family: 'IBM Plex Mono', monospace; font-size: 2.1rem; font-weight: 600; color: {TEXT};
# }}
# .snap-sub {{ color: {MUTED}; font-size: 0.85rem; }}

# hr {{ border-color: {LINE}; }}

# [data-testid="stMetricValue"] {{ font-family: 'IBM Plex Mono', monospace; color: {TEXT}; }}
# [data-testid="stMetricLabel"] {{
#     font-family: 'IBM Plex Mono', monospace; color: {MUTED};
#     text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.1em;
# }}

# .stTextInput input, .stNumberInput input {{
#     background: {PANEL2}; color: {TEXT}; border: 1px solid {LINE};
#     font-family: 'IBM Plex Mono', monospace;
# }}
# </style>
# """, unsafe_allow_html=True)


# def plotly_dark(fig, height=320):
#     fig.update_layout(
#         paper_bgcolor="rgba(0,0,0,0)",
#         plot_bgcolor="rgba(0,0,0,0)",
#         font=PLOTLY_FONT,
#         margin=dict(l=10, r=10, t=30, b=10),
#         height=height,
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=PLOTLY_FONT),
#     )
#     fig.update_xaxes(gridcolor=LINE, zeroline=False)
#     fig.update_yaxes(gridcolor=LINE, zeroline=False)
#     return fig


# # ---------------------------------------------------------------------------
# # Hero
# # ---------------------------------------------------------------------------

# st.markdown("""
# <div class="hero">
#     <div class="hero-eyebrow">AGROINTEL // FIELD INTELLIGENCE</div>
#     <h1 class="hero-title">Orbit to Soil</h1>
#     <p class="hero-sub">
#         Satellite climatology from orbit, live atmosphere overhead,
#         funding on the ground — one field, read from three angles.
#     </p>
# </div>
# """, unsafe_allow_html=True)


# # ---------------------------------------------------------------------------
# # Layer selector
# # ---------------------------------------------------------------------------

# if "layer" not in st.session_state:
#     st.session_state.layer = "orbit"

# c1, c2, c3 = st.columns(3)
# with c1:
#     if st.button("🛰️  ORBIT — NASA POWER", key="btn_orbit", use_container_width=True):
#         st.session_state.layer = "orbit"
# with c2:
#     if st.button("☁️  ATMOSPHERE — OpenWeather", key="btn_atmos", use_container_width=True):
#         st.session_state.layer = "atmosphere"
# with c3:
#     if st.button("🏛️  GRANTS — RVO NL", key="btn_grants", use_container_width=True):
#         st.session_state.layer = "grants"

# st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)


# # ---------------------------------------------------------------------------
# # ORBIT — NASA POWER
# # ---------------------------------------------------------------------------

# def render_orbit():
#     st.markdown('<span class="layer-tag tag-orbit">Satellite · Reanalysis · Agroclimatology</span>', unsafe_allow_html=True)

#     colA, colB, colC, colD = st.columns([1, 1, 1, 1])
#     with colA:
#         lat = st.number_input("Latitude", value=20.0059, format="%.4f")
#     with colB:
#         lon = st.number_input("Longitude", value=73.7910, format="%.4f")
#     with colC:
#         days = st.slider("Days of history", 3, 21, 10)
#     with colD:
#         st.write("")
#         st.write("")
#         fetch_clicked = st.button("Read orbit data", key="fetch_orbit", use_container_width=True)

#     first_load = "orbit_data" not in st.session_state
#     if fetch_clicked or first_load:
#         with st.spinner("Pulling satellite readings..."):
#             try:
#                 end = safe_end_date()
#                 start = (datetime.strptime(end, "%Y%m%d") - timedelta(days=days - 1)).strftime("%Y%m%d")
#                 rows = get_agro_weather_flat(lat, lon, start, end)
#                 st.session_state.orbit_data = rows
#             except Exception as e:
#                 st.error(f"Orbit read failed: {e}")
#                 return

#     rows = st.session_state.get("orbit_data")
#     if not rows:
#         st.info("Set coordinates and hit **Read orbit data**.")
#         return

#     df = pd.DataFrame(rows).replace(-999.0, pd.NA)
#     df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
#     df = df.dropna(subset=["T2M"])
#     if df.empty:
#         st.warning("No processed data yet for this window — NASA POWER lags a few days behind real-time. Try a shorter history.")
#         return
#     latest = df.iloc[-1]

#     # --- snapshot row ---
#     s1, s2, s3, s4, s5 = st.columns(5)
#     snap_items = [
#         (s1, "Temp (avg)", f"{latest['T2M']:.1f}°C", f"{latest['T2M_MIN']:.0f}° / {latest['T2M_MAX']:.0f}°"),
#         (s2, "Rainfall", f"{latest['PRECTOTCORR']:.1f} mm", "last processed day"),
#         (s3, "Humidity", f"{latest['RH2M']:.0f}%", "relative, 2m"),
#         (s4, "Solar", f"{latest['ALLSKY_SFC_SW_DWN']:.1f}", "kWh/m²/day"),
#         (s5, "Root wetness", f"{latest['GWETROOT']:.2f}", "0 dry – 1 sat."),
#     ]
#     for col, label, value, sub in snap_items:
#         with col:
#             st.markdown(f"""
#             <div class="snap-card">
#                 <div class="snap-label">{label}</div>
#                 <div class="snap-value">{value}</div>
#                 <div class="snap-sub">{sub}</div>
#             </div>
#             """, unsafe_allow_html=True)

#     st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

#     # --- temperature band chart ---
#     fig_temp = go.Figure()
#     fig_temp.add_trace(go.Scatter(
#         x=df["date"], y=df["T2M_MAX"], line=dict(width=0), showlegend=False, hoverinfo="skip"
#     ))
#     fig_temp.add_trace(go.Scatter(
#         x=df["date"], y=df["T2M_MIN"], fill="tonexty", fillcolor="rgba(110,140,224,0.15)",
#         line=dict(width=0), name="Range", hoverinfo="skip"
#     ))
#     fig_temp.add_trace(go.Scatter(
#         x=df["date"], y=df["T2M"], line=dict(color=ORBIT, width=3), name="Avg temp",
#         mode="lines+markers", marker=dict(size=5)
#     ))
#     fig_temp.update_layout(title=dict(text="Temperature range (°C)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
#     st.plotly_chart(plotly_dark(fig_temp), use_container_width=True)

#     ct1, ct2 = st.columns(2)
#     with ct1:
#         fig_rain = go.Figure(go.Bar(x=df["date"], y=df["PRECTOTCORR"], marker_color=ACCENT))
#         fig_rain.update_layout(title=dict(text="Rainfall (mm/day)", font=dict(family="Space Grotesk", color=TEXT, size=15)))
#         st.plotly_chart(plotly_dark(fig_rain, height=280), use_container_width=True)
#     with ct2:
#         fig_soil = go.Figure()
#         fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETTOP"], name="Surface", line=dict(color=WARN, width=2)))
#         fig_soil.add_trace(go.Scatter(x=df["date"], y=df["GWETROOT"], name="Root zone", line=dict(color=ORBIT, width=2)))
#         fig_soil.update_layout(title=dict(text="Soil wetness (0–1)", font=dict(family="Space Grotesk", color=TEXT, size=15)), yaxis_range=[0, 1])
#         st.plotly_chart(plotly_dark(fig_soil, height=280), use_container_width=True)

#     with st.expander("Raw data"):
#         st.dataframe(df, use_container_width=True)


# # ---------------------------------------------------------------------------
# # ATMOSPHERE — OpenWeather
# # ---------------------------------------------------------------------------

# def render_atmosphere():
#     st.markdown('<span class="layer-tag tag-atmos">Live conditions</span>', unsafe_allow_html=True)

#     colA, colB = st.columns([3, 1])
#     with colA:
#         city = st.text_input("City", value="Nashik")
#     with colB:
#         st.write("")
#         st.write("")
#         fetch_clicked = st.button("Read atmosphere", key="fetch_atmos", use_container_width=True)

#     first_load = "atmos_data" not in st.session_state
#     if fetch_clicked or first_load:
#         with st.spinner("Checking overhead conditions..."):
#             try:
#                 data = get_weather(city)
#                 st.session_state.atmos_data = data
#             except Exception as e:
#                 st.error(f"Atmosphere read failed: {e}")
#                 return

#     data = st.session_state.get("atmos_data")
#     if not data:
#         st.info("Enter a city and hit **Read atmosphere**.")
#         return

#     main = data.get("main", {})
#     wind = data.get("wind", {})
#     weather = (data.get("weather") or [{}])[0]
#     icon = weather.get("icon", "01d")
#     temp = main.get("temp", 0)
#     humidity = main.get("humidity", 0)
#     wind_speed = wind.get("speed", 0)
#     clouds = data.get("clouds", {}).get("all", 0)

#     top1, top2 = st.columns([1, 3])
#     with top1:
#         st.image(f"https://openweathermap.org/img/wn/{icon}@4x.png", width=140)
#     with top2:
#         st.markdown(f"""
#         <div class="snap-value" style="font-size:3rem">{temp}<span style="font-size:1.3rem;color:{MUTED}">°C</span></div>
#         <div class="snap-sub" style="font-size:1rem">{weather.get('description','').title()} · feels like {main.get('feels_like','—')}°C</div>
#         <div class="snap-sub">{data.get('name','')}, {data.get('sys',{}).get('country','')}</div>
#         """, unsafe_allow_html=True)

#     st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

#     m1, m2, m3, m4 = st.columns(4)
#     for col, label, value, sub in [
#         (m1, "Humidity", f"{humidity}%", "relative"),
#         (m2, "Pressure", f"{main.get('pressure','—')}", "hPa"),
#         (m3, "Wind", f"{wind_speed}", "m/s"),
#         (m4, "Cloud cover", f"{clouds}%", "sky coverage"),
#     ]:
#         with col:
#             st.markdown(f"""
#             <div class="snap-card">
#                 <div class="snap-label">{label}</div>
#                 <div class="snap-value">{value}</div>
#                 <div class="snap-sub">{sub}</div>
#             </div>
#             """, unsafe_allow_html=True)

#     st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

#     g1, g2 = st.columns(2)
#     with g1:
#         fig_h = go.Figure(go.Indicator(
#             mode="gauge+number",
#             value=humidity,
#             title={"text": "Humidity %", "font": {"family": "Space Grotesk", "color": TEXT, "size": 14}},
#             number={"font": {"family": "IBM Plex Mono", "color": TEXT}},
#             gauge={
#                 "axis": {"range": [0, 100], "tickcolor": MUTED},
#                 "bar": {"color": ATMOS},
#                 "bgcolor": PANEL2,
#                 "borderwidth": 0,
#             },
#         ))
#         st.plotly_chart(plotly_dark(fig_h, height=260), use_container_width=True)
#     with g2:
#         fig_c = go.Figure(go.Indicator(
#             mode="gauge+number",
#             value=clouds,
#             title={"text": "Cloud cover %", "font": {"family": "Space Grotesk", "color": TEXT, "size": 14}},
#             number={"font": {"family": "IBM Plex Mono", "color": TEXT}},
#             gauge={
#                 "axis": {"range": [0, 100], "tickcolor": MUTED},
#                 "bar": {"color": ACCENT},
#                 "bgcolor": PANEL2,
#                 "borderwidth": 0,
#             },
#         ))
#         st.plotly_chart(plotly_dark(fig_c, height=260), use_container_width=True)


# # ---------------------------------------------------------------------------
# # GRANTS — RVO Netherlands
# # ---------------------------------------------------------------------------

# def render_grants():
#     st.markdown('<span class="layer-tag tag-grants">Netherlands Enterprise Agency · Open Data</span>', unsafe_allow_html=True)

#     colA, colB = st.columns([3, 1])
#     with colA:
#         st.caption("Dutch government funding schemes open to agricultural businesses — no auth required, pulled live from RVO's open data API.")
#     with colB:
#         fetch_clicked = st.button("Read grants", key="fetch_grants", use_container_width=True)

#     first_load = "grants_data" not in st.session_state
#     if fetch_clicked or first_load:
#         with st.spinner("Checking in with RVO..."):
#             try:
#                 items = get_agri_subsidies()
#                 st.session_state.grants_data = items
#             except Exception as e:
#                 st.error(f"Grants read failed: {e}")
#                 return

#     items = st.session_state.get("grants_data")
#     if not items:
#         st.info("Hit **Read grants** to pull the latest agricultural funding schemes.")
#         return

#     # --- snapshot row ---
#     s1, s2, s3 = st.columns(3)
#     subject_counts = {}
#     for item in items:
#         for subj in item.get("subjects", []):
#             subject_counts[subj] = subject_counts.get(subj, 0) + 1
#     top_subject = max(subject_counts, key=subject_counts.get) if subject_counts else "—"

#     for col, label, value, sub in [
#         (s1, "Schemes found", str(len(items)), "matching agricultural sector"),
#         (s2, "Top category", top_subject, f"{subject_counts.get(top_subject, 0)} schemes"),
#         (s3, "Source", "RVO.nl", "open data, live"),
#     ]:
#         with col:
#             st.markdown(f"""
#             <div class="snap-card">
#                 <div class="snap-label">{label}</div>
#                 <div class="snap-value" style="font-size:1.4rem">{value}</div>
#                 <div class="snap-sub">{sub}</div>
#             </div>
#             """, unsafe_allow_html=True)

#     st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

#     # --- category distribution chart ---
#     if subject_counts:
#         sorted_items = sorted(subject_counts.items(), key=lambda x: x[1])
#         fig = go.Figure(go.Bar(
#             x=[v for _, v in sorted_items],
#             y=[k for k, _ in sorted_items],
#             orientation="h",
#             marker_color=GRANTS,
#         ))
#         fig.update_layout(title=dict(text="Schemes by category", font=dict(family="Space Grotesk", color=TEXT, size=15)))
#         st.plotly_chart(plotly_dark(fig, height=max(220, 40 * len(subject_counts))), use_container_width=True)

#     st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

#     # --- translation toggle ---
#     tcol1, tcol2 = st.columns([3, 1])
#     with tcol1:
#         search = st.text_input("Filter by keyword", placeholder="e.g. mest, energie, krediet")
#     with tcol2:
#         st.write("")
#         if TRANSLATE_AVAILABLE:
#             translate_on = st.toggle("🌐 Translate to English", key="translate_grants")
#         else:
#             translate_on = False
#             st.caption("Install `deep-translator` to enable translation.")

#     filtered = items
#     if search:
#         s = search.lower()
#         filtered = [i for i in items if s in i["title"].lower() or s in i.get("intro", "").lower()]

#     if "translation_cache" not in st.session_state:
#         st.session_state.translation_cache = {}

#     def translated(item):
#         """Returns (title, intro) — translated + cached if toggle is on, original otherwise."""
#         if not translate_on:
#             return item["title"], item.get("intro", "")

#         cache = st.session_state.translation_cache
#         item_id = item["id"]
#         if item_id in cache:
#             return cache[item_id]["title"], cache[item_id]["intro"]

#         try:
#             translator = GoogleTranslator(source="nl", target="en")
#             title_en = translator.translate(item["title"])
#             intro_en = translator.translate(item.get("intro", "")[:400])  # translator has a length cap
#             cache[item_id] = {"title": title_en, "intro": intro_en}
#             return title_en, intro_en
#         except Exception:
#             return item["title"], item.get("intro", "")  # fall back to original on failure

#     # --- cards ---
#     if translate_on:
#         with st.spinner("Translating..."):
#             for item in filtered:
#                 title, intro = translated(item)
#                 st.markdown(f"""
#                 <div class="subsidy-card">
#                     <div class="subsidy-title">{title}</div>
#                     <div class="subsidy-intro">{intro[:220].rsplit(' ', 1)[0]}...</div>
#                     <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a>
#                 </div>
#                 """, unsafe_allow_html=True)
#     else:
#         for item in filtered:
#             st.markdown(f"""
#             <div class="subsidy-card">
#                 <div class="subsidy-title">{item['title']}</div>
#                 <div class="subsidy-intro">{item.get('intro', '')[:220].rsplit(' ', 1)[0]}...</div>
#                 <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a>
#             </div>
#             """, unsafe_allow_html=True)

#     if not filtered:
#         st.caption("No schemes match that filter.")


# # ---------------------------------------------------------------------------
# # Render
# # ---------------------------------------------------------------------------

# if st.session_state.layer == "orbit":
#     render_orbit()
# elif st.session_state.layer == "atmosphere":
#     render_atmosphere()
# else:
#     render_grants()





"""
AgroIntel — Universal Agricultural Intelligence Platform
------------------------------------------------------------
Merged app:
  - Login / registration / farm management / machinery / soil / compliance /
    AI copilot (originally built against database.py + ai_service_free.py)
  - Field Intelligence: live NASA POWER / OpenWeather / RVO NL dashboard
    (nasapower.py, openweather.py, rvo.py)

Requires in the same folder:
    app.py, database.py, ai_service_free.py,
    nasapower.py, openweather.py, rvo.py, .env

Run:
    pip install streamlit streamlit-option-menu pandas plotly requests
                python-dotenv deep-translator
    streamlit run app.py
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
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


# ==================== SESSION STATE ====================

for key, default in {
    'authenticated': False,
    'username': None,
    'user_id': None,
    'page': 'login',
    'ai_question': '',
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
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif;
    }}

    .stApp {{
        background: radial-gradient(
            ellipse at top,
            #0D1A12 0%,
            {BG} 55%
        );
        color: {TEXT};
    }}

    #MainMenu, header, footer {{
        visibility: hidden;
    }}

    /* ==================== HEADER ==================== */

    .main-header {{
        background: linear-gradient(
            135deg,
            {PANEL} 0%,
            {PANEL2} 100%
        );
        border: 1px solid {LINE};
        padding: 1.6rem 2rem;
        border-radius: 14px;
        margin-bottom: 2rem;
    }}

    .main-header h1 {{
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(
            90deg,
            #EDF3EA 0%,
            {ACCENT} 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    .main-header p {{
        margin: 0.3rem 0 0 0;
        color: {MUTED};
        font-size: 1rem;
    }}

    /* ==================== METRIC CARDS ==================== */

    .metric-card {{
        background: {PANEL};
        border: 1px solid {LINE};
        border-left: 4px solid {ACCENT};
        padding: 1.3rem 1.5rem;
        border-radius: 12px;
        height: 100%;
        transition: transform 0.15s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        border-color: {ACCENT};
    }}

    .metric-value {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.1rem;
        font-weight: 600;
        color: {TEXT};
        margin: 0.3rem 0;
    }}

    .metric-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {MUTED};
        font-weight: 500;
    }}

    .metric-sub {{
        font-size: 0.8rem;
        color: {MUTED};
    }}

    /* ==================== SECTION TITLES ==================== */

    .section-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: {TEXT};
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {LINE};
    }}

    /* ==================== AI CARDS ==================== */

    .ai-card {{
        background: {PANEL2};
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid {ORBIT_DIM};
        height: 100%;
        transition: transform 0.15s ease;
    }}

    .ai-card:hover {{
        transform: translateY(-2px);
        border-color: {ORBIT};
    }}

    .ai-card h4 {{
        color: {ACCENT};
        margin-top: 0;
        font-family: 'Space Grotesk', sans-serif;
    }}

    .ai-card .confidence {{
        background: {ORBIT_DIM};
        color: {TEXT};
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }}

    /* ==================== STATUS ==================== */

    .status-badge {{
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }}

    .status-badge.success {{
        background: {ORBIT_DIM};
        color: {ACCENT};
    }}

    .status-badge.warning {{
        background: {GRANTS_DIM};
        color: {WARN};
    }}

    .status-badge.info {{
        background: {ATMOS_DIM};
        color: {ATMOS};
    }}

    .status-badge.danger {{
        background: #3A1F1A;
        color: {DANGER};
    }}

    /* ==================== SIDEBAR ==================== */

    .sidebar-brand {{
        text-align: center;
        padding: 1rem 0;
    }}

    .sidebar-brand h2 {{
        margin: 0;
        font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(
            90deg,
            #EDF3EA 0%,
            {ACCENT} 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    .sidebar-brand p {{
        color: {MUTED};
        font-size: 0.8rem;
    }}

    /* ==================== FIELD CARDS ==================== */

    .field-card {{
        background: {PANEL};
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border: 1px solid {LINE};
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .field-card .field-name {{
        font-weight: 600;
        color: {TEXT};
    }}

    .crop-tag {{
        background: {ORBIT_DIM};
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-size: 0.75rem;
        color: {ACCENT};
        font-family: 'IBM Plex Mono', monospace;
    }}

    /* ==================== WELCOME PAGE ==================== */

    .welcome-container {{
        text-align: center;
        padding: 4rem 2rem;
    }}

    .welcome-container .emoji {{
        font-size: 4rem;
    }}

    .welcome-container h1 {{
        margin: 1rem 0;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        background: linear-gradient(
            90deg,
            #EDF3EA 0%,
            {ACCENT} 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    .welcome-container p {{
        font-size: 1.15rem;
        color: {MUTED};
    }}

    .welcome-container .sub-text {{
        color: {MUTED};
        font-size: 0.9rem;
    }}

    /* ==================== DATA ENTRY ==================== */

    .data-entry-card {{
        background: {PANEL};
        border: 1px solid {LINE};
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }}

    .data-entry-card h3 {{
        color: {TEXT};
        margin-top: 0;
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* ==================== API STATUS ==================== */

    .api-status {{
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
    }}

    .api-status.connected {{
        background: {ORBIT_DIM};
        border: 1px solid {ACCENT};
        color: {TEXT};
    }}

    .api-status.disconnected {{
        background: {GRANTS_DIM};
        border: 1px solid {WARN};
        color: {TEXT};
    }}

    /* ==================== BUTTONS ==================== */

    div[data-testid="stButton"] > button {{
        width: 100%;
        border-radius: 10px;
        border: 1px solid {LINE};
        background: {PANEL};
        color: {TEXT};
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        letter-spacing: 0.02em;
        padding: 0.7rem 0.9rem;
        transition: all 0.15s ease;
    }}

    div[data-testid="stButton"] > button:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
        transform: translateY(-1px);
    }}

    div[data-testid="stButton"] > button:focus:not(:active) {{
        border-color: {ACCENT};
        color: {ACCENT};
    }}

    /* ==================== LAYER TAGS ==================== */

    .layer-tag {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        display: inline-block;
        margin-bottom: 0.8rem;
    }}

    .tag-orbit {{
        background: {ORBIT_DIM};
        color: #C3CDF5;
    }}

    .tag-atmos {{
        background: {ATMOS_DIM};
        color: #B4E4F5;
    }}

    .tag-grants {{
        background: {GRANTS_DIM};
        color: #F5D9A0;
    }}

    /* ==================== SNAP CARDS ==================== */

    .snap-card {{
        background: {PANEL};
        border: 1px solid {LINE};
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
    }}

    .snap-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: {MUTED};
    }}

    .snap-value {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.1rem;
        font-weight: 600;
        color: {TEXT};
    }}

    .snap-sub {{
        color: {MUTED};
        font-size: 0.85rem;
    }}

    /* ==================== SUBSIDY CARDS ==================== */

    .subsidy-card {{
        background: {PANEL};
        border: 1px solid {LINE};
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.7rem;
        transition: border-color 0.15s ease;
    }}

    .subsidy-card:hover {{
        border-color: {GRANTS};
    }}

    .subsidy-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1.05rem;
        color: {TEXT};
        margin-bottom: 0.3rem;
    }}

    .subsidy-intro {{
        color: {MUTED};
        font-size: 0.88rem;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }}

    .subsidy-link {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: {GRANTS};
        text-decoration: none;
    }}

    .subsidy-link:hover {{
        text-decoration: underline;
    }}

    /* ==================== INPUTS ==================== */

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input {{
        background: {PANEL2} !important;
        color: {TEXT} !important;
        border: 1px solid {LINE} !important;
    }}

    [data-testid="stMetricValue"] {{
        font-family: 'IBM Plex Mono', monospace;
        color: {TEXT};
    }}

    [data-testid="stMetricLabel"] {{
        font-family: 'IBM Plex Mono', monospace;
        color: {MUTED};
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.1em;
    }}

    hr {{
        border-color: {LINE};
    }}

    </style>
    """)


apply_custom_css()



OPTION_MENU_STYLE = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": ACCENT, "font-size": "16px"},
    "nav-link": {"font-size": "14px", "text-align": "left", "color": TEXT, "--hover-color": PANEL2},
    "nav-link-selected": {"background-color": ORBIT_DIM, "color": TEXT},
}


# ==================== REGISTRATION PAGE ====================

def show_registration():
    st.markdown("""
        <div class="main-header">
            <h1>📝 Create Your Account</h1>
            <p>Join AgroIntel and start managing your farm intelligently</p>
        </div>
    """, unsafe_allow_html=True)

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

    st.markdown(f"""
        <div class="main-header">
            <h1>👤 My Profile</h1>
            <p>Welcome back, {user['full_name']}!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="data-entry-card"><h3>👤 Personal Information</h3>', unsafe_allow_html=True)
        st.write(f"**Full Name:** {user['full_name']}")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Phone:** {user['phone'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="data-entry-card"><h3>📍 Address Information</h3>', unsafe_allow_html=True)
        st.write(f"**Address:** {user['address'] or 'Not set'}")
        st.write(f"**City:** {user['city'] or 'Not set'}")
        st.write(f"**State:** {user['state'] or 'Not set'}")
        st.write(f"**Country:** {user['country'] or 'Not set'}")
        st.write(f"**Postal Code:** {user['postal_code'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)

    col1, _ = st.columns(2)
    with col1:
        st.markdown('<div class="data-entry-card"><h3>🚜 Farm Information</h3>', unsafe_allow_html=True)
        st.write(f"**Farm Name:** {user['farm_name'] or 'Not set'}")
        st.write(f"**Farm Size:** {user['farm_size'] or 0} acres")
        st.write(f"**Farm Type:** {user['farm_type'] or 'Not set'}")
        st.markdown("</div>", unsafe_allow_html=True)


# ==================== DASHBOARD PAGE ====================

def show_dashboard(data):
    st.markdown(f"""
        <div class="main-header">
            <h1>🌾 AgroIntel Dashboard</h1>
            <p>Welcome back! Here's your farm overview for {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">🌱 Total Acres</div>
            <div class="metric-value">{data['total_acres']:,.0f}</div>
            <div class="metric-sub">acres under cultivation</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📊 Average Yield</div>
            <div class="metric-value">{data['avg_yield']} t/ha</div>
            <div class="metric-sub">across all fields</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">🚜 Active Machinery</div>
            <div class="metric-value">{data['active_machinery']}/{data['total_machinery']}</div>
            <div class="metric-sub">units operational</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📋 Compliance Score</div>
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-sub">overall compliance rating</div></div>""", unsafe_allow_html=True)

    if data['fields']:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">📊 Yield by Field</div>', unsafe_allow_html=True)
            df_fields = pd.DataFrame(data['fields'])
            fig = px.bar(df_fields, x='name', y='yield', color='crop', text='yield',
                         color_discrete_sequence=CHART_SEQUENCE)
            fig.update_traces(texttemplate='%{text:.1f} t/ha', textposition='outside')
            fig.update_layout(xaxis_title='', yaxis_title='Yield (t/ha)')
            st.plotly_chart(plotly_dark(fig, height=350), use_container_width=True)
        with col2:
            st.markdown('<div class="section-title">🌾 Crop Distribution</div>', unsafe_allow_html=True)
            df_fields = pd.DataFrame(data['fields'])
            fig = px.pie(df_fields, values='acres', names='crop', color_discrete_sequence=CHART_SEQUENCE)
            st.plotly_chart(plotly_dark(fig, height=350), use_container_width=True)
    else:
        st.info("No field data available. Add your first field in Farm Management!")

    if data['ai_recommendations']:
        st.markdown('<div class="section-title">🤖 AI-Powered Insights</div>', unsafe_allow_html=True)
        cols = st.columns(min(3, len(data['ai_recommendations'])))
        for idx, recommendation in enumerate(data['ai_recommendations'][:3]):
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class="ai-card">
                        <h4>{recommendation['title']}</h4>
                        <p><strong>{recommendation['field']}</strong></p>
                        <p>{recommendation['recommendation']}</p>
                        <span class="confidence">ROI: {recommendation['roi']}</span>
                        <span class="confidence" style="margin-left:0.5rem;">Confidence: {recommendation['confidence']}%</span>
                    </div>
                """, unsafe_allow_html=True)


# ==================== FARM MANAGEMENT PAGE ====================

def show_farm_management(data):
    st.markdown('<div class="main-header"><h1>🚜 Farm Management</h1></div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-title">📋 Your Fields</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="main-header"><h1>⚙️ Machinery Management</h1></div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-title">📋 Your Machinery</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="main-header"><h1>🧪 Soil Analysis</h1></div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-title">📋 Soil Analysis Data</div>', unsafe_allow_html=True)
    if data['soil']:
        st.dataframe(pd.DataFrame(data['soil']), use_container_width=True)
    else:
        st.info("No soil analysis data available. Add some using the section above!")


# ==================== FARM WEATHER LOG PAGE ====================

def show_weather(data):
    st.markdown('<div class="main-header"><h1>🌤️ Farm Weather Log</h1><p>Historical weather logged for your farm records</p></div>', unsafe_allow_html=True)

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
    st.markdown('<div class="main-header"><h1>📋 Compliance & Reporting</h1></div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{data['compliance_score']}%</div>
            <div class="metric-label">Overall Compliance Score</div>
        </div>
    """, unsafe_allow_html=True)

    if data['compliance']:
        st.dataframe(pd.DataFrame(data['compliance']), use_container_width=True)
    else:
        st.info("No compliance data available")


# ==================== AI COPILOT PAGE ====================

def show_ai_copilot(data):
    st.markdown('<div class="main-header"><h1>🤖 AI Copilot</h1></div>', unsafe_allow_html=True)

    groq_key = os.getenv('GROQ_API_KEY', '')
    if groq_key:
        st.markdown('<div class="api-status connected">🟢 <strong>AI Connected</strong> - Powered by Groq AI (FREE)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status disconnected">🟡 <strong>AI Disconnected</strong> - Click "Get FREE Groq API Key" below to enable</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="ai-card">
            <h4>💬 Ask AgroIntel AI</h4>
            <p>Get predictive, explainable, and actionable guidance for your farm</p>
            <p style="font-size:0.9rem; color:#7F9482; margin-top:0.5rem;">
                💡 Try asking: "What should I plant next season?" or "How is my farm performing?"
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔥 Quick Questions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🌾 Crop Advice", use_container_width=True):
            st.session_state.ai_question = "What crops should I plant next season?"
    with col2:
        if st.button("📊 Farm Performance", use_container_width=True):
            st.session_state.ai_question = "How is my farm performing overall?"
    with col3:
        if st.button("🚜 Machinery Health", use_container_width=True):
            st.session_state.ai_question = "What maintenance do my machines need?"
    with col4:
        if st.button("💰 Profit Optimization", use_container_width=True):
            st.session_state.ai_question = "How can I increase my farm profits?"

    st.markdown("---")

    if not groq_key:
        with st.expander("🔑 Get FREE Groq API Key", expanded=False):
            st.markdown("""
                ### 🆓 Get Your Free Groq API Key (No Credit Card Required)
                1. Go to [Groq Console](https://console.groq.com/)
                2. Sign up with your email (free)
                3. Go to API Keys section
                4. Click "Create API Key"
                5. Copy and paste it below

                🔑 **Pro Tip:** Groq gives you 30 requests per minute for free!
            """)
            api_key = st.text_input("Enter your Groq API Key:", type="password")
            if st.button("💾 Save API Key"):
                if api_key:
                    os.environ['GROQ_API_KEY'] = api_key
                    st.success("✅ API Key saved for this session!")
                    st.rerun()
                else:
                    st.error("❌ Please enter a valid API key")

    user_question = st.text_area(
        "✍️ Ask your question:",
        placeholder="e.g., Which field is most profitable? What should I do about low soil nitrogen?",
        height=80, key="ai_question_input"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        ask_button = st.button("🤖 Ask AI (FREE)", use_container_width=True)

    question = user_question or st.session_state.get('ai_question', '')

    if ask_button and question:
        st.markdown("---")
        with st.spinner("🤔 Analyzing your farm data with AI..."):
            ai = ai_service.GroqAIService()
            result = ai.get_farm_analysis(question, data)

            st.markdown("### 🤖 AI Response")
            if result['success']:
                st.caption(f"⚡ Powered by: {result.get('source', 'Groq AI')} (FREE)")
                st.markdown(f"""
                    <div class="ai-card">
                        <h4>💡 AI Analysis</h4>
                        <div style="white-space: pre-wrap; font-size: 1rem; line-height: 1.6;">
                            {result['response']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ {result.get('error', 'AI error occurred')}")
                st.info("💡 Using offline analysis...")
                st.markdown(f"""
                    <div class="ai-card">
                        <h4>💡 Analysis (Offline Mode)</h4>
                        <div style="white-space: pre-wrap; font-size: 1rem; line-height: 1.6;">
                            {result['response']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        if 'ai_question' in st.session_state:
            del st.session_state.ai_question

        show_related_data(question, data)


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
    st.markdown("""
        <div class="main-header">
            <h1>🛰️ Field Intelligence</h1>
            <p>Satellite climatology from orbit, live atmosphere overhead, funding on the ground.</p>
        </div>
    """, unsafe_allow_html=True)

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

    st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)

    if st.session_state.layer == "orbit":
        _render_orbit()
    elif st.session_state.layer == "atmosphere":
        _render_atmosphere()
    else:
        _render_grants()


def _render_orbit():
    st.markdown('<span class="layer-tag tag-orbit">Satellite · Reanalysis · Agroclimatology</span>', unsafe_allow_html=True)

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
            st.markdown(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value">{value}</div><div class="snap-sub">{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

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
    st.markdown('<span class="layer-tag tag-atmos">Live conditions</span>', unsafe_allow_html=True)

    colA, colB = st.columns([3, 1])
    with colA:
        city = st.text_input("City", value="Nashik")
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
        st.markdown(f"""
        <div class="snap-value" style="font-size:3rem">{temp}<span style="font-size:1.3rem;color:{MUTED}">°C</span></div>
        <div class="snap-sub" style="font-size:1rem">{weather.get('description','').title()} · feels like {main.get('feels_like','—')}°C</div>
        <div class="snap-sub">{data.get('name','')}, {data.get('sys',{}).get('country','')}</div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    for col, label, value, sub in [
        (m1, "Humidity", f"{humidity}%", "relative"),
        (m2, "Pressure", f"{main.get('pressure','—')}", "hPa"),
        (m3, "Wind", f"{wind_speed}", "m/s"),
        (m4, "Cloud cover", f"{clouds}%", "sky coverage"),
    ]:
        with col:
            st.markdown(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value">{value}</div><div class="snap-sub">{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

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
    st.markdown('<span class="layer-tag tag-grants">Netherlands Enterprise Agency · Open Data</span>', unsafe_allow_html=True)

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
            st.markdown(f"""<div class="snap-card"><div class="snap-label">{label}</div>
                <div class="snap-value" style="font-size:1.4rem">{value}</div>
                <div class="snap-sub">{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    if subject_counts:
        sorted_items = sorted(subject_counts.items(), key=lambda x: x[1])
        fig = go.Figure(go.Bar(x=[v for _, v in sorted_items], y=[k for k, _ in sorted_items],
                                orientation="h", marker_color=GRANTS))
        fig.update_layout(title=dict(text="Schemes by category", font=dict(family="Space Grotesk", color=TEXT, size=15)))
        st.plotly_chart(plotly_dark(fig, height=max(220, 40 * len(subject_counts))), use_container_width=True)

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

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
                st.markdown(f"""<div class="subsidy-card"><div class="subsidy-title">{title}</div>
                    <div class="subsidy-intro">{intro[:220].rsplit(' ', 1)[0]}...</div>
                    <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a></div>""",
                    unsafe_allow_html=True)
    else:
        for item in filtered:
            st.markdown(f"""<div class="subsidy-card"><div class="subsidy-title">{item['title']}</div>
                <div class="subsidy-intro">{item.get('intro', '')[:220].rsplit(' ', 1)[0]}...</div>
                <a class="subsidy-link" href="https://www.rvo.nl{item['url']}" target="_blank">Read more on RVO.nl →</a></div>""",
                unsafe_allow_html=True)

    if not filtered:
        st.caption("No schemes match that filter.")


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
        st.markdown("""
            <div class="sidebar-brand">
                <div style="font-size:3rem;">🌾</div>
                <h2>AgroIntel</h2>
                <p>Universal Agricultural Intelligence</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        selected = None

        if st.session_state.authenticated:
            user = db.get_user_by_id(st.session_state.user_id)
            if user:
                st.markdown(f"👋 **Welcome, {user['full_name']}**")
            st.markdown("---")

            selected = option_menu(
                "Navigation",
                ["Dashboard", "Farm Management", "Machinery", "Weather",
                 "Soil Analysis", "Compliance", "🛰️ Field Intelligence", "AI Copilot", "👤 My Profile"],
                icons=["house", "tractor", "gear", "cloud-sun",
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
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
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
            st.markdown("""
                <div class="welcome-container">
                    <div class="emoji">🌾</div>
                    <h1>Welcome to AgroIntel</h1>
                    <p>Universal Agricultural Intelligence Platform</p>
                    <p class="sub-text">Please login or create an account to access your dashboard.</p>
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()