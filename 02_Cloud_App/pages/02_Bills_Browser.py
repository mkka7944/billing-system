import streamlit as st
import pandas as pd
import plotly.express as px
from services import auth, repository
from components import sidebar, data_grid

# --- Setup ---
st.set_page_config(page_title="Bills Browser", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("🧾 Bills Browser")

# --- Filters ---
with st.expander("🔎 Advanced Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    status_filter = c1.multiselect("Payment Status", ["PAID", "UNPAID", "ARREARS"], default=["PAID", "UNPAID"])
    # Future: Date range picker logic here
    
# --- Data ---
with st.spinner("Loading bills..."):
    # Construct filters
    filters = {}
    # Repo currently supports simple equality. For 'IN' or range, we might filter in Pandas or extend repo.
    # For now, fetch all and filter in Pandas for robustness of 'IN' logic without complex repository code yet
    df = repository.fetch_data("bills")

if not df.empty:
    # Apply Python-side filtering for complex logic not yet in generic repo
    if status_filter:
        df = df[df['payment_status'].isin(status_filter)]
        
    # --- Analytics for filtered view ---
    st.markdown("### Snapshot")
    m1, m2, m3 = st.columns(3)
    m1.metric("Visible Records", len(df))
    m2.metric("Total Due", f"PKR {df['amount_due'].sum():,.0f}")
    m3.metric("Avg Amount", f"PKR {df['amount_due'].mean():,.0f}")

    # --- Grid ---
    st.subheader("Bill Records")
    selected = data_grid.display_aggrid(df, selection_mode="multiple")
    
    if selected:
        st.write(f"Selected {len(selected)} bills")
        # Add 'Action' buttons here later (e.g. "Mark Paid")

else:
    st.info("No bills found matching criteria.")
