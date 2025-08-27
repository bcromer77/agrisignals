#!/usr/bin/env python3
"""
🌾 AGRISIGNALS INGESTION PIPELINE
Ingest JSON source packs into MongoDB Atlas with vector embeddings
"""

import os
import json
import hashlib
import tiktoken
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Dependencies
from pymongo import MongoClient
import requests
from time import sleep
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgrisignalsIngestion:
    """Ingestion pipeline"""

    def __init__(self):
        # Load env vars
        self.mongo_uri = os.getenv("MONGODB_ATLAS_URI")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

        if not self.mongo_uri:
            raise ValueError("❌ MONGODB_ATLAS_URI not found in .env")
        if not self.openai_api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in .env")

        logger.info("✅ Env loaded")
        logger.info(f"   MongoDB URI: {'✅' if self.mongo_uri else '❌'}")
        logger.info(f"   OpenAI API Key: {'✅' if self.openai_api_key else '❌'}")
        logger.info(f"   Firecrawl API Key: {'✅' if self.firecrawl_api_key else '⚠️ Missing'}")

        try:
            # Mongo
            self.mongo_client = MongoClient(self.mongo_uri)
            self.db = self.mongo_client["agrisignals_db"]
            self.collection = self.db["sources_collection"]
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connected")

            # OpenAI
            from openai import OpenAI
            self.openai_client = OpenAI()  # will read key from env

            # Tiktoken
            try:
                self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")
            except KeyError:
                self.encoding = tiktoken.get_encoding("cl100k_base")

            logger.info("🚀 Pipeline initialized")
            logger.info(f"   Target DB: {self.db.name}, Collection: {self.collection.name}")

        except Exception as e:
            logger.error(f"❌ Init failed: {e}")
            raise

    def load_json_sources(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """Load sources from JSON files"""
        all_sources = []
        for fp in file_paths:
            try:
                if fp.exists():
                    with open(fp, 'r') as f:
                        sources = json.load(f)
                        all_sources.extend(sources)
                        logger.info(f"✅ Loaded {len(sources)} sources from {fp.name}")
                else:
                    logger.warning(f"⚠️ File not found: {fp}")
            except Exception as e:
                logger.error(f"❌ Error loading {fp}: {e}")
        logger.info(f"📊 Total sources loaded: {len(all_sources)}")
        return all_sources

    def create_source_id(self, source: Dict[str, Any]) -> str:
        identifier = f"{source.get('source_name', '')}{source.get('url', '')}"
        return hashlib.md5(identifier.encode()).hexdigest()

    def scrape_url_simple(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            return r.text[:2000]
        except Exception as e:
            logger.warning(f"⚠️ Scrape failed {url}: {e}")
            return ""

    def create_embedding_text(self, source: Dict[str, Any], scraped: str = "") -> str:
        parts = [
            f"Source: {source.get('source_name','')}",
            f"State: {source.get('state','')}",
            f"Region: {source.get('region','')}",
            f"County: {source.get('county','')}",
            f"Basin: {source.get('basin','')}",
            f"Commodity: {source.get('commodity','')}",
            f"DocType: {source.get('document_type','')}",
            f"Priority: {source.get('priority_score',0)}",
            f"Water: {source.get('water_signal','')}",
            f"Labor: {source.get('labor_signal','')}",
            f"Finance: {source.get('financial_link','')}",
            f"Notes: {source.get('extraction_notes','')}",
        ]
        if scraped:
            parts.append(f"Preview: {scraped[:500]}")
        return " | ".join([p for p in parts if p.split(': ',1)[1]])

    def get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            resp = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text.strip()
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Embedding failed: {e}")
            return None

    def process_source(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sid = self.create_source_id(source)
            scraped = ""
            if source.get('url') and not source['url'].startswith('#'):
                scraped = self.scrape_url_simple(source['url'])
            emb_text = self.create_embedding_text(source, scraped)
            emb = self.get_embedding(emb_text)
            return {
                "source_id": sid,
                "source_name": source.get('source_name',''),
                "url": source.get('url',''),
                "state": source.get('state',''),
                "region": source.get('region',''),
                "county": source.get('county',''),
                "basin": source.get('basin',''),
                "commodity": source.get('commodity',''),
                "document_type": source.get('document_type',''),
                "priority_score": float(source.get('priority_score',0)),
                "water_signal": source.get('water_signal',''),
                "labor_signal": source.get('labor_signal',''),
                "financial_link": source.get('financial_link',''),
                "litigation_type": source.get('litigation_type',''),
                "bond_ticker": source.get('bond_ticker',''),
                "extraction_notes": source.get('extraction_notes',''),
                "embedding": emb,
                "embedding_text": emb_text,
                "scraped_content": scraped[:1000] if scraped else "",
                "ingestion_date": datetime.utcnow().isoformat(),
                "alpha_confidence": float(source.get('priority_score',0)) * 0.85,
                "processed_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"❌ Process error {source.get('source_name','')} : {e}")
            return None

    def batch_ingest(self, sources: List[Dict[str, Any]], batch_size: int = 10):
        stats = {"processed":0,"inserted":0,"updated":0,"errors":0}
        for i in range(0,len(sources),batch_size):
            batch = sources[i:i+batch_size]
            logger.info(f"🔄 Batch {i//batch_size+1}/{(len(sources)-1)//batch_size+1}")
            for s in batch:
                try:
                    doc = self.process_source(s)
                    if doc:
                        result = self.collection.replace_one(
                            {"source_id": doc["source_id"]}, doc, upsert=True
                        )
                        if result.upserted_id: stats["inserted"]+=1
                        else: stats["updated"]+=1
                        stats["processed"]+=1
                    else:
                        stats["errors"]+=1
                except Exception as e:
                    logger.error(f"❌ Batch error: {e}")
                    stats["errors"]+=1
            sleep(1)
        return stats

    def create_indexes(self):
        try:
            self.collection.create_index("state")
            self.collection.create_index("priority_score")
            self.collection.create_index("document_type")
            self.collection.create_index("ingestion_date")
            self.collection.create_index([("state",1),("commodity",1)])
            logger.info("✅ Indexes created")
        except Exception as e:
            logger.error(f"❌ Index error: {e}")

    def run_ingestion(self, json_files: List[Path]):
        logger.info("🌾 Starting ingestion...")
        sources = self.load_json_sources(json_files)
        if not sources:
            logger.error("❌ No sources. Exit.")
            return
        self.create_indexes()
        stats = self.batch_ingest(sources)
        logger.info("📊 Done")
        logger.info(f"   Processed: {stats['processed']}")
        logger.info(f"   Inserted:  {stats['inserted']}")
        logger.info(f"   Updated:   {stats['updated']}")
        logger.info(f"   Errors:    {stats['errors']}")


def main():
    try:
        pipeline = AgrisignalsIngestion()

        # look for sources in repo root
        base_dir = Path(__file__).resolve().parent.parent
        json_files = [
            base_dir / "texas_alpha_sources.json",
            base_dir / "multi_state_alpha_sources (1).json",
            base_dir / "next_state_alpha_sources.json",
            base_dir / "swing_state_alpha_sources.json"
        ]

        pipeline.run_ingestion(json_files)

    except Exception as e:
        logger.error(f"❌ Pipeline failed at startup: {e}")


if __name__ == "__main__":
    main()
