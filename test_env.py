#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

load_dotenv()

print("🔍 Starting environment check...\n")

# --- MongoDB Test ---
try:
    mongo_uri = os.getenv("MONGODB_ATLAS_URI")
    client = MongoClient(mongo_uri)
    client.admin.command("ping")
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

# --- OpenAI Test ---
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY missing from .env")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="Hello world test"
    )
    print("✅ OpenAI API key valid, embedding length:", len(response.data[0].embedding))
except Exception as e:
    print(f"❌ OpenAI API test failed: {e}")

print("\n🔍 Environment check complete")
