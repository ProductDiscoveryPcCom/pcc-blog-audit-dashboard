"""
Explorer tab — full data table with export.
"""

import streamlit as st
import pandas as pd
from utils.helpers import to_csv, to_excel


def render(df_filtered: pd.DataFrame, **kwargs):
    n = len(df_filtered)
    st.markdown(
        f'<div class="section-header">Explorador de URLs — {n} resultados</div>',
        unsafe_allow_html=True,
    )

    display_cols = [
        "url", "meta_title", "categoria", "subcategoria", "tipo_contenido",
        "vigencia", "status_code", "has_product_carousel", "word_count",
        "h2_count", "has_alerts", "pub_date", "lastmod",
    ]
    available = [c for c in display_cols if c in df_filtered.columns]

    st.dataframe(
        df_filtered[available],
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
        },
    )

    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        st.download_button(
            "Exportar CSV",
            to_csv(df_filtered[available]),
            "blog_audit_export.csv",
            "text/csv",
        )
    with col2:
        st.download_button(
            "Exportar Excel",
            to_excel(df_filtered[available]),
            "blog_audit_export.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
