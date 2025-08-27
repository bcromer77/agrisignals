import streamlit as st
from pymongo import MongoClient
import os

def render_ticker():
    """Render a scrolling ticker of the latest AgriSignals intelligence."""

    # --- Auto refresh every 60s ---
    st_autorefresh = st.experimental_rerun  # fallback for old versions
    st_autorefresh = getattr(st, "autorefresh", None)
    if st_autorefresh:
        st_autorefresh(interval=60000, limit=None, key="ticker_refresh")

    # --- Connect to Mongo ---
    client = MongoClient(os.environ["MONGO_URI"])
    db = client[os.environ.get("MONGO_DB", "agrisignals")]

    items = []

    # --- Retail signals ---
    retail = list(db["retail_signals"].find().sort("date", -1).limit(5))
    for r in retail:
        items.append(f"🛒 {r.get('headline', '')} → {r.get('so_what', '')}")

    # --- Auction signals ---
    auctions = list(db["auctions"].find().sort("date", -1).limit(3))
    for a in auctions:
        headline = a.get("market", "Auction")
        items.append(f"🐂 {headline} → {a.get('price', '?')} USD")

    # --- Water restriction signals ---
    water = list(db["water_restrictions"].find().sort("date", -1).limit(3))
    for w in water:
        items.append(f"💧 {w.get('state')} {w.get('area')} → {w.get('note')}")

    # --- Fallback if nothing found ---
    if not items:
        items = [
            "🛒 McDonalds combo cut → affordability hedge",
            "📦 Walmart shrinkflation pushback",
            "🐂 Oklahoma cattle prices spike 12%",
            "💧 Kern County groundwater cuts under SGMA"
        ]

    ticker_text = "  |  ".join(items)

    # --- Render ticker ---
    st.markdown(
        f"""
        <div style="background-color:#111; padding:10px; border-radius:8px; overflow:hidden;">
            <marquee style="color:#FAFAFA; font-weight:bold; font-size:16px;">
                {ticker_text}
            </marquee>
        </div>
        """,
        unsafe_allow_html=True
    )

