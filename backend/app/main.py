from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from datetime import datetime
from typing import Dict, Any, List, Optional
import json, os

from app.db.mongo import db

app = FastAPI(title="Agrisignals API", version="0.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

# ---------- markets fixture loader ----------
def _load_markets_fixture() -> List[Dict[str, Any]]:
    # backend/app/main.py -> up one to backend/, then ".." -> repo root -> fixtures/markets.json
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "fixtures", "markets.json")
    path = os.path.abspath(path)
    with open(path, "r") as f:
        raw = json.load(f)
    docs: List[Dict[str, Any]] = []
    for category, states in raw.items():
        for state, auctions in states.items():
            for name in auctions:
                docs.append({"category": category, "state": state, "market": name})
    return docs

@app.post("/api/dev/load_markets")
def dev_load_markets():
    try:
        docs = _load_markets_fixture()
        for d in docs:
            db.markets.update_one(
                {"state": d["state"], "market": d["market"]},
                {"$set": d}, upsert=True
            )
        return {"inserted_or_updated": len(docs)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})

# ---------- data endpoints ----------
@app.get("/api/markets")
def api_markets(state: Optional[str] = None, category: Optional[str] = None, limit: int = 200):
    try:
        q: Dict[str, Any] = {}
        if state: q["state"] = state
        if category: q["category"] = category
        cur = (db.markets.find(q, {"_id":0, "category":1, "state":1, "market":1})
               .sort([("state",1),("market",1)]).limit(int(limit)))
        data = list(cur)
        return {"count": len(data), "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})

@app.get("/api/auctions/recent")
def auctions_recent(market: Optional[str] = Query(None), state: Optional[str] = Query(None), limit: int = 10):
    try:
        q: Dict[str, Any] = {}
        if market: q["market"] = market
        if state: q["state"] = state
        cur = (db.auctions.find(q, {"_id":0,"market":1,"state":1,"day":1,"heads":1,"avg_cwt":1,
                                    "under_775":1,"over_775":1,"comment":1,"source":1})
               .sort("day",-1).limit(int(limit)))
        rows: List[Dict[str, Any]] = []
        for d in cur:
            d["day"] = str(d.get("day")) if d.get("day") is not None else None
            rows.append(d)
        return {"count": len(rows), "data": rows}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})

@app.get("/api/futures/recent")
def futures_recent(contract_prefix: Optional[str] = None, limit: int = 10):
    try:
        q: Dict[str, Any] = {}
        if contract_prefix:
            q["contract"] = {"$regex": f"^{contract_prefix}", "$options": "i"}
        cur = (db.futures.find(q, {"_id":0,"contract":1,"price":1,"change":1,"timestamp":1,"source":1})
               .sort("timestamp",-1).limit(int(limit)))
        data = list(cur)
        return {"count": len(data), "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})

@app.get("/api/signals/recent")
def signals_recent(limit: int = 20, commodity: Optional[str] = None):
    try:
        q: Dict[str, Any] = {}
        if commodity: q["commodity"] = commodity
        cur = (db.signals.find(q, {"_id":0,"timestamp":1,"commodity":1,"severity":1,"message":1,
                                   "tags":1,"score":1,"components":1})
               .sort("timestamp",-1).limit(int(limit)))
        data = list(cur)
        return {"count": len(data), "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})

# ---------- tiny dashboard ----------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    return FileResponse(html_path)
