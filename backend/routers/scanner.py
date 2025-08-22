from fastapi import APIRouter
from backend.services.county_scanner.pipeline import run_for_county, get_signals, get_sources
router = APIRouter(prefix="/scanner", tags=["scanner"])
@router.get("/run")
def run(county: str, state: str): return run_for_county(county, state)
@router.get("/signals")
def signals(county: str, state: str, commodity: str | None = None, limit: int = 100):
    return get_signals(county, state, commodity, limit)
@router.get("/sources")
def sources(county: str, state: str, limit: int = 50):
    return get_sources(county, state, limit)
