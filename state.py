"""
Centralised session‑state management.

Every key used across the app is declared here with its default value.
Call ``init_state()`` once at the top of ``app.py`` — before any widget.

Optimización 1 — Estado centralizado con defaults explícitos.
"""

import streamlit as st
from datetime import datetime, timedelta

# ── Defaults ────────────────────────────────────────────────────
DEFAULTS = {
    # Auth
    "authenticated": False,
    "login_attempts": 0,
    "lockout_until": None,
    "current_user": None,

    # Pending filters (what the sidebar widgets show)
    "pending_filters": {
        "categorias": [],
        "subcategorias": [],
        "tipos_contenido": [],
        "vigencia": [],
        "carousel": "Todos",
        "alertas": "Todos",
        "status_code": "Todos",
        "search_text": "",
        "date_range": [],
    },

    # Applied filters (what actually drives the data — only updates on "Aplicar")
    "applied_filters": {},

    # Cached filtered DataFrames (invalidated when applied_filters change)
    "filtered_master": None,
    "filtered_gsc_perf": None,
    "filtered_gsc_delta": None,

    # UI / navigation
    "active_tab": "Dashboard",
    "detail_view": None,       # For drill‑down (GSC tab)
    "filters_dirty": False,    # True when pending ≠ applied
}


def init_state():
    """Populate ``st.session_state`` with any missing keys."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            # Deep‑copy dicts / lists so mutations don't leak across sessions
            if isinstance(default, (dict, list)):
                import copy
                st.session_state[key] = copy.deepcopy(default)
            else:
                st.session_state[key] = default


def apply_filters():
    """Snapshot pending → applied and invalidate cached filtered data."""
    import copy
    st.session_state["applied_filters"] = copy.deepcopy(
        st.session_state["pending_filters"]
    )
    st.session_state["filtered_master"] = None
    st.session_state["filtered_gsc_perf"] = None
    st.session_state["filtered_gsc_delta"] = None
    st.session_state["filters_dirty"] = False


def mark_dirty():
    """Flag that pending filters differ from applied ones."""
    st.session_state["filters_dirty"] = True


def reset_detail():
    st.session_state["detail_view"] = None
