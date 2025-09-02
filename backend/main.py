from fastapi import FastAPI
import backend.db as db

app = FastAPI(title="Agrisignals API (dev)")

# Run DB init at startup
@app.on_event("startup")
def startup_event():
    db.init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dbstatus")
def db_status():
    try:
        stats = db.db.command("dbStats")
        return {
            "status": "ok",
            "db": db.MONGODB_DB,
            "collections": stats.get("collections"),
            "objects": stats.get("objects"),
            "storageSize": stats.get("storageSize"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 🚀 Latest signals for hedge funds
@app.get("/signals/recent")
def recent_signals(limit: int = 10):
    try:
        docs = list(
            db.db["signals"]
            .find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return {"count": len(docs), "signals": docs}
    except Exception as e:
        return {"status": "error", "error": str(e)}

