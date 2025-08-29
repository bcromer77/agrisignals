# backend/agents/water_ingest.py
import pandas as pd
from pymongo import MongoClient, ReplaceOne
import datetime as dt
import os
import numpy as np
import requests
import schedule
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mongo connection
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB") or os.getenv("MONGODB_DB", "agrisignals_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Data directory
DATA_DIR = Path("data/water")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------
# Normalization helper
# -----------------------
def normalize_for_mongo(doc):
    """Convert numpy + date types so Mongo can store them"""
    for k, v in doc.items():
        if isinstance(v, (np.float32, np.float64, np.int32, np.int64)):
            doc[k] = float(v)
        elif isinstance(v, dt.date) and not isinstance(v, dt.datetime):
            doc[k] = dt.datetime.combine(v, dt.datetime.min.time())
        elif isinstance(v, dict):
            doc[k] = normalize_for_mongo(v)
        elif isinstance(v, list):
            doc[k] = [normalize_for_mongo(i) if isinstance(i, dict) else
                      float(i) if isinstance(i, (np.float32, np.float64, np.int32, np.int64)) else
                      dt.datetime.combine(i, dt.datetime.min.time()) if isinstance(i, dt.date) and not isinstance(i, dt.datetime)
                      else i for i in v]
    return doc

# -----------------------
# Fetch + clean functions
# -----------------------
def fetch_fresh_colorado_data():
    """Fetch the latest Colorado water data from DWR API"""
    try:
        api_url = "https://dwr.state.co.us/Rest/GET/api/v2/surfacewater/surfacewaterts/telemetrystations/?format=csv&dateFormat=dateOnly"
        logger.info("Fetching fresh Colorado water data from DWR API...")
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()

        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"colorado_water_conditions_{timestamp}.csv"
        filepath = DATA_DIR / filename
        with open(filepath, 'w') as f:
            f.write(response.text)

        logger.info(f"✅ Fresh data saved to {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"❌ Failed to fetch fresh data: {e}")
        existing_files = list(DATA_DIR.glob("*.csv"))
        if existing_files:
            latest_file = max(existing_files, key=os.path.getctime)
            logger.info(f"Using existing file: {latest_file}")
            return str(latest_file)
        raise

def clean_water_data(df):
    """Clean and normalize water conditions data"""
    logger.info("🔍 Applying forensic data cleaning...")
    df['Date Time'] = pd.to_datetime(df['Date Time'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Stage'] = pd.to_numeric(df['Stage'], errors='coerce')

    unreliable_flags = ['Eqp', 'Ssn', 'Bkw', 'Dis']
    reliable_data = df[~df['Flag'].isin(unreliable_flags)]
    reliable_data = reliable_data[~reliable_data['Amount'].isin([-999, -888])]
    active_data = reliable_data[reliable_data['Station Status'] == 'Active']

    def parse_location(loc_str):
        if pd.isna(loc_str) or not loc_str.strip():
            return None, None
        try:
            coords = loc_str.strip("()").split(", ")
            return float(coords[0]), float(coords[1])
        except:
            return None, None

    active_data = active_data.copy()
    active_data[['Latitude', 'Longitude']] = active_data['Location'].apply(
        lambda x: pd.Series(parse_location(x))
    )
    return active_data

# -----------------------
# Risk indicator functions (truncated for brevity but keep all your logic)
# -----------------------
def calculate_burry_risk_indicators(df):
    # ... keep your existing implementation here ...
    return {}

def create_burry_dashboard_data(df, risk_indicators):
    # ... keep your existing implementation here ...
    return {}

# -----------------------
# Main ingestion
# -----------------------
def ingest_water_conditions(csv_path=None):
    try:
        if csv_path is None:
            csv_path = fetch_fresh_colorado_data()

        logger.info(f"🔍 Loading water conditions from {csv_path}")
        df = pd.read_csv(csv_path)
        df_clean = clean_water_data(df)

        logger.info(f"✅ Cleaned {len(df_clean)} records from {len(df)} total")
        risk_indicators = calculate_burry_risk_indicators(df_clean)
        dashboard_data = create_burry_dashboard_data(df_clean, risk_indicators)

        # Convert for Mongo
        risk_doc = normalize_for_mongo({
            **risk_indicators,
            "analysis_date": dt.date.today().isoformat(),
            "ingestion_timestamp": dt.datetime.utcnow()
        })
        dashboard_data = normalize_for_mongo(dashboard_data)

        db.water_risk_analysis.update_one(
            {"analysis_date": risk_doc["analysis_date"]},
            {"$set": risk_doc},
            upsert=True
        )
        db.water_dashboard_data.update_one(
            {"date": dt.date.today().isoformat()},
            {"$set": dashboard_data},
            upsert=True
        )

        logger.info("✅ Updated risk + dashboard collections")
        return dashboard_data
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise

# -----------------------
# Scheduling
# -----------------------
def schedule_daily_ingestion():
    schedule.every().day.at("06:00").do(ingest_water_conditions)
    logger.info("📅 Scheduled daily water ingestion at 6:00 AM")
    while True:
        schedule.run_pending()
        time.sleep(3600)

if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--schedule":
        logger.info("🕐 Starting scheduled mode...")
        schedule_daily_ingestion()
    else:
        try:
            result = ingest_water_conditions()
            logger.info("✅ Water ingestion completed successfully")
        except Exception as e:
            logger.error(f"❌ Water ingestion failed: {e}")

