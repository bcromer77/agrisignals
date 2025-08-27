import os
from pymongo import MongoClient
from openai import OpenAI

class RetailAgent:
    def __init__(self):
        self.name = "RetailAgent"
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        mongo_uri = os.getenv("MONGO_URI")
        mongo_db = os.getenv("MONGO_DB", "agrisignals")
        self.db = MongoClient(mongo_uri)[mongo_db]

    def run(self):
        print("🛒 RetailAgent is running...")

        # Example signal (replace later with Firecrawl/news ingestion)
        news = "McDonald’s is slashing combo meal prices by 15% to regain affordability perception."

        # Store in Mongo
        doc = {
            "retailer": "McDonalds",
            "signal": "Price cuts",
            "details": news,
        }
        self.db["retail_signals"].insert_one(doc)

        print("✅ Inserted retail signal into Mongo:", news[:60])
        return [doc]

