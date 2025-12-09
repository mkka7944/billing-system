# Home.py
import streamlit as st
from dotenv import load_dotenv
import time

# --- CRITICAL: Load environment variables at the very start ---
load_dotenv()

# Now we can import our components that rely on those variables
from components.db import supabase

# --- Page Config & State ---
st.set_page_config(page_title="Suthra Punjab Login", layout="centered")
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- Auth Logic (Unchanged) ---
def login(username, password):
    try:
        user = supabase.table("staff").select("*").eq("username", username).eq("password", password).single().execute().data
        if user and user['is_active']:
            st.session_state.update({
                "logged_in": True, "user_id": user['id'], "user_role": user.get('role'),
                "user_name": user.get('full_name'), "assigned_city": user.get('assigned_city'),
                "assigned_ucs": user.get('assigned_ucs', [])
            })
            st.rerun()
        else:
            st.error("Account locked or invalid credentials.")
    except Exception:
        st.error("Invalid credentials.")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- UI Rendering (Unchanged) ---
if not st.session_state["logged_in"]:
    st.title("🇵🇰 Suthra Punjab Operations")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log In", use_container_width=True, type="primary"):
            login(username, password)
    st.stop()

# --- Logged-in Welcome ---
st.title(f"Welcome, {st.session_state['user_name']}!")
st.sidebar.button("Logout", on_click=logout, use_container_width=True)
st.info("Please use the navigation panel on the left to access the system modules.")