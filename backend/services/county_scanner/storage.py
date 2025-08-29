import os
from typing import List, Dict
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")
OPENAI_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def save_to_mongo(doc: Dict):
    """Embed a document and save it into MongoDB Atlas."""
    text = doc.get("raw_text") or doc.get("title") or ""
    if not text:
        print("⚠️ Skipping empty doc")
        return

    # Create embedding
    resp = client.embeddings.create(model=OPENAI_MODEL, input=text)
    doc["embedding"] = resp.data[0].embedding

    # Insert into Mongo
    mongo = MongoClient(MONGO_URI)
    db = mongo[MONGO_DB]
    col = db["signals"]
    col.insert_one(doc)
    mongo.close()

    print(f"✅ Inserted into Mongo: {doc.get('title')}")

