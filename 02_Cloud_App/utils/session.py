"""
Session management utilities for the billing system.
Provides session timeout and refresh functionality.
"""
import streamlit as st
import time
from datetime import datetime, timedelta

# Session timeout duration (30 minutes)
SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds

def init_session():
    """
    Initialize session state variables for session management.
    """
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = time.time()

def update_last_activity():
    """
    Update the last activity timestamp.
    """
    st.session_state["last_activity"] = time.time()

def is_session_expired():
    """
    Check if the session has expired based on inactivity.
    
    Returns:
        bool: True if session expired, False otherwise
    """
    if "last_activity" not in st.session_state:
        return False
    
    elapsed_time = time.time() - st.session_state["last_activity"]
    return elapsed_time > SESSION_TIMEOUT

def check_session_timeout():
    """
    Check session timeout and logout if expired.
    This should be called at the beginning of each page.
    """
    init_session()
    
    if is_session_expired():
        # Session expired, logout user
        st.warning("Your session has expired due to inactivity. Please log in again.")
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.stop()

def get_session_duration():
    """
    Get the duration of the current session.
    
    Returns:
        int: Number of seconds since last activity
    """
    if "last_activity" not in st.session_state:
        return 0
    
    return int(time.time() - st.session_state["last_activity"])

def format_session_time(seconds):
    """
    Format seconds into a human-readable time string.
    
    Args:
        seconds (int): Number of seconds
        
    Returns:
        str: Formatted time string (e.g., "5m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"