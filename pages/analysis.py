"""
Analysis tab — content gap, word distribution, carousel penetration,
oldest content, heatmap, publication timeline.
"""

import streamlit as st
import altair as alt
import pandas as pd
from styles import (
    BLUE, PURPLE, RED, ORANGE, GREEN, COLORS as METABASE_COLORS,
    BORDER, BG_LIGHT, DARK,
)
from utils.helpers import value_counts_df, crosstab, carousel_penetration, timeline_data

VIGENCIA_CADUCO = "caduco"
VIGENCIA_ACTUALIZABLE = "evergreen_actualizable"


def render(df_filtered: pd.DataFrame, **kwargs):
    st.markdown(
        '<div class="section-header">Análisis de contenido</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Content gap + Word distribution ──────────────────
    col1, col2 = st.columns(2)

    with col1:
        gap_vc = value_counts_df(df_filtered.loc[df_filtered["_ne_categoria"], "categoria"])
        cat_counts = gap_vc.rename(columns={"value": "Categoría", "count": "Artículos"})
        if not cat_counts.empty:
            bars = alt.Chart(cat_counts).mark_bar().encode(
                x=alt.X("Artículos:Q", axis=alt.Axis(title="")),
                y=alt.Y(
                    "Categoría:N",
                    sort=alt.EncodingSortField("Artículos", order="ascending"),
                    axis=alt.Axis(title=""),
                ),
                color=alt.Color(
                    "Artículos:Q",
                    scale=alt.Scale(range=[RED, ORANGE, GREEN]),
                    legend=None,
                ),
                tooltip=["Categoría:N", "Artículos:Q"],
            )
            text = bars.mark_text(align="left", dx=3, fontSize=11).encode(text="Artículos:Q")
            st.altair_chart(
                (bars + text).properties(
                    title="Content gap — categorías con menos contenido",
                    height=max(340, len(cat_counts) * 30 + 60),
                ),
                use_container_width=True,
            )

    with col2:
        if "word_count" in df_filtered.columns:
            df_words = df_filtered[df_filtered["word_count"] > 0]
            if not df_words.empty:
                median_wc = int(df_words["word_count"].median())
                hist = alt.Chart(df_words).mark_bar(color=BLUE).encode(
                    alt.X("word_count:Q", bin=alt.Bin(maxbins=25), title="Palabras"),
                    alt.Y("count()", title="Nº artículos"),
                    tooltip=[
                        alt.Tooltip("word_count:Q", bin=alt.Bin(maxbins=25), title="Rango"),
                        alt.Tooltip("count()", title="Artículos"),
                    ],
                )
                rule = alt.Chart(pd.DataFrame({"x": [median_wc]})).mark_rule(
                    color=PURPLE, strokeDash=[5, 5], strokeWidth=2
                ).encode(x="x:Q")
                label = alt.Chart(
                    pd.DataFrame({"x": [median_wc], "text": [f"Mediana: {median_wc}"]})
                ).mark_text(
                    align="left", dx=5, dy=-10, fontSize=11, color=PURPLE
                ).encode(x="x:Q", text="text:N")
                st.altair_chart(
                    (hist + rule + label).properties(
                        title="Distribución de extensión (palabras por artículo)",
                        height=400,
                    ),
                    use_container_width=True,
                )

    st.markdown("")

    # ── Row 2: Carousel penetration + Oldest content ────────────
    col3, col4 = st.columns(2)

    with col3:
        if "has_product_carousel" in df_filtered.columns and "categoria" in df_filtered.columns:
            df_cat_valid = df_filtered[df_filtered["_ne_categoria"]]
            if not df_cat_valid.empty:
                car_data = carousel_penetration(df_cat_valid)
                car_data["label"] = car_data["pct_carrusel"].apply(lambda x: f"{x:.0f}%")
                bars = alt.Chart(car_data).mark_bar().encode(
                    x=alt.X("pct_carrusel:Q", axis=alt.Axis(title="%")),
                    y=alt.Y(
                        "categoria:N",
                        sort=alt.EncodingSortField("pct_carrusel", order="ascending"),
                        axis=alt.Axis(title=""),
                    ),
                    color=alt.Color(
                        "pct_carrusel:Q",
                        scale=alt.Scale(range=[BG_LIGHT, GREEN]),
                        legend=None,
                    ),
                    tooltip=["categoria:N", "pct_carrusel:Q"],
                )
                text = bars.mark_text(align="left", dx=3, fontSize=11).encode(text="label:N")
                st.altair_chart(
                    (bars + text).properties(
                        title="Penetración de carrusel de producto por categoría",
                        height=max(340, len(car_data) * 30 + 60),
                    ),
                    use_container_width=True,
                )

    with col4:
        df_old = df_filtered[
            df_filtered["vigencia"].isin([VIGENCIA_CADUCO, VIGENCIA_ACTUALIZABLE])
        ]
        if not df_old.empty and "lastmod_parsed" in df_old.columns:
            df_old = df_old.dropna(subset=["lastmod_parsed"]).sort_values(
                "lastmod_parsed", ascending=True
            )
            st.markdown(
                '<div class="section-header" style="font-size:0.95rem">'
                "Contenido prioritario para actualizar</div>",
                unsafe_allow_html=True,
            )
            st.caption("Artículos caducos o actualizables — más antiguos primero")

            n_old = len(df_old)
            max_show = st.slider(
                "Nº de artículos", 10, min(n_old, 100), min(25, n_old),
                key="old_content_slider",
            )
            old_cols = ["url", "meta_title", "vigencia", "lastmod", "categoria"]
            avail = [c for c in old_cols if c in df_old.columns]
            st.dataframe(
                df_old[avail].head(max_show),
                use_container_width=True,
                height=420,
                column_config={
                    "url": st.column_config.LinkColumn("URL"),
                    "meta_title": st.column_config.TextColumn("Título", width="large"),
                    "vigencia": st.column_config.TextColumn("Vigencia"),
                    "lastmod": st.column_config.TextColumn("Últ. modificación"),
                    "categoria": st.column_config.TextColumn("Categoría"),
                },
            )
        elif not df_old.empty:
            st.info("No se pudieron parsear las fechas de última modificación.")
        else:
            st.success("No hay contenido marcado como caduco o actualizable.")

    st.markdown("")

    # ── Row 3: Heatmap Category × Content Type ──────────────────
    df_heat = df_filtered[df_filtered["_ne_categoria"] & df_filtered["_ne_tipo_contenido"]]
    if not df_heat.empty:
        cross = crosstab(df_heat["categoria"], df_heat["tipo_contenido"])
        if not cross.empty and cross.shape[0] > 1 and cross.shape[1] > 1:
            melted = cross.reset_index().melt(
                id_vars="categoria", var_name="tipo_contenido", value_name="count"
            )
            mean_val = cross.values.mean()
            base = alt.Chart(melted).mark_rect().encode(
                x=alt.X("tipo_contenido:N", title=""),
                y=alt.Y("categoria:N", title=""),
                color=alt.Color(
                    "count:Q",
                    scale=alt.Scale(range=[BG_LIGHT, BLUE, PURPLE]),
                    legend=None,
                ),
                tooltip=["categoria:N", "tipo_contenido:N", "count:Q"],
            )
            text = base.mark_text(fontSize=11).encode(
                text="count:Q",
                color=alt.condition(
                    alt.datum.count > mean_val, alt.value("white"), alt.value(DARK)
                ),
            )
            st.altair_chart(
                (base + text).properties(
                    title="Mapa de contenido — Categoría × Tipo",
                    height=max(400, cross.shape[0] * 32 + 80),
                ),
                use_container_width=True,
            )

    st.markdown("")

    # ── Row 4: Publication timeline ─────────────────────────────
    if "pub_date_parsed" in df_filtered.columns:
        tl = timeline_data(df_filtered["pub_date_parsed"])
        if not tl.empty:
            chart = alt.Chart(tl).mark_bar(color=BLUE).encode(
                x=alt.X("year_month:N", title="", axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("Artículos:Q", title="Artículos publicados"),
                tooltip=["year_month:N", "Artículos:Q"],
            ).properties(title="Publicaciones por mes", height=350)
            st.altair_chart(chart, use_container_width=True)
