"""
Dashboard tab — KPIs + overview charts.
"""

import streamlit as st
import altair as alt
import pandas as pd
from styles import COLORS as METABASE_COLORS, GREEN, ORANGE, RED, BLUE, GREY
from utils.helpers import value_counts_df

# Vigencia constants
VIGENCIA_EVERGREEN = "evergreen"
VIGENCIA_ACTUALIZABLE = "evergreen_actualizable"
VIGENCIA_CADUCO = "caduco"


def render(df_filtered: pd.DataFrame, **kwargs):
    n = len(df_filtered)

    # ── KPI row ─────────────────────────────────────────────────
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.metric("URLs totales", f"{n:,}")
    with kpi2:
        ok = int((df_filtered["status_code"] == 200).sum())
        pct = f"{ok / n * 100:.0f}%" if n else "—"
        st.metric("Status 200", f"{ok:,}", pct)
    with kpi3:
        non_200 = int((df_filtered["status_code"] != 200).sum())
        st.metric("Status ≠ 200", f"{non_200:,}")
    with kpi4:
        alerts = int(df_filtered["has_alerts"].sum()) if "has_alerts" in df_filtered.columns else 0
        a_pct = f"{alerts / n * 100:.0f}%" if n else "—"
        st.metric("Con alertas", f"{alerts:,}", a_pct, delta_color="inverse")
    with kpi5:
        car = int(df_filtered["has_product_carousel"].sum()) if "has_product_carousel" in df_filtered.columns else 0
        st.metric("Con carrusel", f"{car:,}")
    with kpi6:
        avg_w = int(df_filtered["word_count"].mean()) if n and "word_count" in df_filtered.columns else 0
        st.metric("Palabras (media)", f"{avg_w:,}")

    st.markdown("")

    # ── Row 1: Category + Content type ──────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        cat_vc = value_counts_df(df_filtered.loc[df_filtered["_ne_categoria"], "categoria"])
        cat_data = cat_vc.rename(columns={"value": "Categoría", "count": "Artículos"})
        if not cat_data.empty:
            bars = alt.Chart(cat_data).mark_bar(color=BLUE).encode(
                x=alt.X("Artículos:Q", axis=alt.Axis(title="")),
                y=alt.Y("Categoría:N", sort="-x", axis=alt.Axis(title="")),
                tooltip=["Categoría:N", "Artículos:Q"],
            )
            text = bars.mark_text(align="left", dx=3, fontSize=11).encode(text="Artículos:Q")
            st.altair_chart(
                (bars + text).properties(
                    title="Artículos por categoría",
                    height=max(320, len(cat_data) * 30 + 60),
                ),
                use_container_width=True,
            )

    with col2:
        type_vc = value_counts_df(df_filtered.loc[df_filtered["_ne_tipo_contenido"], "tipo_contenido"])
        type_data = type_vc.rename(columns={"value": "Tipo", "count": "Artículos"})
        if not type_data.empty:
            donut = alt.Chart(type_data).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("Artículos:Q"),
                color=alt.Color("Tipo:N", scale=alt.Scale(range=METABASE_COLORS)),
                tooltip=["Tipo:N", "Artículos:Q"],
            ).properties(title="Distribución por tipo de contenido", height=400)
            st.altair_chart(donut, use_container_width=True)

    # ── Row 2: Vigencia + Status codes ──────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        vig_vc = value_counts_df(df_filtered.loc[df_filtered["_ne_vigencia"], "vigencia"])
        vig_data = vig_vc.rename(columns={"value": "Vigencia", "count": "Artículos"})
        if not vig_data.empty:
            bars = alt.Chart(vig_data).mark_bar().encode(
                x=alt.X("Vigencia:N", axis=alt.Axis(title="")),
                y=alt.Y("Artículos:Q", axis=alt.Axis(title="")),
                color=alt.Color(
                    "Vigencia:N",
                    scale=alt.Scale(
                        domain=[VIGENCIA_EVERGREEN, VIGENCIA_ACTUALIZABLE, VIGENCIA_CADUCO],
                        range=[GREEN, ORANGE, RED],
                    ),
                    legend=None,
                ),
                tooltip=["Vigencia:N", "Artículos:Q"],
            )
            text = bars.mark_text(dy=-10, fontSize=12).encode(text="Artículos:Q")
            st.altair_chart(
                (bars + text).properties(title="Distribución por vigencia", height=340),
                use_container_width=True,
            )

    with col4:
        st_vc = value_counts_df(df_filtered["status_code"])
        status_data = st_vc.rename(columns={"value": "Status", "count": "URLs"})
        status_data["Status"] = status_data["Status"].astype(str)
        if not status_data.empty:
            s_domain = status_data["Status"].tolist()
            s_range = [
                {"200": GREEN, "301": ORANGE, "404": RED}.get(s, GREY) for s in s_domain
            ]
            donut = alt.Chart(status_data).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("URLs:Q"),
                color=alt.Color("Status:N", scale=alt.Scale(domain=s_domain, range=s_range)),
                tooltip=["Status:N", "URLs:Q"],
            ).properties(title="Códigos de estado HTTP", height=340)
            st.altair_chart(donut, use_container_width=True)
