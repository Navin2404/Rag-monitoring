# dashboard.py
# Ella metrics-um graphs-ah kaaturom
# streamlit run dashboard.py --server.port 8502

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.database.db import get_all_traces, get_summary_stats
from src.monitoring.metrics import get_latency_metrics, get_cost_metrics, get_quality_metrics

st.set_page_config(page_title="📊 Monitoring Dashboard", layout="wide")
st.title("📊 RAG Monitoring Dashboard")
st.caption("Real-time observability for your RAG system")

# Auto refresh every 30 seconds
st.markdown("🔄 Auto-refreshes every 30s")

# ─── HEADER METRICS ───
stats = get_summary_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Queries", stats.get("total_queries", 0))
with col2:
    avg_lat = stats.get("avg_latency", 0)
    st.metric("Avg Latency", f"{avg_lat:.0f}ms" if avg_lat else "N/A")
with col3:
    total_cost = stats.get("total_cost", 0)
    st.metric("Total Cost", f"${total_cost:.4f}" if total_cost else "$0")
with col4:
    avg_q = stats.get("avg_quality", 0)
    st.metric("Avg Quality", f"{avg_q:.2f}" if avg_q else "N/A")
with col5:
    err_rate = stats.get("error_rate", 0)
    st.metric("Error Rate", f"{err_rate:.1f}%", delta_color="inverse")

st.divider()

# ─── LATENCY SECTION ───
st.subheader("⏱ Latency Analysis")

lat_metrics = get_latency_metrics()

if lat_metrics:
    col1, col2, col3 = st.columns(3)

    with col1:
        total = lat_metrics.get("total", {})
        st.markdown("**Total Latency**")
        # p50, p95 kaattu - ithuthaan interview-la impress panrathu
        st.metric("p50", f"{total.get('p50', 0):.0f}ms")
        st.metric("p95", f"{total.get('p95', 0):.0f}ms",
                  help="95% of requests intha time-la mudiyum")

    with col2:
        ret = lat_metrics.get("retrieval", {})
        st.markdown("**Retrieval Latency**")
        st.metric("p50", f"{ret.get('p50', 0):.0f}ms")
        st.metric("p95", f"{ret.get('p95', 0):.0f}ms")

    with col3:
        gen = lat_metrics.get("generation", {})
        st.markdown("**Generation Latency**")
        st.metric("p50", f"{gen.get('p50', 0):.0f}ms")
        st.metric("p95", f"{gen.get('p95', 0):.0f}ms")

# ─── LATENCY OVER TIME GRAPH ───
traces = get_all_traces(100)

if traces:
    df = pd.DataFrame(traces)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Latency line chart
    fig_latency = px.line(
        df, x="timestamp", y="total_latency_ms",
        title="Latency Over Time (ms)",
        labels={"total_latency_ms": "Latency (ms)", "timestamp": "Time"}
    )
    fig_latency.add_hline(
        y=df["total_latency_ms"].quantile(0.95),
        line_dash="dash", line_color="red",
        annotation_text="p95"
    )
    st.plotly_chart(fig_latency, use_container_width=True)

    st.divider()

    # ─── COST SECTION ───
    st.subheader("💰 Cost Analysis")

    cost_metrics = get_cost_metrics()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${cost_metrics.get('total_cost_usd', 0):.4f}")
    with col2:
        st.metric("Avg per Query", f"${cost_metrics.get('avg_cost_per_query', 0):.6f}")
    with col3:
        st.metric("Est. Monthly", f"${cost_metrics.get('estimated_monthly', 0):.2f}")

    # Cost bar chart
    fig_cost = px.bar(
        df.tail(20), x="timestamp", y="cost_usd",
        title="Cost per Query (Last 20 queries)",
        labels={"cost_usd": "Cost (USD)", "timestamp": "Time"}
    )
    st.plotly_chart(fig_cost, use_container_width=True)

    st.divider()

    # ─── QUALITY SECTION ───
    st.subheader("📊 Quality Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # Quality score distribution
        fig_quality = px.histogram(
            df, x="quality_score",
            title="Quality Score Distribution",
            nbins=10
        )
        st.plotly_chart(fig_quality, use_container_width=True)

    with col2:
        # Sentiment pie chart
        sentiment_counts = df["sentiment_label"].value_counts()
        fig_sentiment = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Query Sentiment Distribution"
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)

    st.divider()

    # ─── RECENT TRACES TABLE ───
    st.subheader("🔍 Recent Queries")

    display_cols = [
        "timestamp", "query", "total_latency_ms",
        "cost_usd", "quality_score", "sentiment_label", "status"
    ]

    st.dataframe(
        df[display_cols].head(20),
        use_container_width=True
    )