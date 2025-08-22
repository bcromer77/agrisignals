from fastapi import FastAPI
from backend.routers import scanner, geo
app = FastAPI(title="Agrisignals")
app.include_router(scanner.router)
app.include_router(geo.router)
