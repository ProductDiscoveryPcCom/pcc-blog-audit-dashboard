import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
import io

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Blog Audit — PcComponentes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# METABASE-STYLE CSS
# ══════════════════════════════════════════════════════════════
METABASE_CSS = """
<style>
    /* === GLOBAL === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* === SIDEBAR — dark like Metabase nav === */
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
    section[data-testid="stSidebar"] hr {
        border-color: #3E454C;
    }
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

    /* === KPI CARDS — clean Metabase style === */
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

    /* === TABS — Metabase-style top nav === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid #E8ECF0;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 500;
        font-size: 0.9rem;
        color: #696E7A;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #4C9AFF;
    }
    .stTabs [aria-selected="true"] {
        color: #4C9AFF !important;
        border-bottom: 2px solid #4C9AFF !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.2rem;
    }

    /* === DATAFRAMES === */
    .stDataFrame {
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        overflow: hidden;
    }

    /* === PLOTLY CHARTS container === */
    .stPlotlyChart {
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

    /* === DOWNLOAD BUTTONS === */
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

    /* === HIDE STREAMLIT DEFAULT === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* === LOGIN PAGE === */
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
</style>
"""
st.markdown(METABASE_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PLOTLY THEME — Consistent Metabase look
# ══════════════════════════════════════════════════════════════
METABASE_COLORS = ['#4C9AFF', '#7F56D9', '#EF6C6C', '#F0A756', '#51CF66',
                   '#36B5A0', '#A78BFA', '#FB923C', '#64748B', '#EC4899']

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", color="#2E353B", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=42, l=16, r=16, b=16),
    title=dict(font=dict(size=14, color="#2E353B"), x=0, xanchor='left', pad=dict(l=4)),
    legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#E8ECF0"),
    yaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#E8ECF0"),
    colorway=METABASE_COLORS,
    hoverlabel=dict(bgcolor="#2E353B", font_size=12, font_color="white"),
)


