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

def fetch_fresh_colorado_data():
    """Fetch the latest Colorado water data from Socrata API"""
    try:
        base = "https://data.colorado.gov/resource/4yw9-a5y6.csv"
        # Example: pull latest up to 50k rows
        params = {
            "$limit": 50000
            # You can add filters like:
            # "$where": "date_time >= '2025-08-01T00:00:00.000'"
        }
        logger.info("Fetching fresh Colorado water data from Socrata...")
        r = requests.get(base, params=params, timeout=60, headers={"User-Agent": "agrisignals/1.0"})
        r.raise_for_status()
        
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M")
        fp = DATA_DIR / f"colorado_water_conditions_{timestamp}.csv"
        fp.write_text(r.text)
        
        logger.info(f"✅ Fresh data saved to {fp}")
        return str(fp)
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch fresh data: {e}")
        existing = list(DATA_DIR.glob("*.csv"))
        if existing:
            latest = max(existing, key=os.path.getctime)
            logger.info(f"Using existing file: {latest}")
            return str(latest)
        raise

def clean_water_data(df):
    """Clean and normalize water conditions data - Burry-style forensic filtering"""
    logger.info("🔍 Applying Burry-style forensic data cleaning...")
    
    # Convert date strings to datetime
    df['Date Time'] = pd.to_datetime(df['Date Time'], errors='coerce')
    
    # Handle missing/invalid values
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Stage'] = pd.to_numeric(df['Stage'], errors='coerce')
    
    # BURRY FILTER 1: Remove unreliable data (equipment issues, seasonal closures)
    unreliable_flags = ['Eqp', 'Ssn', 'Bkw', 'Dis']  # Equipment, Seasonal, Backwater, Discontinued
    reliable_data = df[~df['Flag'].isin(unreliable_flags)]
    logger.info(f"Filtered out {len(df) - len(reliable_data)} unreliable stations (flags: {unreliable_flags})")
    
    # BURRY FILTER 2: Remove error codes (-999, -888 indicate no flow/errors)
    reliable_data = reliable_data[~reliable_data['Amount'].isin([-999, -888])]
    
    # BURRY FILTER 3: Focus on active stations only
    active_data = reliable_data[reliable_data['Station Status'] == 'Active']
    logger.info(f"Focusing on {len(active_data)} active stations")
    
    # Extract lat/lon from Location string
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

