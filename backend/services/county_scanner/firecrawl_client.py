import os
from firecrawl import Firecrawl
from dotenv import load_dotenv

# Make sure env is loaded
load_dotenv()

def get_fc():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is missing — check your .env file")
    return Firecrawl(api_key=api_key)

# Example helper
def fc_search(query, limit=10):
    fc = get_fc()
    return fc.search(query, limit=limit, scrapeOptions={"formats": ["markdown"]})

