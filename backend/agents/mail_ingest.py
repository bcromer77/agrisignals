import imaplib, os, re, email, tempfile, datetime as dt
from email.policy import default
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from rapidfuzz import process, fuzz
from pymongo import MongoClient, ReplaceOne
import pdfplumber

# ----------------------
# Config
# ----------------------
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER")          # e.g. cromerbazil@gmail.com
IMAP_PASS = os.getenv("IMAP_PASS")          # app password (recommended)
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")

# Match senders/subjects you care about
SENDER_FILTERS = [
    "notifications@cattleusa.com",
    "cattleusa",
    "larry@cattletrend.com",
    "cattletrend.com",
]
SUBJECT_KEYWORDS = [
    "Market Reports", "Daily Bulletin", "CattleUSA Drive", "Auction Summary",
    "Upcoming", "Sale", "Report"
]

# Restrict which hostnames we’ll auto-download PDFs from
ALLOWED_PDF_DOMAINS = {
    "beehiiv.com", "cattleusa.com", "cattletrend.com",
    "files.beehiiv.com", "mail.beehiiv.com"
}

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "agrisignals")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ----------------------
# Market canonicalization
# ----------------------
def load_markets() -> Tuple[List[Dict[str, Any]], List[str]]:
    markets = list(db.markets.find({}, {"_id":0, "market":1, "state":1, "category":1}))
    names = [m["market"] for m in markets]
    return markets, names

MARKETS, MARKET_NAMES = load_markets()

def canonicalize_market(raw_name:str, score_cutoff=80) -> Tuple[Optional[str], int]:
    if not raw_name:
        return None, 0
    cand = process.extractOne(raw_name, MARKET_NAMES, scorer=fuzz.token_sort_ratio)
    if not cand:
        return None, 0
    name, score, _ = cand
    if score >= score_cutoff:
        return name, score
    return None, score

# ----------------------
# Regex helpers
# ----------------------
HEAD_PAT = re.compile(r"\b(?P<heads>\d{2,6})\s*(?:head|hd)\b", re.I)
DATE_PAT = re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*\s*,?\s*(?P<m>\d{1,2})[/-](?P<d>\d{1,2})(?:[/-](?P<y>\d{2,4}))?", re.I)
DATE2_PAT = re.compile(r"\b(?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\w*\s+(?P<d>\d{1,2})(?:,\s*(?P<y>\d{4}))?", re.I)
AUCTION_BLOCK_ANCHOR = re.compile(r"\b(AUCTION SUMMARY|AUCTION RESULTS)\b", re.I)

def parse_date(text:str, default_year=None) -> Optional[dt.date]:
    if not text:
        return None
    m = DATE_PAT.search(text) or DATE2_PAT.search(text)
    if not m:
        return None
    try:
        if "mon" in m.groupdict():
            mon_str = m.group("mon").lower()[:3]
            month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
            month = month_map.get(mon_str)
            day = int(m.group("d"))
            year = int(m.group("y")) if m.group("y") else (default_year or dt.date.today().year)
        else:
            month = int(m.group("m"))
            day = int(m.group("d"))
            y = m.group("y")
            year = int(y) + (2000 if y and len(y)==2 else 0) if y else (default_year or dt.date.today().year)
        return dt.date(year, month, day)
    except Exception:
        return None

# ----------------------
# Email body parsing
# ----------------------
def extract_lines_from_email(msg: email.message.EmailMessage) -> Tuple[List[str], Optional[str]]:
    """
    Returns: (lines, html_string or None)
    """
    html = None
    text = None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/html":
                try:
                    html = part.get_content()
                except Exception:
                    pass
            elif ctype == "text/plain":
                try:
                    text = part.get_content()
                except Exception:
                    pass
    else:
        ctype = msg.get_content_type()
        try:
            if ctype == "text/html":
                html = msg.get_content()
            else:
                text = msg.get_content()
        except Exception:
            pass

    lines: List[str] = []
    if html:
        soup = BeautifulSoup(html, "lxml")
        blocks = soup.find_all(["tr","li","p","a","div","span"])
        for b in blocks:
            t = b.get_text(" ", strip=True)
            if t:
                lines.append(t)
    else:
        for ln in (text or "").splitlines():
            ln = (ln or "").strip()
            if ln:
                lines.append(ln)

    # de-dup
    uniq, seen = [], set()
    for ln in lines:
        k = ln.lower()
        if k not in seen:
            uniq.append(ln)
            seen.add(k)

    return uniq, html

