from typing import List, Dict
BASE = {
  "water":[
    'site:gov ("{county} County" OR "County of {county}") (water OR drought OR "water restriction" OR groundwater OR SGMA OR GSA OR allocation OR irrigation)',
    'site:usda.gov ("{county}" AND water)'
  ],
  "regulatory":[
    'site:gov ("{county} County" OR "County of {county}") (ordinance OR regulation OR "public notice" OR agenda OR minutes OR RFP OR procurement)'
  ],
  "cattle":[
    'site:usda.gov (cattle AND "{county}")',
    'site:gov (auction OR "sale barn" OR "livestock market") "{county} County"'
  ],
  "citrus":[
    'site:ca.gov (citrus AND (quarantine OR greening OR HLB OR ACP OR pest) AND "{county}")',
    'site:cdfa.ca.gov (citrus AND {county})'
  ],
  "crops":[
    'site:usda.gov ("crop progress" OR NASS) "{county}"',
    'site:gov (harvest OR yields OR planting) "{county} County"'
  ],
  "coffee":[
    'site:hawaii.gov (coffee AND {county})',
    'site:cbp.gov (coffee AND tariff) "{county}"'
  ],
}
TOPIC_TO_COMMODITY={"cattle":"cattle","citrus":"citrus","crops":"crops","coffee":"coffee","water":"water","regulatory":"multi"}
IMPACT_HINTS={"cattle":["price","closure","logistics","disease","tariff"],
              "citrus":["disease","quarantine","policy","procurement"],
              "crops":["weather","yield","policy","planting","harvest"],
              "coffee":["tariff","logistics","policy"],
              "water":["water","restriction","allocation","drought"],
              "regulatory":["regulatory","policy","ordinance","procurement"]}
def county_queries(county:str,state:str)->Dict[str,List[str]]:
    return {t:[p.format(county=county,state=state) for p in pats] for t,pats in BASE.items()}
