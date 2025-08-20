import os
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB",  "agrisignals")

_client = MongoClient(MONGODB_URI)
db = _client[MONGODB_DB]
