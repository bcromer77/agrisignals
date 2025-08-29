# backend/services/orchestrator.py

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
        logging.error(f"Agent {agent} failed: {e}\n{traceback.format_exc()}")
        return []


def ingest_docs(agent_name: str, docs: list[dict]):
    """Save docs into MongoDB + Pinecone, notify if priority high."""
    try:
        for doc in docs:
            save_to_mongo(doc)
            save_to_pinecone(doc)

            # Notify if priority > 9.0 (contrarian alpha signal)
            if hasattr(doc, "priority_score") and doc.priority_score >= 9.0:
                msg = f"🚨 {agent_name} found HIGH priority signal: {doc.extraction_notes}"
                notify_slack(msg)
                notify_whatsapp(msg)

        logging.info(f"Ingested {len(docs)} docs from {agent_name}")
    except Exception as e:
        logging.error(f"Ingestion failed for {agent_name}: {e}\n{traceback.format_exc()}")


def run_all_agents():
    """Run all agents and persist results."""
    results = {}

    # instantiate each agent
    agents = [
        AuctionAgent(),
        CouncilAgent(),
        InfraAgent(),
        DroughtAgent(),
        FlightAgent(),
        HotelAgent(),
        LitigationAgent(),
        RetailAgent(),
    ]

    for agent in agents:
        try:
            docs = run_agent(agent)
            if docs:
                ingest_docs(agent.name, docs)
                results[agent.name] = len(docs)
        except Exception as e:
            logging.error(f"Agent {agent} crashed: {e}\n{traceback.format_exc()}")

    logging.info(f"All agents finished. Summary: {results}")
    return results

