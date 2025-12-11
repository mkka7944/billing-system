import streamlit as st
from services import auth, repository
from components import sidebar, data_grid

st.set_page_config(page_title="Survey Units", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("🏠 Survey Units Registry")

df = repository.fetch_data("survey_units")

if not df.empty:
    st.caption(f"Total Units: {len(df)}")
    data_grid.display_aggrid(df)
else:
    st.warning("No survey unit data found.")
