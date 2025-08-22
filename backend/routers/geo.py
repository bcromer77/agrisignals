from fastapi import APIRouter, Body
from backend.services.geo_agent.agent import (
    suggest_states, suggest_counties, suggest_entities, suggest_sources,
    approve_entity, approve_source
)

router = APIRouter(prefix="/geo", tags=["geo"])

@router.get("/suggest_states")
def route_suggest_states():
    return suggest_states()

@router.get("/suggest_counties")
def route_suggest_counties(state: str):
    return suggest_counties(state)

@router.get("/suggest_entities")
def route_suggest_entities(state: str, county: str):
    return suggest_entities(state, county)

@router.get("/suggest_sources")
def route_suggest_sources(state: str, county: str):
    return suggest_sources(state, county)

@router.post("/approve_entity")
def route_approve_entity(payload: dict = Body(...)):
    approve_entity(payload)
    return {"ok": True}

@router.post("/approve_source")
def route_approve_source(payload: dict = Body(...)):
    approve_source(payload)
    return {"ok": True}
