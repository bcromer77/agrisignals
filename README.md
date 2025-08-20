# AgriSignals MVP

Minimal, end-to-end scaffold to:
- ingest auction + boxed beef data
- store to SQLite
- trigger basic alerts
- expose an API (FastAPI)
- render a Streamlit dashboard (lead-gen ready)

## Quickstart

```bash
make setup
make seed            # load mock data
make run-backend     # http://localhost:8000/docs
make run-dashboard   # http://localhost:8501
```

### Env
Copy `configs/.env.example` to `.env` (root). Defaults use SQLite in project root.

### What’s unique
- **Auction-language alpha**: flags phrases like "sorted twice", "no implants" as quality signals.
- **Choice–Select spread driver**: built-in signal rule to trigger “Axe-style” pairs (TSN vs MCD).
- **Water/visa overlays (hooks)**: ready-made columns to fuse water-rights, H‑2A visa, and weather into pricing context ahead of USDA lag.
