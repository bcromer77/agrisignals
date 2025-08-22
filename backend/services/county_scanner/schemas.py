from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, HttpUrl
from datetime import datetime

ImpactType = Literal["price","closure","procurement","policy","logistics","sentiment","weather","water","labor","regulatory","disease","tariff"]
Commodity  = Literal["coffee","cattle","corn","citrus","crops","water","multi"]

class SourceDoc(BaseModel):
    url: HttpUrl
    title: str
    published_at: Optional[datetime]
    outlet: Optional[str]
    city: Optional[str]
    state: Optional[str]
    county: Optional[str]
    country: Optional[str]
    commodity: Optional[Commodity]
    impact_type: Optional[ImpactType]
    magnitude_pct: Optional[float]
    excerpt: Optional[str]
    raw_text: str

class CountySignal(BaseModel):
    county: str
    state: Optional[str]
    commodity: Commodity
    score: float
    score_breakdown: Dict[str,float]
    sources: List[SourceDoc]