def calculate_burry_risk_indicators(df):
    """Calculate Michael Burry-style water scarcity risk indicators"""
    logger.info("📊 Calculating Burry-style risk indicators...")
    
    risk_indicators = {}
    
    # 1. RESERVOIR DEPLETION RISK (Short Agriculture/Real Estate signals)
    reservoirs = df[df['Station Type'] == 'Reservoir'].copy()
    if not reservoirs.empty:
        # Critical reservoirs with zero storage
        zero_storage = reservoirs[reservoirs['Amount'] == 0]
        risk_indicators['zero_storage_reservoirs'] = len(zero_storage)
        risk_indicators['zero_storage_names'] = zero_storage['Station Name'].tolist()
        
        # Reservoir storage percentiles
        storage_stats = reservoirs['Amount'].describe()
        risk_indicators['reservoir_storage_median'] = storage_stats['50%']
        risk_indicators['reservoir_storage_mean'] = storage_stats['mean']
        
    # 2. STREAM FLOW CRISIS (Agricultural irrigation risk)
    streams = df[df['Station Type'] == 'Stream'].copy()
    if not streams.empty:
        zero_flow_streams = streams[streams['Amount'] == 0]
        risk_indicators['zero_flow_streams'] = len(zero_flow_streams)
        risk_indicators['zero_flow_percentage'] = (len(zero_flow_streams) / len(streams)) * 100
        
        # Critical agricultural districts (Division 2 = Arkansas River basin)
        div2_streams = streams[streams['DIV'] == 2]
        if not div2_streams.empty:
            div2_zero_flow = div2_streams[div2_streams['Amount'] == 0]
            risk_indicators['arkansas_basin_zero_flow_pct'] = (len(div2_zero_flow) / len(div2_streams)) * 100
    
    # 3. DIVERSION STRESS (Water extraction vs availability)
    diversions = df[df['Station Type'] == 'Diversion'].copy()
    if not diversions.empty:
        high_diversions = diversions[diversions['Amount'] > diversions['Amount'].quantile(0.8)]
        risk_indicators['high_extraction_diversions'] = len(high_diversions)
        risk_indicators['total_diversion_flow'] = diversions['Amount'].sum()
    
    # 4. COUNTY-LEVEL VULNERABILITY (Real estate/municipal risk)
    county_risk = []
    for county in df['County'].dropna().unique():
        county_data = df[df['County'] == county]
        county_streams = county_data[county_data['Station Type'] == 'Stream']
        
        if len(county_streams) > 0:
            zero_flow_pct = (county_streams['Amount'] == 0).sum() / len(county_streams) * 100
            avg_flow = county_streams['Amount'].mean()
            
            # Burry's risk classification
            if zero_flow_pct > 30:
                risk_level = "CRITICAL"  # Short real estate, ag stocks
            elif zero_flow_pct > 15:
                risk_level = "HIGH"      # Caution on regional exposure
            elif zero_flow_pct > 5:
                risk_level = "MEDIUM"    # Monitor closely
            else:
                risk_level = "LOW"       # Potential water tech opportunities
            
            county_risk.append({
                "county": county,
                "zero_flow_percentage": round(zero_flow_pct, 2),
                "avg_stream_flow_cfs": round(avg_flow, 2),
                "total_stations": len(county_data),
                "risk_level": risk_level,
                "investment_signal": get_investment_signal(risk_level, zero_flow_pct)
            })
    
    risk_indicators['county_vulnerabilities'] = sorted(county_risk, key=lambda x: x['zero_flow_percentage'], reverse=True)
    
    # 5. MAJOR RIVER HEALTH (Colorado River basin indicators)
    major_rivers = df[df['Station Name'].str.contains('COLORADO RIVER|ARKANSAS RIVER|SOUTH PLATTE', case=False, na=False)]
    if not major_rivers.empty:
        risk_indicators['major_river_avg_flow'] = major_rivers['Amount'].mean()
        risk_indicators['major_river_stations'] = len(major_rivers)
    
    return risk_indicators

def get_investment_signal(risk_level, zero_flow_pct):
    """Generate Burry-style investment signals based on water risk"""
    if risk_level == "CRITICAL":
        return {
            "short_targets": ["ADM", "CORN", "PLD", "XHB", "Regional Banks"],
            "rationale": f"{zero_flow_pct}% zero flow indicates severe agricultural/real estate stress"
        }
    elif risk_level == "HIGH":
        return {
            "short_targets": ["Agricultural REITs", "Local Municipal Bonds"],
            "long_targets": ["XYL", "AWK"],
            "rationale": f"{zero_flow_pct}% zero flow suggests water infrastructure demand"
        }
    elif risk_level == "LOW":
        return {
            "long_targets": ["PHO", "Water Rights", "Infrastructure"],
            "rationale": "Stable water supply supports infrastructure investments"
        }
    else:
        return {"action": "MONITOR", "rationale": "Mixed signals, await clearer trends"}

def create_burry_dashboard_data(df, risk_indicators):
    """Create dashboard data optimized for Burry-style analysis"""
    
    dashboard_data = {
        "last_updated": dt.datetime.now(dt.timezone.utc),
        "data_freshness": df['Date Time'].max() if not df.empty else None,
        "total_stations_analyzed": len(df),
        
        # Key Burry Metrics
        "water_crisis_score": calculate_crisis_score(risk_indicators),
        "investment_opportunities": extract_investment_opportunities(risk_indicators),
        
        # Geographic Risk Heatmap Data
        "county_risk_map": [
            {
                "county": item["county"],
                "risk_level": item["risk_level"],
                "zero_flow_pct": item["zero_flow_percentage"],
                "investment_signal": item["investment_signal"]
            }
            for item in risk_indicators.get('county_vulnerabilities', [])[:20]  # Top 20 riskiest
        ],
        
        # Time Series for Trend Analysis
        "daily_trends": create_daily_trends(df),
        
        # Critical Alerts (Burry would monitor these closely)
        "critical_alerts": generate_critical_alerts(risk_indicators),
        
        # Sector Impact Analysis
        "sector_impacts": {
            "agriculture": {
                "risk_score": risk_indicators.get('arkansas_basin_zero_flow_pct', 0),
                "affected_counties": [c["county"] for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] in ["CRITICAL", "HIGH"]]
            },
            "real_estate": {
                "risk_score": len([c for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] == "CRITICAL"]),
                "vulnerable_markets": [c["county"] for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] == "CRITICAL"]
            },
            "water_infrastructure": {
                "opportunity_score": risk_indicators.get('high_extraction_diversions', 0),
                "demand_indicators": risk_indicators.get('total_diversion_flow', 0)
            }
        }
    }
    
    return dashboard_data

