import streamlit as st
import pandas as pd
import plotly.express as px
from services import auth, repository
from components import metrics, sidebar

# --- Setup ---
st.set_page_config(page_title="Dashboard", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("📊 Executive Dashboard")

# --- Data Fetching ---
with st.spinner("Refreshing analytics..."):
    # Fetch high-level stats (could be optimized with RPC calls in Supabase)
    # For now, fetching full tables for prototype, restrict columns for perf in prod
    bills_df = repository.fetch_data("bills", columns="id, payment_status, amount_due, created_at")
    staff_df = repository.fetch_data("staff", columns="id, is_active")
    tickets_df = repository.fetch_data("tickets", columns="ticket_id, status")
    
# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    metrics.kpi_card("Total Bills", len(bills_df))
with col2:
    rev = bills_df[bills_df['payment_status'] == 'PAID']['amount_due'].sum() if not bills_df.empty else 0
    metrics.kpi_card("Revenue Collected", f"PKR {rev:,.0f}")
with col3:
    pending = len(tickets_df[tickets_df['status'] == 'OPEN']) if not tickets_df.empty else 0
    metrics.kpi_card("Open Tickets", pending, delta=f"{pending} active", color="inverse")
with col4:
    active_staff = len(staff_df[staff_df['is_active']]) if not staff_df.empty else 0
    metrics.kpi_card("Active Staff", active_staff)

st.markdown("---")

# --- Charts ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("💵 Payment Status")
    if not bills_df.empty:
        status_counts = bills_df['payment_status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_pie = px.pie(status_counts, values='Count', names='Status', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No billing data.")

with c2:
    st.subheader("🎫 Ticket Summary")
    if not tickets_df.empty:
        ticket_counts = tickets_df['status'].value_counts().reset_index()
        ticket_counts.columns = ['Status', 'Count']
        fig_bar = px.bar(ticket_counts, x='Status', y='Count', color='Status')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No ticket data.")

st.subheader("Recent Activity")
st.caption("Real-time feed of system events.")
# Placeholder for activity feed
st.text("• System initialization complete.")
