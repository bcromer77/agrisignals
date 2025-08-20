import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

st.set_page_config(page_title="AgriSignals Dashboard", layout="wide")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agrisignals.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

st.title("🐂 AgriSignals — Auction & Boxed Beef Pulse")

# Boxed Beef
bb = pd.read_sql("SELECT date, choice, select, loads FROM boxed_beef ORDER BY date DESC", engine)
st.subheader("Boxed Beef (Choice vs Select)")
st.line_chart(bb.set_index("date")[["choice", "select"]])

# Spread
if len(bb) >= 1:
    bb2 = bb.copy()
    bb2["spread"] = bb2["choice"] - bb2["select"]
    st.subheader("Choice–Select Spread")
    st.line_chart(bb2.set_index("date")[["spread"]])

# Auctions
st.subheader("Recent Auction Highlights")
au = pd.read_sql("SELECT sale_date, market, location, head_count, weight_band, price_cwt, keywords FROM auctions ORDER BY sale_date DESC", engine)
st.dataframe(au)

# Signals
st.subheader("Signals")
sig = pd.read_sql("SELECT date, name, value, triggered, notes FROM signals ORDER BY date DESC", engine)
st.dataframe(sig)

st.caption("Keywords watched: 'sorted twice', 'double-sorted', 'no implants'")
