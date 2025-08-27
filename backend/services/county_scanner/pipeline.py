"""
Live multi-state pipeline for Agrisignals.

What it does:
- Discovers high-signal sources per state & topic (agri + state_finance) via LLM
- Optionally crawls pages (Firecrawl if available; otherwise httpx fetch)
- Summarizes into "signals" with who_bleeds/who_succeeds/confidence_pct
- Embeds and stores sources+signals in MongoDB for vector search
- Provides run_for_county() and get_sources() for the FastAPI router

Env needed:
- OPENAI_API_KEY
- MONGODB_URI
- MONGODB_DB
- (optional) FIRECRAWL_API_KEY

Models (override if you like):
- LLM_MODEL=gpt-4o-mini
- EMBEDDING_MODEL=text-embedding-3-small
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from openai import OpenAI
import httpx

# ---------- optional Firecrawl ----------
try:
    from firecrawl import Firecrawl
except Exception:
    Firecrawl = None
# ---------------------------------------

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "agrisignals")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

OPENAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Firecrawl client if configured
FC = None
if Firecrawl and os.getenv("FIRECRAWL_API_KEY"):
    try:
        FC = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))
    except Exception:
        FC = None  # non-fatal

# Top agri states we care about (expand as needed)
ALL_AGRI_STATES = [
    "CA","WY","NE","MT","IA","TX","MN","IL","KS","WI","NC","IN","MO","SD","ND",
    "WA","ID","CO","OR","MI","GA","FL","AR","OK","MS","AL","AZ","NM","PA","NY",
    "OH","TN","KY","SC","LA","VA"
]

# ---------- Mongo helpers ----------
def _mongo():
    client = MongoClient(MONGODB_URI)
    return client, client[MONGODB_DB]

def _ensure_indexes(db):
    db.sources.create_index([("state", 1), ("topic", 1), ("url", 1)], unique=True)
    db.signals.create_index([("state", 1), ("topic", 1), ("timestamp", -1)])
    db.sources.create_index("embedding")
    db.signals.create_index("embedding")

# ---------- Embedding ----------
def embed(text: str) -> List[float]:
    if not text:
        return []
    resp = OPENAI.embeddings.create(model=EMBEDDING_MODEL, input=text[:6000])
    return resp.data[0].embedding

# ---------- Very light HTML to text ----------
_TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

def html_to_text(html: str) -> str:
    # super light strip
    txt = _TAG_RE.sub(" ", html)
    txt = WS_RE.sub(" ", txt)
    return txt.strip()

# ---------- Fetch / Crawl ----------
def fetch_text(url: str, timeout: int = 15) -> Tuple[str, Optional[str]]:
    """
    Returns (text, error). Uses Firecrawl if available, else httpx.
    """
    # Try firecrawl (best effort)
    if FC:
        try:
            # Different firecrawl versions expose different methods;
            # try a few common ones defensively.
            if hasattr(FC, "crawl_url"):
                data = FC.crawl_url(url)  # may return dict with 'markdown' or 'html'
                content = data.get("markdown") or data.get("html") or json.dumps(data)[:10000]
                return content, None
            if hasattr(FC, "scrape_url"):
                data = FC.scrape_url(url)
                content = data.get("markdown") or data.get("html") or json.dumps(data)[:10000]
                return content, None
        except Exception as e:
            # fall through to httpx
            pass

    # Plain HTTP fetch fallback
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent":"agrisignals/0.1"})
        r.raise_for_status()
        content_type = r.headers.get("content-type","")
        if "html" in content_type.lower():
            return html_to_text(r.text)[:20000], None
        # if PDF or other, just keep raw bytes truncated
        return r.text[:20000], None
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"

# ---------- LLM prompts ----------
DISCOVERY_PROMPT = """You are an alpha-signal scout for a hedge-fund intelligence system called Agrisignals.
Find obscure but high-signal public sources that reveal stress, shortages, or disruptions BEFORE mainstream markets.
Scope:
- REGION: {region}
- TOPIC: {topic}  (valid topics: 'agri', 'state_finance')

Return ONLY valid JSON array. Each item:
{{
  "name": "...",
  "url": "https://...",
  "type": "auction|news|twitter|council|water_board|muni_filings|finance|ngo|community|paywall",
  "priority_score": 0.0_to_1.0,
  "why_signal": "short reason for traders"
}}

