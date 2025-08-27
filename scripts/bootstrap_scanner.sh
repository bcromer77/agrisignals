set -euo pipefail
mkdir -p backend/services/{county_scanner,geo_agent} backend/routers

# 1) schemas.py
cat > backend/services/county_scanner/schemas.py <<'PY'
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
PY

# 2) scoring.py
cat > backend/services/county_scanner/scoring.py <<'PY'
from typing import Optional, Dict

WEIGHTS = {"recency":0.35,"authority":0.25,"impact":0.25,"county_match":0.15}
AUTHORITY_SCORES = {"gov":1.0,"ca.gov":0.95,"usda.gov":0.95,"org":0.7,"com":0.5}

def authority_from_url(url:str)->float:
    return next((v for k,v in AUTHORITY_SCORES.items() if k in (url or "")),0.4)

def recency_score(days_old: Optional[int])->float:
    return 0.6 if days_old is None else max(0.1,min(1.0,1.0-days_old/60))

def county_match_score(target:str,text:str)->float:
    return 1.0 if (target or "").lower() in (text or "").lower() else 0.4

def impact_score(text:str,hints)->float:
    hits=sum(1 for h in hints if h in (text or "").lower()); return min(1.0,0.3+0.15*hits)

def total_score(days_old, url, county, text, hints)->(float,Dict[str,float]):
    b={"recency":recency_score(days_old),"authority":authority_from_url(url),
       "county_match":county_match_score(county,text),"impact":impact_score(text,hints)}
    return sum(WEIGHTS[k]*b[k] for k in WEIGHTS), b
PY

# 3) storage.py
cat > backend/services/county_scanner/storage.py <<'PY'
import os, json, sqlite3
from typing import List, Dict, Optional

class SqlStorage:
    def __init__(self, path:str=None):
        path = path or os.getenv("SQLITE_PATH","agrisignals.db")
        self.conn = sqlite3.connect(path, check_same_thread=False)

    def upsert_sources(self, docs: List[Dict]):
        cur = self.conn.cursor()
        for d in docs:
            cur.execute("""
              INSERT INTO sources(url,title,published_at,outlet,city,state,county,country,commodity,impact_type,magnitude_pct,excerpt,raw_text)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,published_at=excluded.published_at,outlet=excluded.outlet,city=excluded.city,state=excluded.state,county=excluded.county,country=excluded.country,
                commodity=excluded.commodity,impact_type=excluded.impact_type,magnitude_pct=excluded.magnitude_pct,excerpt=excluded.excerpt,raw_text=excluded.raw_text
            """, (
                d.get("url"), d.get("title"),
                d.get("published_at") and d["published_at"].isoformat(),
                d.get("outlet"), d.get("city"), d.get("state"), d.get("county"), d.get("country"),
                d.get("commodity"), d.get("impact_type"), d.get("magnitude_pct"),
                d.get("excerpt"), d.get("raw_text"),
            ))
        self.conn.commit()

    def upsert_signal(self, signal: Dict):
        day=None
        if signal.get("sources"):
            pub=signal["sources"][0].get("published_at")
            if pub: day=pub.date().isoformat()
        self.conn.execute("""
          INSERT INTO county_signals (county,state,commodity,score,score_breakdown,day)
          VALUES (?,?,?,?,?,?)
        """, (signal["county"], signal.get("state"), signal["commodity"], signal["score"], json.dumps(signal["score_breakdown"]), day))
        self.conn.commit()

    def get_signals(self, county:str, state:str, commodity:Optional[str]=None, limit:int=100):
        q="SELECT county,state,commodity,score,score_breakdown,day,created_at FROM county_signals WHERE county=? AND state=?"
        args=[county,state]
        if commodity: q+=" AND commodity=?"; args.append(commodity)
        q+=" ORDER BY created_at DESC LIMIT ?"; args.append(limit)
        rows=self.conn.execute(q,args).fetchall()
        return [ {"county":r[0],"state":r[1],"commodity":r[2],"score":r[3],
                  "score_breakdown":json.loads(r[4] or "{}"),"day":r[5],"created_at":r[6]} for r in rows ]

    def get_sources(self, county:str, state:str, limit:int=50):
        rows=self.conn.execute("""
          SELECT url,title,published_at,outlet,city,state,county,country,commodity,impact_type,magnitude_pct,excerpt
          FROM sources WHERE county=? AND state=? ORDER BY published_at DESC LIMIT ?
        """,(county,state,limit)).fetchall()
        return [ {"url":r[0],"title":r[1],"published_at":r[2],"outlet":r[3],"city":r[4],
                  "state":r[5],"county":r[6],"country":r[7],"commodity":r[8],
                  "impact_type":r[9],"magnitude_pct":r[10],"excerpt":r[11]} for r in rows ]

STORE = SqlStorage()
PY

# 4) queries.py
cat > backend/services/county_scanner/queries.py <<'PY'
from typing import List, Dict
BASE = {
  "water":[
    'site:gov ("{county} County" OR "County of {county}") (water OR drought OR "water restriction" OR groundwater OR SGMA OR GSA OR allocation OR irrigation)',
    'site:usda.gov ("{county}" AND water)'
  ],
  "regulatory":[
    'site:gov ("{county} County" OR "County of {county}") (ordinance OR regulation OR "public notice" OR agenda OR minutes OR RFP OR procurement)'
  ],
  "cattle":[
    'site:usda.gov (cattle AND "{county}")',
    'site:gov (auction OR "sale barn" OR "livestock market") "{county} County"'
  ],
  "citrus":[
    'site:ca.gov (citrus AND (quarantine OR greening OR HLB OR ACP OR pest) AND "{county}")',
    'site:cdfa.ca.gov (citrus AND {county})'
  ],
  "crops":[
    'site:usda.gov ("crop progress" OR NASS) "{county}"',
    'site:gov (harvest OR yields OR planting) "{county} County"'
  ],
  "coffee":[
    'site:hawaii.gov (coffee AND {county})',
    'site:cbp.gov (coffee AND tariff) "{county}"'
  ],
}
TOPIC_TO_COMMODITY={"cattle":"cattle","citrus":"citrus","crops":"crops","coffee":"coffee","water":"water","regulatory":"multi"}
IMPACT_HINTS={"cattle":["price","closure","logistics","disease","tariff"],
              "citrus":["disease","quarantine","policy","procurement"],
              "crops":["weather","yield","policy","planting","harvest"],
              "coffee":["tariff","logistics","policy"],
              "water":["water","restriction","allocation","drought"],
              "regulatory":["regulatory","policy","ordinance","procurement"]}