def calculate_crisis_score(risk_indicators):
    """Calculate overall water crisis score (0-100, higher = more crisis)"""
    score = 0
    
    # Zero flow percentage weight (40% of score)
    zero_flow_pct = risk_indicators.get('zero_flow_percentage', 0)
    score += min(zero_flow_pct * 1.5, 40)
    
    # Reservoir depletion weight (30% of score)
    zero_reservoirs = risk_indicators.get('zero_storage_reservoirs', 0)
    score += min(zero_reservoirs * 5, 30)
    
    # County vulnerability weight (30% of score)
    critical_counties = len([c for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] == "CRITICAL"])
    score += min(critical_counties * 3, 30)
    
    return min(round(score, 1), 100)

def extract_investment_opportunities(risk_indicators):
    """Extract Burry-style investment opportunities"""
    opportunities = {
        "short_positions": [],
        "long_positions": [],
        "derivatives_plays": [],
        "contrarian_bets": []
    }
    
    # High-risk counties suggest shorting regional exposure
    critical_counties = [c for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] == "CRITICAL"]
    if critical_counties:
        opportunities["short_positions"].extend([
            "Agricultural commodities (CORN, ADM)",
            "Regional real estate (PLD, XHB)",
            f"Municipal bonds in {', '.join([c['county'] for c in critical_counties[:3]])}"
        ])
    
    # High diversion activity suggests water tech demand
    if risk_indicators.get('high_extraction_diversions', 0) > 10:
        opportunities["long_positions"].extend([
            "Water technology (XYL, AWK)",
            "Infrastructure ETFs (PHO, PAVE)",
            "Water rights trading opportunities"
        ])
    
    # Major river stress suggests macro plays
    if risk_indicators.get('major_river_avg_flow', 1000) < 100:
        opportunities["derivatives_plays"].extend([
            "Colorado River compact renegotiation plays",
            "Regional bank CDS (agricultural loan exposure)",
            "Commodity volatility options"
        ])
    
    return opportunities

def generate_critical_alerts(risk_indicators):
    """Generate critical alerts for immediate attention"""
    alerts = []
    
    # Zero storage reservoirs
    zero_reservoirs = risk_indicators.get('zero_storage_names', [])
    if zero_reservoirs:
        alerts.append({
            "type": "RESERVOIR_DEPLETION",
            "severity": "CRITICAL",
            "message": f"{len(zero_reservoirs)} reservoirs at zero storage: {', '.join(zero_reservoirs[:3])}{'...' if len(zero_reservoirs) > 3 else ''}",
            "investment_impact": "Short agricultural/real estate exposure in affected regions"
        })
    
    # High zero-flow percentage
    zero_flow_pct = risk_indicators.get('zero_flow_percentage', 0)
    if zero_flow_pct > 20:
        alerts.append({
            "type": "WIDESPREAD_DROUGHT",
            "severity": "HIGH",
            "message": f"{zero_flow_pct:.1f}% of streams showing zero flow",
            "investment_impact": "Consider broad agricultural sector shorts"
        })
    
    # Arkansas basin stress (key agricultural region)
    arkansas_stress = risk_indicators.get('arkansas_basin_zero_flow_pct', 0)
    if arkansas_stress > 25:
        alerts.append({
            "type": "ARKANSAS_BASIN_STRESS",
            "severity": "HIGH",
            "message": f"Arkansas River basin showing {arkansas_stress:.1f}% zero flow",
            "investment_impact": "Target agricultural commodities and regional banks"
        })
    
    return alerts