def apply_metabase_style(fig, height=380):
    """Apply Metabase visual style to any Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig


# ══════════════════════════════════════════════════════════════
# AUTHENTICATION
# ══════════════════════════════════════════════════════════════
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Blog Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">PcComponentes — Dashboard de contenido</div>', unsafe_allow_html=True)
    password = st.text_input("Contraseña", type="password", label_visibility="collapsed",
                             placeholder="Introduce tu contraseña")
    if st.button("Entrar", use_container_width=True):
        if password == st.secrets.get("APP_PASSWORD", ""):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    """Load all data from Google Sheets. Cache for 5 minutes."""
    creds_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["SPREADSHEET_ID"])

    # URLs Master
    ws_master = sh.worksheet('URLs_Master')
    df = pd.DataFrame(ws_master.get_all_records())

    # Alertas
    try:
        ws_alerts = sh.worksheet('Alertas')
        df_alerts = pd.DataFrame(ws_alerts.get_all_records())
    except gspread.exceptions.WorksheetNotFound:
        df_alerts = pd.DataFrame()

    # Clean types
    if not df.empty:
        int_cols = ['status_code', 'h2_count', 'word_count', 'product_count']
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        bool_cols = ['has_noindex', 'has_product_carousel', 'has_alerts']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: str(x).strip().upper() in ('TRUE', 'VERDADERO', '1', 'YES')
                )

        if 'year_in_title' in df.columns:
            df['year_in_title'] = pd.to_numeric(df['year_in_title'], errors='coerce')

        # Parse dates for time-based analysis
        for date_col in ['pub_date', 'lastmod']:
            if date_col in df.columns:
                df[f'{date_col}_parsed'] = pd.to_datetime(df[date_col], errors='coerce')

    return df, df_alerts


try:
    df, df_alerts = load_data()
except Exception as e:
    st.error(f"Error conectando con Google Sheets: {e}")
    st.info("Configura `SPREADSHEET_ID` y `GCP_SERVICE_ACCOUNT` en Settings → Secrets")
    st.stop()

if df.empty:
    st.warning("No hay datos en URLs_Master. Ejecuta primero los workflows de n8n.")
    st.stop()


# ══════════════════════════════════════════════════════════════
# SIDEBAR — Dark nav like Metabase
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📊 Blog Audit")
    st.caption("PcComponentes")
    st.markdown("---")

    # Filters
    st.markdown("##### Filtros")

    # Category
    all_cats = sorted(
        df[df['categoria'].astype(str).str.strip() != '']['categoria'].unique().tolist()
    )
    selected_cats = st.multiselect("Categoría", all_cats, default=[])

    # Subcategory — dependent on selected categories
    if selected_cats:
        all_subcats = sorted(
            df[(df['categoria'].isin(selected_cats)) &
               (df['subcategoria'].astype(str).str.strip() != '')
               ]['subcategoria'].unique().tolist()
        )
    else:
        all_subcats = sorted(
            df[df['subcategoria'].astype(str).str.strip() != '']['subcategoria'].unique().tolist()
        )
    selected_subcats = st.multiselect("Subcategoría", all_subcats, default=[])

    # Content type
    all_types = sorted(
        df[df['tipo_contenido'].astype(str).str.strip() != '']['tipo_contenido'].unique().tolist()
    )
    selected_types = st.multiselect("Tipo de contenido", all_types, default=[])

    # Vigencia
    all_vigencia = sorted(
        df[df['vigencia'].astype(str).str.strip() != '']['vigencia'].unique().tolist()
    )
    selected_vigencia = st.multiselect("Vigencia", all_vigencia, default=[])

    # Carousel
    filter_carousel = st.selectbox(
        "Carrusel de producto", ["Todos", "Con carrusel", "Sin carrusel"]
    )

    # Alerts
    filter_alerts = st.selectbox("Alertas", ["Todos", "Con alertas", "Sin alertas"])

    # Status code — show actual codes found in data
    all_status = sorted(df['status_code'].unique().tolist())
    status_options = ["Todos"] + [str(s) for s in all_status]
    filter_status = st.selectbox("Status code", status_options)

    # Text search
    search_text = st.text_input("Buscar en título / URL", "", placeholder="Escribe para filtrar...")

    st.markdown("---")

    # Apply filters
    df_filtered = df.copy()
    if selected_cats:
        df_filtered = df_filtered[df_filtered['categoria'].isin(selected_cats)]
    if selected_subcats:
        df_filtered = df_filtered[df_filtered['subcategoria'].isin(selected_subcats)]
    if selected_types:
        df_filtered = df_filtered[df_filtered['tipo_contenido'].isin(selected_types)]
    if selected_vigencia:
        df_filtered = df_filtered[df_filtered['vigencia'].isin(selected_vigencia)]
    if filter_carousel == "Con carrusel":
        df_filtered = df_filtered[df_filtered['has_product_carousel'] == True]
    elif filter_carousel == "Sin carrusel":
        df_filtered = df_filtered[df_filtered['has_product_carousel'] == False]
    if filter_alerts == "Con alertas":
        df_filtered = df_filtered[df_filtered['has_alerts'] == True]
    elif filter_alerts == "Sin alertas":
        df_filtered = df_filtered[df_filtered['has_alerts'] == False]
    if filter_status != "Todos":
        df_filtered = df_filtered[df_filtered['status_code'] == int(filter_status)]
    if search_text:
        search_lower = search_text.lower()
        mask = (
            df_filtered['url'].astype(str).str.lower().str.contains(search_lower, na=False) |
            df_filtered.get('meta_title', pd.Series(dtype=str)).astype(str).str.lower().str.contains(
                search_lower, na=False) |
            df_filtered.get('sitemap_title', pd.Series(dtype=str)).astype(str).str.lower().str.contains(
                search_lower, na=False)
        )
        df_filtered = df_filtered[mask]

    n_total = len(df)
    n_filtered = len(df_filtered)
    if n_filtered < n_total:
        st.caption(f"Mostrando **{n_filtered}** de {n_total} URLs")
    else:
        st.caption(f"**{n_total}** URLs totales")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("↻ Recargar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_btn2:
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Explorador", "Alertas", "Análisis"])


# ══════════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab1:

    # --- KPI row ---
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.metric("URLs totales", f"{n_filtered:,}")
    with kpi2:
        ok_count = int((df_filtered['status_code'] == 200).sum())
        ok_pct = f"{ok_count / n_filtered * 100:.0f}%" if n_filtered > 0 else "—"
        st.metric("Status 200", f"{ok_count:,}", ok_pct)
    with kpi3:
        non_200 = int((df_filtered['status_code'] != 200).sum())
        st.metric("Status ≠ 200", f"{non_200:,}")
    with kpi4:
        alerts_count = int(df_filtered['has_alerts'].sum()) if 'has_alerts' in df_filtered.columns else 0
        alerts_pct = f"{alerts_count / n_filtered * 100:.0f}%" if n_filtered > 0 else "—"
        st.metric("Con alertas", f"{alerts_count:,}", alerts_pct, delta_color="inverse")
    with kpi5:
        carousel_count = int(
            df_filtered['has_product_carousel'].sum()
        ) if 'has_product_carousel' in df_filtered.columns else 0
        st.metric("Con carrusel", f"{carousel_count:,}")
    with kpi6:
        avg_words = int(
            df_filtered['word_count'].mean()
        ) if n_filtered > 0 and 'word_count' in df_filtered.columns else 0
        st.metric("Palabras (media)", f"{avg_words:,}")

    st.markdown("")

    # --- Charts row 1 ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        cat_data = df_filtered[
            df_filtered['categoria'].astype(str).str.strip() != ''
        ]['categoria'].value_counts().reset_index()
        cat_data.columns = ['Categoría', 'Artículos']
        if not cat_data.empty:
            cat_data = cat_data.sort_values('Artículos', ascending=True)
            fig_cat = px.bar(
                cat_data, x='Artículos', y='Categoría', orientation='h',
                title='Artículos por categoría',
                text='Artículos'
            )
            fig_cat.update_traces(
                marker_color='#4C9AFF',
                textposition='outside',
                textfont=dict(size=11)
            )
            fig_cat.update_layout(xaxis_title='', yaxis_title='')
            apply_metabase_style(fig_cat, height=max(320, len(cat_data) * 30 + 60))
            st.plotly_chart(fig_cat, use_container_width=True)

    with col_chart2:
        type_data = df_filtered[
            df_filtered['tipo_contenido'].astype(str).str.strip() != ''
        ]['tipo_contenido'].value_counts().reset_index()
        type_data.columns = ['Tipo', 'Artículos']
        if not type_data.empty:
            fig_type = px.pie(
                type_data, names='Tipo', values='Artículos',
                title='Distribución por tipo de contenido',
                hole=0.5,
                color_discrete_sequence=METABASE_COLORS
            )
            fig_type.update_traces(
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=11),
                pull=[0.02] * len(type_data)
            )
            apply_metabase_style(fig_type, height=400)
            st.plotly_chart(fig_type, use_container_width=True)

    # --- Charts row 2 ---
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        vig_data = df_filtered[
            df_filtered['vigencia'].astype(str).str.strip() != ''
        ]['vigencia'].value_counts().reset_index()
        vig_data.columns = ['Vigencia', 'Artículos']
        if not vig_data.empty:
            color_map_vig = {
                'evergreen': '#51CF66',
                'evergreen_actualizable': '#F0A756',
                'caduco': '#EF6C6C'
            }
            fig_vig = px.bar(
                vig_data, x='Vigencia', y='Artículos',
                title='Distribución por vigencia',
                color='Vigencia',
                color_discrete_map=color_map_vig,
                text='Artículos'
            )
            fig_vig.update_traces(textposition='outside', textfont=dict(size=12))
            fig_vig.update_layout(showlegend=False, xaxis_title='', yaxis_title='')
            apply_metabase_style(fig_vig, height=340)
            st.plotly_chart(fig_vig, use_container_width=True)

    with col_chart4:
        status_data = df_filtered['status_code'].value_counts().reset_index()
        status_data.columns = ['Status', 'URLs']
        status_data['Status'] = status_data['Status'].astype(str)
        if not status_data.empty:
            status_color_map = {'200': '#51CF66', '301': '#F0A756', '404': '#EF6C6C'}
            colors_list = [status_color_map.get(s, '#64748B') for s in status_data['Status']]
            fig_status = px.pie(
                status_data, names='Status', values='URLs',
                title='Códigos de estado HTTP',
                hole=0.5,
            )
            fig_status.update_traces(
                marker=dict(colors=colors_list),
                textposition='outside',
                textinfo='label+value+percent',
                textfont=dict(size=11)
            )
            apply_metabase_style(fig_status, height=340)
            st.plotly_chart(fig_status, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 2: EXPLORER
# ══════════════════════════════════════════════════════════════
with tab2:

    st.markdown(
        f'<div class="section-header">Explorador de URLs — {n_filtered} resultados</div>',
        unsafe_allow_html=True
    )

    display_cols = [
        'url', 'meta_title', 'categoria', 'subcategoria', 'tipo_contenido',
        'vigencia', 'status_code', 'has_product_carousel', 'word_count',
        'h2_count', 'has_alerts', 'pub_date', 'lastmod'
    ]
    available_cols = [c for c in display_cols if c in df_filtered.columns]

    st.dataframe(
        df_filtered[available_cols],
        use_container_width=True,
        height=620,
        column_config={
            "url": st.column_config.LinkColumn("URL", width="large"),
            "meta_title": st.column_config.TextColumn("Título", width="large"),
            "categoria": st.column_config.TextColumn("Categoría"),
            "subcategoria": st.column_config.TextColumn("Subcategoría"),
            "tipo_contenido": st.column_config.TextColumn("Tipo"),
            "vigencia": st.column_config.TextColumn("Vigencia"),
            "status_code": st.column_config.NumberColumn("Status", format="%d"),
            "has_product_carousel": st.column_config.CheckboxColumn("Carrusel"),
            "word_count": st.column_config.NumberColumn("Palabras", format="%d"),
            "h2_count": st.column_config.NumberColumn("H2s", format="%d"),
            "has_alerts": st.column_config.CheckboxColumn("Alertas"),
            "pub_date": st.column_config.TextColumn("Publicación"),
            "lastmod": st.column_config.TextColumn("Últ. modificación"),
        }
    )

    # Export buttons
    col_exp1, col_exp2, _ = st.columns([1, 1, 4])
    with col_exp1:
        csv_data = df_filtered[available_cols].to_csv(index=False).encode('utf-8')
        st.download_button("Exportar CSV", csv_data, "blog_audit_export.csv", "text/csv")
    with col_exp2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtered[available_cols].to_excel(writer, index=False, sheet_name='URLs')
        st.download_button(
            "Exportar Excel", buffer.getvalue(),
            "blog_audit_export.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ══════════════════════════════════════════════════════════════
# TAB 3: ALERTS
# ══════════════════════════════════════════════════════════════
with tab3:

    st.markdown('<div class="section-header">Panel de alertas</div>', unsafe_allow_html=True)

    if df_alerts.empty:
        st.info("No hay alertas registradas todavía. Se generarán con el workflow de alertas en n8n.")
    else:
        # Resolve boolean
        df_alerts['_resolved'] = df_alerts['resolved'].apply(
            lambda x: str(x).strip().upper() in ('TRUE', 'VERDADERO', '1', 'YES')
        )
        df_alerts_active = df_alerts[~df_alerts['_resolved']].copy()

        # KPIs
        kpi_a1, kpi_a2, kpi_a3, kpi_a4 = st.columns(4)
        total_active = len(df_alerts_active)
        with kpi_a1:
            st.metric("Alertas activas", total_active)
        with kpi_a2:
            alta = int(
                (df_alerts_active['severity'] == 'ALTA').sum()
            ) if 'severity' in df_alerts_active.columns else 0
            st.metric("Severidad ALTA", alta)
        with kpi_a3:
            media_count = int(
                (df_alerts_active['severity'] == 'MEDIA').sum()
            ) if 'severity' in df_alerts_active.columns else 0
            st.metric("Severidad MEDIA", media_count)
        with kpi_a4:
            baja = int(
                (df_alerts_active['severity'] == 'BAJA').sum()
            ) if 'severity' in df_alerts_active.columns else 0
            st.metric("Severidad BAJA", baja)

        st.markdown("")

        if not df_alerts_active.empty and 'alert_type' in df_alerts_active.columns:
            # Filter by alert type
            alert_types = sorted(df_alerts_active['alert_type'].unique().tolist())
            selected_alert_type = st.multiselect(
                "Filtrar por tipo de alerta", alert_types, default=[]
            )

            df_alerts_show = df_alerts_active.copy()
            if selected_alert_type:
                df_alerts_show = df_alerts_show[
                    df_alerts_show['alert_type'].isin(selected_alert_type)
                ]

            # Sort by severity
            severity_order = {'ALTA': 0, 'MEDIA': 1, 'BAJA': 2}
            if 'severity' in df_alerts_show.columns:
                df_alerts_show['_sort'] = df_alerts_show['severity'].map(severity_order).fillna(3)
                df_alerts_show = df_alerts_show.sort_values('_sort')

            alert_display_cols = ['url', 'alert_type', 'severity', 'detail', 'detected_date']
            alert_available = [c for c in alert_display_cols if c in df_alerts_show.columns]

            st.dataframe(
                df_alerts_show[alert_available],
                use_container_width=True,
                height=480,
                column_config={
                    "url": st.column_config.LinkColumn("URL", width="large"),
                    "alert_type": st.column_config.TextColumn("Tipo"),
                    "severity": st.column_config.TextColumn("Severidad"),
                    "detail": st.column_config.TextColumn("Detalle", width="large"),
                    "detected_date": st.column_config.TextColumn("Detectada"),
                }
            )

            st.markdown("")

            # Charts side by side
            col_al1, col_al2 = st.columns(2)

            with col_al1:
                # Alert type breakdown
                alert_breakdown = df_alerts_active['alert_type'].value_counts().reset_index()
                alert_breakdown.columns = ['Tipo', 'Cantidad']
                if not alert_breakdown.empty:
                    fig_alerts = px.bar(
                        alert_breakdown.sort_values('Cantidad', ascending=True),
                        x='Cantidad', y='Tipo', orientation='h',
                        title='Alertas por tipo',
                        text='Cantidad',
                        color_discrete_sequence=['#EF6C6C']
                    )
                    fig_alerts.update_traces(textposition='outside', textfont=dict(size=11))
                    fig_alerts.update_layout(xaxis_title='', yaxis_title='')
                    apply_metabase_style(
                        fig_alerts,
                        height=max(280, len(alert_breakdown) * 32 + 60)
                    )
                    st.plotly_chart(fig_alerts, use_container_width=True)

            with col_al2:
                # Severity donut
                if 'severity' in df_alerts_active.columns:
                    sev_data = df_alerts_active['severity'].value_counts().reset_index()
                    sev_data.columns = ['Severidad', 'Cantidad']
                    sev_color_map = {
                        'ALTA': '#EF6C6C', 'MEDIA': '#F0A756', 'BAJA': '#4C9AFF'
                    }
                    sev_colors = [
                        sev_color_map.get(s, '#64748B') for s in sev_data['Severidad']
                    ]
                    fig_sev = px.pie(
                        sev_data, names='Severidad', values='Cantidad',
                        title='Alertas por severidad',
                        hole=0.5,
                    )
                    fig_sev.update_traces(
                        marker=dict(colors=sev_colors),
                        textinfo='label+value+percent',
                        textposition='outside'
                    )
                    apply_metabase_style(fig_sev, height=320)
                    st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.success("No hay alertas activas. Todo en orden.")


# ══════════════════════════════════════════════════════════════
# TAB 4: ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab4:

    st.markdown('<div class="section-header">Análisis de contenido</div>', unsafe_allow_html=True)

    # --- Row 1: Content gap + Word count ---
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        cat_counts = df_filtered[
            df_filtered['categoria'].astype(str).str.strip() != ''
        ]['categoria'].value_counts().reset_index()
        cat_counts.columns = ['Categoría', 'Artículos']
        if not cat_counts.empty:
            cat_counts_sorted = cat_counts.sort_values('Artículos', ascending=True)
            fig_gap = px.bar(
                cat_counts_sorted,
                x='Artículos', y='Categoría', orientation='h',
                title='Content gap — categorías con menos contenido',
                text='Artículos',
                color='Artículos',
                color_continuous_scale=['#EF6C6C', '#F0A756', '#51CF66']
            )
            fig_gap.update_traces(textposition='outside', textfont=dict(size=11))
            fig_gap.update_layout(xaxis_title='', yaxis_title='', coloraxis_showscale=False)
            apply_metabase_style(fig_gap, height=max(340, len(cat_counts) * 30 + 60))
            st.plotly_chart(fig_gap, use_container_width=True)

    with col_a2:
        if 'word_count' in df_filtered.columns:
            df_words = df_filtered[df_filtered['word_count'] > 0]
            if not df_words.empty:
                fig_words = px.histogram(
                    df_words, x='word_count', nbins=25,
                    title='Distribución de extensión (palabras por artículo)',
                    color_discrete_sequence=['#4C9AFF']
                )
                fig_words.update_layout(
                    xaxis_title='Palabras',
                    yaxis_title='Nº artículos',
                    bargap=0.08
                )
                median_wc = int(df_words['word_count'].median())
                fig_words.add_vline(
                    x=median_wc, line_dash="dash", line_color="#7F56D9",
                    annotation_text=f"Mediana: {median_wc}",
                    annotation_position="top right",
                    annotation_font=dict(size=11, color="#7F56D9")
                )
                apply_metabase_style(fig_words, height=400)
                st.plotly_chart(fig_words, use_container_width=True)

    st.markdown("")

    # --- Row 2: Carousel penetration + Oldest content ---
    col_a3, col_a4 = st.columns(2)

    with col_a3:
        if 'has_product_carousel' in df_filtered.columns and 'categoria' in df_filtered.columns:
            df_cat_valid = df_filtered[
                df_filtered['categoria'].astype(str).str.strip() != ''
            ]
            if not df_cat_valid.empty:
                carousel_by_cat = df_cat_valid.groupby('categoria').agg(
                    total=('url', 'count'),
                    con_carrusel=('has_product_carousel', 'sum')
                ).reset_index()
                carousel_by_cat['pct_carrusel'] = (
                    carousel_by_cat['con_carrusel'] / carousel_by_cat['total'] * 100
                ).round(1)
                carousel_by_cat = carousel_by_cat.sort_values('pct_carrusel', ascending=True)

                fig_carousel = px.bar(
                    carousel_by_cat, x='pct_carrusel', y='categoria', orientation='h',
                    title='Penetración de carrusel de producto por categoría',
                    text=carousel_by_cat['pct_carrusel'].apply(lambda x: f"{x:.0f}%"),
                    color='pct_carrusel',
                    color_continuous_scale=['#E8ECF0', '#51CF66']
                )
                fig_carousel.update_traces(textposition='outside', textfont=dict(size=11))
                fig_carousel.update_layout(
                    xaxis_title='%', yaxis_title='',
                    coloraxis_showscale=False
                )
                apply_metabase_style(
                    fig_carousel,
                    height=max(340, len(carousel_by_cat) * 30 + 60)
                )
                st.plotly_chart(fig_carousel, use_container_width=True)

    with col_a4:
        df_old = df_filtered[
            df_filtered['vigencia'].isin(['caduco', 'evergreen_actualizable'])
        ].copy()

        if not df_old.empty and 'lastmod_parsed' in df_old.columns:
            df_old = df_old.dropna(subset=['lastmod_parsed'])
            df_old = df_old.sort_values('lastmod_parsed', ascending=True)

            st.markdown(
                '<div class="section-header" style="font-size:0.95rem">'
                'Contenido prioritario para actualizar</div>',
                unsafe_allow_html=True
            )
            st.caption(
                "Artículos caducos o actualizables, ordenados por última "
                "modificación (más antiguos primero)"
            )

            old_display = ['url', 'meta_title', 'vigencia', 'lastmod', 'categoria']
            old_available = [c for c in old_display if c in df_old.columns]

            st.dataframe(
                df_old[old_available].head(25),
                use_container_width=True,
                height=420,
                column_config={
                    "url": st.column_config.LinkColumn("URL"),
                    "meta_title": st.column_config.TextColumn("Título", width="large"),
                    "vigencia": st.column_config.TextColumn("Vigencia"),
                    "lastmod": st.column_config.TextColumn("Últ. modificación"),
                    "categoria": st.column_config.TextColumn("Categoría"),
                }
            )
        elif not df_old.empty:
            st.info("No se pudieron parsear las fechas de última modificación.")
        else:
            st.success("No hay contenido marcado como caduco o actualizable.")

    st.markdown("")

    # --- Row 3: Heatmap Category × Content Type ---
    df_heat = df_filtered[
        (df_filtered['categoria'].astype(str).str.strip() != '') &
        (df_filtered['tipo_contenido'].astype(str).str.strip() != '')
    ]
    if not df_heat.empty:
        cross = pd.crosstab(df_heat['categoria'], df_heat['tipo_contenido'])
        if not cross.empty and cross.shape[0] > 1 and cross.shape[1] > 1:
            fig_heat = px.imshow(
                cross, text_auto=True, aspect='auto',
                title='Mapa de contenido — Categoría × Tipo',
                color_continuous_scale=['#F5F7FA', '#4C9AFF', '#7F56D9']
            )
            fig_heat.update_layout(xaxis_title='', yaxis_title='')
            apply_metabase_style(fig_heat, height=max(400, cross.shape[0] * 32 + 80))
            st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("")

    # --- Row 4: Publication timeline ---
    if 'pub_date_parsed' in df_filtered.columns:
        df_timeline = df_filtered.dropna(subset=['pub_date_parsed']).copy()
        if not df_timeline.empty:
            df_timeline['year_month'] = df_timeline['pub_date_parsed'].dt.to_period('M').astype(str)
            timeline_data = df_timeline.groupby('year_month').size().reset_index(name='Artículos')
            timeline_data = timeline_data.sort_values('year_month')

            fig_timeline = px.bar(
                timeline_data, x='year_month', y='Artículos',
                title='Publicaciones por mes',
                color_discrete_sequence=['#4C9AFF']
            )
            fig_timeline.update_layout(
                xaxis_title='',
                yaxis_title='Artículos publicados',
                bargap=0.15,
                xaxis=dict(tickangle=-45, dtick=3)
            )
            apply_metabase_style(fig_timeline, height=350)
            st.plotly_chart(fig_timeline, use_container_width=True)