def county_queries(county:str,state:str)->Dict[str,List[str]]:
    return {t:[p.format(county=county,state=state) for p in pats] for t,pats in BASE.items()}
PY

# 5) pipeline.py
cat > backend/services/county_scanner/pipeline.py <<'PY'
from datetime import datetime, timezone
from typing import List
from .firecrawl_client import fc_search
from .schemas import SourceDoc, CountySignal
from .queries import county_queries, TOPIC_TO_COMMODITY, IMPACT_HINTS
from .scoring import total_score
from .storage import STORE

def _parse_item(item:dict, county:str, state:str, commodity:str)->dict:
    url=item.get("url") or item.get("link")
    title=item.get("title") or (url or "")
    raw=item.get("markdown") or item.get("content") or ""
    published_at=item.get("publishedAt")
    if published_at:
        try: published_at=datetime.fromisoformat(published_at.replace("Z","+00:00"))
        except: published_at=None
    excerpt=(raw[:500]+"...") if raw else None
    return SourceDoc(url=url,title=title,published_at=published_at,outlet=None,
                     city=None,state=state,county=county,country="USA",
                     commodity=commodity,impact_type=None,magnitude_pct=None,
                     excerpt=excerpt,raw_text=raw or title).dict()

def _days_old(dt):
    if not dt: return None
    return (datetime.now(timezone.utc)-dt).days

def _build_signal(county:str,state:str,topic:str,docs:List[dict])->CountySignal:
    commodity=TOPIC_TO_COMMODITY[topic]; hints=IMPACT_HINTS[topic]
    scored=[]
    for d in docs:
        s, br = total_score(_days_old(d.get("published_at")), d["url"], county,
                            (d.get("raw_text") or "")+(d.get("title") or ""), hints)
        scored.append((s,br,d))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_docs=[d for _,_,d in scored[:10]]
    overall=(sum(s for s,_,_ in scored[:5])/max(1,min(5,len(scored)))) if scored else 0.0
    br = scored[0][1] if scored else {"recency":0,"authority":0,"county_match":0,"impact":0}
    return CountySignal(county=county,state=state,commodity=commodity,score=overall,
                        score_breakdown=br,sources=top_docs)

def run_for_county(county:str,state:str):
    qsets = county_queries(county,state)
    all_signals=[]
    for topic,queries in qsets.items():
        docs=[]
        for q in queries:
            try: res = fc_search(q, limit=6, formats=["markdown"]).get("data",[])
            except Exception as e:
                print("Search error:", q, e); continue
            for it in res:
                try:
                    d=_parse_item(it, county, state, TOPIC_TO_COMMODITY[topic])
                    if d.get("url"): docs.append(d)
                except Exception as e: print("Parse error", e)
        if not docs: continue
        STORE.upsert_sources(docs)
        sig=_build_signal(county,state,topic,docs)
        STORE.upsert_signal(sig.dict())
        all_signals.append(sig.dict())
    return all_signals

def get_signals(county:str,state:str,commodity:str|None=None,limit:int=100):
    return STORE.get_signals(county,state,commodity,limit)

def get_sources(county:str,state:str,limit:int=50):
    return STORE.get_sources(county,state,limit)
PY

# 6) FastAPI main + routers
cat > backend/main.py <<'PY'
from fastapi import FastAPI
from backend.routers import scanner, geo
app = FastAPI(title="Agrisignals")
app.include_router(scanner.router)
app.include_router(geo.router)
PY

cat > backend/routers/scanner.py <<'PY'
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
PY

cat > backend/services/geo_agent/agent.py <<'PY'
def suggest_states(): return [{"name": n, "confidence": 0.8} for n in ["California","Texas","Florida","Kansas","Nebraska","Hawaii"]]
def suggest_counties(state:str): return [{"state":state,"name":"Fresno","confidence":0.8}]
def suggest_entities(state:str, county:str): return []
def suggest_sources(state:str, county:str): return []
def approve_entity(e:dict): return None
def approve_source(s:dict): return None
PY

cat > backend/routers/geo.py <<'PY'
from fastapi import APIRouter, Body
from backend.services.geo_agent.agent import suggest_states, suggest_counties, suggest_entities, suggest_sources, approve_entity, approve_source
router = APIRouter(prefix="/geo", tags=["geo"])
@router.get("/suggest_states")      def _s_states():   return suggest_states()
@router.get("/suggest_counties")    def _s_counties(state: str): return suggest_counties(state)
@router.get("/suggest_entities")    def _s_entities(state: str, county: str): return suggest_entities(state, county)
@router.get("/suggest_sources")     def _s_sources(state: str, county: str): return suggest_sources(state, county)
@router.post("/approve_entity")     def _a_entity(payload: dict = Body(...)): approve_entity(payload); return {"ok": True}
@router.post("/approve_source")     def _a_source(payload: dict = Body(...)): approve_source(payload); return {"ok": True}
PY