def create_daily_trends(df):
    """Create daily trend data for dashboard charts"""
    if df.empty:
        return []
    
    # Group by date and calculate key metrics
    daily_data = df.groupby(df['Date Time'].dt.date).agg({
        'Amount': ['mean', 'median', lambda x: (x == 0).sum()],
        'Station Name': 'count'
    }).round(2)
    
    daily_data.columns = ['avg_flow', 'median_flow', 'zero_flow_count', 'total_stations']
    daily_data = daily_data.reset_index()
    daily_data['zero_flow_percentage'] = (daily_data['zero_flow_count'] / daily_data['total_stations'] * 100).round(2)
    
    return daily_data.to_dict('records')

def ingest_water_conditions(csv_path=None):
    """Main ingestion function with Burry-style analysis"""
    try:
        # Fetch fresh data if no path provided
        if csv_path is None:
            csv_path = fetch_fresh_colorado_data()
        
        logger.info(f"🔍 Loading water conditions from {csv_path}")
        
        # Load and clean data
        df = pd.read_csv(csv_path)
        df_clean = clean_water_data(df)
        
        logger.info(f"✅ Cleaned {len(df_clean)} records from {len(df)} total")
        
        # Calculate Burry-style risk indicators
        risk_indicators = calculate_burry_risk_indicators(df_clean)
        
        # Create dashboard data
        dashboard_data = create_burry_dashboard_data(df_clean, risk_indicators)
        
        # Convert to documents for MongoDB
        water_docs = []
        for _, row in df_clean.iterrows():
            doc = {
                "division": int(row['DIV']) if pd.notna(row['DIV']) else None,
                "water_district": int(row['WD']) if pd.notna(row['WD']) else None,
                "county": row['County'],
                "station_name": row['Station Name'],
                "data_source": row['Data Source'],
                "dwr_abbrev": row['DWR Abbrev'],
                "usgs_station_id": row['USGS Station ID'],
                "station_status": row['Station Status'],
                "station_type": row['Station Type'],
                "measurement_date": row['Date Time'],
                "variable": row['Variable'],
                "stage": float(row['Stage']) if pd.notna(row['Stage']) else None,
                "amount": float(row['Amount']) if pd.notna(row['Amount']) else None,
                "units": row['Units'],
                "flag": row['Flag'],
                "more_info_url": row['More Information'],
                "latitude": row['Latitude'],
                "longitude": row['Longitude'],
                "utm_x": float(row['UTM x']) if pd.notna(row['UTM x']) else None,
                "utm_y": float(row['UTM y']) if pd.notna(row['UTM y']) else None,
                "location_accuracy": row['Location Accuracy'],
                "id_key": row['IDKey'],
                "ingestion_date": dt.datetime.now(dt.timezone.utc),
                "source_file": os.path.basename(csv_path)
            }
            water_docs.append(doc)
        
        # Bulk upsert water conditions
        if water_docs:
            operations = []
            for doc in water_docs:
                filter_key = {"id_key": doc["id_key"], "measurement_date": doc["measurement_date"]}
                operations.append(ReplaceOne(filter_key, doc, upsert=True))
            
            result = db.water_conditions.bulk_write(operations)
            logger.info(f"✅ Upserted {result.upserted_count} water conditions, modified {result.modified_count}")
        
        # Store Burry-style risk indicators
        risk_doc = {
            **risk_indicators,
            "analysis_date": dt.date.today().isoformat(),
            "ingestion_timestamp": dt.datetime.now(dt.timezone.utc),
            "crisis_score": dashboard_data["water_crisis_score"],
            "investment_opportunities": dashboard_data["investment_opportunities"],
            "critical_alerts": dashboard_data["critical_alerts"]
        }
        
        db.water_risk_analysis.update_one(
            {"analysis_date": risk_doc["analysis_date"]},
            {"$set": risk_doc},
            upsert=True
        )
        logger.info("✅ Updated Burry-style risk analysis")
        
        # Store dashboard data
        db.water_dashboard_data.update_one(
            {"date": dt.date.today().isoformat()},
            {"$set": dashboard_data},
            upsert=True
        )
        logger.info("✅ Updated dashboard data")
        
        # Store dataset metadata
        dataset_meta = {
            "id": "colorado-water-conditions-burry",
            "name": "Colorado Water Conditions - Burry Analysis",
            "assetType": "dataset",
            "category": "Water Risk Intelligence",
            "attribution": {
                "agency": "Colorado Division of Water Resources",
                "url": "https://water.state.co.us/",
                "analysis_style": "Michael Burry forensic approach"
            },
            "description": "Real-time water scarcity analysis for investment decision-making",
            "tags": ["water", "colorado", "agriculture", "drought", "investment", "risk", "burry"],
            "license": "Public Domain",
            "burry_metrics": {
                "crisis_score": dashboard_data["water_crisis_score"],
                "zero_flow_percentage": risk_indicators.get('zero_flow_percentage', 0),
                "critical_counties": len([c for c in risk_indicators.get('county_vulnerabilities', []) if c["risk_level"] == "CRITICAL"])
            },
            "investment_signals": dashboard_data["investment_opportunities"],
            "ingestion_date": dt.datetime.now(dt.timezone.utc),
            "source_file": os.path.basename(csv_path)
        }
        
        db.datasets.update_one(
            {"id": dataset_meta["id"]},
            {"$set": dataset_meta},
            upsert=True
        )
        logger.info("✅ Updated dataset metadata")
        
        # Print Burry-style summary
        print_burry_summary(risk_indicators, dashboard_data)
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise

