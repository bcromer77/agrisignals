from backend.db.init_db import init_db
from backend.db.models import SessionLocal
from backend.pipelines.sync_auctions import run_all

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        run_all(db)
    finally:
        db.close()
