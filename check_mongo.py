from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

try:
    client.admin.command("ping")
    print("✅ Successfully connected to MongoDB Atlas!")
    db = client[MONGO_DB]
    print("✅ Using database:", db.name)
except Exception as e:
    print("❌ Connection failed:", e)

