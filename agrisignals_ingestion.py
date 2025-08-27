import os
import sys
import json
import glob
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI

# --- Load env vars ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "agrisignals_db")
COLLECTION = "sources_collection"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not MONGO_URI or not OPENAI_API_KEY:
    sys.exit("❌ Missing MONGO_URI or OPENAI_API_KEY in environment. Check your .env file.")

# --- Mongo + OpenAI Clients ---
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[COLLECTION]
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- Helper: Embedding ---
def generate_embedding(text: str):
    if not text or not text.strip():
        return []
    resp = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]  # truncate for safety
    )
    return resp.data[0].embedding

# --- Helper: Ingest Excel/CSV structured sources (DOL, water levels) ---
def ingest_structured_file(url, source_meta):
    print(f"📥 Processing structured file: {url}")
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        # Auto-detect format
        if url.endswith(".csv"):
            df = pd.read_csv(BytesIO(resp.content))
        else:
            df = pd.read_excel(BytesIO(resp.content))
    except Exception as e:
        print(f"❌ Failed to fetch or parse structured file {url}: {e}")
        return []

    records = []
    for _, row in df.iterrows():
        try:
            state = str(row.get("Worksite State", "")).strip()
            county = str(row.get("Worksite County", "")).strip()
            employer = str(row.get("Employer Name", "")).strip()
            requested = int(row.get("Total Worker Positions Requested", 0))
            certified = int(row.get("Total Worker Positions Certified", 0))
            rate = certified / requested if requested else 0.0

            # Build summary string for embedding
            content = (
                f"{source_meta['commodity']} signal: "
                f"{employer} requested {requested}, {certified} certified "
                f"({rate:.0%}) in {county} County, {state}."
            )

            rec = {
                **source_meta,
                "employer": employer,
                "state": state,
                "county": county,
                "workers_requested": requested,
                "workers_certified": certified,
                "certification_rate": rate,
                "decision_date": str(row.get("Decision Date", "")),
                "scraped_content": content,
                "embedding": generate_embedding(content),
                "ingest_date": datetime.utcnow()
            }
            records.append(rec)
        except Exception as e:
            print(f"⚠️ Error parsing row: {e}")
    return records

# --- Helper: Ingest Web Sources (Firecrawl or fallback to requests.get) ---
def ingest_web_source(url, source_meta):
    print(f"🌍 Fetching web content: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None

    content = (text[:2000] + "...") if len(text) > 2000 else text
    rec = {
        **source_meta,
        "scraped_content": content,
        "embedding": generate_embedding(content),
        "ingest_date": datetime.utcnow()
    }
    return rec

# --- Main Ingestion Loop ---
def main():
    source_files = list(Path(".").glob("*_sources.json"))
    if not source_files:
        sys.exit("❌ No *_sources.json files found in repo root.")

    print(f"📑 Found {len(source_files)} source packs: {[f.name for f in source_files]}")

    for sf in source_files:
        try:
            sources = json.load(open(sf))
        except Exception as e:
            print(f"❌ Failed to load {sf}: {e}")
            continue

        print(f"✅ Loaded {len(sources)} sources from {sf.name}")

        for src in sources:
            url = src.get("url")
            if not url:
                continue

            # Structured file ingestion
            if url.endswith(".csv") or url.endswith(".xlsx"):
                records = ingest_structured_file(url, src)
                if records:
                    collection.insert_many(records)
                    print(f"→ Inserted {len(records)} structured records for {src['source_id']}")
                continue

            # Web/source ingestion
            rec = ingest_web_source(url, src)
            if rec:
                collection.insert_one(rec)
                print(f"→ Inserted web record for {src['source_id']}")

    print("🎉 Ingestion complete.")

if __name__ == "__main__":
    main()
