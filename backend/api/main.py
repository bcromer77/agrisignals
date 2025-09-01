from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from backend.api.triggers_api import router as triggers_router
from pymongo import MongoClient, ASCENDING, DESCENDING
from pydantic import BaseModel, Field
from datetime import datetime
import os, asyncio, json

# -------------------------
# Setup
# -------------------------

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "agrisignals_db")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Ensure indexes (run once on startup)
db["signals"].create_index([("ingestion_date", DESCENDING)])
db["signals"].create_index("state")
db["aggregates"].create_index("key")
db["alerts"].create_index([("timestamp", DESCENDING)])

app = FastAPI(title="Agrisignals API")
app.include_router(triggers_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Models
# -------------------------

class SignalQuery(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    skip: int = Field(default=0, ge=0)

# -------------------------
# Endpoints
# -------------------------

@app.get("/healthz")
def health():
    """Healthcheck endpoint for Railway/Render"""
    try:
        db.command("ping")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.get("/signals")
def get_signals(q: SignalQuery = Depends()):
    """Paginated list of signals"""
    try:
        docs = list(
            db["signals"]
            .find({}, {"_id": 0})
            .sort("ingestion_date", -1)
            .skip(q.skip)
            .limit(q.limit)
        )
        return {"count": len(docs), "results": docs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/signals/latest")
def get_latest_signal():
    """Get most recent single signal"""
    try:
        doc = db["signals"].find_one({}, {"_id": 0}, sort=[("ingestion_date", -1)])
        return {"latest": doc}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/stats/summary")
def stats_summary():
    """Signals count per state"""
    try:
        pipeline = [
            {"$group": {"_id": "$state", "signals": {"$sum": 1}}},
            {"$project": {"state": "$_id", "signals": 1, "_id": 0}},
        ]
        docs = list(db["signals"].aggregate(pipeline))
        return {"states": docs, "total_signals": sum(d["signals"] for d in docs)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/stats/composite")
def composite_stats():
    """Composite labor+water risk per state from aggregates collection"""
    try:
        docs = list(db["aggregates"].find({}, {"_id": 0}))
        return {"count": len(docs), "results": docs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/sse/alerts")
async def alerts_sse():
    """Server-Sent Events stream of new alerts"""
    async def event_generator():
        last_ts = None
        while True:
            query = {"timestamp": {"$gt": last_ts}} if last_ts else {}
            alert = db["alerts"].find_one(query, {"_id": 0}, sort=[("timestamp", -1)])
            if alert:
                last_ts = alert["timestamp"]
                yield f"data: {json.dumps(alert)}\n\n"
            await asyncio.sleep(3)  # adjust polling cadence

    return StreamingResponse(event_generator(), media_type="text/event-stream")
