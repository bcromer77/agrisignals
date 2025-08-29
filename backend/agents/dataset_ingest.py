from pymongo import MongoClient
import json, datetime

MONGO_URI = "your-mongo-uri"
MONGO_DB = "agrisignals"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

with open("colorado_water.json") as f:
    raw = json.load(f)

doc = {
    "id": raw["id"],
    "name": raw["name"],
    "assetType": raw["assetType"],
    "category": raw.get("category"),
    "attribution": {
        "agency": raw.get("attribution"),
        "url": raw.get("attributionLink")
    },
    "description": raw.get("description"),
    "tags": raw.get("tags", []),
    "license": raw["licenseId"],
    "createdAt": datetime.datetime.fromtimestamp(raw["createdAt"]),
    "updatedAt": datetime.datetime.fromtimestamp(raw["rowsUpdatedAt"]),
    "columns": [
        {
            "name": c["name"],
            "type": c["dataTypeName"],
            "description": c.get("description")
        }
        for c in raw["columns"]
    ],
    "sourceUrl": raw["metadata"]["custom_fields"]["Additional Dataset Documentation"]["Data Dictionary"],
    "attachments": raw["metadata"]["attachments"],
    "metadata": {
        "coverage": raw["metadata"]["custom_fields"]["Dataset Coverage"]["Geographic Coverage"],
        "updateFrequency": raw["metadata"]["custom_fields"]["Data Quality"]["Expected Update Frequency"]
    },
    "ingestionDate": datetime.datetime.utcnow()
}

db.datasets.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
print(f"Ingested dataset {doc['id']}")
