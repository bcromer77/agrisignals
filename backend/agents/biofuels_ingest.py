# backend/agents/biofuels_ingest.py
import os, datetime
from pymongo import MongoClient
from PyPDF2 import PdfReader

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "agrisignals")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def parse_biofuels_pdf(pdf_path):
    """Extracts text and parses signals from a USDA Biofuels PDF"""
    reader = PdfReader(pdf_path)
    text = " ".join([page.extract_text() or "" for page in reader.pages])

    # Very naive parsing — just flagging key commodities
    signals = []
    for keyword in ["ethanol", "biodiesel", "corn", "soybean oil", "imports", "exports"]:
        if keyword in text.lower():
            signals.append({
                "title": f"Biofuels mention: {keyword}",
                "raw_text": f"{keyword} context found in USDA report.",
                "commodity": keyword,
                "source_file": os.path.basename(pdf_path),
                "ingestion_date": datetime.datetime.utcnow(),
                "extraction_notes": "Auto-ingested USDA Biofuels Annual",
                "priority_score": 7.5 if keyword in ["imports","exports"] else 6.0
            })
    return signals

def ingest_pdf(pdf_path):
    docs = parse_biofuels_pdf(pdf_path)
    if docs:
        db["signals"].insert_many(docs)
        print(f"✅ Inserted {len(docs)} signals from {pdf_path}")
    else:
        print("⚠️ No signals found.")

if __name__ == "__main__":
    # Run on uploaded USDA report
    ingest_pdf("data/Biofuels Annual_Beijing_China.pdf")

