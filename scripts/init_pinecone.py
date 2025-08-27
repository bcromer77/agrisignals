import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv   # <-- add this

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise RuntimeError("❌ No PINECONE_API_KEY set")

pc = Pinecone(api_key=api_key)

index_name = os.getenv("PINECONE_INDEX", "agri-signals-vectors")

# Check if index exists
if index_name not in [i["name"] for i in pc.list_indexes()]:
    print(f"🆕 Creating index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=3072,  # matches OpenAI `text-embedding-3-large`
        metric="cosine",
spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"✅ Index already exists: {index_name}")

