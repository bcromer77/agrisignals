# backend/routers/subscriptions.py
from fastapi import APIRouter, Body
import sqlite3, os
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
DB = os.getenv("SQLITE_PATH","agrisignals.db")

@router.post("")
def add_sub(sub: dict = Body(...)):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("INSERT INTO subscriptions(channel,address,county,state,commodity,threshold) VALUES(?,?,?,?,?,?)",
        (sub["channel"], sub["address"], sub["county"], sub["state"], sub.get("commodity") or "cattle", sub.get("threshold",60.0)))
    con.commit(); con.close(); return {"ok": True}

@router.get("")
def list_subs():
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("SELECT channel,address,county,state,commodity,threshold,created_at FROM subscriptions ORDER BY created_at DESC").fetchall()
    con.close()
    return [dict(channel=r[0],address=r[1],county=r[2],state=r[3],commodity=r[4],threshold=r[5],created_at=r[6]) for r in rows]

