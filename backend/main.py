from fastapi import FastAPI
from backend.routers import scanner, geo, signals
from backend.db import db  # 👈 make sure this exists and exposes `db`

app = FastAPI(title="Agrisignals")

# Attach routers
app.include_router(scanner.router)
app.include_router(geo.router)
app.include_router(signals.router)

# Direct signals endpoint (MongoDB pull)
@app.get("/signals", tags=["signals"])
async def get_signals(limit: int = 20):
    docs = list(
        db["signals"]
        .find({}, {"_id": 0})
        .sort("ingestion_date", -1)
        .limit(limit)
    )
    return {"signals": docs}

