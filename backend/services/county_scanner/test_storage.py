from backend.services.county_scanner.storage import save_to_mongo

# Dummy test doc
doc = {
    "title": "Test Signal - Water Stress",
    "raw_text": "Nebraska irrigation board issued emergency water allocation cut.",
    "state": "Nebraska",
    "commodity": "corn",
    "priority_score": 9.5,
    "extraction_notes": "Water allocation cuts may affect irrigation and corn yield."
}

if __name__ == "__main__":
    print("🔍 Starting Mongo storage test...")
    try:
        save_to_mongo(doc)
        print("✅ Mongo insert worked.")
    except Exception as e:
        print(f"❌ Mongo insert failed: {e}")

