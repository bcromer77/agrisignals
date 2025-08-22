from typing import Optional, Dict

WEIGHTS = {"recency":0.35,"authority":0.25,"impact":0.25,"county_match":0.15}
AUTHORITY_SCORES = {"gov":1.0,"ca.gov":0.95,"usda.gov":0.95,"org":0.7,"com":0.5}

def authority_from_url(url:str)->float:
    return next((v for k,v in AUTHORITY_SCORES.items() if k in (url or "")),0.4)

def recency_score(days_old: Optional[int])->float:
    return 0.6 if days_old is None else max(0.1,min(1.0,1.0-days_old/60))

def county_match_score(target:str,text:str)->float:
    return 1.0 if (target or "").lower() in (text or "").lower() else 0.4

def impact_score(text:str,hints)->float:
    hits=sum(1 for h in hints if h in (text or "").lower()); return min(1.0,0.3+0.15*hits)

def total_score(days_old, url, county, text, hints)->(float,Dict[str,float]):
    b={"recency":recency_score(days_old),"authority":authority_from_url(url),
       "county_match":county_match_score(county,text),"impact":impact_score(text,hints)}
    return sum(WEIGHTS[k]*b[k] for k in WEIGHTS), b
