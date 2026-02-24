import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Blog Audit — PcComponentes",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem; border-radius: 12px; color: white; text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 0.2rem 0 0 0; font-size: 0.85rem; opacity: 0.85; }
    .alert-alta { border-left: 4px solid #e74c3c; padding-left: 10px; }
    .alert-media { border-left: 4px solid #f39c12; padding-left: 10px; }
    .alert-baja { border-left: 4px solid #3498db; padding-left: 10px; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

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
    ws_alerts = sh.worksheet('Alertas')
    df_alerts = pd.DataFrame(ws_alerts.get_all_records())

    # Clean types
    if not df.empty:
        for col in ['status_code', 'h2_count', 'word_count', 'product_count']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        for col in ['has_noindex', 'has_product_carousel', 'has_alerts']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x).upper() == 'TRUE')
        if 'year_in_title' in df.columns:
            df['year_in_title'] = pd.to_numeric(df['year_in_title'], errors='coerce')

    return df, df_alerts

# Load
try:
    df, df_alerts = load_data()
except Exception as e:
    st.error(f"❌ Error conectando con Google Sheets: {e}")
    st.info("Configura `SPREADSHEET_ID` y `GCP_SERVICE_ACCOUNT` en Settings → Secrets")
    st.stop()

if df.empty:
    st.warning("⚠️ No hay datos en URLs_Master. Ejecuta primero el notebook de Colab.")
    st.stop()

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/14/PcComponentes_logo.png", width=180)
    st.markdown("### 🔍 Blog Audit Dashboard")
    st.caption(f"Última actualización de datos: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("---")

    # Filters
    st.markdown("### Filtros")

    # Category filter
    all_cats = sorted(df[df['categoria'] != '']['categoria'].unique().tolist())
    selected_cats = st.multiselect("Categoría", all_cats, default=[])

    # Content type filter
    all_types = sorted(df[df['tipo_contenido'] != '']['tipo_contenido'].unique().tolist())
    selected_types = st.multiselect("Tipo de contenido", all_types, default=[])

    # Vigencia filter
    all_vigencia = sorted(df[df['vigencia'] != '']['vigencia'].unique().tolist())
    selected_vigencia = st.multiselect("Vigencia", all_vigencia, default=[])

    # Carousel filter
    filter_carousel = st.selectbox("Carrusel de producto", ["Todos", "Con carrusel", "Sin carrusel"])

    # Alerts filter
    filter_alerts = st.selectbox("Alertas", ["Todos", "Con alertas", "Sin alertas"])

    # Status code
    filter_status = st.selectbox("Status code", ["Todos", "200", "301", "404", "Otros"])

    # Text search
    search_text = st.text_input("🔎 Buscar en título/URL", "")

    # Apply filters
    df_filtered = df.copy()
    if selected_cats:
        df_filtered = df_filtered[df_filtered['categoria'].isin(selected_cats)]
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
    if filter_status == "200":
        df_filtered = df_filtered[df_filtered['status_code'] == 200]
    elif filter_status == "301":
        df_filtered = df_filtered[df_filtered['status_code'] == 301]
    elif filter_status == "404":
        df_filtered = df_filtered[df_filtered['status_code'] == 404]
    elif filter_status == "Otros":
        df_filtered = df_filtered[~df_filtered['status_code'].isin([200, 301, 404])]
    if search_text:
        mask = (
            df_filtered['url'].str.contains(search_text, case=False, na=False) |
            df_filtered['meta_title'].str.contains(search_text, case=False, na=False) |
            df_filtered['sitemap_title'].str.contains(search_text, case=False, na=False)
        )
        df_filtered = df_filtered[mask]

    st.markdown("---")
    st.caption(f"Mostrando {len(df_filtered)} de {len(df)} URLs")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Explorador", "🚨 Alertas", "📈 Análisis"])

# ══════════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 📊 KPIs del Blog")

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total URLs", len(df_filtered))
    with col2:
        ok_count = (df_filtered['status_code'] == 200).sum()
        st.metric("Status 200", ok_count, f"{ok_count/len(df_filtered)*100:.0f}%" if len(df_filtered) > 0 else "0%")
    with col3:
        alerts_count = df_filtered['has_alerts'].sum()
        st.metric("Con alertas", int(alerts_count))
    with col4:
        carousel_count = df_filtered['has_product_carousel'].sum()
        st.metric("Con carrusel", int(carousel_count))
    with col5:
        avg_words = int(df_filtered['word_count'].mean()) if len(df_filtered) > 0 else 0
        st.metric("Palabras (media)", f"{avg_words:,}")

    st.markdown("---")

    # Charts row 1
    col_left, col_right = st.columns(2)

    with col_left:
        # Category distribution
        cat_data = df_filtered[df_filtered['categoria'] != '']['categoria'].value_counts().reset_index()
        cat_data.columns = ['Categoría', 'Artículos']
        if not cat_data.empty:
            fig_cat = px.treemap(cat_data, path=['Categoría'], values='Artículos',
                                 title='Distribución por Categoría',
                                 color='Artículos', color_continuous_scale='Viridis')
            fig_cat.update_layout(height=400, margin=dict(t=40, l=10, r=10, b=10))
            st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        # Content type distribution
        type_data = df_filtered[df_filtered['tipo_contenido'] != '']['tipo_contenido'].value_counts().reset_index()
        type_data.columns = ['Tipo', 'Artículos']
        if not type_data.empty:
            fig_type = px.pie(type_data, names='Tipo', values='Artículos',
                              title='Tipos de Contenido', hole=0.4,
                              color_discrete_sequence=px.colors.qualitative.Set2)
            fig_type.update_layout(height=400)
            st.plotly_chart(fig_type, use_container_width=True)

    # Charts row 2
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        # Vigencia distribution
        vig_data = df_filtered[df_filtered['vigencia'] != '']['vigencia'].value_counts().reset_index()
        vig_data.columns = ['Vigencia', 'Artículos']
        color_map = {'evergreen': '#27ae60', 'evergreen_actualizable': '#f39c12', 'caduco': '#e74c3c'}
        if not vig_data.empty:
            fig_vig = px.bar(vig_data, x='Vigencia', y='Artículos',
                              title='Distribución por Vigencia',
                              color='Vigencia', color_discrete_map=color_map)
            fig_vig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_vig, use_container_width=True)

    with col_right2:
        # Status codes
        status_data = df_filtered['status_code'].value_counts().reset_index()
        status_data.columns = ['Status', 'URLs']
        status_data['Status'] = status_data['Status'].astype(str)
        if not status_data.empty:
            fig_status = px.pie(status_data, names='Status', values='URLs',
                                 title='Status Codes',
                                 color_discrete_sequence=['#27ae60', '#f39c12', '#e74c3c', '#95a5a6'])
            fig_status.update_layout(height=350)
            st.plotly_chart(fig_status, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 2: EXPLORER
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 🔍 Explorador de URLs")

    # Select columns to show
    display_cols = ['url', 'meta_title', 'categoria', 'subcategoria', 'tipo_contenido',
                    'vigencia', 'status_code', 'has_product_carousel', 'word_count',
                    'h2_count', 'has_alerts', 'pub_date', 'lastmod']
    available_cols = [c for c in display_cols if c in df_filtered.columns]

    st.dataframe(
        df_filtered[available_cols],
        use_container_width=True,
        height=600,
        column_config={
            "url": st.column_config.LinkColumn("URL", width="large"),
            "meta_title": st.column_config.TextColumn("Título", width="large"),
            "categoria": st.column_config.TextColumn("Categoría"),
            "subcategoria": st.column_config.TextColumn("Subcategoría"),
            "tipo_contenido": st.column_config.TextColumn("Tipo"),
            "vigencia": st.column_config.TextColumn("Vigencia"),
            "status_code": st.column_config.NumberColumn("Status"),
            "has_product_carousel": st.column_config.CheckboxColumn("Carrusel"),
            "word_count": st.column_config.NumberColumn("Palabras"),
            "h2_count": st.column_config.NumberColumn("H2s"),
            "has_alerts": st.column_config.CheckboxColumn("Alertas"),
            "pub_date": st.column_config.TextColumn("Publicación"),
            "lastmod": st.column_config.TextColumn("Última mod."),
        }
    )

    # Export
    col_exp1, col_exp2, _ = st.columns([1, 1, 3])
    with col_exp1:
        csv_data = df_filtered[available_cols].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar CSV", csv_data, "blog_audit_export.csv", "text/csv")
    with col_exp2:
        st.caption(f"{len(df_filtered)} URLs en la selección actual")


# ══════════════════════════════════════════════════════════════
# TAB 3: ALERTS
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 🚨 Panel de Alertas")

    if df_alerts.empty:
        st.info("No hay alertas registradas todavía.")
    else:
        # Filter unresolved
        df_alerts_active = df_alerts[df_alerts['resolved'].apply(lambda x: str(x).upper() != 'TRUE')]

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Alertas activas", len(df_alerts_active))
        with col2:
            alta = len(df_alerts_active[df_alerts_active['severity'] == 'ALTA'])
            st.metric("🔴 Severidad ALTA", alta)
        with col3:
            media = len(df_alerts_active[df_alerts_active['severity'] == 'MEDIA'])
            st.metric("🟡 Severidad MEDIA", media)
        with col4:
            baja = len(df_alerts_active[df_alerts_active['severity'] == 'BAJA'])
            st.metric("🔵 Severidad BAJA", baja)

        st.markdown("---")

        # Filter by type
        alert_types = sorted(df_alerts_active['alert_type'].unique().tolist())
        selected_alert_type = st.multiselect("Filtrar por tipo de alerta", alert_types, default=[])

        df_alerts_show = df_alerts_active.copy()
        if selected_alert_type:
            df_alerts_show = df_alerts_show[df_alerts_show['alert_type'].isin(selected_alert_type)]

        # Sort by severity
        severity_order = {'ALTA': 0, 'MEDIA': 1, 'BAJA': 2}
        df_alerts_show['_sort'] = df_alerts_show['severity'].map(severity_order)
        df_alerts_show = df_alerts_show.sort_values('_sort').drop(columns='_sort')

        st.dataframe(
            df_alerts_show[['url', 'alert_type', 'severity', 'detail', 'detected_date']],
            use_container_width=True,
            height=500,
            column_config={
                "url": st.column_config.LinkColumn("URL", width="large"),
                "alert_type": st.column_config.TextColumn("Tipo"),
                "severity": st.column_config.TextColumn("Severidad"),
                "detail": st.column_config.TextColumn("Detalle", width="large"),
                "detected_date": st.column_config.TextColumn("Detectada"),
            }
        )

        # Alert type breakdown chart
        alert_breakdown = df_alerts_active['alert_type'].value_counts().reset_index()
        alert_breakdown.columns = ['Tipo', 'Count']
        fig_alerts = px.bar(alert_breakdown, x='Count', y='Tipo', orientation='h',
                             title='Alertas por tipo', color='Count',
                             color_continuous_scale='Reds')
        fig_alerts.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_alerts, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 4: ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📈 Análisis de Contenido")

    col_left, col_right = st.columns(2)

    with col_left:
        # Content gap: categories with fewer articles
        cat_counts = df_filtered[df_filtered['categoria'] != '']['categoria'].value_counts().reset_index()
        cat_counts.columns = ['Categoría', 'Artículos']
        if not cat_counts.empty:
            fig_gap = px.bar(cat_counts.sort_values('Artículos'),
                              x='Artículos', y='Categoría', orientation='h',
                              title='Content Gap: artículos por categoría',
                              color='Artículos', color_continuous_scale='RdYlGn')
            fig_gap.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_gap, use_container_width=True)

    with col_right:
        # Word count distribution
        if 'word_count' in df_filtered.columns:
            fig_words = px.histogram(df_filtered[df_filtered['word_count'] > 0],
                                      x='word_count', nbins=30,
                                      title='Distribución de longitud (palabras)',
                                      color_discrete_sequence=['#667eea'])
            fig_words.update_layout(height=450, xaxis_title='Palabras', yaxis_title='Nº artículos')
            st.plotly_chart(fig_words, use_container_width=True)

    st.markdown("---")

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        # Carousel by category
        if 'has_product_carousel' in df_filtered.columns and 'categoria' in df_filtered.columns:
            carousel_by_cat = df_filtered[df_filtered['categoria'] != ''].groupby('categoria').agg(
                total=('url', 'count'),
                con_carrusel=('has_product_carousel', 'sum')
            ).reset_index()
            carousel_by_cat['pct_carrusel'] = (carousel_by_cat['con_carrusel'] / carousel_by_cat['total'] * 100).round(1)
            carousel_by_cat = carousel_by_cat.sort_values('pct_carrusel', ascending=True)

            fig_carousel = px.bar(carousel_by_cat, x='pct_carrusel', y='categoria', orientation='h',
                                   title='% artículos con carrusel de producto por categoría',
                                   color='pct_carrusel', color_continuous_scale='Greens',
                                   text='pct_carrusel')
            fig_carousel.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
            fig_carousel.update_layout(height=450, xaxis_title='%', yaxis_title='')
            st.plotly_chart(fig_carousel, use_container_width=True)

    with col_right2:
        # Oldest content needing update
        df_old = df_filtered[
            (df_filtered['vigencia'].isin(['caduco', 'evergreen_actualizable'])) &
            (df_filtered['lastmod'] != '')
        ].copy()
        if not df_old.empty:
            df_old['lastmod_date'] = pd.to_datetime(df_old['lastmod'], errors='coerce')
            df_old = df_old.dropna(subset=['lastmod_date']).sort_values('lastmod_date')
            st.markdown("### 📅 Contenido más antiguo sin actualizar")
            st.caption("Vigencia 'caduco' o 'evergreen_actualizable', ordenado por última modificación")
            st.dataframe(
                df_old[['url', 'meta_title', 'vigencia', 'lastmod', 'categoria']].head(20),
                use_container_width=True,
                height=400,
                column_config={
                    "url": st.column_config.LinkColumn("URL"),
                    "meta_title": st.column_config.TextColumn("Título", width="large"),
                }
            )

    # Category x Type heatmap
    st.markdown("---")
    st.markdown("### 🗺️ Mapa de contenido: Categoría × Tipo")
    cross = pd.crosstab(
        df_filtered[df_filtered['categoria'] != '']['categoria'],
        df_filtered[df_filtered['tipo_contenido'] != '']['tipo_contenido']
    )
    if not cross.empty:
        fig_heat = px.imshow(cross, text_auto=True, aspect='auto',
                              title='Número de artículos por categoría y tipo',
                              color_continuous_scale='YlOrRd')
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
