import os, requests
from datetime import datetime
import streamlit as st

API_BASE = os.getenv("API_BASE","http://localhost:8000")

st.set_page_config(page_title="Agrisignals — Horizon Scanner", layout="wide")
st.title("🛰️ Horizon Scanner")

with st.sidebar:
    st.header("Controls")
    state  = st.selectbox("State", ["California","Texas","Florida","Kansas","Nebraska","Hawaii"], index=0)
    county = st.text_input("County", "Fresno")
    run_now = st.button("Run scan for county")

def get(path: str, **params):
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

colA, colB = st.columns([2,3], gap="large")

with colA:
    st.subheader("Signals")
    if run_now:
        with st.spinner("Scanning…"):
            try:
                _ = get("/scanner/run", county=county, state=state)
            except Exception as e:
                st.error(f"Scan failed: {e}")

    try:
        sigs = get("/scanner/signals", county=county, state=state, limit=50)
        if not sigs:
            st.info("No signals yet. Click **Run scan for county**.")
        else:
            for s in sigs:
                title = f"{s.get('commodity','').upper()} — score {s.get('score',0):.2f}"
                if s.get('day'): title += f" • {s['day']}"
                with st.expander(title):
                    st.json(s.get("score_breakdown", {}))
    except Exception as e:
        st.error(f"Could not load signals: {e}")

with colB:
    st.subheader("Latest Sources")
    try:
        srcs = get("/scanner/sources", county=county, state=state, limit=30)
        if not srcs:
            st.info("No sources saved for this county yet.")
        else:
            for src in srcs:
                pub = src.get("published_at") or ""
                try:
                    pub = datetime.fromisoformat(pub).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                st.markdown(f"**[{src.get('title','(no title)')}]({src.get('url','#')})**  \n_{pub}_")
                if src.get("excerpt"):
                    txt = src["excerpt"]
                    st.caption(txt[:300] + ("…" if len(txt)>300 else ""))
                st.divider()
    except Exception as e:
        st.error(f"Could not load sources: {e}")
