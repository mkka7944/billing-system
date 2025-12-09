# components/auth.py
import streamlit as st

def is_authenticated():
    """Checks if a user is logged in."""
    return st.session_state.get("logged_in", False)

def is_admin():
    """Checks if the logged-in user has an admin role."""
    return st.session_state.get("user_role") in ["HEAD", "MANAGER"]

def is_head_admin():
    """Checks for the highest-level admin for user management."""
    return st.session_state.get("user_role") == "HEAD"

def enforce_auth(admin_only=False, head_admin_only=False):
    """A guard function to place at the top of each page."""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
    if admin_only and not is_admin():
        st.warning("⛔ Access Denied: This page is for administrators only.")
        st.stop()
    if head_admin_only and not is_head_admin():
        st.warning("⛔ Access Denied: This page requires Head Admin privileges.")
        st.stop()