"""
Data layer — two‑level caching.

Level 1 (heavy):  ``_fetch_sheets()``  — network I/O to Google Sheets.
                  Cached with TTL = 1 h.  Invalidated only by explicit reload.
Level 2 (light):  ``get_filtered_*()`` — in‑memory pandas filtering.
                  Stored in ``st.session_state`` and invalidated when
                  ``applied_filters`` change (via ``state.apply_filters``).

Optimización 3 — Separar fetch pesado de filtrado ligero.
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import logging

logger = logging.getLogger(__name__)

# ── Sheet names ─────────────────────────────────────────────────
SHEET_URLS_MASTER = "URLs_Master"
SHEET_ALERTAS = "Alertas"
SHEET_GSC_PERFORMANCE = "GSC_Performance"
SHEET_GSC_DELTAS = "GSC_Deltas"

# ── Schema constants ────────────────────────────────────────────
REQUIRED_COLUMNS = ["url", "categoria", "status_code"]
INT_COLUMNS = ["status_code", "h2_count", "word_count", "product_count"]
BOOL_COLUMNS = ["has_noindex", "has_product_carousel", "has_alerts"]
DATE_COLUMNS = ["pub_date", "lastmod"]
TRUTHY_VALUES = frozenset(("TRUE", "VERDADERO", "1", "YES", "SÍ", "SI"))

CACHE_TTL_HEAVY = 3600   # 1 hour — Sheets data barely changes intra‑session
CACHE_TTL_LIGHT = 300    # 5 min  — (kept as safety net; real invalidation is via session_state)


# ═══════════════════════════════════════════════════════════════
# LEVEL 1 — Heavy fetch (network)
# ═══════════════════════════════════════════════════════════════
def _get_gspread_client():
    """Build an authorised gspread client from Streamlit secrets."""
    try:
        creds_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    except KeyError:
        raise RuntimeError("Falta el secret `GCP_SERVICE_ACCOUNT` en Settings → Secrets.")
    except json.JSONDecodeError:
        raise RuntimeError("`GCP_SERVICE_ACCOUNT` no es un JSON válido.")

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return gspread.authorize(creds)


def _coerce_master(df: pd.DataFrame) -> pd.DataFrame:
    """Type coercion + pre‑computed helper columns for URLs_Master."""
    if df.empty:
        return df

    # Integers
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Booleans
    for col in BOOL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().isin(TRUTHY_VALUES)

    # Year in title
    if "year_in_title" in df.columns:
        df["year_in_title"] = pd.to_numeric(df["year_in_title"], errors="coerce")

    # Dates
    for date_col in DATE_COLUMNS:
        if date_col in df.columns:
            df[f"{date_col}_parsed"] = pd.to_datetime(df[date_col], errors="coerce")

    # Non‑empty masks (avoids repeated str ops on every rerun)
    for col in ("categoria", "subcategoria", "tipo_contenido", "vigencia"):
        if col in df.columns:
            df[f"_ne_{col}"] = df[col].astype(str).str.strip() != ""

    # Lowercase columns for fast text search
    df["_url_lower"] = df["url"].astype(str).str.lower()
    if "meta_title" in df.columns:
        df["_title_lower"] = df["meta_title"].astype(str).str.lower()
    if "sitemap_title" in df.columns:
        df["_sitemap_lower"] = df["sitemap_title"].astype(str).str.lower()

    return df


def _coerce_gsc_perf(df: pd.DataFrame) -> pd.DataFrame:
    """Type coercion for GSC_Performance sheet."""
    if df.empty:
        return df
    for col in ("clicks", "impressions"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("ctr", "position"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def _coerce_gsc_delta(df: pd.DataFrame) -> pd.DataFrame:
    """Type coercion for GSC_Deltas sheet."""
    if df.empty:
        return df
    int_cols = ["clicks", "clicks_prev", "impressions", "impressions_prev"]
    float_cols = ["clicks_delta_pct", "position", "position_prev", "position_delta"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=CACHE_TTL_HEAVY, show_spinner="Cargando datos de Sheets…")
def fetch_all_sheets():
    """
    Single network round‑trip that returns four DataFrames.
    Cached for 1 h — only invalidated by explicit ``st.cache_data.clear()``.
    """
    gc = _get_gspread_client()

    try:
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
    except KeyError:
        raise RuntimeError("Falta el secret `SPREADSHEET_ID` en Settings → Secrets.")

    try:
        sh = gc.open_by_key(spreadsheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        raise RuntimeError(f"Spreadsheet con ID '{spreadsheet_id}' no encontrado.")

    # URLs_Master (required)
    try:
        df_master = pd.DataFrame(sh.worksheet(SHEET_URLS_MASTER).get_all_records())
        logger.info("Loaded %d rows from %s", len(df_master), SHEET_URLS_MASTER)
    except gspread.exceptions.WorksheetNotFound:
        raise RuntimeError(f"Hoja '{SHEET_URLS_MASTER}' no encontrada.")

    if not df_master.empty:
        missing = [c for c in REQUIRED_COLUMNS if c not in df_master.columns]
        if missing:
            raise RuntimeError(
                f"Columnas obligatorias ausentes en {SHEET_URLS_MASTER}: {', '.join(missing)}"
            )
    df_master = _coerce_master(df_master)

    # Alertas (optional)
    try:
        df_alerts = pd.DataFrame(sh.worksheet(SHEET_ALERTAS).get_all_records())
        logger.info("Loaded %d rows from %s", len(df_alerts), SHEET_ALERTAS)
    except gspread.exceptions.WorksheetNotFound:
        logger.info("Sheet '%s' not found — alerts disabled", SHEET_ALERTAS)
        df_alerts = pd.DataFrame()

    # GSC_Performance (optional)
    try:
        df_gsc_perf = pd.DataFrame(sh.worksheet(SHEET_GSC_PERFORMANCE).get_all_records())
        df_gsc_perf = _coerce_gsc_perf(df_gsc_perf)
        logger.info("Loaded %d rows from %s", len(df_gsc_perf), SHEET_GSC_PERFORMANCE)
    except gspread.exceptions.WorksheetNotFound:
        logger.info("Sheet '%s' not found — GSC performance disabled", SHEET_GSC_PERFORMANCE)
        df_gsc_perf = pd.DataFrame()

    # GSC_Deltas (optional)
    try:
        df_gsc_delta = pd.DataFrame(sh.worksheet(SHEET_GSC_DELTAS).get_all_records())
        df_gsc_delta = _coerce_gsc_delta(df_gsc_delta)
        logger.info("Loaded %d rows from %s", len(df_gsc_delta), SHEET_GSC_DELTAS)
    except gspread.exceptions.WorksheetNotFound:
        logger.info("Sheet '%s' not found — GSC deltas disabled", SHEET_GSC_DELTAS)
        df_gsc_delta = pd.DataFrame()

    return df_master, df_alerts, df_gsc_perf, df_gsc_delta


# ═══════════════════════════════════════════════════════════════
# LEVEL 2 — Light filtering (in‑memory)
# ═══════════════════════════════════════════════════════════════
def _apply_master_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filters to URLs_Master. Pure function — no side effects."""
    if df.empty or not filters:
        return df

    mask = pd.Series(True, index=df.index)

    cats = filters.get("categorias", [])
    if cats:
        mask &= df["categoria"].isin(cats)

    subcats = filters.get("subcategorias", [])
    if subcats:
        mask &= df["subcategoria"].isin(subcats)

    tipos = filters.get("tipos_contenido", [])
    if tipos:
        mask &= df["tipo_contenido"].isin(tipos)

    vigs = filters.get("vigencia", [])
    if vigs:
        mask &= df["vigencia"].isin(vigs)

    carousel = filters.get("carousel", "Todos")
    if carousel == "Con carrusel" and "has_product_carousel" in df.columns:
        mask &= df["has_product_carousel"]
    elif carousel == "Sin carrusel" and "has_product_carousel" in df.columns:
        mask &= ~df["has_product_carousel"]

    alerts = filters.get("alertas", "Todos")
    if alerts == "Con alertas" and "has_alerts" in df.columns:
        mask &= df["has_alerts"]
    elif alerts == "Sin alertas" and "has_alerts" in df.columns:
        mask &= ~df["has_alerts"]

    status = filters.get("status_code", "Todos")
    if status != "Todos":
        mask &= df["status_code"] == int(status)

    search = filters.get("search_text", "")
    if search:
        sl = search.lower()
        sm = df["_url_lower"].str.contains(sl, na=False)
        if "_title_lower" in df.columns:
            sm |= df["_title_lower"].str.contains(sl, na=False)
        if "_sitemap_lower" in df.columns:
            sm |= df["_sitemap_lower"].str.contains(sl, na=False)
        mask &= sm

    dr = filters.get("date_range", [])
    if len(dr) == 2 and "pub_date_parsed" in df.columns:
        mask &= (df["pub_date_parsed"] >= pd.Timestamp(dr[0])) & \
                (df["pub_date_parsed"] <= pd.Timestamp(dr[1]))

    return df.loc[mask]


def get_filtered_master(df_master: pd.DataFrame) -> pd.DataFrame:
    """Return filtered master, using session_state cache."""
    if st.session_state.get("filtered_master") is not None:
        return st.session_state["filtered_master"]

    filters = st.session_state.get("applied_filters", {})
    result = _apply_master_filters(df_master, filters)
    st.session_state["filtered_master"] = result
    return result


def get_filtered_gsc(df_gsc: pd.DataFrame, df_master_filtered: pd.DataFrame) -> pd.DataFrame:
    """Filter GSC data to only include URLs present in the filtered master."""
    if df_gsc.empty or df_master_filtered.empty:
        return df_gsc
    urls = set(df_master_filtered["url"].str.rstrip("/"))
    return df_gsc[df_gsc["url"].str.rstrip("/").isin(urls)]
