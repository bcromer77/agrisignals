"""
Live multi-state pipeline for Agrisignals, enhanced for shorting agricultural banks.

What it does:
- Discovers high-signal sources per state & topic (agri, state_finance, agri_banking) via LLM
- Crawls pages (Firecrawl if available; otherwise httpx fetch with validation)
- Summarizes into signals with who_bleeds/who_succeeds/confidence_pct/strategy
- Embeds and stores sources+signals in MongoDB for vector search
- Provides run_for_county(), get_sources(), and get_signals() for FastAPI router
- Enhanced to target ag banks (e.g., HTLF) under tariff stress (NPLs, bankruptcies)

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
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from openai import OpenAI
import httpx

# ---------- Optional Firecrawl ----------
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
        FC = None  # Non-fatal

# Top agri states (expanded for ag banking focus)
ALL_AGRI_STATES = [
    "CA", "WY", "NE", "MT", "IA", "TX", "MN", "IL", "KS", "WI", "NC", "IN", "MO", "SD", "ND",
    "WA", "ID", "CO", "OR", "MI", "GA", "FL", "AR", "OK", "MS", "AL", "AZ", "NM", "PA", "NY",
    "OH", "TN", "KY", "SC", "LA", "VA"
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
    # New: Index for bank-specific filtering
    db.signals.create_index([("who_bleeds", 1), ("state", 1)])

# ---------- Embedding ----------
def embed(text: str) -> List[float]:
    if not text:
        return []
    resp = OPENAI.embeddings.create(model=EMBEDDING_MODEL, input=text[:6000])
    return resp.data[0].embedding

# ---------- Light HTML to text ----------
_TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

def html_to_text(html: str) -> str:
    txt = _TAG_RE.sub(" ", html)
    txt = WS_RE.sub(" ", txt)
    return txt.strip()

# ---------- Fetch / Crawl with Validation ----------
def fetch_text(url: str, timeout: int = 15) -> Tuple[str, Optional[str]]:
    """
    Returns (text, error). Uses Firecrawl if available, else httpx with status validation.
    New: Validates URLs against financial/ag domains (SEC EDGAR, MSRB EMMA, etc.).
    """
    # New: Validate URL relevance for financial/ag content
    valid_domains = [
        "sec.gov", "emma.msrb.org", "usda.gov", "moody's.com", "spglobal.com", "fitchratings.com",
        "nasbo.org", "state.*.gov", "*.edu", "*.org"  # State govs, NGOs, etc.
    ]
    if not any(re.match(domain.replace("*", ".*"), url.lower()) for domain in valid_domains):
        return "", "Invalid domain for financial/ag signals"

    try:
        # New: Check HTTP status first
        r = httpx.head(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "agrisignals/0.1"})
        if r.status_code != 200:
            return "", f"HTTP Error: {r.status_code}"

        if FC:
            try:
                if hasattr(FC, "crawl_url"):
                    data = FC.crawl_url(url)
                    content = data.get("markdown") or data.get("html") or json.dumps(data)[:10000]
                    return content, None
                if hasattr(FC, "scrape_url"):
                    data = FC.scrape_url(url)
                    content = data.get("markdown") or data.get("html") or json.dumps(data)[:10000]
                    return content, None
            except Exception as e:
                return "", f"Firecrawl Error: {e}"

        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "agrisignals/0.1"})
        r.raise_for_status()
        if "html" in r.headers.get("content-type", "").lower():
            return html_to_text(r.text)[:20000], None
        return r.text[:20000], None
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"

# ---------- LLM prompts ----------
DISCOVERY_PROMPT = """You are an alpha-signal scout for a hedge-fund intelligence system called Agrisignals.
Find obscure but high-signal public sources that reveal stress, shortages, or disruptions BEFORE mainstream markets.
Scope:
- REGION: {region}
- TOPIC: {topic}  (valid topics: 'agri', 'state_finance', 'agri_banking')

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
- For 'agri': Focus on tariffs (25% on Canada/Mexico, 145% on China), export losses ($21B in grains/meat), fertilizer cost spikes, farm bankruptcies (500k+), income declines (30% since 2022).
- For 'state_finance': Include state comptroller/treasurer, ACFRs, NASBO reports, MSRB EMMA issuer pages, Moody's/S&P/Fitch releases, rainy day fund updates, pension reports.
- For 'agri_banking': Target banks with >20% ag loans (e.g., Heartland Financial/HTLF, Glacier Bancorp/GBCI, Farmers & Merchants/FMCB), SEC EDGAR filings, FDIC reports, NPL increases (15-20%), loan loss provisions, regional bankruptcy trends.
- Do NOT invent URLs. Real, checkable links only (e.g., sec.gov, emma.msrb.org, usda.gov).
- JSON ONLY. No commentary.
"""

SIGNAL_PROMPT = """You are condensing raw snippets into tradable signals for fixed income and ag commodities, with a focus on shorting agricultural banks.

