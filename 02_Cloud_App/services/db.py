import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load env vars primarily here to be safe, though Home.py does it too.
load_dotenv()

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client using singleton pattern via st.cache_resource.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        # Graceful error handling
        st.error("❌ Configuration Error: SUPABASE_URL or SUPABASE_KEY is missing.")
        st.stop()
        
    return create_client(url, key)

# Expose a ready-to-use instance
supabase = get_supabase_client()
