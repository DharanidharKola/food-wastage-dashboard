# fw_app.py - Streamlit PostgreSQL Dashboard
# Run with: streamlit run fw_app.py

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
import plotly.express as px

# -------------------------
# Streamlit Page Config
# -------------------------
st.set_page_config(page_title="🍽️ Food Wastage Dashboard", layout="wide")

# -------------------------
# Database Connection
# -------------------------
USER = "postgres"
PASSWORD = "2322"   # <-- replace with your pgAdmin password
HOST = "localhost"
PORT = "5432"
DBNAME = "food_wastage"

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

engine = create_engine(DATABASE_URL)

# -------------------------
# Query Options
# -------------------------
queries = {
    "🔢 Total Rows": "SELECT COUNT(*) AS total_rows FROM food_wastage;",
    "📄 Sample Data (10 rows)": "SELECT * FROM food_wastage LIMIT 10;",
    "📊 KPI Summary": "SELECT * FROM v_fw_kpis;",
    "🏙️ Providers by City": "SELECT * FROM v_fw_providers_by_city;",
    "⏳ Near Expiry (Next 3 Days)": "SELECT * FROM v_fw_near_expiry;",
    "📈 Completed Claims by Day": "SELECT * FROM v_fw_completed_by_day;",
    "🏆 Top 10 Providers by Quantity": """
        SELECT Provider_ID, Name, City, SUM(Quantity) AS total_qty
        FROM food_wastage
        GROUP BY Provider_ID, Name, City
        ORDER BY total_qty DESC
        LIMIT 10;
    """,
    "🍱 Food Type Ranking": """
        SELECT Food_Type, SUM(Quantity) AS total_qty, COUNT(*) AS claims
        FROM food_wastage
        GROUP BY Food_Type
        ORDER BY total_qty DESC;
    """,
    "📍 Receivers by City": """
        SELECT City_receiver, COUNT(*) AS claim_count
        FROM food_wastage
        GROUP BY City_receiver
        ORDER BY claim_count DESC;
    """,
    "📅 Avg Days to Expiry at Claim": """
        SELECT AVG(Expiry_Date - DATE(Timestamp)) AS avg_days_to_expiry
        FROM food_wastage
        WHERE Expiry_Date IS NOT NULL AND Timestamp IS NOT NULL;
    """,
    "❌ Cancellation Rate %": """
        SELECT ROUND(100.0 * SUM(CASE WHEN Status='Cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) 
        AS cancellation_rate_pct
        FROM food_wastage;
    """
}

# -------------------------
# Streamlit Sidebar
# -------------------------
st.sidebar.header("📌 Choose a Query")
selected_query = st.sidebar.selectbox("Select a query to run:", list(queries.keys()))

# -------------------------
# Run Query
# -------------------------
st.subheader(f"Results: {selected_query}")

try:
    with engine.connect() as conn:
        df = pd.read_sql(text(queries[selected_query]), conn)

    st.dataframe(df, use_container_width=True)

    # -------------------------
    # Auto Charts (where applicable)
    # -------------------------
    if "City" in df.columns and "provider_count" in df.columns:
        fig = px.bar(df, x="City", y="provider_count", title="Providers by City", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    elif "Food_Type" in df.columns and "total_qty" in df.columns:
        fig = px.pie(df, names="Food_Type", values="total_qty", title="Food Type Distribution")
        st.plotly_chart(fig, use_container_width=True)

    elif "claim_date" in df.columns and "completed_count" in df.columns:
        fig = px.line(df, x="claim_date", y="completed_count", title="Completed Claims Over Time")
        st.plotly_chart(fig, use_container_width=True)

    elif "City_receiver" in df.columns and "claim_count" in df.columns:
        fig = px.bar(df, x="City_receiver", y="claim_count", title="Receivers by City", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    elif "Name" in df.columns and "total_qty" in df.columns:
        fig = px.bar(df, x="Name", y="total_qty", color="City", title="Top 10 Providers by Quantity", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error running query: {e}")
