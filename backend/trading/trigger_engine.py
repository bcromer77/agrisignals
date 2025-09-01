from datetime import datetime, timezone
from backend.config_loader import STRATEGY

# Dummy live signal data (replace with real feeds later)
LIVE_SIGNALS = {
    "NOAA_FL_Drought_Z": 1.2,
    "USCIS_I129_Pending_QoQ": 18,
    "Twitter_LaborShortage_Score": 0.8,
    "Tariff_0306_0307_Active": 1,
    "CBP_Seafood_Detentions_Z": 2.5,
    "ICE_CertStocks_7dma_pct": -2.5,
    "Brazil_ExportDelay_Score": 0.7,
    "Vietnam_Export_Rebound": 0.3
}


def check_condition(cond, signals):
    """Evaluate one condition {signal, op, value}."""
    val = signals.get(cond["signal"])
    if val is None:
        return False
    if cond["op"] == ">=":
        return val >= cond["value"]
    if cond["op"] == "<=":
        return val <= cond["value"]
    if cond["op"] == "==":
        return val == cond["value"]
    return False


def evaluate_triggers(signals=LIVE_SIGNALS):
    """Return a list of trade instructions if triggers fire."""
    trades = []
    for trig in STRATEGY["triggers"]:
        if all(check_condition(cond, signals) for cond in trig["enter_if"]):
            trades.append({
                "id": trig["id"],
                "legs": trig["legs"],
                "risk": trig["risk"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    return trades


if __name__ == "__main__":
    print("🔥 Trigger Engine run at", datetime.now(timezone.utc).isoformat())
    for trade in evaluate_triggers():
        print(trade)

