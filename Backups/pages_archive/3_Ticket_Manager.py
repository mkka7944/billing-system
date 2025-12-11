# pages/3_Ticket_Manager.py
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from components.auth import enforce_auth
from components.db import supabase

enforce_auth(admin_only=True)

st.title("🎫 Ticket Manager")

# --- Fetch Data ---
try:
    tickets_res = supabase.table('tickets').select('*, staff:reported_by_staff_id(full_name)').order('created_at', desc=True).execute()
    # Use json_normalize to flatten the nested 'staff' data
    df_tickets = pd.json_normalize(tickets_res.data, sep='_')
except Exception as e:
    st.error(f"Could not load tickets: {e}")
    df_tickets = pd.DataFrame() # Ensure df_tickets is an empty dataframe on error

# --- AgGrid Display ---
# FIX: Check if the dataframe is empty before building the grid
if not df_tickets.empty:
    gb = GridOptionsBuilder.from_dataframe(df_tickets)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()
    # Add other configurations as needed
    gridOptions = gb.build()

    st.info("Select tickets from the grid and use the buttons below to approve or reject them.")
    grid_response = AgGrid(df_tickets, gridOptions=gridOptions, enable_enterprise_modules=False, update_mode='MODEL_CHANGED', height=500, fit_columns_on_grid_load=True)

    selected_rows = grid_response['selected_rows']

    # --- Admin Actions ---
    if selected_rows:
        st.subheader("Admin Actions")
        action_cols = st.columns(2)
        if action_cols[0].button("Approve Selected", type="primary"):
            ticket_ids = [row['ticket_id'] for row in selected_rows]
            supabase.table('tickets').update({'status': 'APPROVED'}).in_('ticket_id', ticket_ids).execute()
            st.success("Tickets approved!"); st.rerun()
        
        if action_cols[1].button("Reject Selected"):
            ticket_ids = [row['ticket_id'] for row in selected_rows]
            supabase.table('tickets').update({'status': 'REJECTED'}).in_('ticket_id', ticket_ids).execute()
            st.warning("Tickets rejected!"); st.rerun()
else:
    st.success("✅ No pending tickets found.")