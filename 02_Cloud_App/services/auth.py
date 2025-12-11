import streamlit as st
from services.db import supabase
import time
from utils.security import verify_password
from utils.session import init_session

def login(username, password):
    """
    Authenticates the user against the 'staff' table.
    Returns: True if successful, False otherwise.
    """
    try:
        # First, get the user by username to retrieve the hashed password
        user_response = supabase.table("staff").select("*").eq("username", username).single().execute()
        
        user = user_response.data
        # Check password against the 'password' field (which should contain the hashed password)
        if user and verify_password(password, user.get('password', '')):
            # Password is correct
            
            if not user.get('is_active', True):
                st.error("🚫 Account is inactive. Please contact support.")
                return False

            # Set Session State
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user['id']
            st.session_state["user_role"] = user.get('role', 'staff')
            st.session_state["user_name"] = user.get('full_name', 'User')
            st.session_state["assigned_city"] = user.get('assigned_city')
            
            # Initialize session management
            init_session()
            
            # Persist role for UI logic
            st.toast(f"Welcome back, {user.get('full_name')}!", icon="👋")
            time.sleep(1) # Visual feedback
            return True
        else:
            st.error("Invalid username or password.")
            return False
            
    except Exception as e:
        # In a real app check for specific error codes (e.g. JSONDecodeError means no rows found usually)
        st.error(f"Login failed: Invalid credentials or connection error.")
        return False

def logout():
    """Clears session and reloads."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_current_user():
    """Returns user dict from session if logged in."""
    if not st.session_state.get("logged_in"):
        return None
    return {
        "id": st.session_state.get("user_id"),
        "name": st.session_state.get("user_name"),
        "role": st.session_state.get("user_role"),
        "city": st.session_state.get("assigned_city")
    }

def require_auth():
    """Stops execution if not logged in and shows login form."""
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to access this page.")
        # Ensure we don't switch pages here, just stop rendering content
        # Ideally the sidebar logic handles redirection or hiding
        st.stop()