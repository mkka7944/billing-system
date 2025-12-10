import streamlit as st
import pandas as pd
from services import auth, repository
from components import sidebar, data_grid
from services.db import supabase

st.set_page_config(page_title="Staff Manager", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("👥 Staff Management")

# --- Actions ---
with st.expander("➕ Add New Staff Member"):
    with st.form("new_staff_form"):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full Name")
        username = c2.text_input("Username")
        password = c1.text_input("Password", type="password") # Simple for now
        role = c2.selectbox("Role", ["admin", "surveyor", "manager"], index=1)
        city = st.text_input("Assigned City (District)")
        
        submitted = st.form_submit_button("Create Account")
        if submitted:
            if username and password:
                try:
                    res = repository.upsert_record("staff", {
                        "username": username,
                        "password": password,
                        "full_name": full_name,
                        "role": role,
                        "assigned_city": city,
                        "is_active": True
                    })
                    st.success("Staff member added successfully!")
                    st.rerun() # Refresh grid
                except Exception as e:
                    st.error(f"Error creating staff: {e}")
            else:
                st.warning("Username and Password are required.")

st.markdown("---")

# --- List ---
st.subheader("Staff Directory")
df = repository.fetch_data("staff", columns="id, full_name, username, role, assigned_city, is_active, created_at")

if not df.empty:
    selected = data_grid.display_aggrid(df, selection_mode="single")
    
    if selected:
        user = selected[0]
        st.info(f"Selected: {user['full_name']}")
        # Future: Edit/Delete buttons
else:
    st.info("No staff records found.")
