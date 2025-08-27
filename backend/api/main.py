from fastapi import FastAPI, Depends
from typing import List
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import Session

from backend.db.models import SessionLocal, Auction, BoxedBeef, Signal
from backend.db.init_db import init_db

app = FastAPI(title="AgriSignals API", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AuctionOut(BaseModel):
    id: int
    market: str
    location: str
    sale_date: date
    head_count: int
    weight_band: str
    price_cwt: float
    keywords: str
    source_url: str
    class Config:
        from_attributes = True

class BoxedBeefOut(BaseModel):
    id: int
    date: date
    choice: float
    select: float
    loads: int
    class Config:
        from_attributes = True

class SignalOut(BaseModel):
    id: int
    date: date
    name: str
    value: float
    triggered: bool
    notes: str | None = None
    class Config:
        from_attributes = True

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/auctions", response_model=List[AuctionOut])
def list_auctions(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Auction).order_by(Auction.sale_date.desc()).limit(limit).all()

@app.get("/boxed_beef", response_model=List[BoxedBeefOut])
def list_boxed_beef(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(BoxedBeef).order_by(BoxedBeef.date.desc()).limit(limit).all()

@app.get("/signals", response_model=List[SignalOut])
def list_signals(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Signal).order_by(Signal.date.desc()).limit(limit).all()
