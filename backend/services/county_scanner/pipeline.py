"""
Live multi-state pipeline for Agrisignals, enhanced for shorting agricultural banks.
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

# ---------- Mongo helpers ----------
def _mongo():
    client = MongoClient(MONGODB_URI)
    return client, client[MONGODB_DB]

def _ensure_indexes(db):
    db.sources.create_index([("state", 1), ("topic", 1), ("url", 1)], unique=True)
    db.signals.create_index([("state", 1), ("topic", 1), ("timestamp", -1)])
    db.sources.create_index("embedding")
    db.signals.create_index("embedding")
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

# ---------- Fetch / Crawl ----------
def fetch_text(url: str, timeout: int = 15) -> Tuple[str, Optional[str]]:
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "agrisignals/0.1"})
        r.raise_for_status()
        if "html" in r.headers.get("content-type", "").lower():
            return html_to_text(r.text)[:20000], None
        return r.text[:20000], None
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"

# ---------- LLM prompts ----------
DISCOVERY_PROMPT = """You are an alpha-signal scout for a hedge-fund intelligence system called Agrisignals.
Find obscure but high-signal public sources...
Return ONLY valid JSON array.
"""

SIGNAL_PROMPT = """You are condensing raw snippets into tradable signals...
Return ONLY valid JSON object.
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
        start, end = content.find("["), content.rfind("]")
        if start == -1 or end == -1:
            return []
        return json.loads(content[start:end+1])
    except Exception:
        return []

# ---------- Summarize ----------
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
        start, end = raw.find("{"), raw.rfind("}")
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
        s["embedding"] = embed(f"{s.get('name','')} {s.get('url','')} {s.get('why_signal','')}")
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
        sig["embedding"] = embed(f"{sig.get('headline','')} {sig.get('state','')} {sig.get('topic','')}")
        final.append(sig)
    if final:
        db.signals.insert_many(final)

# ---------- Orchestrators ----------
def run_for_state(state: str, topics: List[str] = ["agri","state_finance","agri_banking"], limit_per_topic: int = 12) -> Dict:
    client, db = _mongo()
    try:
        _ensure_indexes(db)
        ui_summary = {"state": state, "topics": {}, "ran_at": datetime.now(timezone.utc).isoformat()}
        for topic in topics:
            discovered = discover_sources_with_llm(state, topic)
            if not discovered:
                ui_summary["topics"][topic] = {"sources": 0, "signals": 0, "note": "discovery-empty"}
                continue
            discovered = sorted(discovered, key=lambda x: x.get("priority_score",0), reverse=True)[:limit_per_topic]
            upsert_sources(db, state, topic, discovered)
            signals = []
            for s in discovered:
                text, err = fetch_text(s.get("url",""))
                if not err and text:
                    sig = summarize_to_signal(state, topic, text, s.get("url"))
                    if sig:
                        signals.append(sig)
            insert_signals(db, signals)
            ui_summary["topics"][topic] = {"sources": len(discovered), "signals": len(signals)}
        return ui_summary
    finally:
        client.close()

def run_for_states(states: List[str], topics: List[str] = ["agri","state_finance","agri_banking"], limit_per_topic: int = 12) -> List[Dict]:
    return [run_for_state(st, topics, limit_per_topic) for st in states]

def run_for_county(county: str, state: str) -> Dict:
    result = run_for_state(state, ["agri","state_finance","agri_banking"], limit_per_topic=10)
    result["county"] = county
    return result

def get_sources(county: Optional[str], state: str, limit: int = 50) -> List[Dict]:
    client, db = _mongo()
    try:
        cur = db.sources.find({"state": state}).sort([("_id",-1)]).limit(limit)
        return [{k: s.get(k) for k in ["name","url","topic","priority_score","why_signal","state"]} for s in cur]
    finally:
        client.close()

def get_signals(state: Optional[str] = None, limit: int = 50, bank_name: Optional[str] = None) -> List[Dict]:
    client, db = _mongo()
    try:
        query = {"state": state} if state else {}
        if bank_name:
            query["who_bleeds"] = {"$in":[bank_name]}
        cur = db.signals.find(query).sort([("confidence_pct",-1),("timestamp",-1)]).limit(limit)
        return [
            {k: s.get(k) for k in ["headline","state","topic","confidence_pct","who_bleeds","who_succeeds","provenance","strategy","timestamp"]}
            for s in cur
        ]
    finally:
        client.close()

# ---------- CLI quick test ----------
if __name__ == "__main__":
    print(json.dumps(run_for_states(["CA","WY","NE","MT"]), indent=2))

