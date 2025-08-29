# backend/agents/mail_ingest.py
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

# Restrict which hostnames we'll auto-download PDFs from
ALLOWED_PDF_DOMAINS = {
    "beehiiv.com", "cattleusa.com", "cattletrend.com",
    "files.beehiiv.com", "mail.beehiiv.com"
}

# Aligned Mongo env vars (matches API)
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB") or os.getenv("MONGODB_DB", "agrisignals_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ----------------------
# Market canonicalization
# ----------------------
def load_markets() -> Tuple[List[Dict[str, Any]], List[str]]:
    """Load known markets from DB or return defaults"""
    markets = list(db.markets.find({}, {"_id": 0}))
    if not markets:
        # Default fallback markets
        markets = [
            {"name": "Dodge City", "state": "KS", "aliases": ["dodge", "dodge city"]},
            {"name": "Garden City", "state": "KS", "aliases": ["garden", "garden city"]},
            {"name": "Pratt", "state": "KS", "aliases": ["pratt"]},
            {"name": "Amarillo", "state": "TX", "aliases": ["amarillo"]},
            {"name": "Dalhart", "state": "TX", "aliases": ["dalhart"]},
        ]
    
    market_names = []
    for m in markets:
        market_names.append(m["name"])
        market_names.extend(m.get("aliases", []))
    
    return markets, market_names

def canonicalize_market(raw_name: str, score_cutoff=80) -> Tuple[Optional[str], int]:
    """Fuzzy match raw market name to canonical name"""
    markets, market_names = load_markets()
    
    if not raw_name or not market_names:
        return None, 0
    
    match = process.extractOne(raw_name.lower(), 
                              [n.lower() for n in market_names], 
                              scorer=fuzz.ratio)
    
    if match and match[1] >= score_cutoff:
        # Find the canonical market name
        matched_name = match[0]
        for market in markets:
            if (market["name"].lower() == matched_name or 
                matched_name in [a.lower() for a in market.get("aliases", [])]):
                return market["name"], match[1]
    
    return None, 0

# ----------------------
# Date parsing
# ----------------------
def parse_date(text: str, default_year=None) -> Optional[dt.date]:
    """Parse various date formats from email text"""
    if not text:
        return None
    
    # Common patterns
    patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',      # MM/DD/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',      # MM-DD-YYYY
        r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',    # Month DD, YYYY
        r'(\w+)\s+(\d{1,2})',                # Month DD (current year)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    if match.group(1).isdigit():  # MM/DD/YYYY format
                        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        return dt.date(year, month, day)
                    else:  # Month DD, YYYY format
                        month_name, day, year = match.group(1), int(match.group(2)), int(match.group(3))
                        month = dt.datetime.strptime(month_name[:3], "%b").month
                        return dt.date(year, month, day)
                elif len(match.groups()) == 2:  # Month DD format
                    month_name, day = match.group(1), int(match.group(2))
                    month = dt.datetime.strptime(month_name[:3], "%b").month
                    year = default_year or dt.date.today().year
                    return dt.date(year, month, day)
            except (ValueError, AttributeError):
                continue
    
    return None

# ----------------------
# Email processing
# ----------------------
def extract_lines_from_email(msg: email.message.EmailMessage) -> Tuple[List[str], Optional[str]]:
    """Extract text lines and HTML from email message"""
    lines = []
    html_content = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    text = part.get_content()
                    lines.extend(text.splitlines())
                except:
                    pass
            elif content_type == "text/html":
                try:
                    html_content = part.get_content()
                except:
                    pass
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            try:
                text = msg.get_content()
                lines.extend(text.splitlines())
            except:
                pass
        elif content_type == "text/html":
            try:
                html_content = msg.get_content()
                # Also extract text from HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                lines.extend(soup.get_text().splitlines())
            except:
                pass
    
    return lines, html_content

def parse_upcoming_from_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """Parse upcoming auction events from email lines"""
    events = []
    current_block = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_block:
                events.extend(_parse_block(current_block, dt.date.today().year))
                current_block = []
            continue
        current_block.append(line)
    
    # Process final block
    if current_block:
        events.extend(_parse_block(current_block, dt.date.today().year))
    
    return events

