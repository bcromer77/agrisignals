# dashboard/Home.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from dashboard.components.ticker import render_ticker

render_ticker()
import streamlit as st
import pandas as pd

# Load env
load_dotenv()

# Connect Mongo
client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ.get("MONGO_DB", "agrisignals")]

st.set_page_config(page_title="AgriSignals", layout="wide")

# --- Header ---
st.title("AgriSignals")
st.markdown("Live commodity, water, and risk intelligence")
signals = [
    {"title": "Colorado litigation risk rises", "value": "0.84"},
    {"title": "Port of Houston backlog", "value": "12 ships"},
    {"title": "Vegas hotel occupancy", "value": "-18% YoY"},
]

render_ticker(signals)

# --- Commodity Signals ---
st.subheader("📊 Commodity Signals")
cols = st.columns(4)

with cols[0]:
    cattle = db["auctions"].find_one(sort=[("date", -1)])
    if cattle:
        st.metric("🐂 Cattle", f"${cattle.get('price', '?')}", "+12% herd stress")
    else:
        st.write("No cattle data yet")

with cols[1]:
    coffee = db["tariff_indicators"].find_one(sort=[("date", -1)])
    if coffee:
        st.metric("☕ Coffee", f"{coffee.get('indicator', '?')}%", "Brazil drought risk")
    else:
        st.write("No coffee data yet")

with cols[2]:
    corn = db["crop_reports"].find_one(sort=[("date", -1)])
    if corn:
        st.metric("🌽 Corn", corn.get("status", "?"), "+ delays")
    else:
        st.write("No corn data yet")

with cols[3]:
    citrus = db["fruit_signals"].find_one(sort=[("date", -1)])
    if citrus:
        st.metric("🍊 Citrus", "Greening outbreak", citrus.get("region", "Florida"))
    else:
        st.write("No citrus data yet")

# --- Regulatory Horizon Scanning ---
st.subheader("📜 Regulatory Horizon Scanning")
regs = db["council_minutes"].find().limit(5)
for r in regs:
    st.write(f"- {r.get('title')} ({r.get('date')})")

# --- Watchlist ---
st.sidebar.header("Your Watchlist")
watchlist = ["Florida Citrus", "Vegas Tourism", "Brazil Coffee Exports"]
for w in watchlist:
    st.sidebar.write(f"- {w}")

