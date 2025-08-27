#!/usr/bin/env python3
"""
🌾 AGRISIGNALS INGESTION PIPELINE
Complete script to ingest JSON source packs into MongoDB Atlas with vector embeddings
SECURE VERSION - Reads credentials from .env file only
"""

import os
import json
import hashlib
import tiktoken
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Core dependencies
from pymongo import MongoClient
from openai import OpenAI
import requests
from time import sleep
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgrisignalsIngestion:
    """Main ingestion pipeline for Agrisignals alpha sources"""
    
    def __init__(self):
        # Load environment variables from .env file ONLY
        self.mongo_uri = os.getenv("MONGODB_ATLAS_URI")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        
        # Validate required environment variables
        if not self.mongo_uri:
            raise ValueError("❌ MONGODB_ATLAS_URI not found in .env file")
        if not self.openai_api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in .env file")
        
        # Log that we're using environment variables (without exposing them)
        logger.info("✅ Environment variables loaded from .env file")
        logger.info(f"   MongoDB URI: {'✅ Found' if self.mongo_uri else '❌ Missing'}")
        logger.info(f"   OpenAI API Key: {'✅ Found' if self.openai_api_key else '❌ Missing'}")
        logger.info(f"   Firecrawl API Key: {'✅ Found' if self.firecrawl_api_key else '⚠️  Optional - Missing'}")
        
        try:
            # Initialize clients
            self.mongo_client = MongoClient(self.mongo_uri)
            self.db = self.mongo_client["agrisignals_db"]
            self.collection = self.db["sources_collection"]
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            
            # Test MongoDB connection
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection successful")
            
            # Tiktoken encoder for chunking
            self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")
            
            logger.info("🚀 Agrisignals Ingestion Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize pipeline: {e}")
            raise
    
    def load_json_sources(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Load all JSON source files and combine them"""
        all_sources = []
        
        for file_path in file_paths:
            try:
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        sources = json.load(f)
                        all_sources.extend(sources)
                        logger.info(f"✅ Loaded {len(sources)} sources from {file_path}")
                else:
                    logger.warning(f"⚠️  File not found: {file_path}")
            except Exception as e:
                logger.error(f"❌ Error loading {file_path}: {e}")
        
        logger.info(f"📊 Total sources loaded: {len(all_sources)}")
        return all_sources
    
    def create_source_id(self, source: Dict[str, Any]) -> str:
        """Generate unique source ID from name + URL"""
        identifier = f"{source.get('source_name', '')}{source.get('url', '')}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def scrape_url_simple(self, url: str) -> str:
        """Simple web scraping (fallback if Firecrawl not available)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic text extraction (you can enhance this)
            content = response.text[:2000]  # First 2000 chars
            return content
            
        except Exception as e:
            logger.warning(f"⚠️  Scraping failed for {url}: {e}")
            return ""
    
    def create_embedding_text(self, source: Dict[str, Any], scraped_content: str = "") -> str:
        """Create rich text for embedding generation"""
        text_parts = [
            f"Source: {source.get('source_name', 'Unknown')}",
            f"State: {source.get('state', '')}",
            f"Region: {source.get('region', '')}",
            f"County: {source.get('county', '')}",
            f"Basin: {source.get('basin', '')}",
            f"Commodity: {source.get('commodity', '')}",
            f"Document Type: {source.get('document_type', '')}",
            f"Priority Score: {source.get('priority_score', 0)}",
            f"Water Signal: {source.get('water_signal', '')}",
            f"Labor Signal: {source.get('labor_signal', '')}",
            f"Financial Link: {source.get('financial_link', '')}",
            f"Extraction Notes: {source.get('extraction_notes', '')}",
        ]
        
        if scraped_content:
            text_parts.append(f"Content Preview: {scraped_content[:500]}")
        
        # Filter out empty values and join
        filtered_parts = [part for part in text_parts if part.split(": ", 1)[1].strip()]
        return " | ".join(filtered_parts)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text.strip()
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return None
    
    def chunk_text(self, text: str, max_tokens: int = 500) -> List[Dict[str, Any]]:
        """Chunk text if it exceeds token limit"""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return [{"chunk_id": 1, "chunk_text": text, "token_count": len(tokens)}]
        
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "chunk_text": chunk_text,
                "token_count": len(chunk_tokens)
            })
        
        return chunks
    
    def process_source(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single source: scrape, embed, format for MongoDB"""
        try:
            source_id = self.create_source_id(source)
            
            # Scrape content (optional - can be disabled for faster testing)
            scraped_content = ""
            if source.get('url') and not source.get('url').startswith('#'):
                scraped_content = self.scrape_url_simple(source['url'])
            
            # Create embedding text
            embedding_text = self.create_embedding_text(source, scraped_content)
            
            # Generate embedding
            embedding = self.get_embedding(embedding_text)
            if not embedding:
                logger.warning(f"⚠️  No embedding generated for {source.get('source_name')}")
            
            # Create document for MongoDB
            document = {
                "source_id": source_id,
                "source_name": source.get('source_name', ''),
                "url": source.get('url', ''),
                "state": source.get('state', ''),
                "region": source.get('region', ''),
                "county": source.get('county', ''),
                "basin": source.get('basin', ''),
                "commodity": source.get('commodity', ''),
                "document_type": source.get('document_type', ''),
                "priority_score": float(source.get('priority_score', 0)),
                "water_signal": source.get('water_signal', ''),
                "labor_signal": source.get('labor_signal', ''),
                "financial_link": source.get('financial_link', ''),
                "litigation_type": source.get('litigation_type', ''),
                "bond_ticker": source.get('bond_ticker', ''),
                "extraction_notes": source.get('extraction_notes', ''),
                "embedding": embedding,
                "embedding_text": embedding_text,
                "scraped_content": scraped_content[:1000] if scraped_content else "",
                "ingestion_date": datetime.utcnow().isoformat(),
                "alpha_confidence": float(source.get('priority_score', 0)) * 0.85,  # Computed field
                "processed_at": datetime.utcnow()
            }
            
            return document
            
        except Exception as e:
            logger.error(f"❌ Error processing source {source.get('source_name', 'unknown')}: {e}")
            return None
    
    def batch_ingest(self, sources: List[Dict[str, Any]], batch_size: int = 10) -> Dict[str, int]:
        """Ingest sources in batches"""
        stats = {"processed": 0, "inserted": 0, "updated": 0, "errors": 0}
        
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(sources)-1)//batch_size + 1}")
            
            for source in batch:
                try:
                    document = self.process_source(source)
                    if document:
                        # Upsert to MongoDB
                        result = self.collection.replace_one(
                            {"source_id": document["source_id"]},
                            document,
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                        
                        stats["processed"] += 1
                    else:
                        stats["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Batch processing error: {e}")
                    stats["errors"] += 1
            
            # Rate limiting
            sleep(1)
        
        return stats
    
    def create_indexes(self):
        """Create MongoDB indexes for performance"""
        try:
            # Scalar indexes
            self.collection.create_index("state")
            self.collection.create_index("priority_score")
            self.collection.create_index("document_type")
            self.collection.create_index("ingestion_date")
            self.collection.create_index([("state", 1), ("commodity", 1)])
            
            logger.info("✅ MongoDB indexes created successfully")
            
            # Vector index instructions
            vector_index_json = {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 3072,
                        "similarity": "cosine"
                    },
                    {"type": "filter", "path": "state"},
                    {"type": "filter", "path": "priority_score"},
                    {"type": "filter", "path": "document_type"}
                ]
            }
            
            logger.info("📋 Vector index definition (create manually in Atlas UI):")
            logger.info(json.dumps(vector_index_json, indent=2))
            
        except Exception as e:
            logger.error(f"❌ Index creation error: {e}")
    
    def run_ingestion(self, json_files: List[str]):
        """Main ingestion workflow"""
        logger.info("🌾 Starting Agrisignals ingestion pipeline...")
        
        # Load sources
        sources = self.load_json_sources(json_files)
        if not sources:
            logger.error("❌ No sources loaded. Exiting.")
            return
        
        # Create indexes
        self.create_indexes()
        
        # Batch ingest
        stats = self.batch_ingest(sources)
        
        # Summary
        logger.info("📊 INGESTION COMPLETE")
        logger.info(f"   Processed: {stats['processed']}")
        logger.info(f"   Inserted: {stats['inserted']}")
        logger.info(f"   Updated: {stats['updated']}")
        logger.info(f"   Errors: {stats['errors']}")
        
        # Test query
        self.test_vector_search()
    
    def test_vector_search(self):
        """Test vector search functionality"""
        try:
            # Simple aggregation test
            total_docs = self.collection.count_documents({})
            high_priority = self.collection.count_documents({"priority_score": {"$gte": 8.0}})
            
            logger.info(f"📈 Database stats:")
            logger.info(f"   Total documents: {total_docs}")
            logger.info(f"   High priority (≥8.0): {high_priority}")
            
            # Sample documents
            sample = list(self.collection.find({}).limit(3))
            for doc in sample:
                logger.info(f"   Sample: {doc.get('source_name')} (Priority: {doc.get('priority_score')})")
                
        except Exception as e:
            logger.error(f"❌ Test query error: {e}")

def main():
    """Main execution function"""
    try:
        # Initialize pipeline
        pipeline = AgrisignalsIngestion()
        
        # JSON files to ingest (update these paths to match your files)
        json_files = [
            "texas_alpha_sources.json",
            "multi_state_alpha_sources.json", 
            "next_state_alpha_sources.json",
            "swing_state_alpha_sources.json"
        ]
        
        # Run ingestion
        pipeline.run_ingestion(json_files)
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        logger.error("💡 Make sure your .env file contains valid credentials")

if __name__ == "__main__":
    main()
