# backend/agents/auction_pdf_parser.py
import re, statistics, os, datetime, pdfplumber
from typing import Dict, Any, List, Optional
from app.db.mongo import db  # your existing connector

MONTHS = "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"

def _extract_text(path: str) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            parts.append(p.extract_text() or "")
    return "\n".join(parts)

def _date(text: str) -> Optional[str]:
    m = re.search(rf"{MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s*\d{{4}}", text, re.I) or \
        re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text)
    return m.group(0) if m else None

def _market(text: str) -> Optional[str]:
    for line in text.splitlines()[:80]:
        if re.search(r"(Livestock|Auction|Exchange|Stockyard|Stockyards)", line, re.I):
            s = re.sub(r"[^A-Za-z0-9 ,.&'-]", " ", line).strip()
            if 6 <= len(s) <= 80:
                return s
    return None

def _total_head(text: str) -> Optional[int]:
    for pat in [r"(?:sold|receipts|run of)\s+([\d,]+)\s+head",
                r"Total\s+(?:Receipts|Head)\s*[:\-]\s*([\d,]+)"]:
        m = re.search(pat, text, re.I)
        if m:
            return int(m.group(1).replace(",", ""))
    return None

def _prices(text: str, keys: List[str]) -> List[float]:
    vals = []
    for line in text.splitlines():
        if any(re.search(k, line, re.I) for k in keys):
            vals += [float(x) for x in re.findall(r"\$?\s*([12]?\d{2}\.\d{2})\b", line)]
            for n in re.findall(r"\b([12]\d{2})\b", line):
                v = float(n)
                if 100 <= v <= 399: vals.append(v)
    return vals

def parse_pdf(path: str) -> Dict[str, Any]:
    t = _extract_text(path)
    d = {
        "market": _market(t),
        "sale_date": _date(t),
        "total_head": _total_head(t),
        "classes": {}
    }
    for label, keys in [
        ("feeder_steers", ["steer", r"\bstr\b"]),
        ("feeder_heifers", ["heifer", r"\bhfr\b"]),
        ("cows", ["cow", "cows"]),
        ("bulls", ["bull", "bulls"]),
    ]:
        prices = _prices(t, keys)
        if prices:
            d["classes"][label] = {
                "overall_avg_cwt": round(statistics.mean(prices), 2),
                "lots": len(prices)
            }
    d["source"] = {"type":"pdf", "file": os.path.basename(path)}
    d["ingested_at"] = datetime.datetime.utcnow().isoformat()
    return d

def ingest(path: str):
    doc = parse_pdf(path)
    db.auctions.insert_one(doc)
    return doc

