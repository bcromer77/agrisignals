# Placeholder for parsing auction PDFs or HTML into Auction rows.
# In MVP, we'll seed a few mock auctions demonstrating keywords.

from datetime import date, timedelta
from backend.db.models import Auction
from sqlalchemy.orm import Session

def seed_mock_auctions(db: Session):
    today = date.today()
    samples = [
        dict(market="Denison Livestock Auction", location="Denison, IA", sale_date=today - timedelta(days=7),
             head_count=360, weight_band="825-900", price_cwt=236.5, keywords="sorted twice; no implants",
             source_url="https://example.com/denison.pdf"),
        dict(market="Joplin Regional Stockyards", location="Joplin, MO", sale_date=today - timedelta(days=6),
             head_count=1200, weight_band="650-850", price_cwt=228.3, keywords="double-sorted",
             source_url="https://example.com/joplin.pdf"),
        dict(market="OKC Stockyards", location="Oklahoma City, OK", sale_date=today - timedelta(days=5),
             head_count=1800, weight_band="700-950", price_cwt=230.1, keywords="",
             source_url="https://example.com/okc.pdf"),
    ]
    for s in samples:
        db.add(Auction(**s))
    db.commit()