def _parse_block(block: List[str], default_year: int) -> List[Dict[str, Any]]:
    """Parse a block of lines into auction events"""
    events = []
    
    # Look for date and market patterns
    for line in block:
        date_obj = parse_date(line, default_year)
        if date_obj:
            # Try to find market name in same line or nearby lines
            market_name, confidence = canonicalize_market(line)
            
            # Extract estimated head count if present
            head_match = re.search(r'(\d+)\s*head', line, re.IGNORECASE)
            est_heads = int(head_match.group(1)) if head_match else None
            
            event = {
                "sale_date": date_obj.isoformat(),
                "market": market_name,
                "market_confidence": confidence,
                "est_heads": est_heads,
                "raw_text": line,
                "ingestion_date": dt.datetime.utcnow(),
            }
            events.append(event)
    
    return events

# ----------------------
# PDF processing
# ----------------------
def html_find_pdf_urls(html: Optional[str]) -> List[str]:
    """Extract PDF URLs from HTML content"""
    if not html:
        return []
    
    urls = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf'):
            # Check if domain is allowed
            parsed = urlparse(href)
            if parsed.netloc in ALLOWED_PDF_DOMAINS:
                urls.append(href)
    
    return urls

def download_pdf(url: str) -> Optional[str]:
    """Download PDF and return local temp file path"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            f.write(response.content)
            return f.name
    except Exception as e:
        print(f"Failed to download PDF {url}: {e}")
        return None

def extract_pdf_attachments(msg: email.message.EmailMessage) -> List[str]:
    """Extract PDF attachments from email and save to temp files"""
    pdf_paths = []
    
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            if filename and filename.lower().endswith('.pdf'):
                try:
                    content = part.get_content()
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                        f.write(content)
                        pdf_paths.append(f.name)
                except Exception as e:
                    print(f"Failed to extract PDF attachment {filename}: {e}")
    
    return pdf_paths

def parse_pdf_into_rows(pdf_path: str) -> Dict[str, Any]:
    """Parse PDF content into structured data"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text() or ""
            
            # Parse auction data from text
            auctions = _parse_auction_block_text("PDF Content", all_text)
            
            return {
                "source": "pdf",
                "path": pdf_path,
                "pages": len(pdf.pages),
                "auctions": auctions,
                "raw_text": all_text[:1000],  # First 1000 chars for debugging
            }
    except Exception as e:
        print(f"Failed to parse PDF {pdf_path}: {e}")
        return {"source": "pdf", "path": pdf_path, "error": str(e)}

def _parse_auction_block_text(header: str, text: str) -> List[Dict[str, Any]]:
    """Parse auction data from text block"""
    auctions = []
    
    # Look for date patterns
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        date_obj = parse_date(line)
        if date_obj:
            market_name, confidence = canonicalize_market(line)
            
            # Extract head count
            head_match = re.search(r'(\d+)\s*head', line, re.IGNORECASE)
            est_heads = int(head_match.group(1)) if head_match else None
            
            auction = {
                "sale_date": date_obj.isoformat(),
                "market": market_name,
                "market_confidence": confidence,
                "est_heads": est_heads,
                "raw_text": line,
                "source": "pdf",
                "ingestion_date": dt.datetime.utcnow(),
            }
            auctions.append(auction)
    
    return auctions

# ----------------------
# Database operations
# ----------------------
def upsert_upcoming(docs: List[Dict[str, Any]], message_id: Optional[str], subject: str):
    """Insert upcoming auction events into database"""
    if not docs:
        return
    
    # Add metadata
    for doc in docs:
        doc["message_id"] = message_id
        doc["subject"] = subject
        doc["collection"] = "upcoming"
    
    # Bulk upsert
    operations = []
    for doc in docs:
        filter_key = {
            "sale_date": doc["sale_date"],
            "market": doc["market"],
            "message_id": message_id
        }
        operations.append(ReplaceOne(filter_key, doc, upsert=True))
    
    if operations:
        result = db.auctions_schedule.bulk_write(operations)
        print(f"Upserted {result.upserted_count} upcoming auctions, modified {result.modified_count}")

