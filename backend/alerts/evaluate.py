from datetime import timedelta
from sqlalchemy.orm import Session
from backend.db.models import BoxedBeef, Signal
import yaml, os
from datetime import date

RULES_PATH = os.getenv("ALERT_RULES_PATH", "backend/alerts/rules.yaml")

def load_rules():
    with open(RULES_PATH, "r") as f:
        return yaml.safe_load(f)

def evaluate_choice_select_spread(db: Session):
    rules = load_rules()
    r = rules.get("choice_select_spread", {})
    thr = float(r.get("threshold", 30.0))
    consecutive_days = int(r.get("consecutive_days", 3))

    rows = db.query(BoxedBeef).order_by(BoxedBeef.date.desc()).limit(10).all()
    rows = rows[::-1]  # oldest->newest
    streak = 0
    last_val = None
    for b in rows:
        spread = (b.choice or 0) - (b.select or 0)
        last_val = spread
        if spread >= thr:
            streak += 1
        else:
            streak = 0
    triggered = streak >= consecutive_days
    sig = Signal(date=date.today(), name="choice_select_spread", value=last_val or 0.0, triggered=triggered,
                 notes=f"Spread {last_val:.2f} over last day; streak={streak}/{consecutive_days}")
    db.add(sig)
    db.commit()
