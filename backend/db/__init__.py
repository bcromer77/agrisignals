"""
Database connector for Agrisignals.

- Connects to MongoDB using MONGODB_URI and MONGODB_DB env vars.
- Exposes `db` (database handle) and `client` (Mongo client).
- Provides `init_db()` to ensure indexes and verify connection.
"""

import os
from pymongo import MongoClient

# Load env vars
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "agrisignals")

# Create client + DB reference
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

def init_db():
    """
    Initialize MongoDB connection and ensure indexes exist.
    Called at FastAPI startup.
    """
    try:
        # Verify connection
        client.admin.command("ping")

        # Ensure indexes for performance
        db.signals.create_index([("state", 1), ("topic", 1), ("timestamp", -1)])
        db.sources.create_index([("state", 1), ("topic", 1), ("url", 1)], unique=True)
        db.signals.create_index("embedding")
        db.sources.create_index("embedding")

        print(f"✅ MongoDB connected and indexes ensured: {MONGODB_URI}, db={MONGODB_DB}")
    except Exception as e:
        print(f"❌ MongoDB init failed: {e}")
        raise
