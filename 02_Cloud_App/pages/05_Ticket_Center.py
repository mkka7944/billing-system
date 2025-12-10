import streamlit as st
import pandas as pd
from services import auth, repository, db
from components import sidebar, data_grid

st.set_page_config(page_title="Ticket Center", layout="wide")
sidebar.render_sidebar()
auth.require_auth()

st.title("🎫 Ticket Center")

# --- Stats ---
df = repository.fetch_data("tickets")
if not df.empty:
    c1, c2 = st.columns(2)
    c1.metric("Pending", len(df[df['status'] == 'OPEN']))
    c2.metric("Closed/Resolved", len(df[df['status'].isin(['APPROVED', 'REJECTED', 'CLOSED'])]))

# --- Data Grid ---
st.subheader("My Tickets")

if not df.empty:
    # Use existing AgGrid logic
    selected_rows = data_grid.display_aggrid(df, selection_mode="multiple")
    
    if selected_rows:
        st.markdown("### Actions")
        col1, col2 = st.columns(2)
        
        ticket_ids = [row['ticket_id'] for row in selected_rows]
        
        if col1.button("✅ Approve Selected", use_container_width=True):
            try:
                db.supabase.table('tickets').update({'status': 'APPROVED'}).in_('ticket_id', ticket_ids).execute()
                st.toast("Tickets Approved!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if col2.button("🚫 Reject Selected", use_container_width=True):
            try:
                db.supabase.table('tickets').update({'status': 'REJECTED'}).in_('ticket_id', ticket_ids).execute()
                st.toast("Tickets Rejected!", icon="⚠️")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("No tickets to display.")
