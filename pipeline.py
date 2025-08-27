from datetime import datetime, timezone
from typing import List
from .firecrawl_client import fc_search
from .schemas import SourceDoc, CountySignal
from .queries import county_queries, TOPIC_TO_COMMODITY, IMPACT_HINTS
from .scoring import total_score
from .storage import STORE

from backend.agents.auction_agent import AuctionAgent
from backend.agents.council_agent import CouncilAgent
from backend.agents.infra_agent import InfraAgent
from storage import save_to_mongo, save_to_pinecone


# --- Agent Pipeline ---
def run_pipeline():
    agents = [AuctionAgent(), CouncilAgent(), InfraAgent()]
    for agent in agents:
        docs = agent.run()
        if not docs:
            print(f"⚠️  {agent.name} found nothing this round")
            continue
        save_to_mongo(docs)
        save_to_pinecone(docs)
        print(f"📥 {agent.name} ingested {len(docs)} docs")


# --- County Scanner Helpers ---
def _parse_item(item: dict, county: str, state: str, commodity: str) -> dict:
    url = item.get("url") or item.get("link")
    title = item.get("title") or (url or "")
    raw = item.get("markdown") or item.get("content") or ""
    published_at = item.get("publishedAt")
    if published_at:
        try:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except Exception:
            published_at = None
    excerpt = (raw[:500] + "...") if raw else None
    return SourceDoc(
        url=url,
        title=title,
        published_at=published_at,
        outlet=None,
        city=None,
        state=state,
        county=county,
        country="USA",
        commodity=commodity,
        impact_type=None,
        magnitude_pct=None,
        excerpt=excerpt,
        raw_text=raw or title,
    ).dict()


def _days_old(dt):
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).days


def _build_signal(county: str, state: str, topic: str, docs: List[dict]) -> CountySignal:
    commodity = TOPIC_TO_COMMODITY[topic]
    hints = IMPACT_HINTS[topic]
    scored = []
    for d in docs:
        s, br = total_score(
            _days_old(d.get("published_at")),
            d["url"],
            county,
            (d.get("raw_text") or "") + (d.get("title") or ""),
            hints,
        )
        scored.append((s, br, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_docs = [d for _, _, d in scored[:10]]
    overall = (
        sum(s for s, _, _ in scored[:5]) / max(1, min(5, len(scored)))
        if scored else 0.0
    )
    br = scored[0][1] if scored else {"recency": 0, "authority": 0, "county_match": 0, "impact": 0}
    return CountySignal(
        county=county,
        state=state,
        commodity=commodity,
        score=overall,
        score_breakdown=br,
        sources=top_docs,
    )


# --- County Scanner Pipeline ---
def run_for_county(county: str, state: str):
    qsets = county_queries(county, state)
    all_signals = []
    for topic, queries in qsets.items():
        docs = []
        for q in queries:
            try:
                res = fc_search(q, limit=6, formats=["markdown"]).get("data", [])
            except Exception as e:
                print("Search error:", q, e)
                continue

            for it in res:
                try:
                    d = _parse_item(it, county, state, TOPIC_TO_COMMODITY[topic])
                    if d.get("url"):
                        docs.append(d)
                except Exception as e:
                    print("Parse error", e)

        if not docs:
            continue

        STORE.upsert_sources(docs)
        sig = _build_signal(county, state, topic, docs)
        STORE.upsert_signal(sig.dict())
        all_signals.append(sig.dict())

    return all_signals


# --- Convenience getters ---
def get_signals(county: str, state: str, commodity: str | None = None, limit: int = 100):
    return STORE.get_signals(county, state, commodity, limit)


def get_sources(county: str, state: str, limit: int = 50):
    return STORE.get_sources(county, state, limit)


# --- Main entry point ---
if __name__ == "__main__":
    run_pipeline()

from .notifiers import alert_all

def _build_signal(county: str, state: str, topic: str, docs: List[dict]) -> CountySignal:
    ...
    sig = CountySignal(
        county=county,
        state=state,
        commodity=commodity,
        score=overall,
        score_breakdown=br,
        sources=top_docs,
    )

    # 🚨 Alert threshold
    if overall > 0.6:  
        headline = top_docs[0]["title"] if top_docs else "New signal detected"
        alert_all(f"🚨 {county}, {state}: {topic} signal {overall:.2f}\n{headline}\n{top_docs[0]['url']}")

    return sig

