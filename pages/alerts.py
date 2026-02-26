"""
Alerts tab — wrapped in ``@st.fragment`` to isolate reruns.
"""

import streamlit as st
import altair as alt
import pandas as pd
from styles import RED, ORANGE, BLUE
from utils.helpers import value_counts_df, to_csv, to_excel
from data import TRUTHY_VALUES

SEVERITY_ORDER = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}


@st.fragment
def _render_fragment(df_alerts: pd.DataFrame):
    st.markdown('<div class="section-header">Panel de alertas</div>', unsafe_allow_html=True)

    if df_alerts.empty:
        st.info("No hay alertas registradas todavía.")
        return

    # Resolved mask
    resolved = df_alerts["resolved"].astype(str).str.strip().str.upper().isin(TRUTHY_VALUES)
    active = df_alerts[~resolved]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Alertas activas", len(active))
    with k2:
        alta = int((active["severity"] == "ALTA").sum()) if "severity" in active.columns else 0
        st.metric("Severidad ALTA", alta)
    with k3:
        media = int((active["severity"] == "MEDIA").sum()) if "severity" in active.columns else 0
        st.metric("Severidad MEDIA", media)
    with k4:
        baja = int((active["severity"] == "BAJA").sum()) if "severity" in active.columns else 0
        st.metric("Severidad BAJA", baja)

    st.markdown("")

    if active.empty or "alert_type" not in active.columns:
        st.success("No hay alertas activas. Todo en orden.")
        return

    # Filter by type (only reruns this fragment)
    alert_types = sorted(active["alert_type"].unique().tolist())
    sel = st.multiselect("Filtrar por tipo de alerta", alert_types, default=[])
    show = active[active["alert_type"].isin(sel)] if sel else active

    # Sort by severity
    if "severity" in show.columns:
        sort_key = show["severity"].map(SEVERITY_ORDER).fillna(3)
        show = show.iloc[sort_key.argsort()]

    cols = ["url", "alert_type", "severity", "detail", "detected_date"]
    avail = [c for c in cols if c in show.columns]

    st.dataframe(
        show[avail],
        use_container_width=True,
        height=480,
        column_config={
            "url": st.column_config.LinkColumn("URL", width="large"),
            "alert_type": st.column_config.TextColumn("Tipo"),
            "severity": st.column_config.TextColumn("Severidad"),
            "detail": st.column_config.TextColumn("Detalle", width="large"),
            "detected_date": st.column_config.TextColumn("Detectada"),
        },
    )

    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        st.download_button("CSV", to_csv(show[avail]), "alertas.csv", "text/csv", key="al_csv")
    with c2:
        st.download_button(
            "Excel", to_excel(show[avail]), "alertas.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="al_xlsx",
        )

    st.markdown("")

    # Charts
    col_l, col_r = st.columns(2)
    with col_l:
        abt = value_counts_df(active["alert_type"]).rename(
            columns={"value": "Tipo", "count": "Cantidad"}
        )
        if not abt.empty:
            bars = alt.Chart(abt).mark_bar(color=RED).encode(
                x=alt.X("Cantidad:Q", axis=alt.Axis(title="")),
                y=alt.Y("Tipo:N", sort="-x", axis=alt.Axis(title="")),
                tooltip=["Tipo:N", "Cantidad:Q"],
            )
            text = bars.mark_text(align="left", dx=3, fontSize=11).encode(text="Cantidad:Q")
            st.altair_chart(
                (bars + text).properties(
                    title="Alertas por tipo",
                    height=max(280, len(abt) * 32 + 60),
                ),
                use_container_width=True,
            )

    with col_r:
        if "severity" in active.columns:
            sev = value_counts_df(active["severity"]).rename(
                columns={"value": "Severidad", "count": "Cantidad"}
            )
            donut = alt.Chart(sev).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("Cantidad:Q"),
                color=alt.Color(
                    "Severidad:N",
                    scale=alt.Scale(
                        domain=["ALTA", "MEDIA", "BAJA"],
                        range=[RED, ORANGE, BLUE],
                    ),
                ),
                tooltip=["Severidad:N", "Cantidad:Q"],
            ).properties(title="Alertas por severidad", height=320)
            st.altair_chart(donut, use_container_width=True)


def render(df_alerts: pd.DataFrame, **kwargs):
    _render_fragment(df_alerts)
