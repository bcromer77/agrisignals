cd ~/Desktop/Agrisignals/agrisignals
. .venv/bin/activate
export PYTHONPATH=.

cat > backend/jobs/compute_indices.py <<'PY'
import os, json
from datetime import timedelta
import pandas as pd
from backend.db.models import SessionLocal, Auction, BoxedBeef, IndexValue, Signal
from backend.db.init_db import init_db

PREMIUM_WORDS = ["no implants","sorted twice","double-sorted","mineral","tested open","off grass"]
REGIONS_5AREA = ["TX-OK-NM","KS","NE","IA-MN","CO","OTHER"]

def market_to_region(location:str)->str:
    s = (location or "").upper()
    if " TX" in s or " OK" in s or " NM" in s: return "TX-OK-NM"
    if " KS" in s: return "KS"
    if " NE" in s: return "NE"
    if " IA" in s or " MN" in s: return "IA-MN"
    if " CO" in s: return "CO"
    return "OTHER"

def parse_band(band:str):
    try:
        lo,hi = str(band).replace("lbs","").replace(" ","").split("-")
        return float(lo), float(hi)
    except Exception:
        return None, None

def zscore(x, mean, std):
    std = std if std and std>0 else 1.0
    return (x - mean) / std

def compute_csm(rows):
    if len(rows) < 3: return None, 0
    spreads = [(r.choice or 0) - (r.select or 0) for r in rows]
    mom = spreads[-1] - spreads[-3]
    streak = 0
    for i in range(1, min(10, len(spreads))):
        if spreads[-i] - spreads[-i-1] > 0: streak += 1
        else: break
    return mom, streak

def run():
    init_db()
    db = SessionLocal()
    try:
        # Global CSM on boxed beef
        bb_rows = db.query(BoxedBeef).order_by(BoxedBeef.date.asc()).all()
        mom, streak = compute_csm(bb_rows) if bb_rows else (None,0)
        if mom is not None:
            latest_bb = bb_rows[-1].date
            db.add(IndexValue(date=latest_bb, region="ALL", name="CSM", value=float(mom),
                              components=json.dumps({"streak":int(streak)})))

        auctions = db.query(Auction).all()
        if not auctions:
            db.commit(); print("No auctions in DB.")
            return

        df = pd.DataFrame([{
            "sale_date": a.sale_date,
            "market": a.market or "",
            "location": a.location or "",
            "head_count": a.head_count or 0,
            "weight_band": a.weight_band or "",
            "price_cwt": float(a.price_cwt or 0.0),
            "is_prem": any(w in (a.keywords or "").lower() for w in PREMIUM_WORDS),
            "region": market_to_region(a.location or "")
        } for a in auctions])

        # For each region, use its own latest sale_date and its own 7-day history
        for region in REGIONS_5AREA:
            dfr = df[df["region"]==region]
            if dfr.empty: 
                continue
            latest = dfr["sale_date"].max()
            start  = latest - timedelta(days=7)
            today  = dfr[dfr["sale_date"]==latest]
            hist   = dfr[(dfr["sale_date"]< latest) & (dfr["sale_date"]>=start)]
            if today.empty:
                continue

            price_today = float(today["price_cwt"].mean())
            head_today  = float(today["head_count"].sum())
            price_mean, price_std = float(hist["price_cwt"].mean() or 0.0), float(hist["price_cwt"].std() or 0.0)
            head_mean, head_std   = float(hist["head_count"].mean() or 0.0), float(hist["head_count"].std() or 0.0)
            price_z = zscore(price_today, price_mean, price_std)
            head_z  = zscore(head_today,  head_mean,  head_std)
            prem_share = float(today["is_prem"].mean() or 0.0)

            asi = max(0.0, min(100.0, 50 + 15*price_z + 15*head_z + 20*(prem_share*2 - 1)))
            prem = today[today["is_prem"]]["price_cwt"].mean() if today["is_prem"].any() else None
            non  = today[~today["is_prem"]]["price_cwt"].mean() if (~today["is_prem"]).any() else None
            qpi = float((prem - non)) if prem is not None and non is not None else 0.0

            total = today["head_count"].sum()
            heavy = 0
            for _, r in today.iterrows():
                lo,hi = parse_band(r["weight_band"])
                if lo and hi and (lo+hi)/2 >= 750:
                    heavy += r["head_count"]
            wpi = 100.0 * heavy / total if total else 0.0

            db.add(IndexValue(date=latest, region=region, name="ASI", value=float(asi),
                              components=json.dumps({"price_z":price_z,"head_z":head_z,"prem_share":prem_share})))
            db.add(IndexValue(date=latest, region=region, name="QPI", value=float(qpi),
                              components=json.dumps({})))
            db.add(IndexValue(date=latest, region=region, name="WPI", value=float(wpi),
                              components=json.dumps({})))

            asi_thr = float(os.getenv("ASI_TRIGGER","70"))
            qpi_thr = float(os.getenv("QPI_PREMIUM_USD","5"))
            if asi >= asi_thr:
                db.add(Signal(date=latest, name="ASI", value=float(asi), triggered=True,
                              notes=f"ASI {asi:.0f} >= {asi_thr} ({region})"))
            if qpi >= qpi_thr:
                db.add(Signal(date=latest, name="QPI", value=float(qpi), triggered=True,
                              notes=f"QPI {qpi:.2f} >= {qpi_thr} ({region})"))

        db.commit(); print("Per-region indices computed.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
PY

python backend/jobs/compute_indices.py

