import os
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any
from firecrawl import Firecrawl

FC = Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(1,1,8))
def fc_search(q: str, limit: int = 8, formats: List[str] = ["markdown"]) -> Dict[str, Any]:
    return FC.search(q, limit=limit, scrapeOptions={"formats": formats})
