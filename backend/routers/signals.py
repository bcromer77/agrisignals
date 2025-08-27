from fastapi import APIRouter, Query
from pymongo import MongoClient
import os
from datetime import datetime

router = APIRouter(prefix="/signals", tags=["signals"])

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")


@router.get("/stressmap")
def stressmap(state: str | None = None, county: str | None = None, sector: str | None = None, limit: int = 50):
    """
    Aggregate signals into stress scores for choropleth maps and dashboard cards.
    - state / county filters
    - sector = e.g. 'construction', 'nursing', 'fruit', 'beef'
    """
    mongo = MongoClient(MONGO_URI)
    db = mongo[MONGO_DB]
    col = db["signals"]

    # Base query
    q = {}
    if state:
        q["state"] = state
    if county:
        q["county"] = county
    if sector:
        q["sector"] = sector

    cursor = col.find(q).sort("timestamp", -1).limit(limit)

    results = []
    for doc in cursor:
        # Fallback values
        score = doc.get("stress_score", 50)
        results.append({
            "id": str(doc.get("_id")),
            "state": doc.get("state"),
            "county": doc.get("county"),
            "sector": doc.get("sector"),
            "commodity": doc.get("commodity"),
            "headline": doc.get("headline"),
            "stress_score": score,
            "who_bleeds": doc.get("who_bleeds", []),
            "who_benefits": doc.get("who_benefits", []),
            "provenance": doc.get("provenance", []),
            "timestamp": doc.get("timestamp", datetime.utcnow().isoformat())
        })

    mongo.close()
    return {
        "count": len(results),
        "results": results
    }

