from fastapi import FastAPI

app = FastAPI(title="Agrisignals API (dev)")

@app.get("/health")
def health():
    return {"status": "ok"}
