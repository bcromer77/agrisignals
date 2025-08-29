# time_lag_assassin.py - Geopolitical Time Lag Tracker with Local USCIS Data
import os
import pandas as pd
from datetime import datetime, timedelta
import tweepy
from flask import Flask, jsonify
import spacy

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# Twitter Auth (keys from .env)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")  # Full auth vars
auth = tweepy.OAuthHandler(os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET"))
auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_SECRET"))
twitter_api = tweepy.API(auth)

# Map Zones (from image: FL citrus, Midwest corn, TX cattle, CO/NE Platte)
MONITOR_ZONES = {
    "FL_Citrus": {"lat_range": (28, 29), "long_range": (-82, -81)},
    "Midwest_Corn": {"lat_range": (40, 43), "long_range": (-97, -93)},
    "TX_Cattle": {"lat_range": (31, 34), "long_range": (-102, -98)},
    "CO_NE_Platte": {"lat_range": (40, 41), "long_range": (-104, -102)}
}

# Path to downloaded USCIS files (adjust as needed)
DATA_PATH = os.path.expanduser("~/Downloads/agrisignals/")

# USCIS Files (based on provided documents)
USCIS_FILES = [
    "i140_fy2025_q2.xlsx",
    "i140_rec_by_class_country_fy2025_q2.xlsx",
    "i485_performancedata_fy2025_q2.xlsx",
    "net_backlog_frontlog_fy2025_q2.xlsx",
    "i129_quarterly_request_for_evidence_fy2025_q2.xlsx",
    "i130_awaiting_a_visa_availability_fy2025_q2.xlsx",
    "i765_p_allcat_c08_fy2025_q2.xlsx",
    "i765_application_for_employment_fy2025_q2.xlsx",
    "quarterly_all_forms_fy2025_q2.xlsx"
]

def load_uscis_data():
    """Load and process local USCIS XLSX files."""
    data = {}
    report_date = datetime(2025, 3, 31)  # Q2 end date (March 31, 2025)
    for file in USCIS_FILES:
        file_path = os.path.join(DATA_PATH, file)
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, sheet_name=0)  # Default to first sheet
            if "i129_quarterly_request_for_evidence" in file:  # I-129 (H-2A proxy)
                data["visa_delays"] = df[df["Fiscal Year"] == 2025].set_index("Month")[["Pending5"]].sum().to_dict()
            elif "i765_application_for_employment" in file or "i765_p_allcat_c08" in file:  # I-765
                temp_df = df if "i765_application_for_employment" in file else df.drop(columns=["Note(s)"])
                data["employment_auth"] = temp_df[temp_df["EAD Eligibility Category"].str.contains("A03|A04|A055|A06", na=False)].set_index("EAD Eligibility Category")[["Pending4"]].sum().to_dict()
            elif "net_backlog_frontlog" in file:  # Backlog
                data["backlog"] = df[df["Total"] == "All Forms Frontlog11"]["Total"].iloc[0] if not df.empty else 0
            elif "i140" in file:  # I-140 (indirect labor transitions)
                data["i140_status"] = df[df["Fiscal Year"] == 2025].set_index("2nd Quarter")[["Pending4"]].sum().to_dict()
            elif "i485_performancedata" in file:  # I-485 (adjustment status)
                data["i485_status"] = df[df["Field Office by State"] == "Total"].set_index("Field Office by State")[["Pending8"]].sum().to_dict()
            elif "quarterly_all_forms" in file:  # All forms overview
                data["all_forms"] = df[df["Category and Form Number"] == "I-129"].set_index("Category and Form Number")[["Pending5"]].to_dict()
        else:
            print(f"Warning: {file} not found in {DATA_PATH}")
    return data, report_date

