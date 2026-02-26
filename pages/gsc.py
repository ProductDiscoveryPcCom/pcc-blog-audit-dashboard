"""
GSC (Google Search Console) tab — new page.

Reads from GSC_Performance and GSC_Deltas sheets (populated by Colab).
Implements drill‑down: click a URL row → see its top queries.

Optimización 5 — interactividad cruzada via session_state["detail_view"].
"""

import streamlit as st
import altair as alt
import pandas as pd
from styles import BLUE, GREEN, RED, ORANGE, PURPLE, MUTED, GREY, COLORS
from utils.helpers import to_csv, to_excel
from data import get_filtered_gsc


def render(df_filtered: pd.DataFrame, df_gsc_perf: pd.DataFrame,
           df_gsc_delta: pd.DataFrame, **kwargs):
    st.markdown(
        '<div class="section-header">Google Search Console</div>',
        unsafe_allow_html=True,
    )

    # ── Guard: no GSC data ──────────────────────────────────────
    if df_gsc_perf.empty and df_gsc_delta.empty:
        st.info(
            "No hay datos de GSC disponibles. "
            "Ejecuta la Fase 4 del Colab para poblar las hojas GSC_Performance y GSC_Deltas."
        )
        return

    # Filter GSC to match sidebar‑filtered URLs
    gsc_perf = get_filtered_gsc(df_gsc_perf, df_filtered)
    gsc_delta = get_filtered_gsc(df_gsc_delta, df_filtered)

    # ── Period selector ─────────────────────────────────────────
    available_periods = sorted(gsc_delta["periodo"].unique().tolist()) if not gsc_delta.empty else ["7d"]
    period = st.selectbox("Periodo", available_periods, index=0, key="gsc_period")

    delta_period = gsc_delta[gsc_delta["periodo"] == period] if not gsc_delta.empty else pd.DataFrame()

    # ── KPIs ────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    n_urls = delta_period["url"].nunique() if not delta_period.empty else 0
    total_clicks = int(delta_period["clicks"].sum()) if not delta_period.empty else 0
    total_clicks_prev = int(delta_period["clicks_prev"].sum()) if not delta_period.empty else 0
    total_impr = int(delta_period["impressions"].sum()) if not delta_period.empty else 0
    avg_pos = round(delta_period["position"].mean(), 1) if not delta_period.empty else 0

    clicks_delta = round((total_clicks - total_clicks_prev) / max(total_clicks_prev, 1) * 100, 1)

    with k1:
        st.metric("URLs con datos", f"{n_urls:,}")
    with k2:
        st.metric("Clicks totales", f"{total_clicks:,}", f"{clicks_delta:+.1f}%")
    with k3:
        st.metric("Clicks previos", f"{total_clicks_prev:,}")
    with k4:
        st.metric("Impressions", f"{total_impr:,}")
    with k5:
        st.metric("Pos. media", f"{avg_pos:.1f}")

    st.markdown("")

    # ── Main layout: table left, detail right ───────────────────
    col_main, col_detail = st.columns([3, 2])

    with col_main:
        st.markdown("##### URLs — rendimiento por periodo")

        if not delta_period.empty:
            display = delta_period.sort_values("clicks", ascending=False).head(100)
            display_cols = [
                "url", "clicks", "clicks_prev", "clicks_delta_pct",
                "impressions", "position", "position_delta",
            ]
            avail = [c for c in display_cols if c in display.columns]

            # Show as dataframe with selection
            event = st.dataframe(
                display[avail],
                use_container_width=True,
                height=520,
                on_select="rerun",
                selection_mode="single-row",
                key="gsc_table",
                column_config={
                    "url": st.column_config.TextColumn("URL", width="large"),
                    "clicks": st.column_config.NumberColumn("Clicks", format="%d"),
                    "clicks_prev": st.column_config.NumberColumn("Prev", format="%d"),
                    "clicks_delta_pct": st.column_config.NumberColumn("Δ %", format="%.1f%%"),
                    "impressions": st.column_config.NumberColumn("Impr.", format="%d"),
                    "position": st.column_config.NumberColumn("Pos.", format="%.1f"),
                    "position_delta": st.column_config.NumberColumn("Δ Pos.", format="%+.1f"),
                },
            )

            # Drill‑down: capture row selection → update detail_view
            if event and event.selection and event.selection.rows:
                row_idx = event.selection.rows[0]
                selected_url = display.iloc[row_idx]["url"]
                st.session_state["detail_view"] = {
                    "type": "gsc_url_drill",
                    "url": selected_url,
                    "period": period,
                }

            # Export
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                st.download_button(
                    "CSV", to_csv(delta_period), f"gsc_deltas_{period}.csv",
                    "text/csv", key="gsc_d_csv",
                )
            with c2:
                st.download_button(
                    "Excel", to_excel(delta_period), f"gsc_deltas_{period}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="gsc_d_xlsx",
                )
        else:
            st.warning(f"No hay datos de deltas para el periodo {period}.")

    # ── Detail panel (drill‑down) ───────────────────────────────
    with col_detail:
        detail = st.session_state.get("detail_view")

        if detail and detail.get("type") == "gsc_url_drill" and not gsc_perf.empty:
            url = detail["url"]
            per = detail.get("period", period)

            st.markdown(f"##### Queries para:")
            st.caption(url)

            queries = gsc_perf[
                (gsc_perf["url"].str.rstrip("/") == url.rstrip("/")) &
                (gsc_perf["periodo"] == per)
            ].sort_values("clicks", ascending=False)

            if not queries.empty:
                # Top queries bar chart
                top_q = queries.head(10)
                bars = alt.Chart(top_q).mark_bar(color=BLUE).encode(
                    x=alt.X("clicks:Q", title="Clicks"),
                    y=alt.Y("query:N", sort="-x", title=""),
                    tooltip=["query:N", "clicks:Q", "impressions:Q", "position:Q"],
                )
                text = bars.mark_text(align="left", dx=3, fontSize=10).encode(
                    text="clicks:Q"
                )
                st.altair_chart(
                    (bars + text).properties(
                        title=f"Top queries ({per})",
                        height=max(250, len(top_q) * 28 + 50),
                    ),
                    use_container_width=True,
                )

                # Full query table
                q_cols = ["query", "clicks", "impressions", "ctr", "position"]
                q_avail = [c for c in q_cols if c in queries.columns]
                st.dataframe(
                    queries[q_avail],
                    use_container_width=True,
                    height=300,
                    column_config={
                        "query": st.column_config.TextColumn("Query"),
                        "clicks": st.column_config.NumberColumn("Clicks", format="%d"),
                        "impressions": st.column_config.NumberColumn("Impr.", format="%d"),
                        "ctr": st.column_config.NumberColumn("CTR %", format="%.2f%%"),
                        "position": st.column_config.NumberColumn("Pos.", format="%.1f"),
                    },
                )
            else:
                st.info(f"No hay queries registradas para esta URL en {per}.")

            if st.button("✕ Cerrar detalle", key="close_gsc_detail"):
                st.session_state["detail_view"] = None
                st.rerun()

        else:
            st.markdown("##### Detalle de queries")
            st.caption("Selecciona una URL de la tabla para ver sus queries.")

    st.markdown("")

    # ── Bottom: aggregated charts ───────────────────────────────
    if not delta_period.empty:
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            # Top 15 URLs by clicks
            top_urls = delta_period.nlargest(15, "clicks")
            # Truncate URL for display
            top_urls = top_urls.copy()
            top_urls["url_short"] = top_urls["url"].str.replace(
                r"https?://[^/]+/", "", regex=True
            ).str[:60]

            bars = alt.Chart(top_urls).mark_bar(color=BLUE).encode(
                x=alt.X("clicks:Q", title="Clicks"),
                y=alt.Y("url_short:N", sort="-x", title=""),
                tooltip=["url:N", "clicks:Q", "clicks_delta_pct:Q"],
            )
            st.altair_chart(
                bars.properties(title="Top 15 URLs por clicks", height=420),
                use_container_width=True,
            )

        with col_c2:
            # Biggest drops
            drops = delta_period[delta_period["clicks_delta_pct"] < -20].nlargest(
                15, "clicks_prev"
            )
            if not drops.empty:
                drops = drops.copy()
                drops["url_short"] = drops["url"].str.replace(
                    r"https?://[^/]+/", "", regex=True
                ).str[:60]
                bars = alt.Chart(drops).mark_bar(color=RED).encode(
                    x=alt.X("clicks_delta_pct:Q", title="Δ Clicks %"),
                    y=alt.Y("url_short:N", sort="x", title=""),
                    tooltip=["url:N", "clicks:Q", "clicks_prev:Q", "clicks_delta_pct:Q"],
                )
                st.altair_chart(
                    bars.properties(title="Mayores caídas de tráfico", height=420),
                    use_container_width=True,
                )
            else:
                st.success("No hay caídas significativas (>20%) en este periodo.")
