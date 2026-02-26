"""
Sidebar component — Optimización 2: separar selección de aplicación.

Pattern: widgets own their state via ``key``. We never pass ``default``/
``value``/``index`` together with ``key`` — that causes the Streamlit
"default value vs Session State API" conflict.  Instead we:
  1. Seed ``st.session_state[widget_key]`` ONCE (first run only).
  2. Let the widget read/write its own key freely.
  3. After all widgets render, sync their values → ``pending_filters``.
"""

import streamlit as st
import pandas as pd
import logging
from state import apply_filters, mark_dirty

logger = logging.getLogger(__name__)


# ── Helpers ─────────────────────────────────────────────────────
def _seed(key, default):
    """Set a widget key only if it doesn't exist yet (first run)."""
    if key not in st.session_state:
        st.session_state[key] = default


def render_sidebar(df: pd.DataFrame):
    """Render the full sidebar.  Returns nothing — state lives in session_state."""
    with st.sidebar:
        st.markdown("### 📊 Blog Audit")
        st.caption("PcComponentes")
        st.markdown("---")
        st.markdown("##### Filtros")

        # ── Seed widget keys on very first run ──────────────────
        _seed("w_cats", [])
        _seed("w_subcats", [])
        _seed("w_types", [])
        _seed("w_vig", [])
        _seed("w_carousel", "Todos")
        _seed("w_alerts", "Todos")
        _seed("w_status", "Todos")
        _seed("w_search", "")
        # w_dates is seeded below (needs valid date bounds first)

        # ── Category ────────────────────────────────────────────
        all_cats = sorted(df.loc[df["_ne_categoria"], "categoria"].unique().tolist())
        st.multiselect(
            "Categoría", all_cats,
            key="w_cats",
            on_change=mark_dirty,
        )

        # ── Subcategory (dependent on selected categories) ──────
        selected_cats = st.session_state["w_cats"]
        if selected_cats:
            pool = df.loc[
                df["categoria"].isin(selected_cats) & df["_ne_subcategoria"],
                "subcategoria",
            ]
        else:
            pool = df.loc[df["_ne_subcategoria"], "subcategoria"]
        all_subcats = sorted(pool.unique().tolist())

        # Prune stale subcategory selections that are no longer valid
        current_sub = st.session_state.get("w_subcats", [])
        valid_sub = [s for s in current_sub if s in all_subcats]
        if valid_sub != current_sub:
            st.session_state["w_subcats"] = valid_sub

        st.multiselect(
            "Subcategoría", all_subcats,
            key="w_subcats",
            on_change=mark_dirty,
        )

        # ── Content type ────────────────────────────────────────
        all_types = sorted(df.loc[df["_ne_tipo_contenido"], "tipo_contenido"].unique().tolist())
        st.multiselect(
            "Tipo de contenido", all_types,
            key="w_types",
            on_change=mark_dirty,
        )

        # ── Vigencia ────────────────────────────────────────────
        all_vig = sorted(df.loc[df["_ne_vigencia"], "vigencia"].unique().tolist())
        st.multiselect(
            "Vigencia", all_vig,
            key="w_vig",
            on_change=mark_dirty,
        )

        # ── Carousel ────────────────────────────────────────────
        carousel_opts = ["Todos", "Con carrusel", "Sin carrusel"]
        st.selectbox(
            "Carrusel de producto", carousel_opts,
            key="w_carousel",
            on_change=mark_dirty,
        )

        # ── Alerts ──────────────────────────────────────────────
        alert_opts = ["Todos", "Con alertas", "Sin alertas"]
        st.selectbox(
            "Alertas", alert_opts,
            key="w_alerts",
            on_change=mark_dirty,
        )

        # ── Status code ────────────────────────────────────────
        all_status = sorted(df["status_code"].unique().tolist())
        status_opts = ["Todos"] + [str(s) for s in all_status]

        # Prune stale status selection
        if st.session_state["w_status"] not in status_opts:
            st.session_state["w_status"] = "Todos"

        st.selectbox(
            "Status code", status_opts,
            key="w_status",
            on_change=mark_dirty,
        )

        # ── Text search ────────────────────────────────────────
        st.text_input(
            "Buscar en título / URL",
            placeholder="Escribe para filtrar…",
            key="w_search",
            on_change=mark_dirty,
        )

        # ── Date range ──────────────────────────────────────────
        if "pub_date_parsed" in df.columns:
            valid_dates = df["pub_date_parsed"].dropna()
            if not valid_dates.empty:
                _seed("w_dates", [])
                st.date_input(
                    "Rango de publicación",
                    min_value=valid_dates.min().date(),
                    max_value=valid_dates.max().date(),
                    key="w_dates",
                    on_change=mark_dirty,
                )

        st.markdown("---")

        # ═══════════════════════════════════════════════════════
        # Sync widget values → pending_filters (single source of truth)
        # ═══════════════════════════════════════════════════════
        pf = st.session_state["pending_filters"]
        pf["categorias"] = st.session_state["w_cats"]
        pf["subcategorias"] = st.session_state["w_subcats"]
        pf["tipos_contenido"] = st.session_state["w_types"]
        pf["vigencia"] = st.session_state["w_vig"]
        pf["carousel"] = st.session_state["w_carousel"]
        pf["alertas"] = st.session_state["w_alerts"]
        pf["status_code"] = st.session_state["w_status"]
        pf["search_text"] = st.session_state["w_search"]
        pf["date_range"] = st.session_state.get("w_dates", [])

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