Rules:
- Include at least 12–20 sources per state/topic.
- Prefer local/obscure outlets (auction barns, county boards, water districts, union/ICE watchers, NGO newsletters).
- For 'state_finance': add state comptroller/treasurer, ACFR/Annual Comprehensive Financial Reports, NASBO reports,
  MSRB EMMA issuer pages, ratings-agency press releases (Moody's/S&P/Fitch), rainy day fund updates, pension reports.
- Do NOT invent URLs. Real, checkable links only.
- JSON ONLY. No commentary.
"""

SIGNAL_PROMPT = """You are condensing raw snippets into tradable signals for fixed income and ag commodities.

Given:
STATE={state}, TOPIC={topic}
Snippet (recent page content):
\"\"\"{snippet}\"\"\"

Output JSON with fields:
{{
  "headline": "...",
  "state": "{state}",
  "topic": "{topic}",
  "confidence_pct": 0-100,
  "who_bleeds": ["org or group names"],
  "who_succeeds": ["org or group names"],
  "provenance": ["short description or URL host only"]
}}

Make headline concise. If insufficient signal, set confidence_pct < 40.
"""

# ---------- Discovery via LLM ----------
def discover_sources_with_llm(state: str, topic: str) -> List[Dict]:
    prompt = DISCOVERY_PROMPT.format(region=state, topic=topic)
    try:
        resp = OPENAI.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Return only JSON. No prose."},
                {"role":"user","content": prompt}
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()
        # guard against stray text
        start = content.find("[")
        end = content.rfind("]")
        if start == -1 or end == -1:
            return []
        return json.loads(content[start:end+1])
    except Exception:
        return []

# ---------- Summarize into signals ----------
def summarize_to_signal(state: str, topic: str, text: str, source_url: str) -> Optional[Dict]:
    if not text:
        return None
    try:
        resp = OPENAI.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Return only JSON object as specified."},
                {"role":"user","content": SIGNAL_PROMPT.format(state=state, topic=topic, snippet=text[:8000])}
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(raw[start:end+1])
        data["timestamp"] = datetime.utcnow().isoformat()
        data["source_url"] = source_url
        return data
    except Exception:
        return None

# ---------- Upserts ----------
def upsert_sources(db, state: str, topic: str, sources: List[Dict]) -> None:
    ops = []
    for s in sources:
        s["state"] = state
        s["topic"] = topic
        s["embedding"] = embed(f"{s.get('name','')} {s.get('url','')} {s.get('why_signal','')}")
        ops.append(UpdateOne(
            {"state": state, "topic": topic, "url": s.get("url")},
            {"$set": s, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        ))
    if ops:
        db.sources.bulk_write(ops, ordered=False)

def insert_signals(db, signals: List[Dict]) -> None:
    final = []
    for sig in signals:
        if not sig:
            continue
        sig["embedding"] = embed(f"{sig.get('headline','')} {sig.get('state','')} {sig.get('topic','')}")
        final.append(sig)
    if final:
        db.signals.insert_many(final)

# ---------- Main orchestrators ----------
def run_for_state(state: str, topics: List[str] = ["agri","state_finance"], limit_per_topic: int = 12) -> Dict:
    """
    Discovers sources, crawls a bit, summarizes to signals, stores all in Mongo.
    Returns a small summary payload for UI.
    """
    client, db = _mongo()
    try:
        _ensure_indexes(db)

        ui_summary = {"state": state, "topics": {}, "ran_at": datetime.utcnow().isoformat()}

        for topic in topics:
            discovered = discover_sources_with_llm(state, topic)
            if not discovered:
                ui_summary["topics"][topic] = {"sources": 0, "signals": 0, "note": "discovery-empty"}
                continue

            # Trim to limit
            discovered = sorted(discovered, key=lambda x: x.get("priority_score",0), reverse=True)[:limit_per_topic]

            # upsert sources
            upsert_sources(db, state, topic, discovered)

            # fetch a little and summarize
            signals: List[Dict] = []
            for s in discovered:
                url = s.get("url","")
                text, err = fetch_text(url)
                if err or not text:
                    continue
                sig = summarize_to_signal(state, topic, text, url)
                if sig:
                    signals.append(sig)

            insert_signals(db, signals)
            ui_summary["topics"][topic] = {"sources": len(discovered), "signals": len(signals)}

        return ui_summary
    finally:
        client.close()

def run_for_states(states: List[str], topics: List[str] = ["agri","state_finance"], limit_per_topic: int = 12) -> List[Dict]:
    out = []
    for st in states:
        out.append(run_for_state(st, topics, limit_per_topic))
    return out

def run_for_county(county: str, state: str) -> Dict:
    """
    County shim: run at state level, tag county in the response for UI.
    """
    result = run_for_state(state, topics=["agri","state_finance"], limit_per_topic=10)
    result["county"] = county
    return result

def get_sources(county: Optional[str], state: str, limit: int = 50) -> List[Dict]:
    """
    Return the most recent sources stored for a state (county not used yet).
    """
    client, db = _mongo()
    try:
        cur = db.sources.find({"state": state}).sort([("_id", -1)]).limit(limit)
        return [
            {
                "name": s.get("name"),
                "url": s.get("url"),
                "topic": s.get("topic"),
                "priority_score": s.get("priority_score"),
                "why_signal": s.get("why_signal"),
                "state": s.get("state")
            } for s in cur
        ]
    finally:
        client.close()


# ---------- CLI quick test ----------
if __name__ == "__main__":
    # Example: run multiple states quickly from CLI
    states = ["CA","WY","NE","MT"]
    print(json.dumps(run_for_states(states), indent=2))

