from fastapi import APIRouter
from datetime import datetime, timezone
from backend.trading.trigger_engine import run_triggers

router = APIRouter(prefix="/triggers", tags=["triggers"])

@router.get("/")
async def get_triggers():
    results = run_triggers()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "results": results,
    }

