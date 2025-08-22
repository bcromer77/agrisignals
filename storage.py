cat > backend/services/county_scanner/storage.py <<'PY'
import os, json, sqlite3
from typing import List, Dict, Optional

class SqlStorage:
    def __init__(self, path:str=None):
        path = path or os.getenv("SQLITE_PATH","agrisignals.db")
        self.conn = sqlite3.connect(path, check_same_thread=False)

    def upsert_sources(self, docs: List[Dict]):
        cur = self.conn.cursor()
        for d in docs:
            cur.execute("""
              INSERT INTO sources(url,title,published_at,outlet,city,state,county,country,commodity,impact_type,magnitude_pct,excerpt,raw_text)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,published_at=excluded.published_at,outlet=excluded.outlet,city=excluded.city,state=excluded.state,county=excluded.county,country=excluded.country,
                commodity=excluded.commodity,impact_type=excluded.impact_type,magnitude_pct=excluded.magnitude_pct,excerpt=excluded.excerpt,raw_text=excluded.raw_text
            """, (
                d.get("url"), d.get("title"), d.get("published_at") and d["published_at"].isoformat(),
                d.get("outlet"), d.get("city"), d.get("state"), d.get("county"), d.get("country"),
                d.get("commodity"), d.get("impact_type"), d.get("magnitude_pct"), d.get("excerpt"), d.get("raw_text"),
            ))
        self.conn.commit()

    def upsert_signal(self, signal: Dict):
        day=None
        if signal.get("sources"):
            pub=signal["sources"][0].get("published_at")
            if pub: day=pub.date().isoformat()
        self.conn.execute("""
          INSERT INTO county_signals (county,state,commodity,score,score_breakdown,day)
          VALUES (?,?,?,?,?,?)
        """, (signal["county"], signal.get("state"), signal["commodity"], signal["score"], json.dumps(signal["score_breakdown"]), day))
        self.conn.commit()

    def get_signals(self, county:str, state:str, commodity:Optional[str]=None, limit:int=100):
        q="SELECT county,state,commodity,score,score_breakdown,day,created_at FROM county_signals WHERE county=? AND state=?"
        args=[county,state]
        if commodity: q+=" AND commodity=?"; args.append(commodity)
        q+=" ORDER BY created_at DESC LIMIT ?"; args.append(limit)
        rows=self.conn.execute(q,args).fetchall()
        return [ {"county":r[0],"state":r[1],"commodity":r[2],"score":r[3],
                  "score_breakdown":json.loads(r[4] or "{}"),"day":r[5],"created_at":r[6]} for r in rows ]

    def get_sources(self, county:str, state:str, limit:int=50):
        rows=self.conn.execute("""
          SELECT url,title,published_at,outlet,city,state,county,country,commodity,impact_type,magnitude_pct,excerpt
          FROM sources WHERE county=? AND state=? ORDER BY published_at DESC LIMIT ?
        """,(county,state,limit)).fetchall()
        return [ {"url":r[0],"title":r[1],"published_at":r[2],"outlet":r[3],"city":r[4],
                  "state":r[5],"county":r[6],"country":r[7],"commodity":r[8],
                  "impact_type":r[9],"magnitude_pct":r[10],"excerpt":r[11]} for r in rows ]

STORE = SqlStorage()
PY

