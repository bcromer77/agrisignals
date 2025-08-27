import datetime as dt
from pymongo import MongoClient
import os, statistics

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "agrisignals")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def generate_signals():
    today = dt.date.today()
    last7 = today - dt.timedelta(days=7)

    # fetch last 2 weeks auctions
    auctions = list(db.auctions_schedule.find({"sale_date": {"$gte": str(last7)}}))
    if not auctions: return []

    # aggregate head counts by state
    state_counts = {}
    for a in auctions:
        st = a.get("state") or "UNK"
        state_counts.setdefault(st, []).append(a.get("est_heads") or 0)

    signals = []
    for st, vals in state_counts.items():
        avg = statistics.mean(vals) if vals else 0
        if avg > 5000:
            signals.append({
                "timestamp": dt.datetime.utcnow().isoformat(),
                "commodity": "cattle",
                "region": st,
                "severity": "high-volume",
                "message": f"State {st} showing large auction runs avg {avg:.0f} head/week"
            })
        elif avg < 1000:
            signals.append({
                "timestamp": dt.datetime.utcnow().isoformat(),
                "commodity": "cattle",
                "region": st,
                "severity": "low-volume",
                "message": f"State {st} showing very small auction runs avg {avg:.0f} head/week"
            })

    if signals:
        db.signals.insert_many(signals)
    return signals

if __name__ == "__main__":
    out = generate_signals()
    print(f"Generated {len(out)} signals")

