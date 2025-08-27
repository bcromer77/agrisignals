from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agrisignals.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class Auction(Base):
    __tablename__ = "auctions"
    id = Column(Integer, primary_key=True, index=True)
    market = Column(String, index=True)          # e.g. Denison, Joplin, OKC
    location = Column(String, index=True)        # city, state
    sale_date = Column(Date, index=True)
    head_count = Column(Integer)
    weight_band = Column(String)                 # e.g. 650-850
    price_cwt = Column(Float)
    keywords = Column(String)                    # e.g. "sorted twice; no implants"
    source_url = Column(Text)

class BoxedBeef(Base):
    __tablename__ = "boxed_beef"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    choice = Column(Float)
    select = Column(Float)
    loads = Column(Integer)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    name = Column(String, index=True)            # e.g. "choice_select_spread"
    value = Column(Float)
    triggered = Column(Boolean, default=False)
    notes = Column(Text)

class IndexValue(Base):
    __tablename__ = "indices"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    region = Column(String, index=True)          # TX-OK-NM, KS, NE, IA-MN, CO, OTHER, ALL
    name = Column(String, index=True)            # ASI, QPI, WPI, CSM
    value = Column(Float)
    components = Column(Text)                    # JSON blob

class Basis(Base):
    __tablename__ = "basis"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    region = Column(String, index=True)
    cash_cwt = Column(Float)
    futures_cwt = Column(Float)
    basis = Column(Float)

class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    rtype = Column(String, index=True)           # POLICY or BIO
    severity = Column(Integer)
    region = Column(String, index=True)
    source = Column(String)
    text = Column(Text)
