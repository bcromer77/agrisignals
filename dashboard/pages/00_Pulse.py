import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# ---------- basic look & feel (rhissignals-ish) ----------
st.set_page_config(page_title="AgriSignals — Auction & Boxed Beef Pulse", layout="wide")

try:
    _auto(interval=60_000, key="refresh")  # refresh every 60s
except Exception:
    pass

PRIMARY = "#0A84FF"  # subtle blue accent
st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 1.4rem; }}
      h1, h2, h3 {{ letter-spacing: 0.2px; }}
      .kpi {{
         background: #0b0b0c; color: #f5f5f7; border: 1px solid #1f1f22;
         border-radius: 16px; padding: 14px 16px; font-size: 14px;
      }}
      .kpi .value {{ font-size: 28px; font-weight: 700; color: {PRIMARY}; }}
      .kpi .label {{ opacity: .85; }}
      .section-card {{
         background: #0b0b0c; border: 1px solid #1f1f22; border-radius: 16px; padding: 12px;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- db ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agrisignals.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

st.title("🐂 AgriSignals — Auction & Boxed Beef Pulse")

# ---------- boxed beef ----------
# NOTE: single quotes around the whole SQL; "select" kept in double quotes so SQLite treats it as a column name.
bb = pd.read_sql(
    'SELECT date, choice, "select" AS sel, loads FROM boxed_beef ORDER BY date DESC',
    engine,
)

# ensure numeric for math/plots
for col in ["choice", "sel", "loads"]:
    if col in bb.columns:
        bb[col] = pd.to_numeric(bb[col], errors="coerce")

if not bb.empty:
    bb = bb.sort_values("date")
    bb["spread"] = bb["choice"] - bb["sel"]

    # KPIs
    latest = bb.iloc[-1]
    prev = bb.iloc[-2] if len(bb) > 1 else latest
    kpi_cols = st.columns(4)
    kpi_cols[0].markdown(
        f'<div class="kpi"><div class="label">Choice (latest)</div>'
        f'<div class="value">{latest["choice"]:.2f}</div></div>', unsafe_allow_html=True
    )
    kpi_cols[1].markdown(
        f'<div class="kpi"><div class="label">Select (latest)</div>'
        f'<div class="value">{latest["sel"]:.2f}</div></div>', unsafe_allow_html=True
    )
    kpi_cols[2].markdown(
        f'<div class="kpi"><div class="label">Spread (C-S)</div>'
        f'<div class="value">{latest["spread"]:.2f}</div></div>', unsafe_allow_html=True
    )
    d = latest["choice"] - prev["choice"] if len(bb) > 1 else 0.0
    kpi_cols[3].markdown(
        f'<div class="kpi"><div class="label">Choice Δ (d/d)</div>'
        f'<div class="value">{d:+.2f}</div></div>', unsafe_allow_html=True
    )

    # Charts
    st.markdown("### Boxed Beef (Choice vs Select)")
    st.line_chart(bb.set_index("date")[["choice", "sel"]])

    st.markdown("### Choice–Select Spread")
    st.line_chart(bb.set_index("date")[["spread"]])

else:
    st.info("No boxed beef data yet. Run the seeder or ingestor.")

# ---------- auctions ----------
st.markdown("### Recent Auction Highlights")
au = pd.read_sql(
    "SELECT sale_date, market, location, head_count, weight_band, price_cwt, keywords "
    "FROM auctions ORDER BY sale_date DESC",
    engine,
)
st.dataframe(au, use_container_width=True)

# ---------- signals ----------
st.markdown("### Signals")
sig = pd.read_sql(
    "SELECT date, name, value, triggered, notes FROM signals ORDER BY date DESC",
    engine,
)
st.dataframe(sig, use_container_width=True)

st.caption("Keywords watched: 'sorted twice', 'double-sorted', 'no implants'")

