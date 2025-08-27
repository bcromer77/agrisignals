import streamlit as st
import pandas as pd
from pymongo import MongoClient
import os

# Connect to Mongo
client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ.get("MONGO_DB", "agrisignals")]

st.title("🐂 AgriSignals — Commodity & Auction Pulse")
auctions = list(db["auctions"].find().limit(20))
if auctions:
    df = pd.DataFrame(auctions)
    st.write("Raw auction data sample:", df.head())

    # Only plot if fields exist
    required_cols = ["date", "price", "volume"]
    if all(col in df.columns for col in required_cols):
        st.line_chart(df.set_index("date")[["price", "volume"]])
    else:
        st.warning(f"⚠️ Missing fields in auctions collection: {df.columns.tolist()}")
else:
    st.info("No auction data available yet.")

# === Example: Retail Signals ===
retail = list(db["retail_signals"].find().sort("date", -1).limit(10))
if retail:
    rf = pd.DataFrame(retail)[["date", "headline", "so_what", "tradecraft"]]
    st.subheader("🛒 Retail Signals")
    st.dataframe(rf)
else:
    st.info("No retail data yet.")


# === Example: Cattle Auctions ===
auctions = list(db["auction_quotes"].find().limit(10))
if auctions:
    df = pd.DataFrame(auctions)
    st.subheader("Cattle Auctions")
    st.write("Auction data sample:", df.head())

    required_cols = ["date", "market", "price", "volume"]
    if all(col in df.columns for col in required_cols):
        st.dataframe(df[required_cols])
    else:
        st.warning(f"⚠️ Missing fields in auction_quotes: {df.columns.tolist()}")
else:
    st.info("No auction data yet.")

# === Example: Water Restrictions ===
water = list(db["water_restrictions"].find().limit(10))
if water:
    wf = pd.DataFrame(water)
    st.subheader("Water Restrictions")
    st.write("Restriction data sample:", wf.head())

    required_cols = ["state", "area", "level", "note", "date"]
    if all(col in wf.columns for col in required_cols):
        st.dataframe(wf[required_cols])
    else:
        st.warning(f"⚠️ Missing fields in water_restrictions: {wf.columns.tolist()}")
else:
    st.info("No water restriction data yet.")

