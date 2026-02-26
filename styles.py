"""
Metabase‑inspired visual layer.

• ``inject_css()`` — injects the full CSS block via ``st.markdown``.
• ``register_altair_theme()`` — registers + enables a global Altair theme.
• Colour constants reusable across pages.
"""

import streamlit as st
import altair as alt

# ── Palette ─────────────────────────────────────────────────────
COLORS = [
    "#4C9AFF", "#7F56D9", "#EF6C6C", "#F0A756", "#51CF66",
    "#36B5A0", "#A78BFA", "#FB923C", "#64748B", "#EC4899",
]

BLUE = "#4C9AFF"
PURPLE = "#7F56D9"
RED = "#EF6C6C"
ORANGE = "#F0A756"
GREEN = "#51CF66"
TEAL = "#36B5A0"
GREY = "#64748B"
DARK = "#2E353B"
MUTED = "#696E7A"
BORDER = "#E8ECF0"
BG_LIGHT = "#F5F7FA"

STATUS_COLORS = {"200": GREEN, "301": ORANGE, "404": RED}
SEVERITY_COLORS = {"ALTA": RED, "MEDIA": ORANGE, "BAJA": BLUE}
VIGENCIA_DOMAIN = ["evergreen", "evergreen_actualizable", "caduco"]
VIGENCIA_RANGE = [GREEN, ORANGE, RED]

# ── Chart styling dict (reusable in Plotly / raw HTML) ──────────
CHART_STYLE = {
    "font": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    "title_size": 14,
    "label_size": 11,
    "grid_color": "#F0F2F5",
    "domain_color": BORDER,
}


# ── Altair theme ────────────────────────────────────────────────
def _metabase_theme():
    return {
        "config": {
            "font": CHART_STYLE["font"],
            "title": {
                "fontSize": CHART_STYLE["title_size"],
                "color": DARK,
                "anchor": "start",
                "fontWeight": 600,
                "offset": 12,
            },
            "axis": {
                "gridColor": CHART_STYLE["grid_color"],
                "domainColor": CHART_STYLE["domain_color"],
                "labelColor": MUTED,
                "titleColor": DARK,
                "labelFontSize": CHART_STYLE["label_size"],
                "titleFontSize": 12,
            },
            "legend": {"labelColor": MUTED, "labelFontSize": CHART_STYLE["label_size"]},
            "view": {"strokeWidth": 0},
            "background": "transparent",
            "range": {"category": COLORS},
            "arc": {"innerRadius": 60},
        }
    }


def register_altair_theme():
    alt.themes.register("metabase", _metabase_theme)
    alt.themes.enable("metabase")


# ── CSS ─────────────────────────────────────────────────────────
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap&subset=latin');

    /* === GLOBAL === */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background-color: #2E353B;
        color: #E0E0E0;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] label {
        color: #C5CDD5 !important;
    }
    section[data-testid="stSidebar"] hr { border-color: #3E454C; }
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div {
        background-color: #363E46;
        border-color: #4A535C;
        color: #E0E0E0;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background-color: #363E46;
        border-color: #4A535C;
        color: #E0E0E0;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #4C9AFF;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3A87E8;
    }

    /* === Apply filters button — highlighted when filters are dirty === */
    .apply-btn-dirty button {
        background-color: #F0A756 !important;
        animation: pulse-border 1.5s infinite;
    }
    @keyframes pulse-border {
        0%, 100% { box-shadow: 0 0 0 0 rgba(240,167,86,0.5); }
        50% { box-shadow: 0 0 0 6px rgba(240,167,86,0); }
    }

    /* === KPI CARDS === */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] label {
        color: #696E7A !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #2E353B !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }

    /* === NAV RADIO — Metabase tabs === */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 0;
        border-bottom: 2px solid #E8ECF0;
    }
    div[data-testid="stRadio"] > div > label {
        padding: 10px 20px;
        font-weight: 500;
        font-size: 0.9rem;
        color: #696E7A;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        background-color: transparent;
        cursor: pointer;
    }
    div[data-testid="stRadio"] > div > label:hover { color: #4C9AFF; }
    div[data-testid="stRadio"] > div > label[data-checked="true"] {
        color: #4C9AFF !important;
        border-bottom: 2px solid #4C9AFF !important;
        font-weight: 600;
    }
    div[data-testid="stRadio"] > div > label > div:first-child { display: none; }

    /* === DATAFRAMES === */
    .stDataFrame {
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        overflow: hidden;
    }

    /* === CHART containers === */
    .stVegaLiteChart {
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 8px;
        background: #FFFFFF;
    }

    /* === SECTION HEADERS === */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2E353B;
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #E8ECF0;
    }

    /* === DOWNLOAD / EXPORT === */
    .stDownloadButton > button {
        background-color: #FFFFFF;
        border: 1px solid #D0D5DB;
        color: #4C5564;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.82rem;
    }
    .stDownloadButton > button:hover {
        background-color: #F5F7FA;
        border-color: #4C9AFF;
        color: #4C9AFF;
    }

    /* === HIDE DEFAULTS === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* === LOGIN === */
    .login-container {
        max-width: 380px;
        margin: 8vh auto 0 auto;
        background: #FFFFFF;
        border: 1px solid #E8ECF0;
        border-radius: 10px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .login-title {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        color: #2E353B;
        margin-bottom: 0.3rem;
    }
    .login-subtitle {
        text-align: center;
        font-size: 0.85rem;
        color: #696E7A;
        margin-bottom: 1.5rem;
    }

    /* === GSC delta badges === */
    .delta-up   { color: #51CF66; font-weight: 600; }
    .delta-down { color: #EF6C6C; font-weight: 600; }
    .delta-flat { color: #696E7A; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)
