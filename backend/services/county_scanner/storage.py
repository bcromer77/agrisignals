import os
from typing import List, Dict
from pymongo import MongoClient
from openai import OpenAI


# --- Load environment variables ---
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")
OPENAI_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


# --- Save vectors ---
def save_vectors(docs: List[Dict], backend: str = "mongo"):
    """
    Embed documents and save vectors to MongoDB (default).
    Optionally supports Pinecone if backend="pinecone" and API keys are present.
    """

    # 🔑 Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for doc in docs:
        text = doc.get("raw_text") or doc.get("title") or ""
        if not text:
            continue

        # Create embedding
        resp = client.embeddings.create(
            model=OPENAI_MODEL,
            input=text
        )
        vec = resp.data[0].embedding
        doc["embedding"] = vec  # standardize field name

        if backend == "mongo":
            # Connect to Mongo and insert
            mongo = MongoClient(MONGO_URI)
            db = mongo[MONGO_DB]
            col = db["signals"]  # ✅ unified collection for signals
            col.insert_one(doc)
            mongo.close()
            print(f"✅ Inserted into Mongo: {doc.get('title')}")

        elif backend == "pinecone":
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
                index = pc.Index(os.getenv("PINECONE_INDEX", "agri-signals-vectors"))
                index.upsert([
                    {
                        "id": doc.get("_id", os.urandom(8).hex()),
                        "values": vec,
                        "metadata": {k: v for k, v in doc.items() if k != "embedding"}
                    }
                ])
                print(f"✅ Inserted into Pinecone: {doc.get('title')}")
            except ImportError:
                print("⚠️ Pinecone not installed. Skipping Pinecone backend.")

