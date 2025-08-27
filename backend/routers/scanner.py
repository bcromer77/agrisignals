# backend/routers/scanner.py
from fastapi import APIRouter
from backend.services.county_scanner.pipeline import run_for_county, get_sources  # remove get_signals

router = APIRouter(prefix="/scanner", tags=["scanner"])

@router.get("/run")
def run(county: str, state: str):
    return run_for_county(county, state)

@router.get("/sources")
def sources(county: str, state: str, limit: int = 50):
    return get_sources(county, state, limit)

