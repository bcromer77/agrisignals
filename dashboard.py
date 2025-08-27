'''import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --- Load env vars ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "agrisignals_db")
COLLECTION = "sources_collection"

# --- Connect to MongoDB ---
@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

client = init_connection()
db = client[MONGO_DB]
collection = db[COLLECTION]

# --- Streamlit App ---
st.set_page_config(page_title="AgriSignals Dashboard", layout="wide")
st.title("🌾 AgriSignals – Labor, Water & Commodity Risk Dashboard")

# --- Load Data ---
@st.cache_data(ttl=300)
def load_data(limit=5000):
    """Load data from MongoDB with caching"""
    docs = list(collection.find().limit(limit))
    df = pd.DataFrame(docs)
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)
    return df

# Load main dataset
df = load_data()

if df.empty:
    st.warning("⚠️ No data found in MongoDB. Run ingestion pipeline first:")
    st.code("python scripts/agrisignals_ingestion.py")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filters")

# Get unique values for filters
states = sorted(df["state"].dropna().unique()) if "state" in df.columns else []
commodities = sorted(df["commodity"].dropna().unique()) if "commodity" in df.columns else []

state_filter = st.sidebar.multiselect("State", states, default=[])
commodity_filter = st.sidebar.multiselect("Commodity", commodities, default=[])
priority_min = st.sidebar.slider("Minimum Priority Score", 0.0, 10.0, 7.0, 0.5)

# Apply filters
filtered = df.copy()
if state_filter:
    filtered = filtered[filtered["state"].isin(state_filter)]
if commodity_filter:
    filtered = filtered[filtered["commodity"].isin(commodity_filter)]
if "priority_score" in filtered.columns:
    filtered = filtered[filtered["priority_score"] >= priority_min]

# --- Summary Stats ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sources", len(df))
with col2:
    labor_count = len(df[df["commodity"] == "Labor"]) if "commodity" in df.columns else 0
    st.metric("Labor Sources", labor_count)
with col3:
    water_count = len(df[df["commodity"] == "Water"]) if "commodity" in df.columns else 0
    st.metric("Water Sources", water_count)
with col4:
    if "priority_score" in df.columns:
        avg_priority = df["priority_score"].mean()
        st.metric("Avg Priority", f"{avg_priority:.1f}")
    else:
        st.metric("Avg Priority", "N/A")

# --- Labor Stress Visualization ---
st.subheader("👷 H-2A / H-2B Labor Stress Analysis")

labor_data = df[df["commodity"] == "Labor"].copy() if "commodity" in df.columns else pd.DataFrame()

if not labor_data.empty:
    # Check if we have structured labor data
    if "certification_rate" in labor_data.columns:
        # Convert to numeric
        labor_data["certification_rate"] = pd.to_numeric(labor_data["certification_rate"], errors="coerce")
        
        # State-level aggregation
        state_labor = labor_data.groupby("state").agg({
            "certification_rate": "mean",
            "workers_requested": "sum",
            "workers_certified": "sum"
        }).reset_index()
        
        # Choropleth map
        fig = px.choropleth(
            state_labor,
            locations="state",
            locationmode="USA-states",
            color="certification_rate",
            scope="usa",
            hover_data=["workers_requested", "workers_certified"],
            color_continuous_scale="RdYlGn",
            title="H-2 Visa Certification Rates by State"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top employers table
        st.subheader("📊 Top Employers by Worker Requests")
        if "employer" in labor_data.columns:
            employer_summary = labor_data.groupby("employer").agg({
                "workers_requested": "sum",
                "workers_certified": "sum",
                "certification_rate": "mean"
            }).reset_index().sort_values("workers_requested", ascending=False)
            
            st.dataframe(
                employer_summary.head(15),
                column_config={
                    "workers_requested": st.column_config.NumberColumn("Workers Requested"),
                    "workers_certified": st.column_config.NumberColumn("Workers Certified"),
                    "certification_rate": st.column_config.NumberColumn("Cert Rate", format="%.1%")
                }
            )
    else:
        st.info("📋 Labor data found but no structured certification rates available yet.")
        st.dataframe(labor_data[["state", "source_id", "scraped_content"]].head(10))
else:
    st.info("🔍 No labor data found. Make sure labor_alpha_sources.json is ingested.")

# --- Water Risk Visualization ---
st.subheader("💧 Colorado River & Water Risk Signals")

water_data = df[df["commodity"] == "Water"].copy() if "commodity" in df.columns else pd.DataFrame()

if not water_data.empty:
    # Risk score distribution
    if "priority_score" in water_data.columns:
        fig = px.histogram(
            water_data, 
            x="priority_score", 
            title="Water Risk Score Distribution",
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent water alerts
    st.subheader("🚨 Recent Water Risk Alerts")
    if "ingest_date" in water_data.columns:
        water_data["ingest_date"] = pd.to_datetime(water_data["ingest_date"], errors="coerce")
        recent_water = water_data.sort_values("ingest_date", ascending=False).head(10)
    else:
        recent_water = water_data.head(10)
    
    for _, row in recent_water.iterrows():
        with st.expander(f"🌊 {row.get('source_id', 'Water Alert')} - {row.get('state', 'Unknown')}"):
            st.write(f"**Priority Score:** {row.get('priority_score', 'N/A')}")
            st.write(f"**Content:** {row.get('scraped_content', 'No content available')[:500]}...")
            st.write(f"**URL:** {row.get('url', 'No URL')}")
else:
    st.info("🔍 No water data found. Make sure water_alpha_sources.json is ingested.")

# --- Composite Risk Analysis ---
st.subheader("⚡ Composite Risk Analysis")

if not labor_data.empty and not water_data.empty:
    # Calculate composite risk by state
    labor_risk = labor_data.groupby("state")["priority_score"].mean() if "priority_score" in labor_data.columns else pd.Series()
    water_risk = water_data.groupby("state")["priority_score"].mean() if "priority_score" in water_data.columns else pd.Series()
    
    if not labor_risk.empty and not water_risk.empty:
        composite_risk = pd.DataFrame({
            "state": labor_risk.index.union(water_risk.index),
            "labor_risk": labor_risk.reindex(labor_risk.index.union(water_risk.index), fill_value=0),
            "water_risk": water_risk.reindex(labor_risk.index.union(water_risk.index), fill_value=0)
        })
        composite_risk["composite_score"] = (composite_risk["labor_risk"] + composite_risk["water_risk"]) / 2
        composite_risk = composite_risk.sort_values("composite_score", ascending=False)
        
        # Display top risk states
        st.dataframe(
            composite_risk.head(10),
            column_config={
                "labor_risk": st.column_config.NumberColumn("Labor Risk", format="%.1f"),
                "water_risk": st.column_config.NumberColumn("Water Risk", format="%.1f"),
                "composite_score": st.column_config.NumberColumn("Composite Risk", format="%.1f")
            }
        )

# --- Time Series Analysis ---
if "ingest_date" in df.columns:
    st.subheader("📈 Risk Trends Over Time")
    
    df["ingest_date"] = pd.to_datetime(df["ingest_date"], errors="coerce")
    
    if "priority_score" in df.columns:
        # Daily average priority scores
        daily_risk = df.groupby([df["ingest_date"].dt.date, "commodity"])["priority_score"].mean().reset_index()
        daily_risk.columns = ["date", "commodity", "avg_priority"]
        
        fig = px.line(
            daily_risk, 
            x="date", 
            y="avg_priority", 
            color="commodity",
            title="Average Priority Scores by Commodity Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Semantic Search ---
st.subheader("🔍 Semantic Search")
search_query = st.text_input("Search signals (e.g., 'California citrus labor shortage')")

if search_query:
    if "scraped_content" in df.columns:
        # Simple text search (could be enhanced with vector similarity)
        search_results = df[
            df["scraped_content"].str.contains(search_query, case=False, na=False)
        ].head(10)
        
        if not search_results.empty:
            st.write(f"Found {len(search_results)} results:")
            for _, row in search_results.iterrows():
                with st.expander(f"🔍 {row.get('source_id', 'Result')} - {row.get('state', 'Unknown')}"):
                    st.write(f"**Commodity:** {row.get('commodity', 'N/A')}")
                    st.write(f"**Priority:** {row.get('priority_score', 'N/A')}")
                    st.write(f"**Content:** {row.get('scraped_content', '')[:300]}...")
                    st.write(f"**URL:** {row.get('url', 'No URL')}")
        else:
            st.info("No results found for your search query.")

# --- High Priority Alerts ---
st.subheader("🚨 High-Priority Alerts")

if "priority_score" in df.columns:
    high_priority = filtered[filtered["priority_score"] > 9.0]
    
    if not high_priority.empty:
        for _, row in high_priority.iterrows():
            st.error(
                f"**{row.get('source_id', 'Alert')}** ({row.get('state', 'Unknown')}) - "
                f"{row.get('commodity', 'Unknown')} | Priority: {row.get('priority_score', 'N/A')}\\n\\n"
                f"{row.get('scraped_content', 'No content')[:200]}...\\n\\n"
                f"🔗 {row.get('url', 'No URL')}"
            )
    else:
        st.success("✅ No high-priority alerts currently triggered.")

# --- Footer ---
st.markdown("---")
st.markdown("🌾 **AgriSignals** - Early warning system for agricultural commodity risks")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
'''

# Save the file
with open('dashboard.py', 'w') as f:
    f.write(dashboard_code)

print("✅ Created complete dashboard.py")
print("File size:", len(dashboard_code), "characters")