def print_burry_summary(risk_indicators, dashboard_data):
    """Print Michael Burry-style analysis summary"""
    print("\n" + "="*80)
    print("🎯 MICHAEL BURRY WATER SCARCITY ANALYSIS")
    print("="*80)
    
    crisis_score = dashboard_data["water_crisis_score"]
    print(f"💧 WATER CRISIS SCORE: {crisis_score}/100")
    
    if crisis_score > 70:
        print("🚨 CRITICAL: Systemic water crisis detected - Major short opportunities")
    elif crisis_score > 40:
        print("⚠️  HIGH RISK: Significant scarcity signals - Selective shorts + water tech longs")
    elif crisis_score > 20:
        print("📊 MODERATE: Mixed signals - Monitor closely, prepare positions")
    else:
        print("✅ LOW RISK: Stable conditions - Consider water infrastructure longs")
    
    print(f"\n📈 ZERO FLOW STREAMS: {risk_indicators.get('zero_flow_percentage', 0):.1f}%")
    print(f"🏞️  DEPLETED RESERVOIRS: {risk_indicators.get('zero_storage_reservoirs', 0)}")
    print(f"🌾 ARKANSAS BASIN STRESS: {risk_indicators.get('arkansas_basin_zero_flow_pct', 0):.1f}%")
    
    print("\n🎯 TOP INVESTMENT SIGNALS:")
    opportunities = dashboard_data["investment_opportunities"]
    
    if opportunities["short_positions"]:
        print("📉 SHORT POSITIONS:")
        for short in opportunities["short_positions"][:3]:
            print(f"   • {short}")
    
    if opportunities["long_positions"]:
        print("📈 LONG POSITIONS:")
        for long_pos in opportunities["long_positions"][:3]:
            print(f"   • {long_pos}")
    
    print("\n🚨 CRITICAL ALERTS:")
    for alert in dashboard_data["critical_alerts"][:3]:
        print(f"   • {alert['type']}: {alert['message']}")
    
    print("\n🗺️  TOP VULNERABLE COUNTIES:")
    for county in risk_indicators.get('county_vulnerabilities', [])[:5]:
        print(f"   • {county['county']}: {county['zero_flow_percentage']}% zero flow ({county['risk_level']})")
    
    print("="*80)

# CRON-STYLE SCHEDULING
def schedule_daily_ingestion():
    """Schedule daily water data ingestion at 6 AM Mountain Time"""
    schedule.every().day.at("06:00").do(ingest_water_conditions)
    logger.info("📅 Scheduled daily water ingestion at 6:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

if __name__ == "__main__":
    # For immediate run
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--schedule":
        logger.info("🕐 Starting scheduled mode...")
        schedule_daily_ingestion()
    else:
        # Single run
        try:
            result = ingest_water_conditions()
            logger.info("✅ Water ingestion completed successfully")
        except Exception as e:
            logger.error(f"❌ Water ingestion failed: {e}")
