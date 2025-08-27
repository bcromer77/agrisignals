from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Literal, Optional, List, Dict


class SourceDoc(BaseModel):
    url: Optional[HttpUrl]
    title: str
    published_at: Optional[datetime]
    outlet: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    commodity: Optional[Literal["coffee", "cattle", "corn"]]
    impact_type: Optional[
        Literal["price", "closure", "procurement", "policy", "logistics", "sentiment"]
    ]
    magnitude_pct: Optional[float]
    excerpt: Optional[str]
    raw_text: str  # fallback


class CitySignal(BaseModel):
    city: str
    state: Optional[str]
    commodity: str
    score: float
    score_breakdown: Dict
    sources: List[SourceDoc]