def fetch_real_time_signals(event_type):
    """Fetch Twitter signals for visa delays, fruit rotting, and supply chain issues."""
    signals = []
    queries = {
        "visa_delays": "H-2A visa delay farm labor shortage florida texas",
        "fruit_rotting": "rotting fruit citrus florida drought",
        "bj_supply_chain": "BJ's Wholesale supply chain issues agriculture"
    }
    query = queries.get(event_type, "")
    if query:
        tweets = twitter_api.search_tweets(q=query, lang="en", count=20)
        for tweet in tweets:
            signals.append({"date": tweet.created_at, "text": tweet.text, "event": event_type})
    return signals

def analyze_time_lag():
    """Compute lags between Twitter signals and USCIS Q2 data."""
    lags = []
    uscis_data, report_date = load_uscis_data()

    # Visa Delays (H-2A via I-129)
    visa_signals = fetch_real_time_signals("visa_delays")
    pending_i129 = uscis_data.get("visa_delays", {}).get("Pending5", 0) or uscis_data.get("all_forms", {}).get("I-129", {}).get("Pending5", 0)
    for signal in visa_signals:
        signal_date = signal["date"]
        lag_days = (report_date - signal_date).days
        if lag_days > 0 and "delay" in signal["text"].lower():  # Positive lag only
            prob = min(0.9, lag_days / 90)  # 30-90 days → 33-90% prob
            lags.append({
                "event": "H-2A Visa Delay",
                "signal_date": signal_date,
                "report_date": report_date,
                "lag_days": lag_days,
                "probability": prob,
                "zone": "FL_Citrus",
                "who_bleeds": ["Florida citrus farmers", "Tropicana"],
                "who_benefits": ["Frozen imports", "Labor agencies"],
                "tradecraft": f"Short Tropicana if prob >80% (lag {lag_days}d, pending I-129: {pending_i129})"
            })

    # Fruit Rotting (Proxy: Labor Shortages via I-765)
    rotting_signals = fetch_real_time_signals("fruit_rotting")
    pending_i765 = uscis_data.get("employment_auth", {}).get("Pending4", 0)
    for signal in rotting_signals:
        signal_date = signal["date"]
        lag_days = (report_date - signal_date).days
        if lag_days > 0 and "rotting" in signal["text"].lower():
            prob = min(0.9, lag_days / 90)
            lags.append({
                "event": "Fruit Rotting",
                "signal_date": signal_date,
                "report_date": report_date,
                "lag_days": lag_days,
                "probability": prob,
                "zone": "FL_Citrus",
                "who_bleeds": ["Citrus growers", "Coca-Cola"],
                "who_benefits": ["Alt juice suppliers"],
                "tradecraft": f"Short KO if prob >80% (lag {lag_days}d, pending I-765: {pending_i765})"
            })

    # Supply Chain Issues (BJ's via Backlogs)
    supply_signals = fetch_real_time_signals("bj_supply_chain")
    backlog_total = uscis_data.get("backlog", 0) or uscis_data.get("all_forms", {}).get("I-129", {}).get("Pending5", 0)
    for signal in supply_signals:
        signal_date = signal["date"]
        lag_days = (report_date - signal_date).days
        if lag_days > 0 and "supply chain" in signal["text"].lower():
            prob = min(0.9, lag_days / 90)
            lags.append({
                "event": "BJ's Supply Chain Issue",
                "signal_date": signal_date,
                "report_date": report_date,
                "lag_days": lag_days,
                "probability": prob,
                "zone": "General",
                "who_bleeds": ["BJ's Wholesale", "Retail chains"],
                "who_benefits": ["Walmart", "Amazon"],
                "tradecraft": f"Short BJ if prob >80% (lag {lag_days}d, backlog: {backlog_total})"
            })

    return lags

@app.route('/api/time_lag')
def get_time_lag():
    lags = analyze_time_lag()
    return jsonify({"lags": lags, "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    from schedule import every, run_pending
    import time
    every(1).hours.do(analyze_time_lag)
    print("🧠 TIME LAG ASSASSIN - Starting at", datetime.now())
    analyze_time_lag()
    app.run(debug=True, host='0.0.0.0', port=5001)
    while True:
        run_pending()
        time.sleep(60)
