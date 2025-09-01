"""
Database connector for Agrisignals.

- Connects to MongoDB using MONGODB_URI and MONGODB_DB env vars.
- Exposes `db` (database handle) and `client` (Mongo client).
- Automatically ensures indexes for performance.
"""

import os
from pymongo import MongoClient

# Load env vars
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "agrisignals")

# Create client + DB reference
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Optional: Ensure indexes exist
def ensure_indexes():
    try:
        db.signals.create_index([("state", 1), ("topic", 1), ("timestamp", -1)])
        db.sources.create_index([("state", 1), ("topic", 1), ("url", 1)], unique=True)
        db.signals.create_index("embedding")
        db.sources.create_index("embedding")
        print("✅ MongoDB indexes ensured")
    except Exception as e:
        print(f"⚠️ Index creation failed: {e}")

# Run index setup on import
ensure_indexes()

