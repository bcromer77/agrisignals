from fastapi import FastAPI
from backend.routers import scanner, geo, signals  # ✅ include signals

app = FastAPI(title="Agrisignals")

app.include_router(scanner.router)
app.include_router(geo.router)
app.include_router(signals.router)  # ✅ now live

