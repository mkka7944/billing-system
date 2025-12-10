import streamlit as st

def kpi_card(title, value, delta=None, color="normal"):
    """
    Renders a nice KPI card.
    """
    st.metric(label=title, value=value, delta=delta)
