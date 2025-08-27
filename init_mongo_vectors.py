import os
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

# 1. Load secrets from .env.localdev
load_dotenv(".env.localdev")

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
mongo = MongoClient(MONGO_URI)
db = mongo[MONGO_DB]
signals = db["signals"]

# 2. Create collection with vector search index (3072 dimensions)
def init_collection():
    try:
        db.create_collection("signals")
    except Exception:
        pass  # already exists

    db.command({
        "createIndexes": "signals",
        "indexes": [{
            "key": {"embedding": "vector"},
            "name": "embedding_index",
            "vectorSearchOptions": {
                "numDimensions": 3072,
                "similarity": "cosine"
            }
        }]
    })

# 3. Insert signal with embedding
def insert_signal(headline, commodity, timestamp):
    embedding = client.embeddings.create(
        input=headline,
        model="text-embedding-3-large"
    ).data[0].embedding

    doc = {
        "headline": headline,
        "commodity": commodity,
        "embedding": embedding,
        "timestamp": timestamp
    }
    signals.insert_one(doc)
    print("✅ Signal inserted with embedding.")

# 4. Query similar signals
def search_similar(query_text, limit=5):
    query_vec = client.embeddings.create(
        input=query_text,
        model="text-embedding-3-large"
    ).data[0].embedding

    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_vec,
                "path": "embedding",
                "numCandidates": 100,
                "limit": limit
            }
        }
    ]
    results = list(signals.aggregate(pipeline))
    return results


if __name__ == "__main__":
    init_collection()
    insert_signal(
        "Cattle auction prices +14% in Oklahoma",
        "cattle",
        "2025-08-25T14:00:00Z"
    )
    sims = search_similar("cattle auction spike in Oklahoma")
    for s in sims:
        print(s["headline"], s.get("score"))

