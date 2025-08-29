import os, requests, json, time
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "agrisignals_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db["colorado_wells"]

# --- Example Colorado DWR endpoint ---
# (placeholder: adjust if API/CSV feed available)
BASE_URL = "https://dwr.state.co.us/Rest/GET/api/v2/welllogs"  

def fetch_wells(division="1", aquifer="ALAMOSA", limit=100):
    """Fetch wells from Colorado DWR API (or scrape)."""
    params = {
        "division": division,
        "aquifer": aquifer,
        "format": "json",
        "perPage": limit,
        "page": 1
    }
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    return r.json()

def process_and_store(data, division, aquifer):
    docs = []
    for item in data.get("ResultList", []):
        doc = {
            "division": division,
            "aquifer": aquifer,
            "permit_number": item.get("permit"),
            "location": {
                "lat": item.get("latitude"),
                "lon": item.get("longitude")
            },
            "status": item.get("status"),
            "water_level": item.get("waterLevel"),
            "logged_at": datetime.utcnow().isoformat()
        }
        collection.update_one(
            {"permit_number": doc["permit_number"]},
            {"$set": doc},
            upsert=True
        )
        docs.append(doc)
    print(f"✅ Upserted {len(docs)} docs for {division}-{aquifer}")
    return docs

def run():
    divisions = ["1", "2", "3"]  # South Platte, Arkansas, Rio Grande
    aquifers = ["ALAMOSA", "ARAPAHOE", "CHADRON", "CASTLE ROCK CONGLOMERATE"]

    for div in divisions:
        for aq in aquifers:
            try:
                data = fetch_wells(div, aq)
                process_and_store(data, div, aq)
                time.sleep(1)  # respect rate limits
            except Exception as e:
                print(f"⚠️ Failed for {div}-{aq}: {e}")

if __name__ == "__main__":
    run()