def parse_upcoming_from_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Extract simple 'upcoming sale' blocks from the email body itself.
    """
    out: List[Dict[str, Any]] = []
    default_year = dt.date.today().year
    buf: List[str] = []

    for ln in lines:
        if any(tok in ln.lower() for tok in ["auction","stockyards","livestock","exchange"]):
            if buf:
                out.extend(_parse_block(buf, default_year))
                buf = []
        buf.append(ln)
    if buf:
        out.extend(_parse_block(buf, default_year))
    return out

def _parse_block(block: List[str], default_year: int) -> List[Dict[str, Any]]:
    txt = " | ".join(b for b in block if b)
    if not txt:
        return []
    first = next((b for b in block if any(t in b.lower() for t in ["auction","stockyards","livestock","exchange"])), block[0])
    market_raw = re.sub(r"\s+", " ", first).strip() if first else None
    sale_date = parse_date(txt, default_year)
    mheads = HEAD_PAT.search(txt)
    est_heads = int(mheads.group("heads")) if mheads else None

    classes = []
    for key in ["feeder", "calf", "calves", "bred", "pairs", "cows", "heifer", "bull", "fat", "weigh", "weigh-up", "replacement"]:
        if re.search(rf"\b{key}\w*\b", txt, re.I):
            classes.append(key)

    canon, score = canonicalize_market(market_raw or "")
    doc = {
        "market_raw": market_raw,
        "market": canon or market_raw,
        "match_score": score,
        "sale_date": sale_date.isoformat() if sale_date else None,
        "est_heads": est_heads,
        "classes": sorted(set(classes)),
        "ingest": "email_body"
    }
    if canon:
        mk = next((m for m in MARKETS if m["market"] == canon), None)
        if mk:
            doc.update({"state": mk.get("state"), "category": mk.get("category")})
    return [doc]

# ----------------------
# PDF helpers
# ----------------------
def html_find_pdf_urls(html: Optional[str]) -> List[str]:
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue
        # Heuristic: direct .pdf or a known host; Beehiiv often has signed links ending in .pdf
        if href.lower().endswith(".pdf"):
            urls.append(href)
        else:
            host = urlparse(href).hostname or ""
            if any(host.endswith(dom) for dom in ALLOWED_PDF_DOMAINS):
                # some beehiiv links are a redirect to the pdf; include them
                urls.append(href)
    return list(dict.fromkeys(urls))  # dedup preserving order

def download_pdf(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        # If it’s an html redirect page, skip
        content_type = r.headers.get("content-type","").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            return None
        fd, path = tempfile.mkstemp(prefix="agri_", suffix=".pdf")
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        return path
    except Exception as e:
        print(f"[mail_ingest] PDF download failed: {e} for {url}")
        return None

def extract_pdf_attachments(msg: email.message.EmailMessage) -> List[str]:
    """Return temp file paths of any PDF attachments."""
    paths = []
    if not msg.is_multipart():
        return paths
    for part in msg.walk():
        cdispo = (part.get("Content-Disposition") or "").lower()
        ctype = (part.get_content_type() or "").lower()
        if "attachment" in cdispo or ctype == "application/pdf":
            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                fd, path = tempfile.mkstemp(prefix="agri_", suffix=".pdf")
                with os.fdopen(fd, "wb") as f:
                    f.write(payload)
                paths.append(path)
            except Exception as e:
                print(f"[mail_ingest] failed to extract attachment: {e}")
    return paths

# ----------------------
# PDF parsing
# ----------------------
def parse_pdf_into_rows(pdf_path: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "auctions": [ { market, state, day, heads, ... } ],
        "schedule": [ { market, sale_date, est_heads, ... } ],
        "raw_pages": [ {page, text} ]  # for forensic fallback
      }
    """
    out: Dict[str, Any] = {"auctions": [], "schedule": [], "raw_pages": []}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pageno, page in enumerate(pdf.pages, start=1):
                # collect raw for forensic
                txt = ""
                try:
                    txt = page.extract_text() or ""
                except Exception:
                    txt = ""
                if txt.strip():
                    out["raw_pages"].append({"page": pageno, "text": txt})

                # try structured tables first
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []

                if tables:
                    for t in tables:
                        # Many “Auction Summary” PDFs layout as 2 columns blocks; we try to normalize
                        cleaned = [[(c or "").strip() for c in row] for row in t if any(row)]
                        # heuristic: look for market header row in table
                        for row in cleaned:
                            header = " ".join(row).strip()
                            if not header:
                                continue
                            if any(k in header.lower() for k in ["livestock", "stockyards", "auction", "commission"]):
                                # attempt to find heads/date around this header in following rows
                                block_text = " | ".join([" ".join(r) for r in cleaned])
                                out["auctions"].extend(_parse_auction_block_text(header, block_text))
                # also try to parse “AUCTION SUMMARY” sections from raw text
                if AUCTION_BLOCK_ANCHOR.search(txt or ""):
                    out["auctions"].extend(_parse_auction_block_text("", txt))
    except Exception as e:
        print(f"[mail_ingest] PDF parse failed: {e}")

    return out

