import os, sqlite3
path = os.getenv("SQLITE_PATH","agrisignals.db")
con = sqlite3.connect(path)
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS sources(
  url TEXT PRIMARY KEY, title TEXT, published_at TEXT, outlet TEXT,
  city TEXT, state TEXT, county TEXT, country TEXT, commodity TEXT,
  impact_type TEXT, magnitude_pct REAL, excerpt TEXT, raw_text TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS county_signals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  county TEXT, state TEXT, commodity TEXT, score REAL,
  score_breakdown TEXT, day TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS geo_states(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS geo_counties(
  id INTEGER PRIMARY KEY AUTOINCREMENT, state_id INTEGER, name TEXT,
  UNIQUE(state_id,name)
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS geo_entities(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  county_id INTEGER, name TEXT, type TEXT, url TEXT, approved INTEGER DEFAULT 0
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS geo_sources(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id INTEGER, county_id INTEGER, label TEXT, url TEXT, approved INTEGER DEFAULT 0
)""")
con.commit(); con.close()
print("SQLite schema ready at", path)
