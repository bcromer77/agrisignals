"""
Orchestrator for Agrisignals
Runs all GPT-style agents (council, auction, infra, retail, litigation, etc.)
Saves results into MongoDB + Pinecone
Notifies Slack + WhatsApp when high-impact signals detected
"""

import os, sys, traceback, logging
from datetime import datetime

# --- Storage ---
from backend.services.county_scanner.storage import save_to_mongo, save_to_pinecone
from backend.services.county_scanner.schemas import SourceDoc, CountySignal

# --- Agents ---
from backend.agents.auction_agent import AuctionAgent
from backend.agents.council_agent import CouncilAgent
from backend.agents.infra_agent import InfraAgent
from backend.agents.drought_agent import DroughtAgent
from backend.agents.flight_agent import FlightAgent
from backend.agents.hotel_agent import HotelAgent
from backend.agents.litigation_agent import LitigationAgent
from backend.agents.retail_agent import RetailAgent

# --- Notifiers ---
from backend.services.county_scanner.notifiers import notify_slack, notify_whatsapp

# --- Logging setup ---
logging.basicConfig(
    filename="logs/orchestrator.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_agent(agent):
    """Run one agent safely, return docs"""
    try:
        docs = agent.run()
        if not docs:
            logging.warning(f"{agent.name} found nothing")
            return []
        logging.info(f"{agent.name} collected {len(docs)} docs")
        return docs
    except Exception as e:
        logging.error(f"{agent.name} failed: {e}")
        traceback.print_exc()
        return []

def ingest_docs(agent_name, docs):
    """Save docs to storage + check for alerts"""
    if not docs: return

    # Save raw data
    save_to_mongo(docs)
    save_to_pinecone(docs)

    # Simple scoring → trigger alerts if strong signal
    for d in docs:
        score = d.get("score", 0.0)
        if score >= 0.8:  # configurable threshold
            msg = f"🚨 High-impact signal from {agent_name}\nTitle: {d.get('title')}\nURL: {d.get('url')}\nScore: {score:.2f}"
            notify_slack(msg)
            notify_whatsapp(msg)
            logging.info(f"ALERT sent: {msg}")

def run_all_agents():
    """Main orchestrator loop"""
    agents = [
        AuctionAgent(), CouncilAgent(), InfraAgent(),
        DroughtAgent(), FlightAgent(), HotelAgent(),
        LitigationAgent(), RetailAgent()
    ]

    for agent in agents:
        logging.info(f"▶️ Running {agent.name}")
        docs = run_agent(agent)
        ingest_docs(agent.name, docs)

if __name__ == "__main__":
    print("🚀 Orchestrator starting at", datetime.utcnow())
    run_all_agents()
    print("✅ Run complete")

