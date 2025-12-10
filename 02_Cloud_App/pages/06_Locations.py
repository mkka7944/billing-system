import streamlit as st
from services import auth, repository
from components import sidebar, data_grid

st.set_page_config(page_title="Locations", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("📍 Operating Locations (Tehsils)")

df = repository.fetch_data("unique_locations")

if not df.empty:
    st.caption(f"Service Areas: {len(df)}")
    data_grid.display_aggrid(df)
else:
    st.warning("No locations found.")