STATE={state}, TOPIC={topic}
Snippet (recent page content):
\"\"\"{snippet}\"\"\"
  
Output JSON with fields:
{{
  "headline": "...",
  "state": "{state}",
  "topic": "{topic}",
  "confidence_pct": 0-100,
  "who_bleeds": ["org or group names, e.g., Heartland Financial/HTLF"],
  "who_succeeds": ["org or group names"],
  "provenance": ["short description or URL host only"],
  "strategy": "e.g., short via puts, 20% downside | hold | long"
}}

Rules:
- Headline: Concise, e.g., "HTLF NPLs Spike Amid Tariff-Driven Farm Defaults".
- Confidence_pct: >70 for high-signal (NPLs >1%, farm income drop >20%, bankruptcies >500k), <40 for low signal.
- Who_bleeds: Name specific ag banks (e.g., HTLF, GBCI) if tied to distress (NPLs, loan losses).
- Strategy: Suggest actionable trade (e.g., "short via puts, target 20% downside" for high-confidence distress).
- Provenance: Cite source (e.g., "sec.gov", "local news").
"""

# ---------- Discovery via LLM ----------
def discover_sources_with_llm(state: str, topic: str) -> List[Dict]:
    prompt = DISCOVERY_PROMPT.format(region=state, topic=topic)
    try:
        resp = OPENAI.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Return only JSON. No prose."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()
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
                {"role": "system", "content": "Return only JSON object as specified."},
                {"role": "user", "content": SIGNAL_PROMPT.format(state=state, topic=topic, snippet=text[:8000])}
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(raw[start:end+1])
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
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
        s["embedding"] = embed(f"{s.get('name', '')} {s.get('url', '')} {s.get('why_signal', '')}")
        ops.append(UpdateOne(
            {"state": state, "topic": topic, "url": s.get("url")},
            {"$set": s, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True
        ))
    if ops:
        db.sources.bulk_write(ops, ordered=False)

def insert_signals(db, signals: List[Dict]) -> None:
    final = []
    for sig in signals:
        if not sig:
            continue
        sig["embedding"] = embed(f"{sig.get('headline', '')} {sig.get('state', '')} {sig.get('topic', '')}")
        final.append(sig)
    if final:
        db.signals.insert_many(final)

# ---------- Main orchestrators ----------
def run_for_state(state: str, topics: List[str] = ["agri", "state_finance", "agri_banking"], limit_per_topic: int = 12) -> Dict:
    client, db = _mongo()
    try:
        _ensure_indexes(db)

        ui_summary = {"state": state, "topics": {}, "ran_at": datetime.now(timezone.utc).isoformat()}

        for topic in topics:
            discovered = discover_sources_with_llm(state, topic)
            if not discovered:
                ui_summary["topics"][topic] = {"sources": 0, "signals": 0, "note": "discovery-empty"}
                continue

            discovered = sorted(discovered, key=lambda x: x.get("priority_score", 0), reverse=True)[:limit_per_topic]

            upsert_sources(db, state, topic, discovered)

            signals: List[Dict] = []
            for s in discovered:
                url = s.get("url", "")
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

def run_for_states(states: List[str], topics: List[str] = ["agri", "state_finance", "agri_banking"], limit_per_topic: int = 12) -> List[Dict]:
    out = []
    for st in states:
        out.append(run_for_state(st, topics, limit_per_topic))
    return out

def run_for_county(county: str, state: str) -> Dict:
    result = run_for_state(state, topics=["agri", "state_finance", "agri_banking"], limit_per_topic=10)
    result["county"] = county
    return result

def get_sources(county: Optional[str], state: str, limit: int = 50) -> List[Dict]:
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

def get_signals(state: Optional[str] = None, limit: int = 50, bank_name: Optional[str] = None) -> List[Dict]:
    """
    Enhanced: Filter by bank_name in who_bleeds and prioritize NPL/bankruptcy signals.
    """
    client, db = _mongo()
    try:
        query = {"state": state} if state else {}
        if bank_name:
            query["who_bleeds"] = {"$in": [bank_name]}  # New: Filter by bank name
        cur = db.signals.find(query).sort([
            ("confidence_pct", -1),  # New: Prioritize high-confidence signals
            ("timestamp", -1)
        ]).limit(limit)
        return [
            {
                "headline": s.get("headline"),
                "state": s.get("state"),
                "topic": s.get("topic"),
                "confidence_pct": s.get("confidence_pct"),
                "who_bleeds": s.get("who_bleeds"),
                "who_succeeds": s.get("who_succeeds"),
                "provenance": s.get("provenance"),
                "strategy": s.get("strategy"),
                "timestamp": s.get("timestamp"),
            }
            for s in cur
        ]
    finally:
        client.close()

# ---------- CLI quick test ----------
if __name__ == "__main__":
    states = ["CA", "WY", "NE", "MT"]
    print(json.dumps(run_for_states(states), indent=2))
