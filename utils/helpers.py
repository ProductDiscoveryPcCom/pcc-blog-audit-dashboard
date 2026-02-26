"""
Reusable chart helpers and export functions.
"""

import streamlit as st
import pandas as pd
import io


# ═══════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════
def value_counts_df(series: pd.Series) -> pd.DataFrame:
    """Return value_counts as a DataFrame with [value, count]."""
    vc = series.value_counts().reset_index()
    vc.columns = ["value", "count"]
    return vc


def crosstab(idx: pd.Series, col: pd.Series) -> pd.DataFrame:
    return pd.crosstab(idx, col)


def carousel_penetration(df_subset: pd.DataFrame) -> pd.DataFrame:
    agg = df_subset.groupby("categoria").agg(
        total=("url", "count"),
        con_carrusel=("has_product_carousel", "sum"),
    ).reset_index()
    agg["pct_carrusel"] = (agg["con_carrusel"] / agg["total"] * 100).round(1)
    return agg.sort_values("pct_carrusel", ascending=True)


def timeline_data(pub_dates: pd.Series) -> pd.DataFrame:
    s = pub_dates.dropna()
    if s.empty:
        return pd.DataFrame()
    ym = s.dt.to_period("M").astype(str)
    tl = ym.value_counts().reset_index()
    tl.columns = ["year_month", "Artículos"]
    return tl.sort_values("year_month")


# ═══════════════════════════════════════════════════════════════
# EXPORT HELPERS (cached)
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def to_csv(data: pd.DataFrame) -> bytes:
    return data.to_csv(index=False).encode("utf-8")


@st.cache_data
def to_excel(data: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="URLs")
    return buf.getvalue()
