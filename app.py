"""
PcComponentes Blog Audit Dashboard — v6 modular.

Optimisations applied:
  1. Centralised state       → state.py
  2. Pending / applied       → components/sidebar.py
  3. Two‑level caching       → data.py
  4. Modular file structure   → pages/, components/, utils/
  5. Drill‑down (GSC)        → pages/gsc.py + session_state["detail_view"]
  6. Clean orchestrator       → this file
"""

import streamlit as st
import logging

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Page config (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Blog Audit — PcComponentes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init ────────────────────────────────────────────────────────
from state import init_state
from styles import inject_css, register_altair_theme
from components.auth import render_login
from components.sidebar import render_sidebar
from data import fetch_all_sheets, get_filtered_master

init_state()
inject_css()
register_altair_theme()

# ── Auth gate ───────────────────────────────────────────────────
if not render_login():
    st.stop()

# ── Load data (level‑1 cache — heavy, TTL 1 h) ─────────────────
try:
    df_master, df_alerts, df_gsc_perf, df_gsc_delta = fetch_all_sheets()
except RuntimeError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    logging.exception("Unexpected error loading data")
    st.error(f"Error inesperado: {e}")
    st.info("Configura `SPREADSHEET_ID` y `GCP_SERVICE_ACCOUNT` en Settings → Secrets")
    st.stop()

if df_master.empty:
    st.warning("No hay datos en URLs_Master. Ejecuta primero el Colab de auditoría.")
    st.stop()

# ── Sidebar (writes to pending_filters, applies on button) ─────
render_sidebar(df_master)

# ── Filtered data (level‑2 cache — light, session_state) ───────
df_filtered = get_filtered_master(df_master)

# ── Navigation ──────────────────────────────────────────────────
NAV = ["Dashboard", "Explorador", "Alertas", "Análisis", "GSC"]
active = st.radio("nav", NAV, horizontal=True, label_visibility="collapsed")

# ── Routing — only the active page renders ──────────────────────
if active == "Dashboard":
    from pages.dashboard import render
    render(df_filtered)

elif active == "Explorador":
    from pages.explorer import render
    render(df_filtered)

elif active == "Alertas":
    from pages.alerts import render
    render(df_alerts=df_alerts)

elif active == "Análisis":
    from pages.analysis import render
    render(df_filtered)

elif active == "GSC":
    from pages.gsc import render
    render(
        df_filtered=df_filtered,
        df_gsc_perf=df_gsc_perf,
        df_gsc_delta=df_gsc_delta,
    )