def upsert_auctions(docs: List[Dict[str, Any]], message_id: Optional[str], subject: str, origin: str):
    """Insert completed auction data into database"""
    if not docs:
        return
    
    # Add metadata
    for doc in docs:
        doc["message_id"] = message_id
        doc["subject"] = subject
        doc["origin"] = origin
        doc["collection"] = "auctions"
    
    # Bulk upsert
    operations = []
    for doc in docs:
        filter_key = {
            "sale_date": doc["sale_date"],
            "market": doc["market"],
            "message_id": message_id
        }
        operations.append(ReplaceOne(filter_key, doc, upsert=True))
    
    if operations:
        result = db.auctions_completed.bulk_write(operations)
        print(f"Upserted {result.upserted_count} completed auctions, modified {result.modified_count}")

def insert_raw_pages(raw_pages: List[Dict[str, Any]], pdf_ref: Dict[str, Any]):
    """Insert raw PDF page data for debugging"""
    if not raw_pages:
        return
    
    for page in raw_pages:
        page.update(pdf_ref)
        page["ingestion_date"] = dt.datetime.utcnow()
    
    db.raw_pdf_pages.insert_many(raw_pages)
    print(f"Inserted {len(raw_pages)} raw PDF pages")

# ----------------------
# Main execution
# ----------------------
def run_once():
    """Run mail ingestion once"""
    if not IMAP_USER or not IMAP_PASS:
        print("IMAP credentials not configured")
        return
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select(IMAP_FOLDER)
        
        # Search for relevant emails (last 7 days)
        since_date = (dt.date.today() - dt.timedelta(days=7)).strftime("%d-%b-%Y")
        
        # Build search criteria
        search_criteria = []
        for sender in SENDER_FILTERS:
            search_criteria.append(f'FROM "{sender}"')
        
        search_query = f'(SINCE {since_date}) ({" OR ".join(search_criteria)})'
        
        status, messages = mail.search(None, search_query)
        if status != 'OK':
            print("Failed to search emails")
            return
        
        message_ids = messages[0].split()
        print(f"Found {len(message_ids)} emails to process")
        
        for msg_id in message_ids[-10:]:  # Process last 10 emails
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue
            
            # Parse email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email, policy=default)
            
            subject = msg.get('Subject', '')
            sender = msg.get('From', '')
            message_id = msg.get('Message-ID', '')
            
            print(f"Processing: {subject[:50]}...")
            
            # Extract content
            lines, html_content = extract_lines_from_email(msg)
            
            # Parse upcoming auctions from text
            upcoming_events = parse_upcoming_from_lines(lines)
            if upcoming_events:
                upsert_upcoming(upcoming_events, message_id, subject)
            
            # Process PDF attachments
            pdf_paths = extract_pdf_attachments(msg)
            for pdf_path in pdf_paths:
                pdf_data = parse_pdf_into_rows(pdf_path)
                if pdf_data.get("auctions"):
                    upsert_auctions(pdf_data["auctions"], message_id, subject, "attachment")
                
                # Clean up temp file
                try:
                    os.unlink(pdf_path)
                except:
                    pass
            
            # Process PDF URLs from HTML
            if html_content:
                pdf_urls = html_find_pdf_urls(html_content)
                for url in pdf_urls:
                    pdf_path = download_pdf(url)
                    if pdf_path:
                        pdf_data = parse_pdf_into_rows(pdf_path)
                        if pdf_data.get("auctions"):
                            upsert_auctions(pdf_data["auctions"], message_id, subject, "url")
                        
                        # Clean up temp file
                        try:
                            os.unlink(pdf_path)
                        except:
                            pass
        
        mail.close()
        mail.logout()
        print("Mail ingestion completed")
        
    except Exception as e:
        print(f"Mail ingestion failed: {e}")

if __name__ == "__main__":
    run_once()
