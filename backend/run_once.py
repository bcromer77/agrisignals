from agents.auction_pdf_parser import ingest
import glob
for pdf in glob.glob("/data/auctions/*.pdf"):
    ingest(pdf)

