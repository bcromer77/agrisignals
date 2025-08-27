# scripts/migrate_subscriptions.py
import sqlite3, os
db = os.getenv("SQLITE_PATH","agrisignals.db")
con = sqlite3.connect(db); cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS subscriptions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel TEXT,         -- 'slack' | 'whatsapp'
  address TEXT,         -- webhook URL or whatsapp:+15551234567
  county TEXT, state TEXT, commodity TEXT,
  threshold REAL DEFAULT 60.0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
)""")
con.commit(); con.close(); print("subscriptions ready")

