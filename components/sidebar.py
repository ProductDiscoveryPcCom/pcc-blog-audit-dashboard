"""
Sidebar component — Optimización 2: separar selección de aplicación.

Widgets write to ``st.session_state["pending_filters"]``.
The "Aplicar filtros" button snapshots pending → applied and invalidates caches.
"""

import streamlit as st
import pandas as pd
import logging
from state import apply_filters, mark_dirty

logger = logging.getLogger(__name__)


def render_sidebar(df: pd.DataFrame):
    """Render the full sidebar.  Returns nothing — state lives in session_state."""
    with st.sidebar:
        st.markdown("### 📊 Blog Audit")
        st.caption("PcComponentes")
        st.markdown("---")
        st.markdown("##### Filtros")

        pf = st.session_state["pending_filters"]

        # ── Category ────────────────────────────────────────────
        all_cats = sorted(df.loc[df["_ne_categoria"], "categoria"].unique().tolist())
        pf["categorias"] = st.multiselect(
            "Categoría", all_cats,
            default=pf.get("categorias", []),
            key="w_cats",
            on_change=mark_dirty,
        )

        # ── Subcategory (dependent) ────────────────────────────
        if pf["categorias"]:
            pool = df.loc[
                df["categoria"].isin(pf["categorias"]) & df["_ne_subcategoria"],
                "subcategoria",
            ]
        else:
            pool = df.loc[df["_ne_subcategoria"], "subcategoria"]
        all_subcats = sorted(pool.unique().tolist())

        # Keep only still‑valid defaults
        valid_sub = [s for s in pf.get("subcategorias", []) if s in all_subcats]
        pf["subcategorias"] = st.multiselect(
            "Subcategoría", all_subcats,
            default=valid_sub,
            key="w_subcats",
            on_change=mark_dirty,
        )

        # ── Content type ────────────────────────────────────────
        all_types = sorted(df.loc[df["_ne_tipo_contenido"], "tipo_contenido"].unique().tolist())
        pf["tipos_contenido"] = st.multiselect(
            "Tipo de contenido", all_types,
            default=pf.get("tipos_contenido", []),
            key="w_types",
            on_change=mark_dirty,
        )

        # ── Vigencia ────────────────────────────────────────────
        all_vig = sorted(df.loc[df["_ne_vigencia"], "vigencia"].unique().tolist())
        pf["vigencia"] = st.multiselect(
            "Vigencia", all_vig,
            default=pf.get("vigencia", []),
            key="w_vig",
            on_change=mark_dirty,
        )

        # ── Carousel ────────────────────────────────────────────
        carousel_opts = ["Todos", "Con carrusel", "Sin carrusel"]
        pf["carousel"] = st.selectbox(
            "Carrusel de producto", carousel_opts,
            index=carousel_opts.index(pf.get("carousel", "Todos")),
            key="w_carousel",
            on_change=mark_dirty,
        )

        # ── Alerts ──────────────────────────────────────────────
        alert_opts = ["Todos", "Con alertas", "Sin alertas"]
        pf["alertas"] = st.selectbox(
            "Alertas", alert_opts,
            index=alert_opts.index(pf.get("alertas", "Todos")),
            key="w_alerts",
            on_change=mark_dirty,
        )

        # ── Status code ────────────────────────────────────────
        all_status = sorted(df["status_code"].unique().tolist())
        status_opts = ["Todos"] + [str(s) for s in all_status]
        current_status = pf.get("status_code", "Todos")
        idx = status_opts.index(current_status) if current_status in status_opts else 0
        pf["status_code"] = st.selectbox(
            "Status code", status_opts,
            index=idx,
            key="w_status",
            on_change=mark_dirty,
        )

        # ── Text search ────────────────────────────────────────
        pf["search_text"] = st.text_input(
            "Buscar en título / URL", pf.get("search_text", ""),
            placeholder="Escribe para filtrar…",
            key="w_search",
            on_change=mark_dirty,
        )

        # ── Date range ──────────────────────────────────────────
        if "pub_date_parsed" in df.columns:
            valid_dates = df["pub_date_parsed"].dropna()
            if not valid_dates.empty:
                pf["date_range"] = st.date_input(
                    "Rango de publicación",
                    value=pf.get("date_range", []),
                    min_value=valid_dates.min().date(),
                    max_value=valid_dates.max().date(),
                    key="w_dates",
                    on_change=mark_dirty,
                )

        st.markdown("---")

        # ── Apply button (Optimización 2 core) ─────────────────
        is_dirty = st.session_state.get("filters_dirty", False)
        # First load — auto‑apply so dashboard shows all data
        if not st.session_state.get("applied_filters"):
            apply_filters()

        btn_container = st.container()
        with btn_container:
            if is_dirty:
                st.markdown(
                    '<div class="apply-btn-dirty">',
                    unsafe_allow_html=True,
                )
            if st.button("Aplicar filtros", use_container_width=True, type="primary"):
                apply_filters()
                st.rerun()
            if is_dirty:
                st.markdown("</div>", unsafe_allow_html=True)
                st.caption("⚡ Hay filtros sin aplicar")

        st.markdown("---")

        # ── Counts ──────────────────────────────────────────────
        from data import get_filtered_master
        df_f = get_filtered_master(df)
        n_total, n_filtered = len(df), len(df_f)
        if n_filtered < n_total:
            st.caption(f"Mostrando **{n_filtered}** de {n_total} URLs")
        else:
            st.caption(f"**{n_total}** URLs totales")

        st.markdown("---")

        # ── Utility buttons ─────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↻ Recargar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state["current_user"] = None
                logger.info("User logged out")
                st.rerun()
