from fastapi import FastAPI
import backend.db as db  # 👈 import your db module

app = FastAPI(title="Agrisignals API (dev)")

# Run DB initialization once at startup
@app.on_event("startup")
async def startup_event():
    db.init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

