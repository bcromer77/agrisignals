# dashboard/pages/00_Pulse.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
import pandas as pd

# --- Load env ---
load_dotenv()

# --- Streamlit page config ---
st.set_page_config(page_title="AgriSignals - Pulse", layout="wide")

# --- DB Connection ---
try:
    client = MongoClient(os.environ["MONGO_URI"])
    db = client[os.environ.get("MONGO_DB", "agrisignals")]
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- Layout Header ---
st.title("🌾 AgriSignals Pulse Dashboard")
st.markdown("Live intelligence feed across commodities, water, and risks")

# --- Commodity Signals ---
st.subheader("📊 Commodity Signals")
cols = st.columns(3)

# --- Cattle Auctions ---
with cols[0]:
    latest_cattle = db["auctions"].find_one(sort=[("date", -1)])
    if latest_cattle:
        st.metric(
            "Cattle Price",
            f"${latest_cattle.get('price', '?')}",
            "+12%"  # 🔜 later: calculate dynamically vs. last week
        )
    else:
        st.info("No cattle auction data yet")

# --- Coffee Futures ---
with cols[1]:
    coffee = db["tariff_indicators"].find_one(sort=[("date", -1)])
    if coffee:
        st.metric(
            "Coffee Futures",
            f"{coffee.get('indicator', '?')}%",
            "+3%"  # 🔜 later: link to Brazil drought index
        )
    else:
        st.info("No coffee futures data yet")

# --- Water Restrictions ---
with cols[2]:
    water = db["water_restrictions"].find_one(sort=[("date", -1)])
    if water:
        st.metric(
            f"Water Stress ({water.get('state', 'N/A')})",
            f"{water.get('level', '?')}%",
            "Rising" if water.get("active") else "Stable"
        )
    else:
        st.info("No water restriction data yet")

