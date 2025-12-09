# components/db.py
import streamlit as st
from supabase import create_client
import os

@st.cache_resource
def get_db_connection():
    """
    Initializes and returns the Supabase client.
    It reads the credentials from the environment, which should have been
    loaded by the main Home.py file.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    # This check is a safeguard. If the app is started incorrectly, it will fail gracefully.
    if not url or not key:
        st.error("Supabase credentials are not set. Please ensure your .env file is correct and the app is started from Home.py.")
        st.stop()
        
    return create_client(url, key)

# This line creates a single, cached instance of the Supabase client
# that all other pages can import and use.
supabase = get_db_connection()