def _parse_auction_block_text(header: str, text: str) -> List[Dict[str, Any]]:
    """
    Very forgiving parser over a blob of text that includes one or more markets,
    heads, dates, and weight-band price lines.
    """
    results: List[Dict[str, Any]] = []
    # split on markets heuristically
    chunks = re.split(r"(?<=\n|\r)(?=[^\n\r]*?(Auction|Stockyards|Livestock|Commission))", text, flags=re.I)
    if len(chunks) <= 1:
        chunks = [text]

    for chunk in chunks:
        chunk = (chunk or "").strip()
        if not chunk:
            continue

        # market name: first line with those keywords
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        market_line = next((ln for ln in lines if any(k in ln.lower() for k in ["auction","stockyards","livestock","commission"])), None)
        if not market_line and header:
            market_line = header

        market_raw = market_line
        canon, score = canonicalize_market(market_raw or "")

        # heads/date
        mheads = HEAD_PAT.search(chunk)
        heads = int(mheads.group("heads")) if mheads else None
        d = parse_date(chunk)

        # try to capture 2-column weight-band lines (simple heuristic)
        bands = []
        for ln in lines:
            if re.search(r"\b(\d{3,4})-(\d{3,4})\s*lbs?\b", ln, re.I) or re.search(r"\b\d{3,4}\s*lbs?\b", ln, re.I):
                # capture trailing price numbers in the same line
                prices = re.findall(r"(\d{2,3}\.\d{2}|\d{2,3})", ln)
                bands.append({"line": ln, "prices": prices})

        doc = {
            "market_raw": market_raw,
            "market": canon or market_raw,
            "match_score": score,
            "day": d.isoformat() if d else None,
            "heads": heads,
            "weight_bands": bands if bands else None,
            "ingest": "pdf"
        }
        if canon:
            mk = next((m for m in MARKETS if m["market"] == canon), None)
            if mk:
                doc.update({"state": mk.get("state"), "category": mk.get("category")})

        # Skip completely empty markets
        if doc.get("market"):
            results.append(doc)

    return results

# ----------------------
# Mongo upserts
# ----------------------
def upsert_upcoming(docs: List[Dict[str, Any]], message_id: Optional[str], subject: str):
    ops = []
    for d in docs:
        if not d.get("market"):
            continue
        key = {"market": d["market"], "sale_date": d.get("sale_date")}
        d.setdefault("source", "email")
        d.setdefault("source_meta", {})
        d["source_meta"].update({"message_id": message_id, "subject": subject})
        ops.append(ReplaceOne(key, {"$set": d}, upsert=True))
    if ops:
        db.auctions_schedule.bulk_write(ops)

def upsert_auctions(docs: List[Dict[str, Any]], message_id: Optional[str], subject: str, origin: str):
    ops = []
    for d in docs:
        if not d.get("market"):
            continue
        key = {
            "market": d["market"],
            # prefer day for results; fallback to (market, weight_bands hash) if day missing
            "day": d.get("day"),
        }
        d.setdefault("source", origin)
        d.setdefault("source_meta", {})
        d["source_meta"].update({"message_id": message_id, "subject": subject})
        ops.append(ReplaceOne(key, {"$set": d}, upsert=True))
    if ops:
        db.auctions.bulk_write(ops)

def insert_raw_pages(raw_pages: List[Dict[str, Any]], pdf_ref: Dict[str, Any]):
    if not raw_pages:
        return
    for rp in raw_pages:
        rec = {"page": rp.get("page"), "text": rp.get("text"), "pdf": pdf_ref, "ts": dt.datetime.utcnow()}
        db.auctions_raw.insert_one(rec)

# ----------------------
# Main runner
# ----------------------
def run_once():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select(IMAP_FOLDER)

    typ, data = mail.search(None, '(UNSEEN)')
    if typ != 'OK':
        print("[mail_ingest] search failed")
        return

    for num in data[0].split():
        typ, msg_data = mail.fetch(num, '(RFC822)')
        if typ != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1], policy=default)
        from_hdr = (msg.get("From") or "").lower()
        subj = msg.get("Subject") or ""
        msg_id = msg.get("Message-ID")

        if not (any(f in from_hdr for f in SENDER_FILTERS) or any(k.lower() in subj.lower() for k in SUBJECT_KEYWORDS)):
            continue

        try:
            # 1) email body → upcoming
            lines, html = extract_lines_from_email(msg)
            upcoming = parse_upcoming_from_lines(lines)
            if upcoming:
                upsert_upcoming(upcoming, msg_id, subj)

            # 2) find PDF links in body and download
            pdf_paths: List[str] = []
            for url in html_find_pdf_urls(html):
                host = urlparse(url).hostname or ""
                if any(host.endswith(dom) for dom in ALLOWED_PDF_DOMAINS):
                    path = download_pdf(url)
                    if path:
                        pdf_paths.append(path)

            # 3) also extract attached PDFs
            pdf_paths.extend(extract_pdf_attachments(msg))

            # 4) parse each PDF → auctions + raw pages
            for p in pdf_paths:
                parsed = parse_pdf_into_rows(p)
                if parsed.get("auctions"):
                    upsert_auctions(parsed["auctions"], msg_id, subj, origin="email_pdf")
                if parsed.get("schedule"):
                    upsert_upcoming(parsed["schedule"], msg_id, subj)
                if parsed.get("raw_pages"):
                    insert_raw_pages(parsed["raw_pages"], {"path": os.path.basename(p), "subject": subj, "message_id": msg_id})

        except Exception as e:
            print(f"[mail_ingest] error: {e}")

    mail.close()
    mail.logout()

if __name__ == "__main__":
    run_once()

