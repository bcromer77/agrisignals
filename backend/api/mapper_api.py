# backend/api/mapper_api.py
from fastapi import FastAPI
from backend.services.complication_mapper import complication_mapper

app = FastAPI()

@app.get("/complications")
def get_complications():
    test_signal = {
        "title": "Oklahoma cattle auction prices up 12%",
        "raw_text": "Cattle auctions in Oklahoma reported prices up 12% due to drought pressure.",
        "dataset_data": {"station": "PLAJURCO", "amount": 41, "units": "CFS"},
        "twitter_posts": [
            {"handle": "@FarmPolicy", "text": "NE farmers warn of loan defaults amid Platte crisis."},
        ]
    }
    return complication_mapper(test_signal)

