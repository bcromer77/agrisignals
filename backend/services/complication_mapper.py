# backend/services/complication_mapper.py

"""
Agrisignals Complication Mapper
Turns raw signals (news, twitter, datasets, PDFs) into actionable "complications":
- so_what: what the signal means
- who_bleeds: who loses
- who_benefits: who gains
- tradecraft_note: Axelrod-style hedge/alpha play
"""

import os
from datetime import datetime
import pandas as pd
import spacy
import yfinance as yf

# Optional: external feeds
import requests
import fitz  # PyMuPDF for PDFs
import feedparser

nlp = spacy.load("en_core_web_sm")

# --- Commodity keywords ---
COMMODITIES = {
    "cattle": ["cattle", "beef", "auction"],
    "corn": ["corn", "ethanol", "feed"],
    "coffee": ["coffee", "brazil", "frost"],
    "citrus": ["citrus", "orange", "hurricane", "greening"],
    "cannabis": ["cannabis", "weed", "legalize", "marijuana"],
    "regulatory": ["tariff", "visa", "epa", "fda", "rfk", "policy"],
    "municipal": ["bond", "foreclosure", "water board", "muni"],
    "water": ["platte", "cfs", "diversion", "reservoir", "drought"],
}

# --- Entities for exposures ---
ENTITY_MAP = {
    "cattle": {
        "entities": ["McDonalds", "Burger King", "Tyson", "JBS", "Walmart"],
        "tradecraft": {
            "McDonalds": "Surge pricing & menu swaps hedge beef volatility",
            "Burger King": "No hedge strategy detected",
            "Tyson": "Hedging in futures markets",
            "JBS": "No hedge strategy detected",
            "Walmart": "Substituting SKUs and sourcing via Canada/Mexico pact",
        },
    },
    "corn": {
        "entities": ["ADM", "Cargill", "PepsiCo", "Ethanol refiners"],
    },
    "coffee": {
        "entities": ["Starbucks", "Nestle", "Dunkin"],
    },
    "citrus": {
        "entities": ["Tropicana", "Coca-Cola", "PepsiCo", "Retail chains"],
    },
    "cannabis": {
        "entities": ["Tilray", "Canopy Growth", "State tax revenues"],
    },
}

# --- Helpers ---
def extract_pdf_text(pdf_url: str) -> str:
    """Extract text from PDF via PyMuPDF"""
    try:
        resp = requests.get(pdf_url, timeout=30)
        doc = fitz.open(stream=resp.content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text[:2000]
    except Exception as e:
        return f"Error extracting {pdf_url}: {e}"


def detect_signals(text: str) -> list[str]:
    """Return commodity categories detected in text"""
    text = text.lower()
    hits = []
    for comm, kws in COMMODITIES.items():
        if any(kw in text for kw in kws):
            hits.append(comm)
    return hits


# --- Main mapper ---
def complication_mapper(signal: dict) -> dict:
    complications = []

    title = signal.get("title", "").lower()
    raw_text = signal.get("raw_text", "").lower()
    dataset_data = signal.get("dataset_data", {})
    twitter_posts = signal.get("twitter_posts", [])
    news_df: pd.DataFrame = signal.get("news_df", pd.DataFrame())

    # Aggregate all text
    texts = [title, raw_text]
    if not news_df.empty:
        texts.extend(news_df["text"].tolist())
    texts.extend([p["text"] for p in twitter_posts])

    all_hits = []
    for t in texts:
        all_hits.extend(detect_signals(t))

    # --- Core commodity complications ---
    for comm in set(all_hits):
        if comm in ENTITY_MAP:
            entities = ENTITY_MAP[comm]["entities"]
            tradecraft = ENTITY_MAP[comm].get("tradecraft", {})
            for e in entities:
                comp = {
                    "so_what": f"{e} exposed to {comm} volatility",
                    "who_bleeds": [e],
                    "who_benefits": ["Alternative suppliers", "Substitutes"],
                    "tradecraft_note": tradecraft.get(e, "No hedge strategy detected"),
                }
                complications.append(comp)

        elif comm == "regulatory":
            complications.append({
                "so_what": "Regulatory change impacting agri/food markets",
                "who_bleeds": ["Importers", "Labor-dependent farmers"],
                "who_benefits": ["Domestic producers", "Lobby-aligned firms"],
                "tradecraft_note": "Track chatter on H-2 visas, tariffs, RFK sugar stance",
            })

        elif comm == "municipal":
            complications.append({
                "so_what": "Municipal stress: water boards, bonds, foreclosures",
                "who_bleeds": ["Local taxpayers", "Muni bondholders"],
                "who_benefits": ["Distressed-debt funds", "Alt water suppliers"],
                "tradecraft_note": "Watch muni disclosures before S&P downgrades",
            })

        elif comm == "water":
            amt = dataset_data.get("amount", None)
            if amt is not None and amt < 120:  # Platte compact threshold
                try:
                    adm_price = yf.Ticker("ADM").history(period="1d")["Close"].iloc[-1]
                except Exception:
                    adm_price = 60.0
                complications.append({
                    "so_what": "South Platte water scarcity – Compact violation risk",
                    "probability": 0.85,
                    "who_bleeds": ["ADM", "Regional ag lenders"],
                    "who_benefits": ["Xylem (XYL)", "Ecolab (ECL)"],
                    "tradecraft_note": f"Short ADM puts (≈${adm_price:.2f}), long XYL infra spend",
                })

    return {
        "complications": complications,
        "total_complications": len(complications),
        "timestamp": datetime.utcnow().isoformat(),
    }


# --- Run standalone ---
if __name__ == "__main__":
    test_signal = {
        "title": "Oklahoma cattle auction prices up 12%",
        "raw_text": "Cattle auctions in Oklahoma reported prices up 12% due to drought pressure.",
        "dataset_data": {"station": "PLAJURCO", "amount": 41, "units": "CFS"},
        "twitter_posts": [
            {"handle": "@FarmPolicy", "text": "NE farmers warn of loan defaults amid Platte crisis."},
            {"handle": "@DWR_CO", "text": "Curtailments likely in Weld County due to low flows."},
        ],
    }
    intel = complication_mapper(test_signal)
    print(f"🧠 Generated {intel['total_complications']} complications at {intel['timestamp']}")
    for c in intel["complications"]:
        print("-", c["so_what"])
        print("  Who bleeds:", c["who_bleeds"])
        print("  Who benefits:", c["who_benefits"])
        print("  Tradecraft:", c["tradecraft_note"])

