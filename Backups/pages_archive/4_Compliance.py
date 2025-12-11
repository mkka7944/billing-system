# pages/4_Compliance.py
import streamlit as st
import pandas as pd
from streamlit_image_select import image_select
from components.auth import enforce_auth, is_admin
from components.db import supabase

enforce_auth()

st.title("📸 Compliance & Field Visits")

# Separate views for different roles
if is_admin():
    st.subheader("Review Recent Visits")
    visits_res = supabase.table('compliance_visits').select('*').order('created_at', desc=True).limit(20).execute()
    visits = visits_res.data
    
    if visits:
        img = image_select(
            label="Select a visit photo to review",
            images=[v['image_drive_id'] for v in visits if v.get('image_drive_id')],
            captions=[f"Visit on {v['visit_date']}" for v in visits if v.get('image_drive_id')]
        )
else:
    st.subheader("Log a New Visit")
    # This requires setting up image hosting (e.g., Supabase Storage)
    # For now, this is a placeholder for the camera input component
    st.warning("Image upload and camera functionality to be implemented.")
    st.camera_input("Capture Proof of Visit")