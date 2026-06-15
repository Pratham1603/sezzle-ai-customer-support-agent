import streamlit as st
import requests
import pandas as pd

API_URL = "https://harerpratham-sezzle-ai-customer-support-agent.hf.space/analytics"

st.set_page_config(
    page_title="Sezzle AI Dashboard",
    layout="wide"
)

st.title("📊 Sezzle AI Support Analytics Dashboard")

# Fetch data
def fetch_data():
    try:
        res = requests.get(API_URL)
        return res.json()
    except:
        return None

data = fetch_data()

if not data:
    st.error("❌ Cannot connect to FastAPI. Make sure server is running.")
    st.stop()

# =========================
# KPI Cards
# =========================

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Conversations", data["total_conversations"])
col2.metric("Refund Requests", data["refund_requests"])
col3.metric("Cancel Orders", data["cancel_orders"])
col4.metric("Order Status", data["order_status_requests"])
col5.metric("Escalations", data["escalations"])
col6.metric("AI Confidence", f"{data['avg_confidence']:.2f}")

st.divider()

# =========================
# Simple Insights
# =========================

st.subheader("📌 Quick Insights")

total = data["total_conversations"]
esc = data["escalations"]

if total > 0:
    escalation_rate = (esc / total) * 100
    st.write(f"⚠️ Escalation Rate: **{escalation_rate:.2f}%**")
else:
    st.write("No data yet.")

st.divider()

st.subheader("📊 Intent Distribution")

intent_df = pd.DataFrame(
    list(data["intent_distribution"].items()),
    columns=["Intent", "Count"]
)

st.bar_chart(
    intent_df.set_index("Intent")
)

st.dataframe(intent_df)

st.divider()

st.subheader("💬 Recent Conversations")

recent = requests.get(
    "https://harerpratham-sezzle-ai-customer-support-agent.hf.space/recent-conversations"
).json()

recent_df = pd.DataFrame(recent)

st.dataframe(
    recent_df,
    use_container_width=True
)

st.divider()

st.subheader("📈 Daily Conversation Trend")

trend_data = requests.get(
    "https://harerpratham-sezzle-ai-customer-support-agent.hf.space/daily-trends"
).json()

trend_df = pd.DataFrame(trend_data)

if not trend_df.empty:

    trend_df = trend_df.set_index("date")

    st.line_chart(trend_df)

else:
    st.info("No trend data available yet.")