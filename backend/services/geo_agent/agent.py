def suggest_states(): return [{"name": n, "confidence": 0.8} for n in ["California","Texas","Florida","Kansas","Nebraska","Hawaii"]]
def suggest_counties(state:str): return [{"state":state,"name":"Fresno","confidence":0.8}]
def suggest_entities(state:str, county:str): return []
def suggest_sources(state:str, county:str): return []
def approve_entity(e:dict): return None
def approve_source(s:dict): return None
