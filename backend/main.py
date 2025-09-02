from fastapi import FastAPI
from backend.db import init_db, db as mongo_db, MONGODB_DB

app = FastAPI(title="Agrisignals API (dev)")

@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ DB init failed at startup: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dbstatus")
def db_status():
    try:
        stats = mongo_db.command("dbStats")
        return {
            "status": "ok",
            "db": MONGODB_DB,
            "collections": stats.get("collections"),
            "objects": stats.get("objects"),
            "storageSize": stats.get("storageSize"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
